"""Network Connection Management Module.

This module provides a comprehensive framework for establishing and managing
network connections to remote devices, with support for both secure SSH and
legacy Telnet protocols.

The module implements a connection hierarchy with an abstract base class and
concrete implementations for different connection types:

- Connection (ABC): Abstract base class defining the connection interface
- SSHConnection: Secure SSH connections using paramiko (recommended)
- TelnetConnection: Legacy telnet connections (deprecated)

Classes:
    Connection: Abstract base class for all connection types
    SSHConnection: Secure SSH connection implementation
    TelnetConnection: Legacy telnet connection (deprecated)

Example:
    Basic SSH connection usage:

    ```python
    from router_test_kit.connection import SSHConnection
    from router_test_kit.device import LinuxDevice

    # Create device and connection
    device = LinuxDevice(username="admin", password="password")
    conn = SSHConnection(timeout=30)

    # Connect and execute commands
    conn.connect(device, "192.168.1.1")
    result = conn.write_command("show version")
    conn.disconnect()
    ```

Security Notice:
    This module includes deprecated telnet functionality for backward compatibility.
    All new implementations should use SSHConnection for secure communications.
    Telnet support will be removed in a future major version.
"""

import logging
import re
import socket
import time
import warnings
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Union

import paramiko

# Suppress the telnetlib import-time DeprecationWarning (Python 3.11+).
# A per-instantiation warning is issued by TelnetConnection.__init__ instead,
# so users who only use SSH see no noise at all.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import telnetlib

from router_test_kit.device import Device

# ---------------------------------------------------------------------------
# Module-level guard decorators
# These are defined at module level so mypy can type-check them correctly.
# They operate on any Connection-like object via duck-typing (Any).
# ---------------------------------------------------------------------------

def _check_occupied(func: Callable[..., Any]) -> Callable[..., Any]:
    """Raise ConnectionRefusedError if the connection is already in use."""
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self._is_occupied:
            raise ConnectionRefusedError(
                "This connection is already in use. Please close the connections that use it first."
            )
        return func(self, *args, **kwargs)
    return wrapper


def _check_device_type(
    required_type: str, is_root: bool = False
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Raise if the connected device is the wrong type or the connection is inactive."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if self.destination_device.type != required_type:
                raise ValueError(
                    f"This method is available only for {required_type} devices, "
                    f'but the destination device is of type "{self.destination_device.type}".'
                )
            if not self.is_connected:
                raise ConnectionError("Device is not connected")
            if is_root and not self.is_root:
                raise PermissionError("Root privileges required to perform this action")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def _check_connection(func: Callable[..., Any]) -> Callable[..., Any]:
    """Raise ConnectionError if the connection is not active."""
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not self.is_connected:
            raise ConnectionError("Device is not connected")
        return func(self, *args, **kwargs)
    return wrapper

logger = logging.getLogger(__name__)


class Connection(ABC):
    """Abstract base class for network connections to remote devices.

    This class defines the interface that all connection implementations must follow.
    It provides common functionality for connection management including timeout handling,
    device association, and connection state tracking.

    The class includes decorators for ensuring connection exclusivity and device type
    validation, which are used by concrete implementations.

    Attributes:
        destination_device (Optional[Device]): The target device for this connection
        destination_ip (Optional[str]): IP address of the destination device
        timeout (int): Connection timeout in seconds (default: 10)
        prompt_symbol (Optional[str]): Expected command prompt symbol

    Private Attributes:
        _is_occupied (bool): Indicates if connection is in use by another process

    Example:
        This is an abstract class and cannot be instantiated directly.
        Use concrete implementations like SSHConnection:

        ```python
        conn = SSHConnection(timeout=30)
        conn.connect(device, "192.168.1.1")
        ```
    """

    def __init__(self, timeout: int = 10):
        """Initialize a new connection instance.

        Args:
            timeout: Connection timeout in seconds. Defaults to 10.

        Note:
            This is an abstract class and should not be instantiated directly.
            Use concrete implementations like SSHConnection or TelnetConnection.
        """
        self.destination_device: Optional[Device] = None
        self.destination_ip: Optional[str] = None
        self.resulting_telnet_connection: Optional[Any] = None
        self.timeout = timeout
        self._is_occupied = False
        self.prompt_symbol: Optional[str] = None

    @abstractmethod
    def connect(
        self, destination_device: "Device", destination_ip: str
    ) -> "Connection":
        """Establish a connection to the specified device.

        This method must be implemented by concrete connection classes to establish
        the actual network connection to the target device.

        Args:
            destination_device: The device object containing connection credentials
            destination_ip: IP address of the target device

        Returns:
            Connection: This connection instance for method chaining

        Raises:
            ConnectionAbortedError: If the connection cannot be established
            TimeoutError: If the connection attempt times out
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the remote device.

        This method must be implemented by concrete connection classes to properly
        close and clean up the network connection.

        Note:
            After calling this method, the connection object should not be used
            for further communication until connect() is called again.
        """
        pass

    @_check_occupied
    def write_command(
        self,
        command: str,
        expected_prompt_pattern: Optional[list[str]] = None,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Writes a command to the telnet connection and returns the response.

        This method sends a command to the device via the telnet connection, waits for a response, and then returns that response.
        The response is expected to end with a prompt symbol or match an expected pattern, which is specified by the `expected_prompt_pattern` parameter.

        Args:
            command (str): The command to be sent to the device.
            expected_prompt_pattern (Optional[List[str]]): A list of regex patterns that the response is expected to match. If None, the method waits for the prompt symbol. Defaults to None.
            timeout (Optional[int]): The maximum time to wait for a response, in seconds. If None, the method uses the default timeout. Defaults to None.

        Returns:
            Optional[str]: The response from the device, or None if there was no response.

        Raises:
            ConnectionError: If the telnet connection is not established.
        """
        self.flush()  # Make sure nothing is in the buffer

        if self.resulting_telnet_connection is not None:
            # If the command is a string, encode it to bytes first
            encoded_command: bytes = (
                command.encode("ascii") + b"\r"
                if hasattr(command, "encode")
                else command  # type: ignore[assignment]
            )
            self.resulting_telnet_connection.write(encoded_command)
            assert self.prompt_symbol is not None, "Prompt symbol is not defined."

            # "expect" can wait for multiple patterns
            if expected_prompt_pattern:
                response = self.resulting_telnet_connection.expect(
                    expected_prompt_pattern,
                    timeout or self.timeout,
                )[2]  # The third element of the tuple is the response
            # but "read_until", while only for one pattern (prompt_symbol), is more reliable
            else:
                response = self.resulting_telnet_connection.read_until(
                    self.prompt_symbol.encode("ascii"), timeout or self.timeout
                )
            response = response.decode("ascii") if response else None
        else:
            raise ConnectionError(
                "No connection object from Telnet found during write_command."
            )
        return response

    @_check_occupied
    def flush(self, time_interval: float = 0.1) -> None:
        """
        This method waits for a short period of time to allow any remaining data to arrive,
        then reads and discards all data that has arrived at the telnet connection.
        """
        try:
            time.sleep(time_interval)
            if self.resulting_telnet_connection is not None:
                self.resulting_telnet_connection.read_very_eager()
        except EOFError as eof:
            logger.error(
                f"EOFError. Usually something is wrong while loading the connection. | {eof}"
            )
            raise EOFError from eof

    @_check_occupied
    def flush_deep(self, time_interval: float = 0.1, retries_timeout: int = 60) -> None:
        """Flush the connection buffer until the prompt symbol is seen or timeout is reached.

        Args:
            time_interval: Seconds to wait between flush attempts. Defaults to 0.1.
            retries_timeout: Total seconds to wait before giving up. 0 means no limit.

        Raises:
            TimeoutError: If the prompt is not seen within retries_timeout seconds.
        """
        logger.debug("Deep flushing ...")
        end_pattern = f"{self.prompt_symbol}"
        if retries_timeout > 0:
            start_time = time.time()
        while True:
            response = self.write_command("\n", timeout=time_interval)
            if response is not None and end_pattern in response.strip():
                break
            if retries_timeout > 0 and time.time() - start_time > retries_timeout:
                raise TimeoutError("Timeout while flushing deep")

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the underlying transport connection is currently active."""
        pass

    @_check_occupied
    def read_until(self, prompt: bytes, timeout: Optional[int] = None) -> Optional[str]:
        """
        Reads data from the telnet connection until a specified prompt is encountered or until timeout.

        Args:
            prompt (bytes): The prompt to read until.
            timeout (Optional[int]): The maximum time to wait for the prompt, in seconds. If None, the method uses the default timeout. Defaults to None.

        Returns:
            Optional[str]: The data read from the connection, or None if no data was read.
        """
        if timeout is not None:
            self.timeout = timeout
        if self.resulting_telnet_connection is not None:
            response = self.resulting_telnet_connection.read_until(prompt, self.timeout)
            response = response.decode("ascii") if response else None
        else:
            raise NotImplementedError(
                "No connection object from Telnet found during read_until."
            )
        return response

    @_check_device_type("oneos")
    def load_config(self, config_path: str) -> None:
        """
        Loads a configuration file to a OneOS device.

        Args:
            config_path (str): The path to the configuration file.

        Raises:
            ValueError: If the device is not a OneOS device.
            OSError: If the configuration file fails to open (might not exist).
            ConnectionError: If the device is not connected.
        """
        assert self.destination_device is not None
        logger.debug(f"Loading config {config_path.split('/')[-1]} ...")
        self.write_command("term len 0")
        with open(config_path) as fp:
            for line in fp:
                if line.strip().startswith("!"):
                    continue  # Skip comment lines
                if "hostname" in line:
                    self.destination_device.hostname = line.split()[-1]
                response = self.write_command(line)

        # Check that prompt has exited config terminal fully. Search for "localhost#" (default) or "<configured_hostname>#"
        self.prompt_symbol = f"{self.destination_device.hostname}#"
        response = self.write_command("\n").strip()
        if response != self.prompt_symbol:
            logger.warning(
                f"Loading config might have failed, prompt is not as expected. Received {response} but expected {self.prompt_symbol} instead"
            )
            logger.debug(
                'Sometimes the developer has miscalculated the "exit" commands in the BSA'
            )
            self.write_command("end")
        logger.info(
            f"Loaded configuration to device {self.destination_device.hostname}"
        )

    @_check_device_type("oneos")
    def patch_config(self, config_path: str) -> None:
        """Apply a partial configuration to a OneOS6 device (patch, not full reload).

        Args:
            config_path: Local path to the configuration file to apply.
        """
        assert self.prompt_symbol is not None
        logger.debug(f"Patching config {config_path.split('/')[-1]} ...")
        # If it has beed set as <hostname><prompt_symbol>, just keep the <prompt_symbol>
        # That is to avoid looking for "localhost#" but getting "localhost(config)#" during reconfig
        if len(self.prompt_symbol) != 1:
            self.prompt_symbol = self.prompt_symbol[-1]
        self.load_config(config_path)

    @_check_device_type("linux")
    def set_sudo(self, root_password: Optional[str] = None) -> None:
        """
        Sets sudo privileges for a Linux device.
        The prompt symbol is updated to '#' to reflect the change to the root user.

        Args:
            root_password (Optional[str]): The root password. If None, the method uses the password of the destination device. Defaults to None.

        Raises:
            ValueError: If the device is not a Linux device.
            ConnectionError: If the device is not connected.
            AssertionError: If the method fails to switch to the root user.
        """
        assert self.destination_device is not None
        if root_password is None:
            root_password = self.destination_device.password
        self.write_command("sudo su", expected_prompt_pattern=[b"password for user:"])
        self.write_command(root_password, expected_prompt_pattern=[b"#"])
        self.prompt_symbol = "#"  # In Linux, changes from '$' to '#' if root
        assert self.is_root, "Failed to identify root user"
        logger.info(
            f"Sudo privileges set for linux device: {self.destination_device.hostname}"
        )

    @property
    def is_root(self) -> bool:
        """
        Checks if the current user is root on a Linux device by writing the 'whoami' command and checking the response.

        Returns:
            bool: True if the current user is root, False otherwise.
        """
        user = self.write_command("whoami", [rb"\$", b"#"]).split()[1].strip()
        return user == "root"

    @_check_device_type("linux", is_root=True)
    def set_interface_ip(
        self,
        interface_name: str,
        ip_addr: str,
        netmask: str = "24",
        interface_state: str = "up",
    ) -> None:
        """
        Sets the IP address, netmask, and state of a specified interface on a Linux device.

        Args:
            interface_name (str): The name of the interface.
            ip_addr (str): The IP address to set.
            netmask (str, optional): The netmask to set. Defaults to "24".
            interface_state (str, optional): The state of the interface. Must be 'up' or 'down'. Defaults to "up".

        Raises:
            ValueError: If the IP address is invalid, if the interface does not exist or if the device type is not Linux.
            ConnectionError: If the device is not connected.
            PermissionError: If the user does not have root privileges.
        """
        if not re.match(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", ip_addr):
            raise ValueError("Invalid IP address.")
        if interface_state not in ["up", "down"]:
            logger.error(
                f"Invalid state: {interface_state}. Must be 'up' or 'down'. Passing 'up' by default."
            )
            interface_state = "up"
        if self._get_interface(interface_name) is None:
            raise ValueError(f"Interface {interface_name} not found")
        self.write_command(f"ip addr add {ip_addr}/{netmask} dev {interface_name}")
        self.write_command(f"ip link set {interface_name} {interface_state}")
        logger.info(
            f"Interface {interface_name} set to IP {ip_addr} with netmask {netmask} and state {interface_state}"
        )

    @_check_device_type("linux", is_root=True)
    def delete_interface_ip(
        self, interface_name: str, ip_addr: str, netmask: str = "24"
    ) -> None:
        """
        Deletes the IP address from a specified interface on a Linux device.

        Args:
            interface_name (str): The name of the interface.
            ip_addr (str): The IP address to delete.
            netmask (str, optional): The netmask of the IP address. Defaults to "24".

        Raises:
            ValueError: If the IP address is invalid, if the interface does not exist or if the device type is not Linux.
            ConnectionError: If the device is not connected.
            PermissionError: If the user does not have root privileges.
        """
        if not re.match(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", ip_addr):
            raise ValueError("Invalid IP address.")
        if self._get_interface(interface_name) is None:
            raise ValueError(f"Interface {interface_name} not found")
        self.write_command(f"ip addr del {ip_addr}/{netmask} dev {interface_name}")
        logger.info(
            f"IP {ip_addr} with netmask {netmask} deleted from interface {interface_name}"
        )

    def _get_interfaces(self) -> list[str]:
        """
        Gets a list of all interfaces on the device.
        """
        interfaces = re.split(r"\r\n(?=\d)", self.write_command("ip a"))[
            1:
        ]  # Disregard the CLI command
        return interfaces

    def _get_interface(self, interface_name: str) -> Optional[str]:
        """
        Gets information about a specific interface on the device.
        """
        interface_list = self._get_interfaces()
        for interface in interface_list:
            if interface_name in interface:
                return interface
        return None

    @_check_device_type("oneos")
    def unload_interface(
        self, interface_line: str, wrap_command: bool = True
    ) -> Optional[str]:
        """
        Resets the configuration of a specified interface to its default settings.
        OneOS6 WARNING: "By configuring the interface back to default, it is possible that some services will not work any more"

        Args:
            interface_line (str): The line of the full interface name to reset (i.e. interface gigabitethernet 0/0).
            wrap_command (bool, optional): If True, the method enters and exits the "configure terminal" command.

        Returns:
            Optional[str]: The response from the device after sending the 'default' command, or None if there was no response.
        """
        self.write_command("config terminal") if wrap_command else None
        response = self.write_command(f"default {interface_line}")
        self.write_command("end") if wrap_command else None
        return response

    @_check_device_type("oneos")
    def unload_config(
        self,
        unload_specific_commands: Optional[list[str]] = None,
        check_is_empty: bool = False,
    ) -> None:
        """
        Unloads the configuration of the device using a bottom-up approach.
        The configurations on the bottom of the config inherit properties from the configurations above them.

        Sometimes, even by that approach, some commands cannot be unloaded. In that case, the user must manually unload them,
            by providing the no-commands in the unload_specific_commands parameter.

        The config is retrieved by the very slow "show running-config" command. If check_is_empty is True,
            "show running-config" is called again (another couple of seconds wait time), that's why default is to not check.

        Args:
            unload_specific_commands (Optional[List[str]]): A list of specific commands to unload. Defaults to None.
            check_is_empty (bool, optional): If True, the method checks if the configuration is empty after unloading. Defaults to False.

        Raises:
            ValueError: If the configuration is not fully unloaded and check_is_empty is True, or if device type is not oneos.
            ConnectionError: If the device is not connected.
        """
        assert self.destination_device is not None
        logger.debug(
            f"Unloading config for device {self.destination_device.hostname} ..."
        )
        self.write_command("term len 0")
        self.flush()

        config_lines = self.write_command("show running-config").split("\n")
        config_lines_reverse = config_lines[::-1]  # Traverse from bottom to top

        self.prompt_symbol = "#"
        self.write_command("config terminal")

        # Unload ip routes
        for line in config_lines_reverse:
            if re.search(r"^(ip(v6|) (route|host)|aaa authentication login)", line):
                self.write_command(f"no {line}")
            elif re.search(r"^radius-server", line):
                self.write_command(f"no radius-server {line.split(' ')[1]}")
            if "exit" in line:
                break

        # Unload interfaces
        for line in config_lines_reverse:
            if line.startswith("interface"):
                # If any of the interfaces listed in permanent_interfaces is a substring of the line
                if any(
                    interface in line
                    for interface in self.destination_device.PHYSICAL_INTERFACES_LIST  # type: ignore[attr-defined]
                ):
                    self.unload_interface(line, wrap_command=False)
                else:
                    self.write_command(f"no {line}")

        # Get all the lines until the first interface
        interface_index = next(
            (i for i, line in enumerate(config_lines) if line.startswith("interface")),
            None,
        )
        config_lines_until_interfaces = config_lines[:interface_index]
        # Get all the lines that are not preceded with space -> assumes that they are unloaded as part of the main line unload
        main_lines = [
            line
            for line in config_lines_until_interfaces
            if (not line.startswith(" ") and "exit" not in line)
        ]
        for line in main_lines[:1:-1]:  # Traverse from bottom to top again
            if "license activate" in line:
                continue
            # NOTE: Ignore cases that the "no" prefix will not work, expect the user to manually unload these in the loop below
            self.write_command(f"no {line}")

        # Finally, if user knows that there are configuration leftovers, unload it manually
        if unload_specific_commands is not None:
            for command in unload_specific_commands:
                self.write_command(command)

        self.write_command("hostname localhost")
        self.write_command("end")
        self.flush()

        # NOTE: By default, keep check to False because "show running-config" takes ~4s to return response
        if check_is_empty and not self.is_config_empty(
            self.write_command("show running-config")
        ):
            logger.error(
                f"Config not fully unloaded for device {self.destination_device.hostname}"
            )
            return
        logger.info(
            f"Config unloading effort finished for device {self.destination_device.hostname}"
        )

    def is_config_empty(
        self, configuration: str, except_lines: Optional[list[str]] = None
    ) -> bool:
        """
        Checks if the configuration of the device is fully empty and return boolean.
        """
        assert self.destination_device is not None
        config_lines = configuration.split("\n")
        if (
            "show running-config" not in config_lines[0]
            or "localhost#" not in config_lines[-1]
        ):
            logger.debug(f"Returned config is not okay: {config_lines}")
            return False

        # Remove lines that should not be checked (lines in `except_lines` list)
        config_lines = [
            line
            for line in config_lines
            if all(exception not in line for exception in (except_lines or []))
        ]

        # Ensure empty interfaces pattern
        interface_lines = config_lines[1:-1]
        for i in range(len(interface_lines)):
            if i % 2 == 0:
                line = interface_lines[i].split()
                if (
                    line[0] != "interface"
                    or line[1] not in self.destination_device.PHYSICAL_INTERFACES_LIST  # type: ignore[attr-defined]
                ):
                    return False
            else:
                if "exit" not in interface_lines[i]:
                    return False
        return True

    @_check_connection
    def ping(self, ip: str, nbr_packets: int = 1, ping_timeout: int = 1) -> str:
        """
        Sends a ping command to a specified IP address from the device.
        Supports both Linux and OneOS devices.
        """
        assert self.destination_device is not None
        if self.destination_device.type == "oneos":
            response = self.write_command(
                f"ping {ip} -n {nbr_packets} -w {ping_timeout}"
            )
            logger.info(f"Ping {nbr_packets * 5} packets at IP: {ip}")
            return response
        elif self.destination_device.type == "linux":
            response = self.write_command(
                f"ping {ip} -c {nbr_packets} -W {ping_timeout}"
            )
            logger.info(f"Ping {nbr_packets} packets at IP: {ip}")
            return response
        else:
            raise NotImplementedError(
                f"Ping not implemented for device type {self.destination_device.type}"
            )

    @_check_device_type("linux")
    def hping3(
        self,
        destination_ip: str,
        nbr_packets: Optional[int] = None,
        interval: Optional[str] = None,
        flood: bool = False,
        port: Optional[int] = None,
        type: Optional[str] = None,
    ) -> None:
        """
        Execute hping3 command on the Linux device.
        For more information about hping3, see https://linux.die.net/man/8/hping3
        """
        valid_types = ["tcp", "udp", "icmp", "rawip", "syn", "ack", "fin", "rst"]
        full_command = "hping3 "
        if nbr_packets is not None:
            full_command += f"-c {nbr_packets} "
        if interval is not None:
            full_command += f"-i {interval} "
        if flood:
            full_command += "--flood "
        if port is not None:
            full_command += f"-p {port} "
        if type is not None and type.lower() in valid_types:
            full_command += f"--{type} "
        self.write_command(full_command + destination_ip)

    @_check_device_type("oneos")
    def reconfigure(self, commands_list: list[str]) -> None:
        """
        Reconfigures a OneOS device with a list of commands.
        The list of commands is expected to include the exact commands
            to be sent to the device, with their "exit" commands.

        Args:
            commands_list (List[str]): The list of commands to send to the device, excluding the "config terminal" and "end" commands.

        Raises:
            ValueError: If the device is not a OneOS device.
            ConnectionError: If the device is not connected.
        """
        logger.debug("Reconfiguring device ...")
        self.write_command("term len 0")
        self.write_command("config terminal")
        for command in commands_list:
            self.write_command(command)
        self.write_command("end")
        self.flush()
        logger.debug(f"reconfig commands: {' | '.join(commands_list)}")
        logger.info("Device reconfigured")


class SSHConnection(Connection):
    """
    Represents a secure SSH connection to a remote device.
    This is the recommended secure alternative to TelnetConnection.

    Uses the paramiko library to establish and manage secure SSH connections.
    Supports both password authentication and key-based authentication.
    """

    def __init__(self, timeout: int = 10):
        """Initialize an SSH connection.

        Args:
            timeout: Connection and read timeout in seconds. Defaults to 10.
        """
        super().__init__(timeout)
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.ssh_channel: Optional[paramiko.Channel] = None

    @_check_occupied
    def connect(
        self, destination_device: "Device", destination_ip: str
    ) -> "Connection":
        """
        Establishes an SSH connection to the destination device.

        Args:
            destination_device (Device): The device object containing credentials
            destination_ip (str): The IP address of the destination device

        Returns:
            Connection: This connection object for method chaining

        Raises:
            ConnectionAbortedError: If the SSH connection could not be established
        """
        self.prompt_symbol = destination_device.DEFAULT_PROMPT_SYMBOL
        self.destination_device = destination_device
        self.destination_ip = destination_ip

        try:
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the device
            self.ssh_client.connect(
                hostname=destination_ip,
                username=destination_device.username,
                password=destination_device.password,
                timeout=self.timeout,
                look_for_keys=False,  # Don't look for SSH keys unless specifically configured
                allow_agent=False,  # Don't use SSH agent
            )

            # Create an interactive shell channel
            self.ssh_channel = self.ssh_client.invoke_shell()
            self.ssh_channel.settimeout(self.timeout)

            # Wait for initial prompt and flush any welcome messages
            time.sleep(0.5)  # Give device time to send welcome message
            self._flush_channel()

            if not self.is_connected:
                raise ConnectionAbortedError(
                    "SSH connection established but channel failed"
                )

            logger.info(
                f"SSH connected to {self.destination_device.hostname} at {self.destination_ip}"
            )
            return self

        except Exception as e:
            if self.ssh_client:
                self.ssh_client.close()
            raise ConnectionAbortedError(f"SSH connection failed: {str(e)}") from e

    def _flush_channel(self) -> None:
        """Flush any pending data from the SSH channel."""
        if self.ssh_channel and self.ssh_channel.recv_ready():
            try:
                self.ssh_channel.recv(4096)
            except socket.timeout:
                pass  # Expected when no data available

    @_check_occupied
    def disconnect(self) -> None:
        """Closes the SSH connection and channel."""
        assert self.destination_device is not None
        if self.ssh_channel:
            self.ssh_channel.close()
            self.ssh_channel = None

        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

        if self.is_connected:
            raise ConnectionError("SSH connection could not be closed")

        logger.info(
            f"SSH disconnected from {self.destination_device.hostname} at {self.destination_ip}"
        )

    @property
    def is_connected(self) -> bool:
        """Check if the SSH connection and channel are active."""
        transport = self.ssh_client.get_transport() if self.ssh_client is not None else None
        return (
            self.ssh_client is not None
            and self.ssh_channel is not None
            and not self.ssh_channel.closed
            and transport is not None
            and transport.is_active()
        )

    @_check_occupied
    def write_command(
        self,
        command: str,
        expected_prompt_pattern: Optional[list[str]] = None,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Sends a command via SSH and returns the response.

        Args:
            command (str): The command to send
            expected_prompt_pattern (Optional[List[str]]): Regex patterns to wait for
            timeout (Optional[int]): Timeout in seconds

        Returns:
            Optional[str]: The command response

        Raises:
            ConnectionError: If SSH connection is not established
        """
        if not self.is_connected:
            raise ConnectionError("SSH connection is not established")

        if self.ssh_channel is None:
            raise ConnectionError("SSH channel is not available")

        # Clear any pending data
        self._flush_channel()

        # Send the command
        command_with_newline = command + "\n"
        self.ssh_channel.send(command_with_newline.encode("utf-8"))

        # Read the response
        response_parts = []
        command_timeout = timeout or self.timeout
        start_time = time.time()

        while True:
            if time.time() - start_time > command_timeout:
                logger.warning(
                    f"Command '{command}' timed out after {command_timeout} seconds"
                )
                break

            if self.ssh_channel.recv_ready():
                try:
                    data = self.ssh_channel.recv(4096).decode("utf-8")
                    response_parts.append(data)

                    # Check if we have a complete response
                    full_response = "".join(response_parts)

                    if expected_prompt_pattern:
                        # Check against expected patterns
                        for pattern in expected_prompt_pattern:
                            if re.search(pattern, full_response):
                                return full_response
                    else:
                        # Check for prompt symbol
                        if self.prompt_symbol and self.prompt_symbol in full_response:
                            return full_response

                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error reading SSH response: {e}")
                    break
            else:
                time.sleep(0.1)

        return "".join(response_parts) if response_parts else None

    @_check_occupied
    def flush(self, time_interval: float = 0.1) -> None:
        """Flush any pending data from the SSH channel."""
        time.sleep(time_interval)
        self._flush_channel()

    @_check_occupied
    def flush_deep(self, time_interval: float = 0.1, retries_timeout: int = 60) -> None:
        """Perform deep flush with retries until prompt appears."""
        logger.debug("SSH deep flushing...")
        start_time = time.time()

        while True:
            self.flush(time_interval)

            # Try to get current prompt
            if self.ssh_channel and self.ssh_channel.recv_ready():
                try:
                    data = self.ssh_channel.recv(1024).decode("utf-8")
                    if self.prompt_symbol and self.prompt_symbol in data:
                        break
                except (OSError, UnicodeDecodeError):
                    pass

            if retries_timeout > 0 and time.time() - start_time > retries_timeout:
                logger.warning(f"Deep flush timed out after {retries_timeout} seconds")
                break

            time.sleep(time_interval)


class TelnetConnection(Connection):
    """
    Represents a Telnet connection, always originating from the Host device to another device.
    It uses the telnetlib library to establish and manage the connection.

    .. deprecated:: 0.2.0
        TelnetConnection is deprecated due to security concerns. Telnet transmits data in plain text.
        Use SSHConnection instead for secure communication.

    .. warning::
        This class will be removed in a future version. Please migrate to SSHConnection.
    """

    def __init__(self, timeout: int = 10):
        """Initialize a Telnet connection.

        Args:
            timeout: Connection and read timeout in seconds. Defaults to 10.

        .. deprecated::
            Emit a DeprecationWarning. Migrate to SSHConnection.
        """
        super().__init__(timeout)

        # Issue deprecation warning
        warnings.warn(
            "TelnetConnection is deprecated and will be removed in a future version. "
            "Use SSHConnection instead for secure communication.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.resulting_telnet_connection = telnetlib.Telnet()  # Not connected

    @_check_occupied
    def connect(self, destination_device: "Device", destination_ip: str) -> Connection:
        """
        First connection from Host Device to any other Device.
        It uses an instantiated telnetlib.Telnet object, which is not connected yet.
        Returns the resulting Connection object, which carries the now connected telnetlib.Telnet object.

        Args:
            destination_device (Device): The device object representing the destination device.
                                         This object should contain the necessary credentials.
            destination_ip (str): The IP address of the destination device.

        Returns:
            Connection: The resulting Connection object, which carries the now connected telnetlib.Telnet object.

        Raises:
            ConnectionAbortedError: If the connection could not be established.
        """
        # Important to have a default, because if device is being reused (connect, set sudo, disconnect and then connect again),
        # it will connect as a user but the prompt_symbol will be #, which is not the default for a user
        self.prompt_symbol = destination_device.DEFAULT_PROMPT_SYMBOL
        self.destination_device = destination_device
        self.destination_ip = destination_ip

        assert self.resulting_telnet_connection is not None
        assert self.prompt_symbol is not None
        self.resulting_telnet_connection.open(
            host=self.destination_ip, timeout=self.timeout
        )
        possible_login_prompts = [b"Username:", b"login:"]
        self._write_credentials(possible_login_prompts, destination_device.username)
        possible_password_prompts = [b"Password:"]
        self._write_credentials(possible_password_prompts, destination_device.password)
        encoded_prompt = self.prompt_symbol.encode("ascii")
        self.resulting_telnet_connection.read_until(encoded_prompt, self.timeout)

        if not self.is_connected:
            raise ConnectionAbortedError("Connection aborted: Could not connect")
        logger.info(
            f"Connected to {self.destination_device.hostname} at {self.destination_ip}"
        )
        return self

    def _write_credentials(
        self, list_str_to_expect: list[bytes], str_to_write: Optional[str]
    ) -> None:
        """Wait for one of the expected prompts then write the credential string.

        Args:
            list_str_to_expect: Byte patterns to wait for (e.g. [b"Username:", b"login:"]).
            str_to_write: Credential string to send (username or password).

        Raises:
            EOFError: If none of the expected prompts appear within the timeout.
        """
        if self.resulting_telnet_connection is not None:
            n, match, previous_text = self.resulting_telnet_connection.expect(
                list_str_to_expect, self.timeout
            )
            if n != -1:
                credential = (str_to_write or "").encode("ascii") + b"\r"
                self.resulting_telnet_connection.write(credential)
            else:
                logging.error(
                    f"EOFError: No match found. Match: {match}, Previous text: {previous_text}"
                )
                raise EOFError
        else:
            logging.error(
                "No connection object from telnetlib found. It has been closed or was never created."
            )

    @_check_occupied
    def disconnect(self) -> None:
        """Close the Telnet connection and free resources.

        Raises:
            ConnectionError: If the connection could not be fully closed.
        """
        assert self.resulting_telnet_connection is not None
        assert self.destination_device is not None
        self.resulting_telnet_connection.close()
        if self.is_connected:
            raise ConnectionError("Connection could not be closed")
        logger.info(
            f"Disconnected from {self.destination_device.hostname} at {self.destination_ip}"
        )

    @property
    def is_connected(self) -> bool:
        """
        Checks if the telnet connection is active, by attempting to access the socket.
        """
        if not self.resulting_telnet_connection:
            return False
        try:
            # If the Telnet connection is not active, this will raise an exception
            _ = self.resulting_telnet_connection.get_socket().getsockopt(
                socket.SOL_SOCKET, socket.SO_TYPE
            )
            return True
        except Exception:
            return False


class TelnetCLIConnection(Connection):
    """
    Represents a CLI (Command Line Interface) connection over Telnet, used as a hop from a connected device to another.
    It is the equivalent of an open terminal, and then the developer executing "telnet <ip>".
    For the initialization of this connection type, a already connected TelnetConnection object is required.

    When instantiated properly, the base connection is set to "occupied" and is not available for use by other connections.
    If this TelnetCLIConnection object is used as a base connection for another TelnetCLIConnection object, then it is also set as "occupied".
    The base connections are freed when the exit() or the disconnect() methods of this object are called.
    """

    def __init__(self, source_connection: "TelnetConnection", timeout: int = 10):
        """Initialize a CLI hop over an existing Telnet connection.

        Args:
            source_connection: An already-connected TelnetConnection to use as the
                transport for this hop.
            timeout: Read timeout in seconds. Defaults to 10.

        Raises:
            ConnectionError: If source_connection has no underlying telnet object.
            ConnectionRefusedError: If source_connection is already occupied.
        """
        super().__init__(timeout)
        self.source_connection = source_connection
        if self.source_connection.resulting_telnet_connection is None:
            raise ConnectionError(
                "No connection object found during TelnetCLIConnection instantiation."
            )
        if self.source_connection._is_occupied:
            raise ConnectionRefusedError(
                "The source connection is already in use. Please close the connections that use it first."
            )
        self.resulting_telnet_connection = (
            self.source_connection.resulting_telnet_connection
        )
        self._is_disconnected: bool = True  # For internal use, to monitor when explicitly disconnecting. is_connected checks for the socket only

    @_check_occupied
    def connect(self, destination_device: "Device", destination_ip: str) -> Connection:
        """
        This method uses the source device's connection to establish a new Telnet connection to the next destination device.

        Args:
            destination_device (Device): The device object representing the destination device.
                                         This object should contain the necessary credentials.
            destination_ip (str): The IP address of the destination device.

        Returns:
            Connection: The resulting Connection object, which carries the now connected telnetlib.Telnet object.

        Raises:
            ConnectionRefusedError: If the connection is refused by the destination device.
            ConnectionAbortedError: If the necessary prompts are not retrieved during the login process.
            ConnectionError: If the connection could not be established or if there is an error during the connection process.
        """
        # Will need the info from the source_connection's destination_device until fully connecting (i.e. prompt_symbol)
        assert self.source_connection.destination_device is not None
        self.destination_device = (
            self.source_connection.destination_device
        )  # pass by reference
        self.prompt_symbol = self.source_connection.prompt_symbol
        username = destination_device.username or ""
        password = destination_device.password or ""

        response = self.write_command(
            f"telnet {destination_ip}",
            expected_prompt_pattern=[b"Username:", b"login:"],
            timeout=self.timeout,
        )
        if "Connection closed by foreign host" in response:
            raise ConnectionRefusedError(
                "Connection refused: could not connect to next hop."
            )
        if "Username:" not in response and "login:" not in response:
            raise ConnectionAbortedError(
                "Connection aborted: Username or Login prompts not retrieved."
            )
        response = self.write_command(
            username + "\n",
            expected_prompt_pattern=[b"Password:"],
            timeout=self.timeout,
        )
        if "Password:" not in response:
            raise ConnectionAbortedError(
                "Connection aborted: Password prompt not retrieved."
            )
        response = self.write_command(
            password + "\n",
            expected_prompt_pattern=[b"connected", b"Welcome"],
            timeout=self.timeout,
        )
        if "connected" not in response and "Welcome" not in response:
            raise ConnectionError("Connection error: Could not connect to next hop.")

        # Finally, update with the most recent connection info
        self.source_connection._is_occupied = True
        self.destination_device = destination_device
        self.prompt_symbol = self.destination_device.DEFAULT_PROMPT_SYMBOL
        self.destination_ip = destination_ip
        self._is_disconnected = False

        if not self.is_connected:
            raise ConnectionError("Connection could not be established")
        logger.info(
            "Connected "
            + f"from {self.source_connection.destination_device.hostname} "
            + f"to {self.destination_device.hostname} at {self.destination_ip}"
        )
        return self

    @property
    def is_occupied(self) -> bool:
        """
        Checks if the connection is currently in use.
        """
        if not self.is_connected:
            self.source_connection._is_occupied = False
            self._is_occupied = False
        return self._is_occupied

    @_check_occupied
    def disconnect(self) -> None:
        """Exit the CLI hop and release the source connection back to available state."""
        self.exit()

    @_check_occupied
    def exit(self) -> Union["TelnetConnection", "TelnetCLIConnection"]:
        """
        Exits the current connection, but it doesn't close the socket, just returns to the previous hop.

        Returns:
            Union[TelnetConnection, TelnetCLIConnection]: The previous hop's connection object.
        """
        assert self.source_connection.destination_device is not None
        self.source_connection._is_occupied = False
        # Write "exit" to jump back to previous hop
        self.write_command(
            command="exit",
            expected_prompt_pattern=[b"closed", b"Connection closed by foreign host."],
            timeout=self.timeout,
        )
        # Obligatory to return connection object because it might be of a different type
        self._is_disconnected = True
        logger.info(
            f"Jumped back to previous hop at device {self.source_connection.destination_device.hostname}"
        )
        return self.source_connection

    @property
    def is_connected(self) -> bool:
        """Return True if the source connection is active and this hop has not been exited."""
        return self.source_connection.is_connected and not self._is_disconnected
