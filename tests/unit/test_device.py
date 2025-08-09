"""Unit tests for device module."""

import subprocess
import unittest.mock as mock

from router_test_kit.device import HostDevice, LinuxDevice, OneOS6Device


class TestHostDevice:
    """Test cases for HostDevice class."""

    def test_write_command_success(self):
        """Test successful command execution."""
        with mock.patch('subprocess.run') as mock_run:
            mock_result = mock.Mock()
            mock_result.returncode = 0
            mock_result.stdout = "command output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = HostDevice.write_command("echo hello")

            assert result == "command output"
            mock_run.assert_called_once_with(
                "echo hello",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )

    def test_write_command_with_stderr(self):
        """Test command execution that returns both stdout and stderr."""
        with mock.patch('subprocess.run') as mock_run:
            mock_result = mock.Mock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = "warning"
            mock_run.return_value = mock_result

            result = HostDevice.write_command("test command")

            assert result == "output\nwarning"

    def test_write_command_failure(self):
        """Test command execution that fails."""
        with mock.patch('subprocess.run') as mock_run:
            mock_result = mock.Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "error message"
            mock_run.return_value = mock_result

            result = HostDevice.write_command("false")

            assert result is None

    def test_write_command_timeout(self):
        """Test command execution that times out."""
        with mock.patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

            result = HostDevice.write_command("sleep 60")

            assert result is None

    def test_write_command_os_error(self):
        """Test command execution that raises OSError."""
        with mock.patch('subprocess.run') as mock_run:
            mock_run.side_effect = OSError("Command not found")

            result = HostDevice.write_command("nonexistent_command")

            assert result is None

    def test_write_command_quiet_mode(self):
        """Test command execution in quiet mode suppresses error logging."""
        with mock.patch('subprocess.run') as mock_run, \
             mock.patch('router_test_kit.device.logger') as mock_logger:
            mock_result = mock.Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "error"
            mock_run.return_value = mock_result

            result = HostDevice.write_command("false", quiet=True)

            assert result is None
            mock_logger.error.assert_not_called()

    def test_write_command_print_response(self):
        """Test command execution with print_response flag."""
        with mock.patch('subprocess.run') as mock_run, \
             mock.patch('router_test_kit.device.logger') as mock_logger:
            mock_result = mock.Mock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = HostDevice.write_command("echo test", print_response=True)

            assert result == "success"
            mock_logger.debug.assert_called()


class TestLinuxDevice:
    """Test cases for LinuxDevice class."""

    def test_init_with_defaults(self):
        """Test LinuxDevice initialization with default values."""
        device = LinuxDevice()

        assert device.username == "user"
        assert device.password == "user"
        assert device.type == "linux"
        assert device.hostname == "linux-user"

    def test_init_with_custom_values(self):
        """Test LinuxDevice initialization with custom values."""
        device = LinuxDevice(username="testuser", password="testpass")

        assert device.username == "testuser"
        assert device.password == "testpass"
        assert device.type == "linux"
        assert device.hostname == "linux-testuser"

    def test_default_constants(self):
        """Test LinuxDevice default constants."""
        assert LinuxDevice.DEFAULT_USERNAME == "user"
        assert LinuxDevice.DEFAULT_PASSWORD == "user"
        assert LinuxDevice.DEFAULT_PROMPT_SYMBOL == "$"


class TestOneOS6Device:
    """Test cases for OneOS6Device class."""

    def test_init_with_defaults(self):
        """Test OneOS6Device initialization with default values."""
        device = OneOS6Device()

        assert device.username == "admin"
        assert device.password == "admin"
        assert device.type == "oneos"

    def test_init_with_custom_values(self):
        """Test OneOS6Device initialization with custom values."""
        device = OneOS6Device(username="testadmin", password="testpass")

        assert device.username == "testadmin"
        assert device.password == "testpass"
        assert device.type == "oneos"

    def test_default_constants(self):
        """Test OneOS6Device default constants."""
        assert OneOS6Device.DEFAULT_USERNAME == "admin"
        assert OneOS6Device.DEFAULT_PASSWORD == "admin"
        assert OneOS6Device.DEFAULT_PROMPT_SYMBOL == "#"

    def test_physical_interfaces_list(self):
        """Test OneOS6Device has required physical interfaces list."""
        assert hasattr(OneOS6Device, 'PHYSICAL_INTERFACES_LIST')
        assert "gigabitethernet" in OneOS6Device.PHYSICAL_INTERFACES_LIST
        assert "fastethernet" in OneOS6Device.PHYSICAL_INTERFACES_LIST
