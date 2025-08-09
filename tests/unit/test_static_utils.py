"""
Unit tests for router_test_kit.static_utils module.

These tests focus on pure functions that don't have external dependencies.
"""

import json
import os
import subprocess
import tempfile
from unittest.mock import patch, MagicMock

from router_test_kit.static_utils import (
    get_packet_loss, 
    is_valid_ip,
    load_json,
    print_banner,
    execute_shell_commands_on_host,
    ping,
    get_interface_ips,
    set_interface_ip,
    del_interface_ip,
    scp_file_to_home_dir,
)


class TestGetPacketLoss:
    """Test cases for the get_packet_loss function."""

    def test_successful_ping_zero_packet_loss(self):
        """Test parsing ping response with 0% packet loss."""
        response = "2 packets transmitted, 2 received, 0% packet loss, time 11ms"
        result = get_packet_loss(response)
        assert result == "0"

    def test_partial_packet_loss(self):
        """Test parsing ping response with partial packet loss."""
        response = "5 packets transmitted, 3 received, 40% packet loss, time 4005ms"
        result = get_packet_loss(response)
        assert result == "40"

    def test_complete_packet_loss(self):
        """Test parsing ping response with 100% packet loss."""
        response = "3 packets transmitted, 0 received, 100% packet loss, time 2010ms"
        result = get_packet_loss(response)
        assert result == "100"

    def test_single_digit_packet_loss(self):
        """Test parsing ping response with single digit packet loss."""
        response = "10 packets transmitted, 9 received, 10% packet loss, time 9008ms"
        result = get_packet_loss(response)
        assert result == "10"

    def test_multiline_response(self):
        """Test parsing ping response spanning multiple lines."""
        response = """PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=119 time=14.2 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=119 time=14.1 ms

--- 8.8.8.8 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 14.121/14.161/14.202/0.040 ms"""
        result = get_packet_loss(response)
        assert result == "0"

    @patch("router_test_kit.static_utils.logger")
    def test_no_match_found_logs_critical(self, mock_logger):
        """Test that function logs critical error when no percentage found."""
        response = "Invalid ping response without percentage"
        result = get_packet_loss(response)

        # Should log a critical error
        mock_logger.critical.assert_called_once()
        assert (
            "Could not find packet loss percentage"
            in mock_logger.critical.call_args[0][0]
        )

        # Function returns None when no match found
        assert result is None

    def test_empty_string(self):
        """Test handling of empty string input."""
        with patch("router_test_kit.static_utils.logger") as mock_logger:
            result = get_packet_loss("")
            assert result is None
            mock_logger.critical.assert_called_once()

    def test_percentage_in_different_context(self):
        """Test that function finds percentage even in different context."""
        response = "Network performance: 25% packet loss detected during test"
        result = get_packet_loss(response)
        assert result == "25"


class TestIsValidIp:
    """Test cases for the is_valid_ip function."""

    def test_valid_ipv4_addresses(self):
        """Test validation of valid IPv4 addresses."""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "127.0.0.1",
            "0.0.0.0",
            "255.255.255.255",
        ]

        for ip in valid_ips:
            assert is_valid_ip(ip) is True, f"Expected {ip} to be valid"

    def test_valid_ipv6_addresses(self):
        """Test validation of valid IPv6 addresses."""
        valid_ips = [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:db8:85a3::8a2e:370:7334",
            "::1",
            "::",
            "fe80::1",
            "2001:db8::1",
        ]

        for ip in valid_ips:
            assert is_valid_ip(ip) is True, f"Expected {ip} to be valid"

    def test_invalid_ip_addresses(self):
        """Test validation of invalid IP addresses."""
        invalid_ips = [
            "256.256.256.256",  # Out of range
            "192.168.1",  # Incomplete
            "192.168.1.1.1",  # Too many octets
            "192.168.1.a",  # Non-numeric
            "not_an_ip",  # Not an IP at all
            "",  # Empty string
            "192.168.01.1",  # Leading zeros (technically invalid)
            "192.168.1.256",  # Out of range octet
            "hello.world.com",  # Domain name
            "2001:0db8:85a3::8a2e::7334",  # Invalid IPv6 (double ::)
        ]

        for ip in invalid_ips:
            assert is_valid_ip(ip) is False, f"Expected {ip} to be invalid"

    def test_whitespace_handling(self):
        """Test handling of whitespace in IP addresses."""
        # Leading/trailing whitespace should make IP invalid
        assert is_valid_ip(" 192.168.1.1") is False
        assert is_valid_ip("192.168.1.1 ") is False
        assert is_valid_ip(" 192.168.1.1 ") is False

        # Internal whitespace should make IP invalid
        assert is_valid_ip("192.168. 1.1") is False
        assert is_valid_ip("192. 168.1.1") is False

    def test_edge_cases(self):
        """Test edge cases for IP validation."""
        # Test boundary values
        assert is_valid_ip("0.0.0.0") is True
        assert is_valid_ip("255.255.255.255") is True

        # Test near-boundary invalid values
        assert is_valid_ip("-1.0.0.0") is False
        assert is_valid_ip("256.0.0.0") is False


class TestLoadJson:
    """Test cases for the load_json function."""
    
    def test_load_valid_json_file(self):
        """Test loading a valid JSON file."""
        test_data = {"name": "test", "value": 123}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
            
        try:
            result = load_json(temp_file)
            assert result == test_data
        finally:
            os.unlink(temp_file)


class TestPrintBanner:
    """Test cases for the print_banner function."""
    
    @patch('router_test_kit.static_utils.logger')
    def test_print_banner_single_message(self, mock_logger):
        """Test printing banner with single message."""
        print_banner("Test Message")
        
        # Should log border and message
        assert mock_logger.info.call_count == 3
        calls = mock_logger.info.call_args_list
        assert calls[0][0][0] == "*" * 80  # First border
        assert "Test Message" in calls[1][0][0]  # Message (centered)
        assert calls[2][0][0] == "*" * 80  # Second border


class TestExecuteShellCommands:
    """Test cases for the execute_shell_commands_on_host function."""
    
    @patch('subprocess.run')
    def test_execute_successful_command(self, mock_run):
        """Test executing successful shell command."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=['echo', 'test'],
            returncode=0,
            stdout="test output",
            stderr=""
        )
        
        result = execute_shell_commands_on_host(['echo test'])
        assert result == "test output"
        
    @patch('subprocess.run')
    @patch('router_test_kit.static_utils.logger')
    def test_execute_command_with_error(self, mock_logger, mock_run):
        """Test executing command that returns error."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=['false'],
            returncode=1,
            stdout="",
            stderr="command failed"
        )
        
        result = execute_shell_commands_on_host(['false'])
        assert result == "command failed"
        
        # Should log error
        mock_logger.error.assert_called()


class TestPing:
    """Test cases for the ping function."""
    
    @patch('router_test_kit.static_utils.execute_shell_commands_on_host')
    def test_ping_default_count(self, mock_execute):
        """Test ping with default count."""
        mock_execute.return_value = "ping output"
        
        result = ping("8.8.8.8")
        
        mock_execute.assert_called_once_with(["ping -c 1 8.8.8.8"])
        assert result == "ping output"


class TestGetInterfaceIps:
    """Test cases for the get_interface_ips function."""
    
    @patch('router_test_kit.static_utils.execute_shell_commands_on_host')
    def test_get_interface_ips_with_both_ipv4_and_ipv6(self, mock_execute):
        """Test extracting both IPv4 and IPv6 addresses."""
        mock_output = """2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0
    inet6 fe80::42:acff:fe11:2/64 scope link"""
       
        mock_execute.return_value = mock_output
        
        ipv4s, ipv6s = get_interface_ips("eth0")
        
        assert ipv4s == ["172.17.0.2"]
        assert ipv6s == ["fe80::42:acff:fe11:2"]


class TestSetInterfaceIp:
    """Test cases for the set_interface_ip function."""
    
    @patch('router_test_kit.static_utils.execute_shell_commands_on_host')
    def test_set_interface_ip_default_netmask(self, mock_execute):
        """Test setting IP with default netmask."""
        set_interface_ip("eth0", "192.168.1.100", "password")
        
        expected_command = "echo password | sudo -S ip addr add 192.168.1.100/24 dev eth0"
        mock_execute.assert_called_once_with([expected_command], quiet=True)


class TestDelInterfaceIp:
    """Test cases for the del_interface_ip function."""
    
    @patch('router_test_kit.static_utils.get_interface_ips')
    @patch('router_test_kit.static_utils.execute_shell_commands_on_host')
    def test_del_interface_ip_multiple_ips(self, mock_execute, mock_get_ips):
        """Test deleting IP when interface has multiple IPs."""
        mock_get_ips.return_value = (["192.168.1.100", "192.168.1.101"], [])
        
        del_interface_ip("eth0", "192.168.1.100", "password")
        
        expected_command = "echo password | sudo -S ip addr del 192.168.1.100/24 dev eth0"
        mock_execute.assert_called_once_with([expected_command])


class TestScpFileToHomeDir:
    """Test cases for the scp_file_to_home_dir function."""
    
    @patch('router_test_kit.static_utils.HostDevice')
    def test_scp_file_sshpass_not_installed(self, mock_host_device):
        """Test SCP when sshpass is not installed."""
        mock_device = MagicMock()
        mock_device.write_command.return_value = "command not found"
        mock_host_device.return_value = mock_device
        
        with patch('router_test_kit.static_utils.logger') as mock_logger:
            result = scp_file_to_home_dir("/tmp/test.txt", "user@192.168.1.1", "password")
            
            assert result is None
            mock_logger.critical.assert_called()
