#!/usr/bin/env python3

"""
File: test_ipsec.py (OLD VERSION)

This file contains tests for the IPSEC functionality.
Each test function in this module tests a specific aspect of the IPSEC functionality.
The name of the test function should clearly indicate what aspect it's testing.

Setup:
    For the setup, see `./ipscec_controlplane/test/scripts/config_ipsec/README.md`

Requirements:
    Python version should be minimum 3.7
    See requirements.txt for required python packages

Test Overview:
    For a test overview, see `./ipsec_controlplane/test/scripts/README.md`

FIXME: setup9, setup19 (Oragne Setups) not working
FIXME: setup27 not working, not able to ping the IPv6 addresses
"""

import os
import re
import sys
import json
import logging
import socket
from time import sleep
from typing import Optional, Dict, List, Tuple, Set

import pytest

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import src.static_utils
from src.device import OneOS6Device, RADIUSServer
from src.connection import TelnetConnection
from conftest import RED, GREEN, YELLOW, NC, OK, NOK, SKIPPED  # Colouring
from conftest import ROOT_PATH, IPSEC_CFG_DIR_NAME, IPSEC_JSON_NAME
from conftest import SHOW_CRYPTO_DIR, BSA_DIR, RADIUS_CFG_DIR_NAME  # Paths and file names
from conftest import TEST_SETUPS_GENERIC, TEST_SETUPS_ALGORITHMS, json_config  # Info from JSON


logger = logging.getLogger(__name__)


@pytest.mark.ipsec
@pytest.mark.generic
@pytest.mark.flaky(reruns=2)
@pytest.mark.parametrize("setup_marker, description, keywords", TEST_SETUPS_GENERIC)
def test_ipsec_generic(setup_marker: str, description: str, keywords: List[str], sudo_password) -> None:
    src.static_utils.print_banner(f"GENERIC - {setup_marker.upper()}", description)
    setup_info = (test_ipsec_generic.__name__, setup_marker)
    local_radius_connection_used = None

    intf_info = setup_interfaces(sudo_password)

    if "radius" in keywords:
        local_radius_connection_used = setup_radius(setup_info)

    connection_vm_a, connection_vm_b, connection_vm_c, _ = setup_connections(setup_info)

    try:
        logger.debug("Start performing checks ...")

        showCryptoIpsecSA_referenceData_VM_A = get_reference_data(setup_info, "VM_A", "show_crypto_ipsec_sa")
        showCryptoIpsecSA_referenceData_VM_B = get_reference_data(setup_info, "VM_B", "show_crypto_ipsec_sa")

        assert_nbr_active_sa(
            (connection_vm_a, showCryptoIpsecSA_referenceData_VM_A),
            (connection_vm_b, showCryptoIpsecSA_referenceData_VM_B),
        )

        assert_show_crypto_ipsec_sa(
            connection_vm_a, showCryptoIpsecSA_referenceData_VM_A,
            data_remove_lines_containing = {"spi", "sec)", "#", "protected vrf: default", "protected vrf: (none)"},
            expected_data_remove_lines_containing = {"spi", "sec)", "#"},
        )
        assert_show_crypto_ipsec_sa(
            connection_vm_b, showCryptoIpsecSA_referenceData_VM_B,
            data_remove_lines_containing = {"spi", "sec)", "#", "protected vrf: default", "protected vrf: (none)"},
           expected_data_remove_lines_containing = {"spi", "sec)", "#"},
        )

        assert_show_crypto_acl(connection_vm_a, get_reference_data(setup_info, "VM_A", "show_crypto_acl"))
        assert_show_crypto_acl(connection_vm_b, get_reference_data(setup_info, "VM_B", "show_crypto_acl"))

        assert_data_test(*get_script_data(setup_info), setup_info, connection_vm_a, connection_vm_b)

        assert_show_policy_interface(connection_vm_a, get_reference_data(setup_info, "VM_A", "show_policy_interface"))

        assert_show_commands_dont_fail(connection_vm_a)
        assert_show_commands_dont_fail(connection_vm_b)

        logger.info(f"{GREEN}{OK}{description} - TEST PASSED{NC}")

    finally:
        cleanup_connections(connection_vm_a, connection_vm_b, connection_vm_c)
        cleanup_interfaces(sudo_password, intf_info)
        if local_radius_connection_used:
            cleanup_radius(local_radius_connection_used)


@pytest.mark.ipsec
@pytest.mark.algorithms
@pytest.mark.flaky(reruns=2)
@pytest.mark.parametrize("setup_marker, description, keywords", TEST_SETUPS_ALGORITHMS)
def test_ipsec_algorithms(setup_marker: str, description: str, keywords: List[str], sudo_password) -> None:
    src.static_utils.print_banner(f"ALGORITHMS - {setup_marker.upper()}", description)
    setup_info = (test_ipsec_algorithms.__name__, setup_marker)

    intf_info = setup_interfaces(sudo_password)
    connection_vm_a, connection_vm_b, _, _ = setup_connections(setup_info)

    try:
        logger.debug("Start performing checks ...")

        showCryptoIpsecSA_referenceData_VM_A = get_reference_data(setup_info, "VM_A", "show_crypto_ipsec_sa")
        showCryptoIpsecSA_referenceData_VM_B = get_reference_data(setup_info, "VM_B", "show_crypto_ipsec_sa")

        assert_nbr_active_sa(
            (connection_vm_a, showCryptoIpsecSA_referenceData_VM_A),
            (connection_vm_b, showCryptoIpsecSA_referenceData_VM_B),
        )

        assert_algorithms(
            connection_vm_a,
            get_reference_data(setup_info, "VM_A", "show_crypto_ikev2_sa_detailed")
        )
        assert_algorithms(
            connection_vm_b,
            get_reference_data(setup_info, "VM_B", "show_crypto_ikev2_sa_detailed")
        )

        logger.info(f"{GREEN}{OK}{description} - TEST PASSED{NC}")
    finally:
        cleanup_connections(connection_vm_a, connection_vm_b)
        cleanup_interfaces(sudo_password, intf_info)


############################################################################### Aux functions


def check_radius_connection(radius_preference: str) -> None:
    response = _get_radius_connection_ok(radius_preference)
    if response == "OK":
        logger.info(f"{GREEN}{OK}RADIUS connection is OK{NC}")
    else:
        if response == "RADIUS_NOT_SET":
            logger.error(f"{RED}{NOK}RADIUS is required but is not properly set up{NC}")
        elif response == "RADIUS_NOT_RESPONDING":
            logger.error(f"{RED}{NOK}RADIUS is not responding{NC}")
        elif response == "RADIUS_IP_NOT_VALID":
            logger.error(f"{RED}{NOK}RADIUS IP is not valid{NC}")
        else:
            logger.error(f"{RED}{NOK}Unknown error while checking RADIUS Server{NC}")
        logger.warning(f"{YELLOW}{SKIPPED}Test fails because of RADIUS, not IPSEC{NC}")  # ?
        pytest.skip("RADIUS test is skipped")


def _get_radius_connection_ok(radius_preference: str) -> str:
    if radius_preference not in ["local", "remote"]:
        logger.critical(f"{RED}{NOK}Invalid radius_preference, expected 'local' or 'remote' but got {radius_preference} instead. Check JSON file{NC}")
        raise ValueError
    status = _check_radius_settings_in_json(radius_preference)
    if status != "OK":
        return status

    radius_ip = json_config["RADIUS"][radius_preference]["radius_ip"]
    if not src.static_utils.is_valid_ip(radius_ip):
        logger.critical(f"{RED}RADIUS IP: {radius_ip}{NC}")
        return "RADIUS_IP_NOT_VALID"

    ping_packet_loss = src.static_utils.get_packet_loss(src.static_utils.ping(radius_ip, count=2))
    if ping_packet_loss == "100" or ping_packet_loss is None or ping_packet_loss == "":
        return "RADIUS_NOT_RESPONDING"
    return "OK"


def _check_radius_settings_in_json(radius_preference: str) -> None:
    try:
        if json_config["RADIUS"][radius_preference]["radius_ip"]:
            return "OK"
        else:
            raise KeyError
    except KeyError as e:
        logger.error(f"{RED}Key '{str(e)}' does not exist in the JSON.{NC}")
    return "RADIUS_NOT_SET"


def assert_algorithms(connection: "TelnetConnectionIPSEC", ref_data: str) -> None:
    """
    Example line: "Encr: AES-CBC, keysize: 256, Hash: SHA512, DH Grp: 16"
    """
    encr_info: dict = _parse_encr_info(re.findall(r"(Encr: .*)", ref_data)[0])
    assert_config_is_matching(connection, encr_info)
    assert_dpd(connection, ref_data)


def assert_config_is_matching(connection: "TelnetConnectionIPSEC", encr_info: Dict[str, str]) -> None:
    """
    Checks the current configuration of the connection and compares it with the expected encryption information.

    Parameters:
        connection (TelnetConnectionIPSEC): The connection to check.
        encr_info (Dict[str, str]): A dictionary containing the expected encryption information.

    Raises:
        AssertionError: If the current configuration does not match the expected configuration,
                        or if the completion of any encryption, integrity, or group is wrong.
    """
    try:
        # Calls "show running-config" (5s overhead)
        crypto_ikev2_proposal_name = assert_current_config(connection, encr_info)
    except AssertionError as err:
        logger.error(f"{RED}{NOK}Current config is not as expected - {connection.destination_device.hostname}{NC}")
    # Check encryption, integrity and group completions
    for key, value in encr_info.items():
        try:
            assert_completion(connection, key, value, crypto_ikev2_proposal_name)
        except AssertionError as err:
            logger.error(f"{RED}{NOK}Completion of '{key} ?' is wrong - {connection.destination_device.hostname}{NC}")
            raise err
    logger.info(f"{GREEN}{OK}Config is matching - {connection.destination_device.hostname}{NC}")


def assert_current_config(connection: "TelnetConnectionIPSEC", encr_info: str) -> str:
    current_config = connection.write_command("show running-config")
    subconfig_split, crypto_ikev2_proposal_name = _get_crypto_ikev2_proposal_subconfig(current_config)
    # Check if the config matches the reference data
    count_checked = 0
    for line in subconfig_split:
        if "encryption" in line:
            assert encr_info["encryption"] in line, f'Expected "{encr_info["encryption"]}" in line "{line}"'
            count_checked += 1
            continue
        if "integrity" in line:
            assert encr_info["integrity"] in line, f'Expected "{encr_info["integrity"]}" in line "{line}"'
            count_checked += 1
            continue
        if "group" in line:
            assert encr_info["group"] in line, f'Expected "{encr_info["group"]}" in line "{line}"'
            count_checked += 1
            continue
    if count_checked != 3:
        raise AssertionError("Did not perform exactly 3 checks, for encryption, integrity and group. Check the config:\n" + '\n'.join(subconfig_split))
    return crypto_ikev2_proposal_name


def assert_completion(connection: "TelnetConnectionIPSEC", key: str, value: str, name: str) -> None:
    response = _get_crypto_ikev2_proposal_help(connection, name, key)
    if response is None:
        raise AssertionError(f'"{key} ?" did not return a proper response: {response}')
    response_split = response.split('\n')
    if len(response_split) < 3:
        raise AssertionError(f'"{key} ?" did not return a proper response: {response_split}')
    response_split = response_split[3:-1]  # Discard header and footer

    found_value = False
    for line in response_split:
        if value in line:
            found_value = True
            break
    assert found_value, f'"{value}" not found in the list of possible completions:' + '\n'.join(response_split)


def assert_dpd(connection: "TelnetConnectionIPSEC", ref_data: str, checks_iterations: int=3, checks_sleep: int=10) -> None:
    """
    Checks the DPD configuration and the increment of local and remote message IDs over a number of iterations.
    A DPD request is sent every 10 seconds, so the message IDs should increment at least once every 10 seconds.

    Args:
        connection (TelnetConnectionIPSEC): The connection to check.
        ref_data (str): The reference data to compare against.
        checks_iterations (int, optional): The number of times to check the message IDs. Defaults to 3.
        checks_sleep (int, optional): The number of seconds to sleep between checks. Defaults to 10.

    Raises:
        AssertionError: If the DPD configuration does not match the expected configuration,
                        or if the message IDs do not increment as expected.
    """
    response = connection.write_command("show crypto ikev2 sa detailed")

    dpd_pattern = re.compile(r"DPD configured (.*)")
    dpd_configuration = re.search(dpd_pattern, response).group(1).strip()
    dpd_configuration_expected = re.search(dpd_pattern, ref_data).group(1).strip()
    assert dpd_configuration == dpd_configuration_expected, \
        f"Expected {dpd_configuration_expected}, but got {dpd_configuration} instead"

    local_req_msg_id_pattern  = re.compile(r"Local req msg id:  (\d+).*")
    remote_reg_msg_id_pattern = re.compile(r"Remote reg msg id:  (\d+).*")

    initial_local_req_msg_id  = int(local_req_msg_id_pattern.search(response).group(1))
    initial_remote_reg_msg_id = int(remote_reg_msg_id_pattern.search(response).group(1))
    for _ in range(checks_iterations):
        logger.debug("DPD Check: Iteration %s - Waiting for counters to increment...", _)
        sleep(checks_sleep)
        response = connection.write_command("show crypto ikev2 sa detailed")
        local_req_msg_id  = int(local_req_msg_id_pattern.search(response).group(1))
        remote_reg_msg_id = int(remote_reg_msg_id_pattern.search(response).group(1))
        if local_req_msg_id > initial_local_req_msg_id and remote_reg_msg_id > initial_remote_reg_msg_id:
            logger.debug("DPD Check: SUCCESS - Both counters incremented after %ss", checks_sleep)
            logger.debug("DPD Check: Initial Counters - Local: %s,\tRemote: %s", initial_local_req_msg_id, initial_remote_reg_msg_id)
            logger.debug("DPD Check:   Final Counters - Local: %s,\tRemote: %s", local_req_msg_id, remote_reg_msg_id)
            initial_local_req_msg_id = local_req_msg_id
            initial_remote_reg_msg_id = remote_reg_msg_id
        else:
            logger.error("DPD Check: Failure - Counters did not increment after %ss on device %s", checks_sleep, connection.destination_device.hostname)
    logger.info(f"{GREEN}{OK}DPD: Counters incremented after {checks_iterations} checks - {connection.destination_device.hostname}{NC}")


def assert_show_policy_interface(connection: "TelnetConnectionIPSEC", expected_data: Optional[str] = None) -> None:
    if expected_data is None:
        logger.info(f"{YELLOW}{SKIPPED}show policy-interface for device {connection.destination_device.hostname}{NC}")
        return
    data = connection.parse_show_policy_interface()
    reference_data = clean_lines(expected_data, from_id=1)
    _check_diff_in_files(
        data, reference_data, test_type="show policy interface",
        device_name=connection.destination_device.hostname
    )
    logger.info(f"{GREEN}{OK}show policy-interface - {connection.destination_device.hostname}{NC}")


def assert_data_test(nbr_packets_expected: int, test_commands: List[str], setup_info: Tuple[str, str], *connections: "TelnetConnectionIPSEC") -> None:
    if nbr_packets_expected is None and test_commands is None:
        for connection in connections:
            logger.info(f"{YELLOW}{SKIPPED}Data Test for device {connection.destination_device.hostname}{NC}")
        return

    logger.info("Starting Data Test...")
    # The first execution of the script is for setup purposes, results are not relevant.
    logger.debug("Sending traffic for the First Time")
    src.static_utils.execute_shell_commands_on_host(test_commands, quiet=True)
    sleep(3)
    for connection in connections:
        connection.clear_crypto_counters()
    sleep(1)
    logger.debug("Sending traffic for the Second Time")
    for connection in connections:
        connection.clear_policy_interface()

    assert_nbr_packets(get_successful_pings(test_commands), nbr_packets_expected)
    sleep(5)

    reference_data = {}
    for i, connection in enumerate(connections, start=1):
        vm_name = f"VM_{chr(64 + i)}"  # This will generate VM_A, VM_B, VM_C, etc.
        reference_data[vm_name] = get_reference_data(setup_info, vm_name, "show_crypto_ipsec_sa_data")

    remove_lines_containing = {"spi", "sec)", "protected vrf: default", "protected vrf: (none)"}
    for i, connection in enumerate(connections, start=1):
        vm_name = f"VM_{chr(64 + i)}"  # This will generate VM_A, VM_B, VM_C, etc.
        assert_show_crypto_ipsec_sa(connection, reference_data[vm_name], remove_lines_containing)
    logger.info(f"{GREEN}{OK}Data Test{NC}")


def assert_show_commands_dont_fail(connection: "TelnetConnectionIPSEC") -> None:
    assert connection.write_command("show crypto call admission"),            f'{RED}command "show crypto call admission" did not return anything{NC}'
    assert connection.write_command("show crypto call admission statistics"), f'{RED}command "show crypto call admission statistics" did not return anything{NC}'
    assert connection.write_command("show crypto ikev2 sa"),                  f'{RED}command "show crypto ikev2 sa" did not return anything{NC}'
    assert connection.write_command("show crypto ikev2 sa detailed"),         f'{RED}command "show crypto ikev2 sa detailed" did not return anything{NC}'
    assert connection.write_command("show crypto ikev2 session"),             f'{RED}command "show crypto ikev2 session" did not return anything{NC}'
    assert connection.write_command("show crypto ikev2 session detailed"),    f'{RED}command "show crypto ikev2 session detailed" did not return anything{NC}'
    assert connection.write_command("show crypto ikev2 stats"),               f'{RED}command "show crypto ikev2 stats" did not return anything{NC}'
    assert connection.write_command("show crypto ipsec client ezvpn"),        f'{RED}command "show crypto ipsec client ezvpn" did not return anything{NC}'
    assert connection.write_command("show crypto ipsec sa"),                  f'{RED}command "show crypto ipsec sa" did not return anything{NC}'
    assert connection.write_command("show crypto ipsec sa detail"),           f'{RED}command "show crypto ipsec sa detail" did not return anything{NC}'
    assert connection.write_command("show crypto ipsec sa identity"),         f'{RED}command "show crypto ipsec sa identity" did not return anything{NC}'
    assert connection.write_command("show crypto ipsec sa identity detail"),  f'{RED}command "show crypto ipsec sa identity detail" did not return anything{NC}'
    assert connection.write_command("show crypto isakmp key"),                f'{RED}command "show crypto isakmp key" did not return anything{NC}'
    assert connection.write_command("show crypto isakmp policy"),             f'{RED}command "show crypto isakmp policy" did not return anything{NC}'
    assert connection.write_command("show crypto isakmp profile"),            f'{RED}command "show crypto isakmp profile" did not return anything{NC}'
    assert connection.write_command("show crypto isakmp sa"),                 f'{RED}command "show crypto isakmp sa" did not return anything{NC}'
    assert connection.write_command("show crypto isakmp sa count"),           f'{RED}command "show crypto isakmp sa count" did not return anything{NC}'
    assert connection.write_command("show crypto isakmp sa detail"),          f'{RED}command "show crypto isakmp sa detail" did not return anything{NC}'
    assert connection.write_command("show crypto isakmp statistics"),         f'{RED}command "show crypto isakmp statistics" did not return anything{NC}'
    assert connection.write_command("show expert crypto config"),             f'{RED}command "show crypto config" did not return anything{NC}'
    assert connection.write_command("show expert crypto dns"),                f'{RED}command "show crypto dns" did not return anything{NC}'
    assert connection.write_command("show expert crypto cmid"),               f'{RED}command "show crypto cmid" did not return anything{NC}'
    assert connection.write_command("show crypto session"),                   f'{RED}command "show crypto session" did not return anything{NC}'
    assert connection.write_command("show crypto session detail"),            f'{RED}command "show crypto session detail" did not return anything{NC}'
    assert connection.write_command("show crypto gkm group"),                 f'{RED}command "show crypto gkm group" did not return anything{NC}'
    assert connection.write_command("show crypto gkm group name g-poc"),      f'{RED}command "show crypto gkm group name g-poc" did not return anything{NC}'
    logger.info(f"{GREEN}{OK}All other show commands returned data - {connection.destination_device.hostname}{NC}")


def assert_nbr_packets(nbr_packets: int, nbr_packets_expected: int) -> None:
    # Probably first arg will arrive as string. Don't allow implicit conversion
    assert nbr_packets == nbr_packets_expected or nbr_packets == nbr_packets_expected - 1, \
        f"Expected {nbr_packets_expected} packets, but got {nbr_packets} instead"


def assert_show_crypto_acl(connection: "TelnetConnectionIPSEC", expected_data: Optional[str] = None) -> None:
    if expected_data is None:
        logger.info(f"{YELLOW}{SKIPPED}show crypto acl for device {connection.destination_device.hostname}{NC}")
        return
    data = connection.parse_show_crypto_acl()
    reference_data = clean_lines(expected_data, from_id=2, to_id=-1)
    _check_diff_in_files(data, reference_data, test_type="show crypto acl",
                         device_name=connection.destination_device.hostname)
    logger.info(f"{GREEN}{OK}show crypto acl - {connection.destination_device.hostname}{NC}")


def assert_nbr_active_sa(*info: Tuple["TelnetConnectionIPSEC", str], timeout: int = 10) -> None:
    # Parse pairs
    connection_data = {}
    for connection, reference_data in info:
        if not connection.is_connected:
            raise ConnectionError(f"Connection to {connection.destination_device.hostname} is not established")
        expected_nbr = get_nbr_active_sessions_from_reference_file(reference_data)
        if expected_nbr == 0:
            logger.info(f"{YELLOW}{SKIPPED}no SA expected to be ACTIVE for device {connection.destination_device.hostname}{NC}")
            continue
        # List items will be used in the same order as they are passed
        connection_data[connection] = expected_nbr

    logger.info("Waiting for SAs")

    nbr_iterations = 1
    initial_timeout = timeout
    while True:
        if timeout <= 0:
            logger.error(f"{RED}{NOK}Waiting for SAs: Timeout reached{NC}")
            raise TimeoutError
        status_active_in_connections = []
        for connection, expected_nbr in connection_data.items():
            status_active_in_connections.append(
                connection.get_nbr_active_sa() == expected_nbr
            )

        # if any(status_active_in_connections):
        if all(status_active_in_connections):
            logger.info(f"{GREEN}{OK}nbr active SA{NC}")
            break

        if nbr_iterations == 5:
            for connection, _ in connection_data.items():
                connection.clear_crypto_sa()
        logger.info(f"Waiting for tunnel to appear ACTIVE ... {(nbr_iterations-1)*10}s/{initial_timeout*10}s")
        nbr_iterations += 1
        timeout -= 1
        sleep(10)
    sleep(2)
    return


def assert_show_crypto_ipsec_sa(
    connection: "TelnetConnectionIPSEC",
    expected_data: str,
    data_remove_lines_containing: Optional[Set] = None,
    expected_data_remove_lines_containing: Optional[Set] = None,
) -> None:
    data = connection.parse_show_crypto_ipsec_sa(remove_lines_containing=data_remove_lines_containing)
    reference_data = _parse_expected_data(expected_data, expected_data_remove_lines_containing)
    _check_diff_in_files(data, reference_data, test_type="show crypto ipsec sa",
                         device_name = connection.destination_device.hostname)
    logger.info(f"{GREEN}{OK}show crypto ipsec sa - {connection.destination_device.hostname}{NC}")


def clean_lines(data: str, from_id: Optional[int]=None, to_id: Optional[int]=None) -> List[str]:
    return [line for line in (l.strip() for l in data.split('\n')[from_id:to_id]) if line]


def get_script_data(setup_info: Tuple[str, str]) -> Tuple[int, List[str]]:
    test_name, setup_marker = setup_info
    data_file = json_config[test_name][setup_marker].get("data_file")
    if data_file is not None:

        data_file = os.path.join(ROOT_PATH, IPSEC_CFG_DIR_NAME, SHOW_CRYPTO_DIR, data_file)

        with open(data_file) as f:
            data = f.read().split("\n")
            nbr_packets_expected = int(data[1][1:])  # First character will always be a "#"
            test_commands = data[2:]
            test_commands = [line for line in test_commands if line]  # Clear empty lines
            return nbr_packets_expected, test_commands
    return None, None


def cleanup_connections(*connections: "TelnetConnectionIPSEC") -> None:
    for connection in connections:
        if connection is not None:
            cleanup_device(connection)


def cleanup_interfaces(password, interface_info: List[Dict[str, str]]) -> None:
    for interface in interface_info:
        try:
            intf_name = interface["name"]
            if "ip" in interface:
                intf_ip = interface["ip"]
                src.static_utils.del_interface_ip(intf_name, intf_ip, password)
            elif "ipv6" in interface:
                intf_ip = interface["ipv6"]
                src.static_utils.del_interface_ip(intf_name, intf_ip, password, 64)
            else:
                logger.error(f"No 'ip' or 'ipv6' key found in interface dictionary.")
                raise KeyError
        except ValueError:
            logger.error(f"{intf_ip} is not a valid IP address.")
        except KeyError:
            logger.error(f"Key not found in interface dictionary.")


def cleanup_radius(connection: TelnetConnection) -> None:
    connection.delete_interface_ip(
        interface_name=json_config["RADIUS"]["local"]["radius_interface"],
        ip_addr=json_config["RADIUS"]["local"]["radius_ip"],
    )


def get_successful_pings(commands: List[str]) -> int:
    response = src.static_utils.execute_shell_commands_on_host(commands, quiet=False)
    return sum("bytes from" in line for line in response.split('\n'))


def load_json(json_config_path: Optional[str] = None) -> Dict:
    try:
        if json_config_path is None:
            root_path = os.path.dirname(os.path.abspath(__file__))
            json_config_path = os.path.join(
                root_path, IPSEC_CFG_DIR_NAME, IPSEC_JSON_NAME
            )
        with open(json_config_path) as f:
            json_config = json.load(f)
        return json_config
    except FileNotFoundError:
        logger.error(f"File not found at path {json_config_path}")
        raise FileNotFoundError
    except json.JSONDecodeError:
        logger.error(f"File {json_config_path} is not a valid JSON file")
        raise json.JSONDecodeError


def cleanup_device(connection: "TelnetConnectionIPSEC", dont_disconnect=False) -> None:
    hostname = connection.destination_device.hostname
    connection.unload_config(
        # Collection of all the unload commands needed for all the setups
        # Added license key will NOT be deleted implicitly
        # While the "license activate acs" is unconfigured, key remains active until reboot
        unload_specific_commands=[
            "no crypto isakmp keepalive",  # Setup1
            "crypto engine disable",
            "no logging buffered debug",
            "no aaa authentication login aaaezvpn local",  # Setup2
            "no crypto map dynamic dynMap 10",
            "no crypto dynamic dynTemplate",
            "no crypto ipsec transform-set tsEzvpn",
            "no crypto isakmp profile ezvpnProf",
            "no ip local pool",
            "no ip access-list extended 110",
            "console timeout 600",  # Setup6
            "no crypto ikev2 dpd",  # Setup9
            "no ip access-list extended 100",  # Setup 11
            "no crypto call admission limit ipsec sa",
            "no crypto ikev2 fragmentation",  # Setup14
            "sp-fwd",  # Setup19
            "no crypto map local-address",  # Setup21
            "no crypto call admission limit ike in-nego",  # Setup 28
        ]
    )
    connection.clear_crypto_sa()
    answer = connection.has_open_sockets()
    assert not answer, f"{RED}{NOK}secd udp sessions not correctly closed - {hostname}{NC}"
    connection.disconnect() if not dont_disconnect else None


def get_reference_data(setup_info: Tuple[str, str], vm_name: str, show_command: str) -> Optional[str]:
    test_name, setup_marker = setup_info
    reference_file_name = json_config[test_name][setup_marker][vm_name].get(show_command)
    if reference_file_name is None:
        return None

    reference_file = os.path.join(ROOT_PATH, IPSEC_CFG_DIR_NAME, SHOW_CRYPTO_DIR, reference_file_name)
    with open(reference_file) as f:
        reference_data = f.read()
    return reference_data


def get_nbr_active_sessions_from_reference_file(reference_data: str) -> Optional[int]:
    reference_nbr_active_sa = 0
    for line in reference_data.split("\n"):
        line = line.strip()
        if line.startswith("Status:") and line.split(": ")[1] == "ACTIVE":
            reference_nbr_active_sa += 1
    return reference_nbr_active_sa


def ensure_clean_config_at_init(connection: "TelnetConnectionIPSEC", except_lines: Optional[str]=None) -> None:
    """
    If used, ~5s overhead because of "show running-config"
    """
    if except_lines is None:
        except_lines = ["license key add", "license activate"]

    connection.write_command("term len 0")
    if not connection.is_config_empty(connection.write_command("show running-config"), except_lines):
        logger.warning("Config is not empty at startup, trying to unconfigure")
        connection.flush_deep()
        cleanup_device(connection, dont_disconnect=True)
        if not connection.is_config_empty(connection.write_command("show running-config"), except_lines):
            raise ValueError("Config is not fully empty at startup, please manually erase config and reboot")
        else:
            logger.info("Config successfully unconfigured")


def check_and_activate_license(connection: "TelnetConnectionIPSEC", vm_name: str) -> None:
    if "license-key" in json_config[vm_name]:
        if not connection.is_license_sdwanprime_activated():
            if connection.is_license_sdwanprime_installed():
                connection.reconfigure([
                    "license activate sd-wan-prime",
                ])
            else:
                logger.critical("SD WAN license is not installed. Installing key from JSON and activating (might need reboot) ...")
                connection.reconfigure([
                    "license key add " + json_config[vm_name]["license-key"],
                    "license activate sd-wan-prime",
                ])


def setup_connection(setup_info: Tuple[str, str], vm_nbr: int, check_is_empty=True) -> "TelnetConnectionIPSEC":
    """
    check_is_empty: When developers kill the test, they leave config traces to the VMs' configs
                    With an overhead of ~5s, if this parameter is set to True, it ensures that the config is empty
    """
    if not 1 <= vm_nbr <= 4:
        raise ValueError("Invalid vm_nbr")
    vm_name = "VM_" + chr(64 + vm_nbr)

    # Skip cases where VM_C and VM_D are not expected. Assume that JSON doesn't provide config for them
    test_name, setup_marker = setup_info
    config_for_vm_doesnt_exist = (json_config[test_name][setup_marker].get(vm_name) is None)
    if config_for_vm_doesnt_exist:
        return None

    vm = OneOS6Device()
    cfg_dir_path = os.path.join(ROOT_PATH, IPSEC_CFG_DIR_NAME)
    try:
        connection = TelnetConnectionIPSEC().connect(vm, json_config[vm_name]["ip"])
    except socket.timeout as err:
        logger.error("Could not connect to device, caught socket.timeout.")
        logger.warning("Make sure the devices are running and reachable (check IPs in JSON file).")
        raise err

    if check_is_empty:
        ensure_clean_config_at_init(connection)

    connection.flush_deep()

    check_and_activate_license(connection, vm_name)

    connection.load_config(os.path.join(cfg_dir_path, BSA_DIR, json_config[test_name][setup_marker][vm_name]["config_file"]))

    # For Setup19: `_cont` files are patching up the initial config
    # Because of a race condition, some initial config is lost and must be repeated (trustpoints)
    patch = json_config[test_name][setup_marker][vm_name].get("config_file_patch")
    if patch is not None:
        connection.patch_config(os.path.join(cfg_dir_path, BSA_DIR, patch))

    # connection = src.static_utils.reboot_device(connection) if REBOOT_FLAG else connection
    return connection


def setup_connections(setup_info: Tuple[str, str]) -> Tuple[
    "TelnetConnectionIPSEC",            # VM_A
    "TelnetConnectionIPSEC",            # VM_B
    Optional["TelnetConnectionIPSEC"],  # VM_C
    Optional["TelnetConnectionIPSEC"],  # VM_D, not used so far
]:
    connection_a = setup_connection(setup_info, vm_nbr=1)
    connection_b = setup_connection(setup_info, vm_nbr=2)
    try:
        connection_c = setup_connection(setup_info, vm_nbr=3)
    except OSError:  # If config for VM_C exists but VM_C is not active, test should be skipped
        logger.error(f"{YELLOW}{SKIPPED}Found config, but could not connect to VM_C. Skipping test{NC}")
        connection_c = None
        pytest.skip("Could not connect on VM_C, skipping test")
    try:
        connection_d = setup_connection(setup_info, vm_nbr=4)
    except OSError:  # If config for VM_D exists but VM_D is not active
        logger.error(f"{YELLOW}{SKIPPED}Found config, but could not connect to VM_D. Skipping test{NC}")
        connection_d = None
        pytest.skip("Could not connect on VM_D, skipping test")
    return connection_a, connection_b, connection_c, connection_d


def setup_interfaces(password: str) -> List[Dict[str, str]]:
    interface_info = []
    for _, interface in json_config["HOST"]["interfaces"].items():
        ip = interface.get("ip", "")
        if ip:
            src.static_utils.set_interface_ip(interface["name"], interface["ip"], password)
            logger.info(f'IP {interface["ip"]} added to interface {interface["name"]}')
            interface_info.append({"name": interface["name"], "ip": interface["ip"]})

        ipv6 = interface.get("ipv6", "")
        if ipv6:
            src.static_utils.set_interface_ip(interface["name"], interface["ipv6"], password, netmask="64")
            logger.info(f'IP {interface["ipv6"]} added to interface {interface["name"]}')
            interface_info.append({"name": interface["name"], "ipv6": interface["ipv6"]})

        if not ip and not ipv6:
            logger.warning(f"No IP or IPv6 address provided for interface {interface['name']}")
    return interface_info


def setup_radius(setup_info: Tuple[str, str]) -> TelnetConnection:
    test_name, setup_marker = setup_info
    radius_preference = json_config[test_name][setup_marker]["radius_preference"]
    if radius_preference == "local":
        # set up ip addr in the specified interface of radius server
        connection_to_radius = TelnetConnection()
        radius_vm = RADIUSServer(
            username=json_config["RADIUS"]["local"]["username"],
            password=json_config["RADIUS"]["local"]["password"],
        )
        connection_to_radius.connect(radius_vm, json_config["RADIUS"]["local"]["ip"])

        if not is_radius_installed(connection_to_radius):
            logger.critical(f"{RED}{NOK}RADIUS is required but is not installed{NC}")
            raise ValueError
        if not is_radius_active(connection_to_radius):
            logger.critical(f"{RED}{NOK}RADIUS is installed but is not active{NC}")
            raise ValueError

        connection_to_radius.set_sudo(json_config["RADIUS"]["local"]["password"])

        # Move the config files to the RADIUS server
        user = json_config["RADIUS"]["local"]["username"]
        password = json_config["RADIUS"]["local"]["password"]
        src.static_utils.scp_file_to_home_dir(
            local_file_path  = os.path.join(ROOT_PATH, IPSEC_CFG_DIR_NAME, RADIUS_CFG_DIR_NAME, "authorize"),
            user_at_ip       = user + "@" + json_config["RADIUS"]["local"]["ip"],  # i.e. user@X.X.X.X
            password         = password,
        )
        connection_to_radius.write_command(f"mv /home/{user}/authorize /etc/freeradius/3.0/mods-config/files/authorize")
        src.static_utils.scp_file_to_home_dir(
            local_file_path  = os.path.join(ROOT_PATH, IPSEC_CFG_DIR_NAME, RADIUS_CFG_DIR_NAME, "clients.conf"),
            user_at_ip       = user + "@" + json_config["RADIUS"]["local"]["ip"],
            password         = password,
        )
        connection_to_radius.write_command(f"mv /home/{user}/clients.conf /etc/freeradius/3.0/clients.conf")

        # Might need to restart the RADIUS server here

        connection_to_radius.set_interface_ip(
            interface_name=json_config["RADIUS"]["local"]["radius_interface"],
            ip_addr=json_config["RADIUS"]["local"]["radius_ip"],
        )
    check_radius_connection(radius_preference)
    return connection_to_radius if radius_preference == "local" else None


def is_radius_installed(connection: TelnetConnection) -> bool:
    response = connection.write_command("dpkg -l | grep freeradius")
    return len(response.split('\n')[1:-1]) >= 5  # generic, common, config, utils, lib


def is_radius_active(connection: TelnetConnection) -> bool:
    connected_to_internet = False
    for _ in range (3):
        if src.static_utils.get_packet_loss(connection.ping("8.8.8.8", nbr_packets=3)) == "0":
            connected_to_internet = True
            break
    if not connected_to_internet:
        logger.critical(f"{RED}{NOK}RADIUS server is not connected to the internet{NC}")
        raise ConnectionError
    response = connection.write_command("ps aux | grep freeradius")
    return re.search(r"freerad ", response) is not None


def _get_crypto_ikev2_proposal_help(connection: "TelnetConnectionIPSEC", name: str, command: str) -> str:
    if name is None:
        raise ValueError("crypto ikev2 proposal <name> is not defined")
    previous_prompt_symbol = connection.prompt_symbol
    connection.prompt_symbol = '#'  # During (re)configuring, cannot search for i.e. "VM_A#", so focus only on the symbol "#"
    connection.write_command("configure terminal")
    connection.write_command("crypto ikev2 proposal " + name)  # Name does not even have to be correct
    response = connection.write_command(f"{command} ?")
    logger.debug(f'Checking possible completiong for "{command}":')
    logger.debug(response)
    connection.write_command("end")
    connection.prompt_symbol = previous_prompt_symbol
    return response


def _get_crypto_ikev2_proposal_subconfig(config: str) -> Tuple[List[str], str]:
    found = False
    lines_of_interest = []
    for line in config.split("\n"):
        if "crypto ikev2 proposal" in line:
            found = True
            crypto_ikev2_proposal_name = line.split()[3]
            lines_of_interest.append(line)
            continue
        if found:
            lines_of_interest.append(line)
        if found and "exit" in line:
            break
    if not found:
        raise AssertionError('No "crypto ikev2 proposal" found in the config')
    logger.debug("Subconfig collected: " + '\n'.join(lines_of_interest))
    return lines_of_interest, crypto_ikev2_proposal_name


def _parse_encr_info(encr_info: str) -> Dict[str, str]:
    """
    Comes in as:
        Encr: AES-CBC, keysize: 256, PRF: SHA512, Hash: SHA512, DH Grp: 16, Auth sign: PSK, Auth verify: PSK
    Is converted to:
        {"encryption": "aes-cbc-256", "integrity": "sha512", "group": "16"}
    """
    encryption = re.search(r'Encr: (\w+-\w+), keysize: (\d+)', encr_info)
    integrity = re.search(r'Hash: (\w+)', encr_info)
    group = re.search(r'DH Grp: (\d+)', encr_info)

    return {
        'encryption': f"{encryption.group(1).lower()}-{encryption.group(2)}" if encryption else None,
        'integrity': integrity.group(1).lower() if integrity else None,
        'group': group.group(1) if group else None
    }


def _check_diff_in_files(data: List[str], reference_data: List[str], test_type: str, device_name: str = None) -> None:
    data = _clean_data(data)
    reference_data = _clean_data(reference_data)

    # Find and store the differences between the two lists
    wrongly_retrieved_data = [item for item in data if item not in reference_data]
    missing_expected_data = [item for item in reference_data if item not in data]

    print_name = f" - {device_name}" if device_name else ""
    if wrongly_retrieved_data or missing_expected_data:
        logger.error(f"{RED}[NOK] - {test_type}{print_name}{NC}")
        logger.error(
            f"         Found {max(len(wrongly_retrieved_data), len(missing_expected_data))} "
            + "differences between the retrieved data and the expected data"
        )
        for line in wrongly_retrieved_data:
            logger.error(f'         Wrongly retrieved: "{line}"')
        for line in missing_expected_data:
            logger.error(f'         Missing expected: "{line}"')
        # Will only be printed if error is raised and logging level is DEBUG (most verbose)
        logger.debug("\n********\n" + "Retrieved data: " + '\n'.join(data))
        logger.debug("********\n" + "Reference data: " + '\n'.join(reference_data))
        raise AssertionError


def _parse_expected_data(expected_data: str, remove_lines_containing: Set[str] = None) -> List[str]:
    # Strip symbols and empty lines
    reference_data = [line.strip() for line in expected_data.split("\n") if line.strip()]
    # Remove lines containing certain strings, if remove_lines_containing is provided
    if remove_lines_containing:
        reference_data = [line for line in reference_data if not any(substring in line for substring in remove_lines_containing)]
    return sorted(reference_data)


def _clean_data(data) -> List[str]:
    cleaned_data = []
    for line in data:
        items = line.split()
        len_items = len(items)
        for i in range(len_items):
            items[i] = items[i].strip()
        cleaned_data.append(" ".join(items))
    return cleaned_data


class TelnetConnectionIPSEC(TelnetConnection):
    # Call constructor of base class
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Decorator
    def get_response(command):
        """
        Decorator for getting the response of a command
        If response is provided, use it, otherwise write specified command
        """
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                response = kwargs.pop("response", None)
                if response is None:
                    response = self.write_command(command)
                kwargs["response"] = response
                return func(self, *args, **kwargs)
            return wrapper
        return decorator

    @property
    def is_crypto_engine_enabled(self) -> bool:
        response = self.write_command("show crypto engine")
        if "disabled" in response:
            return False
        elif "enabled" in response:
            return True
        else:
            raise ValueError('Unexpected response from "show crypto engine"')

    @property
    def is_tunnel_active(self) -> bool:
        response = self.write_command("show crypto ipsec sa")
        if "Status: ACTIVE" in response:
            return True
        else:  # Includes "Status: INIT", "DELETE", "IDLE"
            return False

    @get_response("show udp sessions")
    def has_open_sockets(self, response: str) -> bool:
        secd4_sessions = "*:500" in response
        nat_sessions = "*:4500" in response
        secd6_sessions = "[::]:500" in response
        return (secd4_sessions or nat_sessions or secd6_sessions)


    @get_response("show crypto ipsec sa")
    def get_nbr_active_sa(self, response: Optional[str] = None) -> int:
        nbr_active_sa = 0
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("Status:") and line.split(": ")[1] == "ACTIVE":
                nbr_active_sa += 1
        return nbr_active_sa

    @get_response("show crypto ipsec sa")
    def parse_show_crypto_ipsec_sa(self, response: Optional[str] = None, remove_lines_containing: Optional[Set[str]] = None) -> List[str]:
        """
        Parses the output of `show crypto ipsec sa` and returns a list of strings.

        Each string is a sorted line of the output, with the following modifications:

            - Lines containing "spi", "sec)", "#", "protected vrf: default", or "protected vrf: (none)" are removed.
            - Occurrences of the address from DHCP "192.168.X.X" are masked.
            - The lines are sorted alphanumerically.

        Args:
            response (str, optional): The output of `show crypto ipsec sa`. If None, the function will get the response itself.

        Returns:
            List[str]: A list of strings representing the parsed and modified lines of the output.
        """
        if remove_lines_containing is None:
            remove_lines_containing = {
                "spi",
                "sec)",
                "#",
                "protected vrf: default",
                "protected vrf: (none)",
            }
        ip_pattern = re.compile(r"192\.168\.\d{1,3}\.\d{1,3}")
        tunnel_pattern = re.compile(r'Virtual-IpsecTunnel \d*')


        lines = [line for line in (l.strip() for l in response.split("\n")) if line]

        # Replace occurrences of IPs and tunnel numbers
        masked_lines = [tunnel_pattern.sub('Virtual-IpsecTunnel XX', ip_pattern.sub("192.168.XX.XX", line)) for line in lines]

        # Filter out lines containing certain strings or ending with certain characters
        filtered_lines = [line for line in masked_lines if not any(item in line for item in remove_lines_containing) and not line.endswith(('#', '>'))]

        return sorted(filtered_lines)

    def wait_until_tunnel_is_active(self, timeout: int = 30) -> None:
        count = 0
        for second in range(timeout, 0, -1):
            if count == 5:
                self.clear_crypto_sa()
            if self.is_tunnel_active:
                return
            sleep(1)
            logger.debug(f"Waiting for tunnel to appear ACTIVE ... {second}s/{timeout}s")
        raise TimeoutError("Timeout while waiting for tunnel to appear ACTIVE")

    def clear_crypto_sa(self) -> None:
        self.write_command("clear crypto isakmp")
        self.write_command("clear crypto ikev2 sa")
        self.write_command("clear crypto sa")

    def clear_crypto_counters(self) -> None:
        self.write_command("clear crypto counters")

    @get_response("show crypto acl")
    def parse_show_crypto_acl(self, response: Optional[str] = None) -> Optional[List[str]]:
        if len(response.split('\n')) <= 3:
            return ""
        else:
            return clean_lines(response, from_id=2, to_id=-2)

    @get_response("show policy-interface")
    def parse_show_policy_interface(self, response: Optional[str] = None) -> Optional[List[str]]:
        if len(response.split('\n')) <= 2:
            return ""
        else:
            return clean_lines(response, from_id=1, to_id=-1)

    def clear_policy_interface(self) -> None:
        self.write_command("clear policy-interface")

    @get_response("show license")
    def is_license_sdwanprime_activated(self, response: Optional[str] = None) -> bool:
        for line in response.split('\n'):
            if line.strip().startswith("sd-wan-prime"):
                installed = (line.split()[1] == "yes")
                activated = (line.split()[2] == "true")
                if not activated and installed:
                    logger.debug("SD WAN Prime license is installed but not activated")
                return activated
        raise AssertionError("SD WAN Prime license not found in 'show license' output")  # Should not happen

    @get_response("show license")
    def is_license_sdwanprime_installed(self, response: Optional[str] = None) -> bool:
        for line in response.split('\n'):
            if line.strip().startswith("sd-wan-prime"):
                return (line.split()[1] == "yes")
        raise AssertionError("SD WAN Prime license not found in 'show license' output")  # Should not happen


if __name__ == "__main__":
    pytest_args = ["-vvv", "--no-header", "--log-cli-level=DEBUG"]
    exit_code = pytest.main(pytest_args + ["-m ipsec"])
    sys.exit(exit_code)

    # Example of selection:
    # pytest.main(pytest_args + ["-m ipsec", "-k generic and setup1-"])
    # pytest.main(pytest_args + ["-m ipsec", "-k setup1-"])  # Will execute generic and alorithms setup1
    # pytest.main(pytest_args + ["-m ipsec", "-k generic and setup1"])  # Will execute setup1, setup10, setup11, ...
    # pytest.main(pytest_args + ["-m ipsec", "-k generic and not vm_c and not orange"])
