"""
Simplified tests for connection module focusing on basic functionality.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from router_test_kit.connection import SSHConnection, TelnetConnection
from router_test_kit.device import Device


class TestSSHConnectionBasics:
    """Basic tests for SSHConnection class."""
    
    def test_init(self):
        """Test SSHConnection initialization."""
        conn = SSHConnection(timeout=10)
        assert conn.timeout == 10
        assert conn.ssh_client is None  # Initially None until connect() is called
        assert conn.ssh_channel is None
        assert conn.destination_device is None
        assert conn.destination_ip is None
        assert conn._is_occupied is False

    def test_occupied_property(self):
        """Test the _is_occupied property."""
        conn = SSHConnection()
        assert conn._is_occupied is False
        conn._is_occupied = True
        assert conn._is_occupied is True


class TestTelnetConnectionBasics:
    """Basic tests for TelnetConnection class."""
    
    def test_init(self):
        """Test TelnetConnection initialization."""
        with patch('warnings.warn'):  # Suppress deprecation warning
            conn = TelnetConnection(timeout=15)
            assert conn.timeout == 15
            assert conn.resulting_telnet_connection is not None
            assert conn.destination_device is None
            assert conn.destination_ip is None
            assert conn._is_occupied is False

    def test_occupied_property(self):
        """Test the _is_occupied property for TelnetConnection."""
        with patch('warnings.warn'):
            conn = TelnetConnection()
            assert conn._is_occupied is False
            conn._is_occupied = True
            assert conn._is_occupied is True

    def test_deprecation_warning(self):
        """Test that TelnetConnection issues deprecation warning."""
        with patch('warnings.warn') as mock_warn:
            TelnetConnection()
            mock_warn.assert_called_once()


class TestConnectionUtilities:
    """Test utility functions in connection module."""
    
    def test_ssh_connection_creation(self):
        """Test creating SSH connection instances."""
        conn = SSHConnection(timeout=20)
        assert conn.timeout == 20
        assert isinstance(conn, SSHConnection)

    @patch('warnings.warn')
    def test_telnet_connection_creation(self, mock_warn):
        """Test creating Telnet connection instances."""
        conn = TelnetConnection(timeout=25)
        assert conn.timeout == 25
        assert isinstance(conn, TelnetConnection)


class TestConnectionMethods:
    """Test connection method behavior without complex mocking."""
    
    def test_ssh_disconnect_without_connection(self):
        """Test SSH disconnect when no connection exists."""
        conn = SSHConnection()
        # Set required attributes to avoid AttributeError
        conn.destination_device = MagicMock()
        conn.destination_device.hostname = "test"
        conn.destination_ip = "192.168.1.1"
        
        # Should not raise exception when ssh_client is None
        conn.disconnect()
        assert conn.ssh_channel is None

    @patch('warnings.warn')
    def test_telnet_disconnect_without_connection(self, mock_warn):
        """Test Telnet disconnect when no connection exists."""
        conn = TelnetConnection()
        # Set required attributes
        conn.destination_device = MagicMock()
        conn.destination_device.hostname = "test"
        conn.destination_ip = "192.168.1.1"
        
        # Mock the close method to avoid AttributeError
        with patch.object(conn, 'resulting_telnet_connection') as mock_conn:
            mock_conn.close.return_value = None
            mock_conn.get_socket.side_effect = Exception("No connection")
            conn.disconnect()

    def test_ssh_flush_without_channel(self):
        """Test SSH flush when no channel exists."""
        conn = SSHConnection()
        # Should not raise exception
        conn.flush()

    def test_ssh_attributes(self):
        """Test SSH connection attribute access."""
        conn = SSHConnection(timeout=30)
        assert hasattr(conn, 'timeout')
        assert hasattr(conn, 'ssh_client')
        assert hasattr(conn, 'ssh_channel')
        assert hasattr(conn, 'destination_device')
        assert hasattr(conn, 'destination_ip')
        assert hasattr(conn, '_is_occupied')

    @patch('warnings.warn')
    def test_telnet_attributes(self, mock_warn):
        """Test Telnet connection attribute access."""
        conn = TelnetConnection(timeout=35)
        assert hasattr(conn, 'timeout')
        assert hasattr(conn, 'resulting_telnet_connection')
        assert hasattr(conn, 'destination_device')
        assert hasattr(conn, 'destination_ip')
        assert hasattr(conn, '_is_occupied')
