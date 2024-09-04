import re
import json
import time
import logging
import subprocess
import ipaddress
import sys
import os
from typing import List, Optional, Tuple

import pytest

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.device import HostDevice
from src.connection import TelnetConnection

logger = logging.getLogger(__name__)


class TestCollector:
    """ A pytest plugin to collect test items. """
    def pytest_collection_finish(self, session):
        """ Called after test collection has been completed and modified. """
        self.test_items = session.items


def get_tests() -> TestCollector:
    collector = TestCollector()
    pytest.main(["--no-header", "--no-summary", "-qq", "--collect-only"], plugins=[collector])
    test_items = collector.test_items
    return test_items


def load_json(file_path):
    # Assuming that the file is JSON
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data


def print_banner(*messages: str, banner_legth = 80) -> None:
    """Prints a banner out of any number of messages."""
    border = "*" * banner_legth
    logger.info(border)
    for message in messages:
        logger.info(message.center(banner_legth))
    logger.info(border)


def execute_shell_commands_on_host(commands: List[str], print_response = False, quiet = False) -> Optional[str]:
    # Might require root privileges
    responses = []
    for command in commands:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0 and not quiet:
            logger.error(f"Error executing command: {command}")
            logger.error(f"Error message: {stderr.decode()}")
        else:
            response = stdout.decode()
            if print_response and not quiet:
                logger.debug(f"Command executed successfully: {command}")
                logger.debug(f"Output: {response}")
        if stdout:
            responses.append(stdout.decode())
        if stderr:
            responses.append(stderr.decode())
    if responses:
        return '\n'.join(responses)
    else:
        return None


def set_interface_ip(interface_name: str, ip: str, password: str, netmask: str = "24") -> None:
    if '/' not in ip:
        ip = f"{ip}/{netmask}"
    command = f"echo {password} | sudo -S ip addr add {ip} dev {interface_name}"
    execute_shell_commands_on_host([command], quiet=True)


def del_interface_ip(interface: str, ip: str, password: str, netmask: str = "24") -> None:
    if '/' not in ip:
        ip = f"{ip}/{netmask}"
    command = f"echo {password} | sudo -S ip addr del {ip} dev {interface}"

    # If the IP to be deleted is the only one on the interface, skip
    # Useful for: if developer uses their standard IP, it will not be deleted
    ipv4s, ipv6s = get_interface_ips(interface)
    if len(ipv4s) == 1 and ip.split('/')[0] in ipv4s:
        return
    if len(ipv6s) == 1 and ip.split('/')[0] in ipv6s:
        return
    execute_shell_commands_on_host([command])


def get_interface_ips(interface: str) -> Tuple[List[str], List[str]]:
    response = execute_shell_commands_on_host([f"ip addr show {interface}"])
    ipv4_pattern = r"\binet (\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)"
    ipv4_matches = re.findall(ipv4_pattern, response)
    ipv6_pattern = r"\binet6 ([a-f0-9:]+)"
    ipv6_matches = re.findall(ipv6_pattern, response)
    return ipv4_matches if ipv4_matches else [], ipv6_matches if ipv6_matches else []


def reboot_device(connection: "TelnetConnection", timeout: int = 60) -> "TelnetConnection":
    if connection is None or not connection.is_connected():
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


def ping(destination_ip: str, count: int = 1) -> str:
    return execute_shell_commands_on_host([f"ping -c {count} {destination_ip}"])


def get_packet_loss(response: str) -> str:
    """
    Example of result line in response:
        '2 packets transmitted, 2 received, 0% packet loss, time 11ms'
    Returned value:
        '0' (if pings have been successful)
    """
    match = re.search(r"\d+(?=%)", response)
    if match:
        return match.group()
    else:
        logger.critical(f"Ping: Could not find packet loss percentage in response: {response}")


def is_valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def scp_file_to_home_dir(local_file_path: str, user_at_ip: str, password: str) -> None:
    # Check if sshpass is installed on device
    host_vm = HostDevice()
    response = host_vm.write_command("sshpass")
    # response = execute_shell_commands_on_host(["sshpass"])
    if "Usage: sshpass" not in response:
        logger.critical('sshpass is not installed on the device. Please install it by "sudo apt install sshpass"')
    command = f"sshpass -p {password} scp {local_file_path} {user_at_ip}:~"
    response = host_vm.write_command(command)
    if response is None:
        return
    elif "No such file or directory" in response:
        logger.critical(f"Some file path is not valid. Local: {local_file_path}, @: {user_at_ip}")
        raise FileNotFoundError
    else:
        logger.critical(f"Unknown error occurred while copying file to the device. Got response: {response}")
        return ValueError
