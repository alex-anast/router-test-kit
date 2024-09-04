# conftest.py


import os
import sys
import re
import json
import getpass
import logging
from typing import List, Tuple

import pytest

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.static_utils import print_banner, load_json


ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
IPSEC_CFG_DIR_NAME = "configs_ipsec"
IKEV2_DIR_NAME = "ikev2"
IPSEC_JSON_NAME = "ipsec.json"
RADIUS_CFG_DIR_NAME = "configs_radius"
SHOW_CRYPTO_DIR = "showCrypto"
BSA_DIR = "bsa"
REBOOT_FLAG = False

# Color codes for printing to the console
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
NC = "\033[0m"
OK = "[OK]  - "
NOK = "[NOK] - "
SKIPPED = "[SKIPPED] - "


logger = logging.getLogger(__name__)
json_config = load_json(os.path.join(ROOT_PATH, IPSEC_CFG_DIR_NAME, IPSEC_JSON_NAME))
finished_header = False


def print_help():
    print()
    print("Usage: test_offline_vm.sh -a <linux ip address VM_A> -b <linux ip address VM_B>[<list of tests>]")
    print()
    print("This test script makes following assumptions:")
    print("  * 2 VMs are required (VM_A and VM_B); 1 VM optional for NAT (VM_C); 1 VM optional for second client (VM_D)")
    print("  * VM_A:GigabitEthernet 0/0 -------  VM_B:GigabitEthernet 0/0 virtnet1 172.31.1.0   .1<->.2")
    print("  * VM_A:GigabitEthernet 0/1 -------  VM_C:GigabitEthernet 0/0 virtnet3 172.31.2.0   .1<->.3")
    print("  * VM_B:GigabitEthernet 0/1 -------  VM_C:GigabitEthernet 0/1 virtnet2 172.31.3.0   .2<->.3")
    print("  * VM_A:GigabitEthernet 0/0 -------  Host PC                  virtnet1 172.31.1.0")
    print("  * VM_A:GigabitEthernet 0/1 -------  Host PC                  virtnet3 172.31.2.0")
    print("  * VM_D:GigabitEthernet 0/0 -------  VM_C:GigabitEthernet 0/2 virtnet4 172.31.4.0")
    print("  * all VMs (except VM_C) are  connected to the internet on interface GigabitEthernet 0/2")
    print("  * All VMs have their Linux port 2222 available: addresses are passed on the command line")
    print("  * the script uses a ssh public key authentication - to put the key on the dut (needed once) execute ")
    print("  *  ssh-copy-id -i ipsec_testsetup.key -p 2222 root@<linux-IP-of-DUT>")
    print("  * On all VMs a public key for ssh with user root is installed (this requires persistent memory)")
    print("  * Run this script as root")
    print("  * On all VMs a user kubu with password kubu and administrator rights is added -> check /media/user/pub/password")
    print()

    print('Execute specific tests:')
    print('    i.e. execute test setups 1, 2 and 3:')
    print('        $ pytest test_ipsec -k "test_setup1 or test_setup2 or test_setup3"')
    print('    i.e. execute all tests but the NAT test')
    print('        $ pytest test_ipsec -k "not test_setup10"')

    print()
    print("Pytest Options Quickview:")
    print("    -v, --verbose    increase info of pytest summary")
    print("    -q, --quiet      decrease info of pytest summary")
    print("    --log-cli-level=LOG_CLI_LEVEL,")
    print("                     set the log level for the console logging")
    print("    --no-header      Disable header")
    print("    -h, --help       print pytest help")
    print("    --ipsec-help     print this help")
    print()
    print("Possible tests:")
    print_tests()
    print()


def pytest_addoption(parser):
    parser.addoption("--ipsec-help", action="store_true", help="ONEOS: Print help information regarding the ipsec tests")


def pytest_configure(config):
    if config.getoption("ipsec_help"):
        print_help()
        os._exit(0)


def print_tests():
    """Print all tests available in the pytest collection"""
    # Import in the scope of this function only to avoid circular dependency
    from test_ipsec import TEST_SETUPS_GENERIC

    for test_nbr, test_setup, test_name in TEST_SETUPS_GENERIC:
        print(f"{test_setup}:\t{test_name}")


@pytest.fixture(scope="function", autouse=True)
def print_custom_banner(request):
    test_name = request.node.name
    print('\n' + f"{YELLOW}=== START: {test_name} ==={NC}")
    yield  # This allows the test to run
    print(f"{YELLOW}===  END:  {test_name} ==={NC}" + '\n')


def pytest_sessionstart(session):
    """Effort to keep the same banner format as in old IPSEC tests."""
    root_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(root_path, IPSEC_CFG_DIR_NAME, IPSEC_JSON_NAME)
    with open(json_path) as f:
        json_config = json.load(f)

    vm_a_ip = json_config.get('VM_A', {}).get('ip', 'No assigned IP')
    vm_b_ip = json_config.get('VM_B', {}).get('ip', 'No assigned IP')
    vm_c_ip = json_config.get('VM_C', {}).get('ip', 'No assigned IP')
    vm_d_ip = json_config.get('VM_D', {}).get('ip', 'No assigned IP')

    print_banner(
        f"VM_A: {vm_a_ip}",
        f"VM_B: {vm_b_ip}",
        f"VM_C: {vm_c_ip}",
        f"VM_D: {vm_d_ip}",
    )


def pytest_itemcollected(item):
    try:
        keywords = item.callspec.params.get("keywords", [])
    except AttributeError:
        return  # If the item has no callspec, return
    if "keywords" in item.nodeid:
        try:
            temp = item.nodeid.split("keywords")[0]
            temp += "-".join(keywords) + ']'
            item._nodeid = temp
            item.name = temp
        except TypeError as te:
            logger.critical(f"Failed to modify the nodeid for {item.name} - keywords list is type {type(keywords)}")
            raise te


def pytest_collection_modifyitems(config, items):
    """Called after the collection of all available tests."""
    global COLLECTED_SETUPS
    COLLECTED_SETUPS = items


def pytest_deselected(items):
    """
    A pytest hook that is called when items are deselected.
    There is no "pytest_selected" hook.
    Modified the hook to print the deselected and selected items for execution.

    FIXME: If I add a second test function, it will crash on the callspec.params (key error)
    """
    global finished_header
    if finished_header:
        return
    global COLLECTED_SETUPS
    selected_items = [item for item in COLLECTED_SETUPS if item not in items]
    deselected_items = items
    reporter = items[0].session.config.pluginmanager.get_plugin("terminalreporter")

    if deselected_items:
        reporter.line("\n\nDeselected items for execution:", bold=True, yellow=True)
        for item in deselected_items:
            try:
                test_function_name = item.nodeid.split("[")[0].split('::')[-1]
                setup_marker = item.callspec.params.get("setup_marker", "N/A")
                description = item.callspec.params.get("description", "N/A")
                reporter.line(f"  - {test_function_name} - {setup_marker}: {description}")
            except AttributeError:
                reporter.line(f"  - {item.name}")

    if selected_items:
        reporter.line("\nSelected items for execution:", bold=True, green=True)
        for item in selected_items:
            try:
                test_function_name = item.nodeid.split("[")[0].split('::')[-1]
                setup_marker = item.callspec.params.get("setup_marker", "N/A")
                description = item.callspec.params.get("description", "N/A")
                reporter.line(f"  - {test_function_name} - {setup_marker}: {description}")
            except AttributeError:
                reporter.line(f"  - {item.name}")
        print()
    finished_header = True


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    report_types = ["passed", "failed", "skipped"]
    reports = {report_type: terminalreporter.getreports(report_type) for report_type in report_types}
    passed, failed, skipped = [[report for report in reports[status]] for status in report_types]

    # For each test, three reports are retrieved: setup, execution and teardown
    passed_counts = _count_report_occurences(passed)
    skipped_counts = _count_report_occurences(skipped)
    # Remove reports that are not thrice in the list -> if any phase of report is missing, consider test as failed
    passed = [report for report in passed if passed_counts[report.nodeid] == 3]
    skipped = [report for report in skipped if skipped_counts[report.nodeid] == 3]
    # Remove duplicates based on nodeid
    passed = list({report.nodeid: report for report in passed}.values())
    failed = list({report.nodeid: report for report in failed}.values())
    skipped = list({report.nodeid: report for report in skipped}.values())

    _print_reports(terminalreporter, skipped, 'Skipped tests', 'yellow')
    _print_reports(terminalreporter, passed, 'Successful tests', 'green')
    _print_reports(terminalreporter, failed, 'Unsuccessful tests', 'red')


def _print_reports(terminalreporter, reports, section_title, color):
    if reports:
        # Ensure two new lines
        terminalreporter.ensure_newline()
        terminalreporter.line('')
        terminalreporter.ensure_newline()

        terminalreporter.section(section_title, sep='-', bold=True, **{color: True})
        content = os.linesep.join(report.nodeid for report in reports)
        terminalreporter.line(_parse_content(content))


def _count_report_occurences(reports):
    report_counts = {}
    for report in reports:
        if report.nodeid in report_counts:
            report_counts[report.nodeid] += 1
        else:
            report_counts[report.nodeid] = 1
    return report_counts


def _parse_content(content: str) -> str:
    parsed_content = ""
    for line in content.split('\n'):
        try:
            test_name, params = line.split('[')
            test_name = test_name.split('.py::')[-1]
            setup, rest = params.split('-', 1)
            final_string = test_name + " - " + setup + ': ' + rest.rstrip(']')
            pattern = r"(?<!\s)(-\w+)+$"  # Remove the keywords
            cleaned_text = re.sub(pattern, '', final_string)
            parsed_content += cleaned_text + '\n'
        # If there is no extra information, the line is the test name
        except ValueError:
            test_name = line
            test_name = test_name.split('.py::')[-1]
            parsed_content += test_name + '\n'
    return parsed_content


@pytest.fixture(scope="session")
def sudo_password():
    if os.geteuid() != 0:
        password = getpass.getpass("This script requires root privileges. Please enter the host machine sudo password: ")
        return password
    else:
        return None


def load_test_setups(test_name: str) -> List[Tuple[str, str, List[str]]]:
    """
    Convert the test setups from the ipsec.json file into a list of tuples.
    Each tuple contains the setup marker, description, and keywords.
    """
    test_setups_data = json_config.get(test_name, {})
    test_setups = []

    for setup_marker, setup_data in test_setups_data.items():
        # Extract setup marker from the setup name
        setup_marker_str = setup_marker.split("_")[-1]
        description = setup_data.get("description")
        keywords = setup_data.get("keywords", [])

        if not description:
            logger.warning(f"Warning: No description found for setup {setup_marker}. Skipping this setup.")
            continue
        # Convert setup marker to lowercase and remove any non-alphanumeric characters
        setup_marker_clean = re.sub(r"[^a-zA-Z0-9]", "", setup_marker_str.lower())
        # If keywords is not a list, convert it to a list
        if not isinstance(keywords, list):
            keywords = [keywords]

        test_setups.append((setup_marker_clean, description, keywords))

    return test_setups


def transform_test_setups(test_setups):
    transformed_setups = []
    for setup in test_setups:
        marker, desc, keywords = setup
        keywords_list = KeywordsList(keywords)
        transformed_setup = (marker, desc, keywords_list)
        transformed_setups.append(transformed_setup)
    return transformed_setups


class KeywordsList(list):
    """
    Overwrite the __repr__ method to manage and display something useful for the keywords
    """
    def __repr__(self):
        return f"KeywordsList(len={len(self)})"


TEST_SETUPS_GENERIC = transform_test_setups(load_test_setups("test_ipsec_generic"))
TEST_SETUPS_ALGORITHMS = transform_test_setups(load_test_setups("test_ipsec_algorithms"))
COLLECTED_SETUPS = []
