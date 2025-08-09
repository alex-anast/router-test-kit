"""
Unit tests for router_test_kit.static_utils module.

These tests focus on pure functions that don't have external dependencies.
"""

from unittest.mock import patch

from router_test_kit.static_utils import get_packet_loss, is_valid_ip


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
