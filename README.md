# Router Test Kit

The motivation for this project is to provide a simple and out-of-the-box, easy-to-use framework for testing (virtual) routers. Initially, the framework was designed to work with OneOS6 routers from OneAccess Networks. It is based on a telnet connection, therefore it is compatible with CISCO routers, Ubuntu Server images etc.

For a thorough documentation (incomplete), see here: [alex-anast.com/router-test-kit](https://alex-anast.com/router-test-kit/)

## Badges

![PyPI version](https://img.shields.io/pypi/v/router-test-kit)<br>
![License](https://img.shields.io/github/license/alex-anast/router-test-kit)<br>
![Dependencies](https://img.shields.io/librariesio/github/alex-anast/router-test-kit)

## Table of Contents

- [Router Test Kit](#router-test-kit)
  - [Badges](#badges)
  - [Table of Contents](#table-of-contents)
  - [Demo](#demo)
  - [Description](#description)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Features](#features)
    - [`device.py`](#devicepy)
    - [`connection.py`](#connectionpy)
    - [`static_utils.py`](#static_utilspy)
  - [Examples](#examples)
  - [License](#license)

## Demo

[![Watch the video](https://img.youtube.com/vi/sNybO2tVy_w/0.jpg)](https://www.youtube.com/watch?v=sNybO2tVy_w)


## Description

Virtual Router Test Kit is a Python framework for testing routers. It is based on a telnet connection (py-package: `telnetlib`). The framework is designed to be simple and easy to use, with a focus on the most common operations that are performed on a router.

The project is inspired based on the OneOS6 devices of OneAccess Networks (very similar to CISCO), but it is not limited by them. It has been extended to support Ubuntu Server images, and it can be easily extended to support other devices as well, as long as they support a telnet connection.

The easiest way to try it out is to set up two (or more) Virtual Machines and interact with them with the help of this framework. Examples of that, basic and complex, are shown in the [Examples](#examples) section.

## Installation

The project is available on PyPi, so you can install it using `pip`:

```bash
python3 -m pip install router-test-kit
```

Alternatively, you can clone the repository and install it locally:

```bash
git clone git@github.com:alex-anast/router-test-kit.git
```

## Usage

Assuming that the prerequisites are met and the installation has been successful, you can start using the test framework right away.

For a more in-detail section, see [the documentation page](https://alex-anast.github.io/router-test-kit/usage/).

## Features

### `device.py`

- **Device Abstraction**:
  - Provides an abstract base class (`Device`) to represent various types of network devices.
- **LinuxDevice Support**:
  - Implements Linux-based devices (`LinuxDevice`), including support for user and root-level access.
- **OneOS6Device Support**:
  - Implements OneOS6 device support with built-in interfaces and specific configurations for this device type.
- **RADIUS Server Device**:
  - Implements a specific `RADIUSServer` class based on the `LinuxDevice` for managing RADIUS servers.
- **Device Credential Management**:
  - Supports the use of default or custom credentials (username and password) for all device types.
- **Command Execution on Host Device**:
  - Executes shell commands on the host machine using the `HostDevice.write_command` method, with optional logging and error handling.

### `connection.py`

- **Connection Abstraction**:
  - Provides an abstract base class (`Connection`) for managing network connections between devices.
- **Telnet Connection Support**:
  - Implements a `TelnetConnection` class to establish and manage Telnet connections to devices.
- **Telnet CLI Connection Support**:
  - Supports creating Telnet CLI connections (`TelnetCLIConnection`) from a device already connected via Telnet.
- **Connection Management**:
  - Facilitates connection management, including establishing, checking, and terminating Telnet sessions.
- **Command Execution**:
  - Supports sending commands to devices and retrieving their responses via Telnet, with built-in timeout handling.
- **Root Access for Linux Devices**:
  - Supports switching to root user (`sudo su`) and managing root-level operations on Linux devices.
- **Network Interface Management**:
  - Allows setting and deleting IP addresses on network interfaces of Linux devices.
- **Configuration Management**:
  - Supports loading, patching, and unloading configurations on OneOS devices.
- **Ping and Network Testing**:
  - Provides ping functionality for both Linux and OneOS devices, and supports extended network testing with hping3 on Linux devices.

### `static_utils.py`

- **Test Collection**:
  - Includes a pytest plugin (`TestCollector`) to collect and manage test items during test runs.
- **JSON File Loading**:
  - Supports loading configurations from JSON files via the `load_json` function.
- **Banner Printing**:
  - Provides `print_banner` for printing structured banners with custom messages, useful for logging or test outputs.
- **Shell Command Execution**:
  - Allows execution of multiple shell commands on the host device, with optional output logging and error handling.
- **Network Interface Management**:
  - Functions to set and remove IP addresses on network interfaces of devices (`set_interface_ip`, `del_interface_ip`).
- **Rebooting Devices**:
  - Provides a method to reboot a device and wait for it to become available again (reboot_device).
- **Network Testing**:
  - Offers `ping` and `get_packet_loss` functions to perform network reachability tests and measure packet loss.
- **File Transfer**:
  - Supports transferring files to a device using SCP (`scp_file_to_home_dir`), with error handling for missing tools like `sshpass`.

## Examples

For a very short script regarding the most simple connection possible, take a look at the [Usage section from the docs](https://alex-anast.github.io/router-test-kit/usage/).

For more complete examples, see:

- [example1_connect.py](./examples/example1_connect.py)
- [example2_ping_between_vms.py](./examples/example2_ping_between_vms.py)

For a very detailed, but not executable example, see:

- [test_ipsec.py](./tests/test_ipsec.py)

## Future TODOs

Here is a list of suggestions for improving the project, categorized by area.

### Project Structure & Dependencies

*   **Consolidate Project Configuration**: Currently, the project might have `setup.py`, and `pyproject.toml`. It would be beneficial to consolidate all project metadata into `pyproject.toml` and remove `setup.py` if possible. This aligns with modern Python packaging standards (PEP 621).
*   **Use a Modern Build Backend**: Switch from a `setup.py`-based build to a `pyproject.toml`-native build backend like `setuptools` (without `setup.py`), `flit`, or `poetry`.
*   **Use `pathlib` for Path Manipulation**: The `os.path` module is used for path manipulation. It would be more modern and object-oriented to refactor this to use the `pathlib` module instead.

### Code & API

*   **Replace Telnet with a more secure protocol**: The current implementation uses `telnetlib`, which is insecure. A major improvement would be to add support for SSH using a library like `paramiko` or `asyncssh`. The `Connection` class could be refactored to support different connection backends.
*   **Improve `run_shell_command`**: The `HostDevice.write_command` and `execute_shell_commands_on_host` in `static_utils.py` can be improved to use `subprocess.run` instead of `subprocess.Popen` for simpler usage and better error handling.
*   **Improve `TelnetConnection`**: The `TelnetConnection` class in `connection.py` can be refactored to use a more robust Telnet library, such as `telnetlib3`, which supports async operations, making the framework more efficient for handling multiple connections.

### Testing

*   **Add Unit Tests**: The project currently only has integration tests. It would be beneficial to add unit tests for the `static_utils.py` and `connection.py` modules. This would allow for more granular testing and faster feedback.
*   **Use `pytest` Fixtures more extensively**: The tests in `test_ipsec.py` can be refactored to better use `pytest` fixtures for setting up and tearing down test resources (like connections and device configurations). This would make the tests more modular and easier to maintain.
*   **Improve Test Coverage**: The test suite can be expanded to cover more of the codebase. Tools like `coverage.py` can be used to measure test coverage and identify untested code.
*   **Use `pytest-xdist`**: The `pytest-xdist` plugin can be used to run tests in parallel, which can significantly reduce test execution time, especially for I/O-bound integration tests.

### Documentation

*   **Update `README.md`**: The `README.md` file should be kept up-to-date to reflect the changes made to the project.
*   **Improve `docs/`**: The documentation in the `docs/` directory can be improved to be more comprehensive and to include examples of how to use the library.
*   **Use a Documentation Generator**: A documentation generator like `Sphinx` can be used to generate professional-looking HTML documentation from the docstrings in the code. This would make it easier to keep the documentation up-to-date.

### CI/CD

*   **Add a CI Pipeline**: A CI pipeline (e.g., using GitHub Actions) can be set up to automatically run tests and linters on every push and pull request. This would help to ensure that the codebase is always in a good state.
*   **Use `pre-commit`**: The `pre-commit` framework can be used to run linters (like `ruff`, `black`, `mypy`) and other checks before each commit. This would help to catch errors early and to maintain a consistent code style.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
