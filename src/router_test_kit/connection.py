# connection.py


"""
This module contains the implementation for establishing and managing
    network connections between devices.
    Connection class contains the core actions of the connection,
    while TelnetConnection and TelnetCLIConnection have to do with how the connection is established.

TelnetConnection: Connection originating from the host device to another device.
                  Creates, initialises and uses a Telnet object from telnetlib library.

TelnetCLIConnection: Connection originating from an already connected device to another device.
                     Uses the Telnet object from the TelnetConnection to connect to the next device.
                     This class requires that already-connected Telnet object
                         in order to be instantiated and used.
                     If established, the base connection is not available for use by other connections,
                         until the TelnetCLIConnection is closed.
"""


import logging
import re
import socket
import time
import sys
import os
from abc import ABC, abstractmethod
from typing import Optional, List, Union

import telnetlib

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.device import Device


logger = logging.getLogger(__name__)


class Connection(ABC):
    def __init__(self, timeout: int=10):
        self.destination_device = None
        self.destination_ip = None
        self.resulting_telnet_connection = None
        self.timeout = timeout
        self._is_occupied = False  # Signifies if the connection is in use by another connection
        self.prompt_symbol = None

    @abstractmethod
    def connect():
        pass

    @abstractmethod
    def disconnect():
        pass

    def check_occupied(func):
        """
        Decorator to check if the connection is already in use and hence not available.

        This decorator is used to wrap methods that should not be executed if the connection is already in use.

        Raises:
            ConnectionRefusedError: If the connection is already in use.
        """
        def wrapper(self, *args, **kwargs):
            if self._is_occupied:
                raise ConnectionRefusedError("This connection is already in use. Please close the connections that use it first.")
            return func(self, *args, **kwargs)
        return wrapper

    def check_device_type(required_type, is_root: bool=False):
        """
        Decorator to check the device type and connection privileges before executing a function.

        Args:
            required_type (str): The required device type for the function to be executed.
            is_root (bool, optional): If True, the function requires root privileges to be executed. Defaults to False.

        Raises:
            ValueError: If the device is not of the required type.
            ConnectionError: If the device is not connected.
            PermissionError: If root privileges are required but the user does not have them.
        """
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                if self.destination_device.type != required_type:
                    raise ValueError(f'This method is available only for {required_type} devices, but the destination device is of type "{self.destination_device.type}".')
                # Perform the connection check too, since it's a common requirement
                if not self.is_connected:
                    raise ConnectionError("Device is not connected")
                if is_root and not self.is_root:
                    raise PermissionError("Root privileges required to perform this action")
                return func(self, *args, **kwargs)
            return wrapper
        return decorator

    def check_connection(func):
        """
        Decorator to check if the device is connected before executing a function.

        Raises:
            ConnectionError: If the device is not connected.
        """
        def wrapper(self, *args, **kwargs):
            if not self.is_connected:
                raise ConnectionError("Device is not connected")
            return func(self, *args, **kwargs)
        return wrapper

    @check_occupied
    def write_command(self, command: str, expected_prompt_pattern: Optional[List[str]]=None, timeout: Optional[int]=None) -> Optional[str]:
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
            command = command.encode("ascii") + b"\r" if hasattr(command, 'encode') else command
            self.resulting_telnet_connection.write(command)
            assert self.prompt_symbol is not None, "Prompt symbol is not defined."

            # "expect" can wait for multiple patterns
            if expected_prompt_pattern:
                response = self.resulting_telnet_connection.expect(
                    expected_prompt_pattern, timeout or self.timeout,
                )[2]  # The third element of the tuple is the response
            # but "read_until", while only for one pattern (prompt_symbol), is more reliable
            else:
                response = self.resulting_telnet_connection.read_until(
                    self.prompt_symbol.encode("ascii"), timeout or self.timeout
                )
            response = response.decode('ascii') if response else None
        else:
            raise ConnectionError("No connection object from Telnet found during write_command.")
        return response

    @check_occupied
    def flush(self, time_interval: int = 0.1) -> None:
        """
        This method waits for a short period of time to allow any remaining data to arrive,
        then reads and discards all data that has arrived at the telnet connection.
        """
        try:
            time.sleep(time_interval)
            if self.resulting_telnet_connection is not None:
                self.resulting_telnet_connection.read_very_eager()
        except EOFError as eof:
            logger.error(f"EOFError. Usually something is wrong while loading the connection. | {eof}")
            raise EOFError

    @check_occupied
    def flush_deep(self, time_interval: int = 0.1, retries_timeout: int = 60) -> None:
        logger.debug("Deep flushing ...")
        end_pattern = f"{self.prompt_symbol}"
        if retries_timeout > 0:
            start_time = time.time()
        while True:
            response = self.write_command('\n', timeout=time_interval)
            if response is not None and end_pattern in response.strip():
                break
            if retries_timeout > 0 and time.time() - start_time > retries_timeout:
                raise TimeoutError("Timeout while flushing deep")

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @check_occupied
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
            response = self.resulting_telnet_connection.read_until(
                prompt, self.timeout
            )
            response = response.decode('ascii') if response else None
        else:
            raise NotImplementedError("No connection object from Telnet found during read_until.")
        return response

    @check_device_type("oneos")
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
        response = self.write_command('\n').strip()
        if response != self.prompt_symbol:
            logger.warning(f"Loading config might have failed, prompt is not as expected. Received {response} but expected {self.prompt_symbol} instead")
            logger.debug('Sometimes the developer has miscalculated the "exit" commands in the BSA')
            self.write_command("end")
        logger.info(f"Loaded configuration to device {self.destination_device.hostname}")

    @check_device_type("oneos")
    def patch_config(self, config_path: str) -> None:
        logger.debug(f"Patching config {config_path.split('/')[-1]} ...")
        # If it has beed set as <hostname><prompt_symbol>, just keep the <prompt_symbol>
        # That is to avoid looking for "localhost#" but getting "localhost(config)#" during reconfig
        if len(self.prompt_symbol) != 1:
            self.prompt_symbol = self.prompt_symbol[-1]
        self.load_config(config_path)


    @check_device_type("linux")
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
        if root_password is None:
            root_password = self.destination_device.password
        self.write_command("sudo su", expected_prompt_pattern=[b'password for user:'])
        self.write_command(root_password, expected_prompt_pattern=[b'#'])
        self.prompt_symbol = '#'  # In Linux, changes from '$' to '#' if root
        assert self.is_root, "Failed to identify root user"
        logger.info(f"Sudo privileges set for linux device: {self.destination_device.hostname}")

    @property
    def is_root(self) -> bool:
        """
        Checks if the current user is root on a Linux device by writing the 'whoami' command and checking the response.

        Returns:
            bool: True if the current user is root, False otherwise.
        """
        user = self.write_command("whoami", [b'\$', b'#']).split()[1].strip()
        return user == "root"

    @check_device_type("linux", is_root=True)
    def set_interface_ip(self, interface_name: str, ip_addr: str, netmask: str = "24", interface_state: str = "up") -> None:
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
            logger.error(f"Invalid state: {interface_state}. Must be 'up' or 'down'. Passing 'up' by default.")
            interface_state = "up"
        if self._get_interface(interface_name) is None:
            raise ValueError(f"Interface {interface_name} not found")
        self.write_command(f"ip addr add {ip_addr}/{netmask} dev {interface_name}")
        self.write_command(f"ip link set {interface_name} {interface_state}")
        logger.info(f"Interface {interface_name} set to IP {ip_addr} with netmask {netmask} and state {interface_state}")

    @check_device_type("linux", is_root=True)
    def delete_interface_ip(self, interface_name: str, ip_addr: str, netmask: str = "24") -> None:
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
        logger.info(f"IP {ip_addr} with netmask {netmask} deleted from interface {interface_name}")

    def _get_interfaces(self) -> Optional[List[List[str]]]:
        """
        Gets a list of all interfaces on the device.
        """
        interfaces = re.split(r'\r\n(?=\d)', self.write_command("ip a"))[1:]  # Disregard the CLI command
        return interfaces

    def _get_interface(self, interface_name: str):
        """
        Gets information about a specific interface on the device.
        """
        interface_list = self._get_interfaces()
        for interface in interface_list:
            if interface_name in interface:
                return interface
        return None

    @check_device_type("oneos")
    def unload_interface(self, interface_line: str, wrap_command: bool = True) -> Optional[str]:
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

    @check_device_type("oneos")
    def unload_config(self, unload_specific_commands: Optional[List[str]] = None, check_is_empty: bool = False) -> None:
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
        logger.debug(f"Unloading config for device {self.destination_device.hostname} ...")
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
                if any(interface in line for interface in self.destination_device.PHYSICAL_INTERFACES_LIST):
                    self.unload_interface(line, wrap_command=False)
                else:
                    self.write_command(f"no {line}")

        # Get all the lines until the first interface
        interface_index = next((i for i, line in enumerate(config_lines) if line.startswith("interface")), None)
        config_lines_until_interfaces = config_lines[:interface_index]
        # Get all the lines that are not preceded with space -> assumes that they are unloaded as part of the main line unload
        main_lines = [line for line in config_lines_until_interfaces if (not line.startswith(' ') and not "exit" in line)]
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
        if check_is_empty and not self.is_config_empty(self.write_command("show running-config")):
            logger.error(f"Config not fully unloaded for device {self.destination_device.hostname}")
            return
        logger.info(f"Config unloading effort finished for device {self.destination_device.hostname}")

    def is_config_empty(self, configuration: str, except_lines: Optional[List[str]]=None) -> bool:
        """
        Checks if the configuration of the device is fully empty and return boolean.
        """
        config_lines = configuration.split("\n")
        if "show running-config" not in config_lines[0] or "localhost#" not in config_lines[-1]:
            logger.debug(f"Returned config is not okay: {config_lines}")
            return False

        # Remove lines that should not be checked (lines in `except_lines` list)
        config_lines = [line for line in config_lines if all(exception not in line for exception in except_lines)]

        # Ensure empty interfaces pattern
        interface_lines = config_lines[1:-1]
        for i in range(len(interface_lines)):
            if i % 2 == 0:
                line = interface_lines[i].split()
                if line[0] != "interface" or \
                   line[1] not in self.destination_device.PHYSICAL_INTERFACES_LIST:
                    return False
            else:
                if "exit" not in interface_lines[i]:
                    return False
        return True

    @check_connection
    def ping(self, ip: str, nbr_packets: int = 1, ping_timeout: int = 1) -> str:
        """
        Sends a ping command to a specified IP address from the device.
        Supports both Linux and OneOS devices.
        """
        if self.destination_device.type == "oneos":
            response = self.write_command(f"ping {ip} -n {nbr_packets} -w {ping_timeout}")
            logger.info(f"Ping {nbr_packets * 5} packets at IP: {ip}")
            return response
        elif self.destination_device.type == "linux":
            response = self.write_command(f"ping {ip} -c {nbr_packets} -W {ping_timeout}")
            logger.info(f"Ping {nbr_packets} packets at IP: {ip}")
            return response
        else:
            raise NotImplementedError(f"Ping not implemented for device type {self.destination_device.type}")

    @check_device_type("linux")
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

    @check_device_type("oneos")
    def reconfigure(self, commands_list: List[str]) -> None:
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


class TelnetConnection(Connection):
    """
    Represents a Telnet connection, always originating from the Host device to another device.
    It uses the telnetlib library to establish and manage the connection.
    """

    def __init__(self, timeout: int=10):
        super().__init__(timeout)
        self.resulting_telnet_connection = telnetlib.Telnet()  # Not connected

    @Connection.check_occupied
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

        self.resulting_telnet_connection.open(host=self.destination_ip, timeout=self.timeout)
        possible_login_prompts = [b"Username:", b"login:"]
        self._write_credentials(possible_login_prompts, destination_device.username)
        possible_password_prompts = [b"Password:"]
        self._write_credentials(possible_password_prompts, destination_device.password)
        encoded_prompt = self.prompt_symbol.encode("ascii")
        self.resulting_telnet_connection.read_until(encoded_prompt, self.timeout)

        if not self.is_connected:
            raise ConnectionAbortedError("Connection aborted: Could not connect")
        logger.info(f"Connected to {self.destination_device.hostname} at {self.destination_ip}")
        return self

    def _write_credentials(self, list_str_to_expect: List[str], str_to_write: str) -> None:
        if self.resulting_telnet_connection is not None:
            n, match, previous_text = self.resulting_telnet_connection.expect(
                list_str_to_expect, self.timeout
            )
            if n != -1:
                self.resulting_telnet_connection.write(str_to_write.encode("ascii") + b"\r")
            else:
                logging.error(f"EOFError: No match found. Match: {match}, Previous text: {previous_text}")
                raise EOFError
        else:
            logging.error("No connection object from telnetlib found. It has been closed or was never created.")

    @Connection.check_occupied
    def disconnect(self) -> None:
        self.resulting_telnet_connection.close()
        if self.is_connected:
            raise ConnectionError("Connection could not be closed")
        logger.info(f"Disconnected from {self.destination_device.hostname} at {self.destination_ip}")

    @property
    def is_connected(self) -> bool:
        """
        Checks if the telnet connection is active, by attempting to access the socket.
        """
        if not self.resulting_telnet_connection:
            return False
        try:
            # If the Telnet connection is not active, this will raise an exception
            _ = self.resulting_telnet_connection.get_socket().getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
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

    def __init__(self, source_connection: "TelnetConnection", timeout: int=10):
        super().__init__(timeout)
        self.source_connection = source_connection
        if self.source_connection.resulting_telnet_connection is None:
            raise ConnectionError("No connection object found during TelnetCLIConnection instantiation.")
        if self.source_connection._is_occupied:
            raise ConnectionRefusedError("The source connection is already in use. Please close the connections that use it first.")
        self.resulting_telnet_connection = self.source_connection.resulting_telnet_connection
        self._is_disconnected = True  # For internal use, to monitor when explicitly disconnecting. is_connected checks for the socket only

    @Connection.check_occupied
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
        self.destination_device = self.source_connection.destination_device  # pass by reference
        self.prompt_symbol = self.source_connection.prompt_symbol
        username = destination_device.username
        password = destination_device.password

        response = self.write_command(f"telnet {destination_ip}", expected_prompt_pattern=[b'Username:', b'login:'], timeout=self.timeout)
        if "Connection closed by foreign host" in response:
            raise ConnectionRefusedError("Connection refused: could not connect to next hop.")
        if "Username:" not in response and "login:" not in response:
            raise ConnectionAbortedError("Connection aborted: Username or Login prompts not retrieved.")
        response = self.write_command(username + '\n', expected_prompt_pattern=[b'Password:'], timeout=self.timeout)
        if "Password:" not in response:
            raise ConnectionAbortedError("Connection aborted: Password prompt not retrieved.")
        response = self.write_command(password + '\n', expected_prompt_pattern=[b'connected', b'Welcome'], timeout=self.timeout)
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
        logger.info(f"Connected " \
                  + f"from {self.source_connection.destination_device.hostname} " \
                  + f"to {self.destination_device.hostname} at {self.destination_ip}")
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

    @Connection.check_occupied
    def disconnect(self) -> None:
        self.exit()

    @Connection.check_occupied
    def exit(self) -> Union["TelnetConnection", "TelnetCLIConnection"]:
        """
        Exits the current connection, but it doesn't close the socket, just returns to the previous hop.

        Returns:
            Union[TelnetConnection, TelnetCLIConnection]: The previous hop's connection object.
        """
        self.source_connection._is_occupied = False
        # Write "exit" to jump back to previous hop
        self.write_command(command="exit",
                           expected_prompt_pattern= [
                               b'closed', b'Connection closed by foreign host.'
                            ],
                           timeout=self.timeout)
        # Obligatory to return connection object because it might be of a different type
        self._is_disconnected = True
        logger.info(f"Jumped back to previous hop at device {self.source_connection.destination_device.hostname}")
        return self.source_connection

    @property
    def is_connected(self) -> bool:
        return self.source_connection.is_connected and not self._is_disconnected
