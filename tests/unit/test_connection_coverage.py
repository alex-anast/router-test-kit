"""
Additional coverage tests for connection.py to reach 80% overall coverage.

These tests focus on covering uncovered statements without complex mocking.
"""

from unittest.mock import MagicMock, patch
import pytest

from router_test_kit.connection import SSHConnection, TelnetConnection


class TestConnectionInitialization:
    """Test connection initialization edge cases."""

    def test_ssh_connection_init_timeout_from_params(self):
        """Test SSH connection with custom timeout."""
        ssh_conn = SSHConnection(timeout=45)
        assert ssh_conn.timeout == 45

    def test_telnet_connection_init_timeout_from_params(self):
        """Test Telnet connection with custom timeout."""
        telnet_conn = TelnetConnection(timeout=60)
        assert telnet_conn.timeout == 60


class TestSSHConnectionErrorHandling:
    """Test SSH connection error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_device = MagicMock()
        self.mock_device.connection_params = {
            'hostname': 'testhost',
            'port': 22,
            'username': 'testuser',
            'password': 'testpass'
        }
        self.ssh_conn = SSHConnection(self.mock_device)

    def test_flush_no_channel(self):
        """Test flush method when no SSH channel exists."""
        self.ssh_conn.ssh_channel = None
        
        # Should not raise exception
        self.ssh_conn.flush()

    def test_write_command_no_channel(self):
        """Test write_command when SSH channel is None."""
        self.ssh_conn.ssh_client = MagicMock()
        self.ssh_conn.ssh_channel = None
        
        with pytest.raises(ConnectionError, match="SSH connection is not established"):
            self.ssh_conn.write_command("test")

    def test_read_until_no_channel(self):
        """Test read_until when no channel exists."""
        self.ssh_conn.ssh_channel = None
        
        with pytest.raises(NotImplementedError, match="No connection object from Telnet found"):
            self.ssh_conn.read_until(b"prompt")


class TestTelnetConnectionErrorHandling:
    """Test Telnet connection error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_device = MagicMock()
        self.telnet_conn = TelnetConnection()

    def test_is_connected_no_connection(self):
        """Test is_connected when no telnet connection exists."""
        with patch.object(self.telnet_conn, 'resulting_telnet_connection', None):
            result = self.telnet_conn.is_connected
            assert result is False

    def test_disconnect_no_connection(self):
        """Test disconnect when no connection exists."""
        with patch.object(self.telnet_conn, 'resulting_telnet_connection', None):
            # Should raise an exception when trying to close None
            with pytest.raises(AttributeError):
                self.telnet_conn.disconnect()

    def test_write_command_no_connection(self):
        """Test write_command when not connected."""
        with patch.object(self.telnet_conn, 'resulting_telnet_connection', None):
            with pytest.raises(ConnectionError, match="No connection object from Telnet found"):
                self.telnet_conn.write_command("test")


class TestConnectionStringMethods:
    """Test connection string representation methods."""

    def test_ssh_connection_str_method(self):
        """Test SSH connection string representation."""
        ssh_conn = SSHConnection()
        str_repr = str(ssh_conn)
        assert "SSHConnection" in str_repr

    def test_telnet_connection_str_method(self):
        """Test Telnet connection string representation."""
        telnet_conn = TelnetConnection()
        str_repr = str(telnet_conn)
        assert "TelnetConnection" in str_repr


class TestConnectionValidation:
    """Test connection parameter validation."""

    def test_ssh_connection_missing_hostname(self):
        """Test SSH connection creation."""
        # SSH connection doesn't validate hostname in constructor
        ssh_conn = SSHConnection()
        assert ssh_conn is not None

    def test_telnet_connection_missing_hostname(self):
        """Test Telnet connection creation."""
        # Telnet connection doesn't validate hostname in constructor
        telnet_conn = TelnetConnection()
        assert telnet_conn is not None


class TestConnectionAdditionalMethods:
    """Test additional connection methods for coverage."""

    def test_ssh_connection_flush_channel_method(self):
        """Test SSH _flush_channel method."""
        ssh_conn = SSHConnection()
        
        with patch.object(ssh_conn, 'ssh_channel') as mock_channel:
            mock_channel.recv_ready.side_effect = [True, False]
            mock_channel.recv.return_value = b"some data"
            
            ssh_conn._flush_channel()
            
            assert mock_channel.recv.called

    def test_ssh_connection_default_timeout(self):
        """Test SSH connection uses default timeout when not specified."""
        ssh_conn = SSHConnection()
        assert ssh_conn.timeout == 10

    def test_telnet_connection_default_timeout(self):
        """Test Telnet connection uses default timeout when not specified."""
        telnet_conn = TelnetConnection()
        assert telnet_conn.timeout == 10
