"""Static Utilities and Helper Functions Module.

This module provides a collection of utility functions for network testing,
command execution, and system operations. It includes functions for:

- Network operations (ping, packet loss analysis, IP validation)
- File operations (JSON loading, SCP transfers)
- System commands (shell command execution)  
- Test utilities (pytest integration, data processing)

The utilities are designed to support router and network device testing
scenarios, providing common operations needed across different test cases.

Functions:
    Network Utilities:
    - ping(): Execute ping commands and return results
    - get_packet_loss(): Extract packet loss percentage from ping output
    - is_valid_ip(): Validate IP address strings (IPv4/IPv6)
    - get_interface_ips(): Get IP addresses assigned to network interfaces
    
    System Utilities:
    - execute_shell_commands_on_host(): Execute shell commands with error handling
    - scp_file_to_home_dir(): Transfer files using SCP
    
    Data Utilities:
    - load_json(): Load and parse JSON configuration files
    - print_banner(): Print formatted banner messages
    
    Test Utilities:
    - get_tests(): Collect pytest test items
    - TestCollector: Pytest plugin for test collection

Example:
    Common usage patterns:
    
    ```python
    from router_test_kit.static_utils import ping, get_packet_loss, is_valid_ip
    
    # Network testing
    result = ping("8.8.8.8", count=3)
    loss = get_packet_loss(result)
    print(f"Packet loss: {loss}%")
    
    # IP validation  
    if is_valid_ip("192.168.1.1"):
        print("Valid IP address")
    ```

Note:
    Many functions in this module execute system commands or access network
    resources. Ensure proper permissions and network connectivity when using
    these utilities in test environments.
"""

import ipaddress
import json
import logging
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import pytest

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from router_test_kit.connection import TelnetConnection
from router_test_kit.device import HostDevice

logger = logging.getLogger(__name__)


class TestCollector:
    """A pytest plugin to collect test items."""

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        """Called after test collection has been completed and modified."""
        self.test_items = session.items


def get_tests() -> List[pytest.Item]:
    """Collect test items using pytest collection."""
    collector = TestCollector()
    pytest.main(
        ["--no-header", "--no-summary", "-qq", "--collect-only"], plugins=[collector]
    )
    return collector.test_items


def load_json(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data as dictionary
    """
    with open(file_path, encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data


def print_banner(*messages: str, banner_legth: int = 80) -> None:
    """Print formatted banner messages with decorative borders.
    
    Creates a visually appealing banner by surrounding the provided messages
    with asterisk borders. Each message is centered within the banner width.
    
    Args:
        *messages: Variable number of string messages to display in the banner
        banner_legth: Width of the banner in characters. Defaults to 80.
        
    Example:
        ```python
        print_banner("Welcome", "Router Test Suite", "Version 1.0")
        ```
        
        Output:
        ```
        ********************************************************************************
                                        Welcome
                                   Router Test Suite
                                      Version 1.0
        ********************************************************************************
        ```
        
    Note:
        Messages are logged using the logger.info() method, so they will appear
        in both console output and log files based on logging configuration.
    """
    border = "*" * banner_legth
    logger.info(border)
    for message in messages:
        logger.info(message.center(banner_legth))
    logger.info(border)


def execute_shell_commands_on_host(
    commands: List[str], print_response: bool = False, quiet: bool = False
) -> Optional[str]:
    """Execute shell commands on the host system.
    
    Args:
        commands: List of commands to execute
        print_response: Whether to log successful command execution
        quiet: Whether to suppress error logging
        
    Returns:
        Combined output of all commands, or None if no output
    """
    responses = []
    for command in commands:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )

            if result.returncode != 0 and not quiet:
                logger.error("Error executing command: %s", command)
                logger.error("Error message: %s", result.stderr)
            else:
                if print_response and not quiet:
                    logger.debug("Command executed successfully: %s", command)
                    logger.debug("Output: %s", result.stdout)

            if result.stdout:
                responses.append(result.stdout)
            if result.stderr:
                responses.append(result.stderr)

        except subprocess.TimeoutExpired:
            if not quiet:
                logger.error("Command timed out: %s", command)
        except OSError:
            if not quiet:
                logger.exception("Failed to execute command: %s", command)

    return "\n".join(responses) if responses else None


def set_interface_ip(
    interface_name: str, ip: str, password: str, netmask: str = "24"
) -> None:
    if "/" not in ip:
        ip = f"{ip}/{netmask}"
    command = f"echo {password} | sudo -S ip addr add {ip} dev {interface_name}"
    execute_shell_commands_on_host([command], quiet=True)


def del_interface_ip(
    interface: str, ip: str, password: str, netmask: str = "24"
) -> None:
    if "/" not in ip:
        ip = f"{ip}/{netmask}"
    command = f"echo {password} | sudo -S ip addr del {ip} dev {interface}"

    # If the IP to be deleted is the only one on the interface, skip
    # Useful for: if developer uses their standard IP, it will not be deleted
    ipv4s, ipv6s = get_interface_ips(interface)
    if len(ipv4s) == 1 and ip.split("/")[0] in ipv4s:
        return
    if len(ipv6s) == 1 and ip.split("/")[0] in ipv6s:
        return
    execute_shell_commands_on_host([command])


def get_interface_ips(interface: str) -> Tuple[List[str], List[str]]:
    """Get IPv4 and IPv6 addresses assigned to a network interface.
    
    Args:
        interface: Name of the network interface
        
    Returns:
        Tuple of (IPv4 addresses, IPv6 addresses)
    """
    response = execute_shell_commands_on_host([f"ip addr show {interface}"])
    if not response:
        return [], []

    ipv4_pattern = r"\binet (\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)"
    ipv4_matches = re.findall(ipv4_pattern, response)
    ipv6_pattern = r"\binet6 ([a-f0-9:]+)"
    ipv6_matches = re.findall(ipv6_pattern, response)
    return ipv4_matches if ipv4_matches else [], ipv6_matches if ipv6_matches else []


def reboot_device(
    connection: TelnetConnection, timeout: int = 60
) -> TelnetConnection:
    """Reboot a device and wait for it to come back online.
    
    Args:
        connection: Active telnet connection to device
        timeout: Maximum time to wait for device to come back online
        
    Returns:
        Renewed connection to the device
        
    Raises:
        ConnectionError: If connection is not established
        TimeoutError: If device doesn't come back online within timeout
    """
    if connection is None or not connection.is_connected:
        raise ConnectionError("Connection is not established. Cannot reboot device.")

    vm_ip = connection.destination_ip
    vm = connection.destination_device
    connection.write_command("show expert system command bash")
    connection.write_command("/sbin/reboot")
    connection.disconnect()

    start_time = time.time()
    while True:
        packet_loss = get_packet_loss(vm_ip)
        if packet_loss == 0:
            break
        if timeout and time.time() - start_time > timeout:
            raise TimeoutError(f"Rebooting device {vm} took too long. Timeout reached.")

    connection.connect(vm, vm_ip)
    return connection


def ping(destination_ip: str, count: int = 1) -> Optional[str]:
    """Ping a destination and return the result.
    
    Args:
        destination_ip: IP address to ping
        count: Number of ping packets to send
        
    Returns:
        Ping command output, or None if command failed
    """
    return execute_shell_commands_on_host([f"ping -c {count} {destination_ip}"])


def get_packet_loss(response: str) -> Optional[str]:
    """Extract packet loss percentage from ping command output.
    
    Args:
        response: Output from ping command
        
    Returns:
        Packet loss percentage as string, or None if not found
        
    Example:
        '2 packets transmitted, 2 received, 0% packet loss, time 11ms'
        Returns '0'
    """
    if not response:
        logger.critical("Ping: Empty response provided")
        return None

    match = re.search(r"\d+(?=%)", response)
    if match:
        return match.group()
    else:
        logger.critical(
            "Ping: Could not find packet loss percentage in response: %s", response
        )
        return None


def is_valid_ip(ip: str) -> bool:
    """Check if a string represents a valid IP address (IPv4 or IPv6).
    
    Args:
        ip: String to validate as IP address
        
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def scp_file_to_home_dir(local_file_path: str, user_at_ip: str, password: str) -> None:
    """Copy a local file to remote host's home directory using SCP.
    
    Args:
        local_file_path: Path to local file to copy
        user_at_ip: Remote destination in format 'user@ip'
        password: Password for remote authentication
        
    Raises:
        FileNotFoundError: If local file or remote path is invalid
        ValueError: If unknown error occurs during transfer
    """
    # Check if sshpass is installed on device
    host_vm = HostDevice()
    response = host_vm.write_command("sshpass")

    if not response or "Usage: sshpass" not in response:
        logger.critical(
            'sshpass is not installed on the device. Please install it by "sudo apt install sshpass"'
        )
        return

    command = f"sshpass -p {password} scp {local_file_path} {user_at_ip}:~"
    response = host_vm.write_command(command)

    if response is None:
        return
    elif "No such file or directory" in response:
        logger.critical(
            "Some file path is not valid. Local: %s, @: %s", local_file_path, user_at_ip
        )
        raise FileNotFoundError
    else:
        logger.critical(
            "Unknown error occurred while copying file to the device. Got response: %s", response
        )
        raise ValueError("SCP transfer failed")
