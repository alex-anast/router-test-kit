"""
Unit tests for router_test_kit.connection module.

These tests focus on the SSH connection implementation using mocks.
"""

from unittest.mock import MagicMock, patch

import pytest

from router_test_kit.connection import SSHConnection, TelnetConnection
from router_test_kit.device import Device


class TestSSHConnection:
    """Test cases for the SSHConnection class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ssh_conn = SSHConnection(timeout=5)
        self.mock_device = MagicMock(spec=Device)
        self.mock_device.username = "testuser"
        self.mock_device.password = "testpass"
        self.mock_device.hostname = "testhost"
        self.mock_device.DEFAULT_PROMPT_SYMBOL = "$ "
        self.destination_ip = "192.168.1.1"

    def test_init(self):
        """Test SSHConnection initialization."""
        conn = SSHConnection(timeout=10)
        assert conn.timeout == 10
        assert conn.ssh_client is None
        assert conn.ssh_channel is None
        assert not conn._is_occupied

    @patch("router_test_kit.connection.paramiko.SSHClient")
    def test_connect_success(self, mock_ssh_client_class):
        """Test successful SSH connection."""
        # Setup mocks
        mock_ssh_client = MagicMock()
        mock_ssh_channel = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        mock_ssh_client.invoke_shell.return_value = mock_ssh_channel
        mock_ssh_channel.closed = False
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_ssh_client.get_transport.return_value = mock_transport
        mock_ssh_channel.recv_ready.return_value = False

        # Test connection
        result = self.ssh_conn.connect(self.mock_device, self.destination_ip)

        # Verify SSH client setup
        mock_ssh_client_class.assert_called_once()
        mock_ssh_client.set_missing_host_key_policy.assert_called_once()
        mock_ssh_client.connect.assert_called_once_with(
            hostname=self.destination_ip,
            username="testuser",
            password="testpass",
            timeout=5,
            look_for_keys=False,
            allow_agent=False,
        )
        mock_ssh_client.invoke_shell.assert_called_once()
        mock_ssh_channel.settimeout.assert_called_once_with(5)

        # Verify connection state
        assert result is self.ssh_conn
        assert self.ssh_conn.ssh_client is mock_ssh_client
        assert self.ssh_conn.ssh_channel is mock_ssh_channel
        assert self.ssh_conn.destination_device is self.mock_device
        assert self.ssh_conn.destination_ip == self.destination_ip
        assert self.ssh_conn.prompt_symbol == "$ "

    @patch("router_test_kit.connection.paramiko.SSHClient")
    def test_connect_failure(self, mock_ssh_client_class):
        """Test SSH connection failure."""
        # Setup mock to raise exception
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        mock_ssh_client.connect.side_effect = Exception("Connection failed")

        # Test connection failure
        with pytest.raises(Exception) as exc_info:
            self.ssh_conn.connect(self.mock_device, self.destination_ip)

        assert "SSH connection failed" in str(exc_info.value)
        mock_ssh_client.close.assert_called_once()

    def test_is_connected_true(self):
        """Test is_connected property when connected."""
        # Setup connected state
        self.ssh_conn.ssh_client = MagicMock()
        self.ssh_conn.ssh_channel = MagicMock()
        self.ssh_conn.ssh_channel.closed = False
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        self.ssh_conn.ssh_client.get_transport.return_value = mock_transport

        assert self.ssh_conn.is_connected is True

    def test_is_connected_false_no_client(self):
        """Test is_connected property when no client."""
        assert self.ssh_conn.is_connected is False

    def test_is_connected_false_closed_channel(self):
        """Test is_connected property when channel is closed."""
        self.ssh_conn.ssh_client = MagicMock()
        self.ssh_conn.ssh_channel = MagicMock()
        self.ssh_conn.ssh_channel.closed = True

        assert self.ssh_conn.is_connected is False

    def test_disconnect(self):
        """Test SSH disconnection."""
        # Setup connected state
        mock_ssh_client = MagicMock()
        mock_ssh_channel = MagicMock()
        self.ssh_conn.ssh_client = mock_ssh_client
        self.ssh_conn.ssh_channel = mock_ssh_channel
        self.ssh_conn.destination_device = self.mock_device
        self.ssh_conn.destination_ip = self.destination_ip

        # Mock the internal state to simulate disconnection
        mock_ssh_channel.closed = True
        mock_ssh_client.get_transport.return_value = None

        self.ssh_conn.disconnect()

        # Verify cleanup
        mock_ssh_channel.close.assert_called_once()
        mock_ssh_client.close.assert_called_once()
        assert self.ssh_conn.ssh_channel is None
        assert self.ssh_conn.ssh_client is None

    def test_write_command_success(self):
        """Test successful command execution."""
        # Setup connected state
        mock_ssh_channel = MagicMock()
        mock_ssh_client = MagicMock()
        self.ssh_conn.ssh_channel = mock_ssh_channel
        self.ssh_conn.ssh_client = mock_ssh_client

        # Setup connection state
        mock_ssh_channel.closed = False
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_ssh_client.get_transport.return_value = mock_transport

        # Mock channel behavior
        mock_ssh_channel.recv_ready.side_effect = [False, True, False]
        mock_ssh_channel.recv.return_value = b"command output\n$ "

        # Set prompt symbol through proper connection flow
        with patch.object(self.ssh_conn, '_flush_channel'):
            self.ssh_conn.prompt_symbol = "$ "
            result = self.ssh_conn.write_command("test command")

        # Verify command was sent
        mock_ssh_channel.send.assert_called_once_with(b"test command\n")
        assert result == "command output\n$ "

    def test_write_command_not_connected(self):
        """Test write_command when not connected."""
        # Ensure connection state shows as disconnected
        self.ssh_conn.ssh_client = None
        self.ssh_conn.ssh_channel = None

        with pytest.raises(ConnectionError, match="SSH connection is not established"):
            self.ssh_conn.write_command("test")

    def test_write_command_no_channel(self):
        """Test write_command when no channel available."""
        # Mock the is_connected method at the class level to return True
        with patch.object(SSHConnection, 'is_connected', new_callable=lambda: property(lambda self: True)):
            self.ssh_conn.ssh_channel = None
            with pytest.raises(ConnectionError, match="SSH channel is not available"):
                self.ssh_conn.write_command("test")

    @patch("router_test_kit.connection.time.sleep")
    def test_flush(self, mock_sleep):
        """Test flush method."""
        mock_ssh_channel = MagicMock()
        self.ssh_conn.ssh_channel = mock_ssh_channel
        mock_ssh_channel.recv_ready.return_value = True
        mock_ssh_channel.recv.return_value = b"some data"

        self.ssh_conn.flush(0.2)

        mock_sleep.assert_called_once_with(0.2)
        mock_ssh_channel.recv.assert_called_once_with(4096)

    def test_flush_no_data(self):
        """Test flush when no data available."""
        mock_ssh_channel = MagicMock()
        self.ssh_conn.ssh_channel = mock_ssh_channel
        mock_ssh_channel.recv_ready.return_value = False

        # Should not raise exception
        self.ssh_conn.flush()

        mock_ssh_channel.recv.assert_not_called()

    @patch("router_test_kit.connection.time.sleep")
    @patch("router_test_kit.connection.time.time")
    def test_flush_deep_timeout(self, mock_time, mock_sleep):
        """Test flush_deep with timeout."""
        mock_ssh_channel = MagicMock()
        self.ssh_conn.ssh_channel = mock_ssh_channel

        # Mock time progression to trigger timeout
        mock_time.side_effect = [0, 0.1, 65, 66]  # Start, first check, timeout, logging
        mock_ssh_channel.recv_ready.return_value = True
        mock_ssh_channel.recv.return_value = b"some data"

        # Use patch to set prompt symbol
        with patch.object(type(self.ssh_conn), 'prompt_symbol', "$ ", create=True):
            self.ssh_conn.flush_deep(retries_timeout=60)

        # Should have attempted flush and then timed out
        assert mock_sleep.call_count >= 1

    def test_occupied_decorator(self):
        """Test that occupied decorator prevents method execution."""
        self.ssh_conn._is_occupied = True

        with pytest.raises(Exception):  # ConnectionRefusedError or similar
            self.ssh_conn.connect(self.mock_device, self.destination_ip)


class TestTelnetConnection:
    """Test cases for the TelnetConnection class."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('warnings.warn'):  # Suppress deprecation warning during tests
            self.telnet_conn = TelnetConnection(timeout=5)
        self.mock_device = MagicMock(spec=Device)
        self.mock_device.username = "testuser"
        self.mock_device.password = "testpass"
        self.mock_device.hostname = "testhost"
        self.mock_device.DEFAULT_PROMPT_SYMBOL = "$ "
        self.destination_ip = "192.168.1.1"

    def test_init(self):
        """Test TelnetConnection initialization."""
        with patch('warnings.warn') as mock_warn:
            conn = TelnetConnection(timeout=10)
            assert conn.timeout == 10
            assert conn.resulting_telnet_connection is not None
            # Should issue deprecation warning
            mock_warn.assert_called_once()

    @patch('router_test_kit.connection.telnetlib.Telnet')
    def test_connect_success(self, mock_telnet):
        """Test successful Telnet connection."""
        mock_telnet_instance = MagicMock()
        self.telnet_conn.resulting_telnet_connection = mock_telnet_instance
        
        # Mock successful authentication process
        mock_telnet_instance.expect.side_effect = [
            (0, b"Username:", b""),  # Username prompt found
            (0, b"Password:", b""),  # Password prompt found
        ]
        mock_telnet_instance.read_until.return_value = b"$ "
        
        # Mock the socket to make is_connected return True
        mock_socket = MagicMock()
        mock_socket.getsockopt.return_value = 1  # Valid socket type
        mock_telnet_instance.get_socket.return_value = mock_socket
        
        result = self.telnet_conn.connect(self.mock_device, self.destination_ip)
        
        assert result == self.telnet_conn
        assert self.telnet_conn.destination_device == self.mock_device
        assert self.telnet_conn.destination_ip == self.destination_ip

    @patch('router_test_kit.connection.telnetlib.Telnet')
    def test_connect_failure(self, mock_telnet):
        """Test Telnet connection failure."""
        mock_telnet_instance = MagicMock()
        self.telnet_conn.resulting_telnet_connection = mock_telnet_instance
        
        # Mock connection failure
        mock_telnet_instance.open.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            self.telnet_conn.connect(self.mock_device, self.destination_ip)

    def test_is_connected_true(self):
        """Test is_connected returns True when connected."""
        mock_telnet_instance = MagicMock()
        mock_socket = MagicMock()
        mock_telnet_instance.get_socket.return_value = mock_socket
        mock_socket.getsockopt.return_value = 1  # Valid socket type
        
        self.telnet_conn.resulting_telnet_connection = mock_telnet_instance
        
        assert self.telnet_conn.is_connected is True

    def test_is_connected_false_no_connection(self):
        """Test is_connected returns False when no connection."""
        self.telnet_conn.resulting_telnet_connection = None
        
        assert self.telnet_conn.is_connected is False

    def test_is_connected_false_socket_error(self):
        """Test is_connected returns False when socket error occurs."""
        mock_telnet_instance = MagicMock()
        mock_telnet_instance.get_socket.side_effect = Exception("Socket error")
        
        self.telnet_conn.resulting_telnet_connection = mock_telnet_instance
        
        assert self.telnet_conn.is_connected is False

    @patch('router_test_kit.connection.logger')
    def test_disconnect(self, mock_logger):
        """Test Telnet disconnection."""
        mock_telnet_instance = MagicMock()
        self.telnet_conn.resulting_telnet_connection = mock_telnet_instance
        self.telnet_conn.destination_device = self.mock_device
        self.telnet_conn.destination_ip = self.destination_ip
        
        # Mock the socket behavior to simulate disconnection after close()
        mock_socket = MagicMock()
        mock_telnet_instance.get_socket.return_value = mock_socket
        
        # Track whether close() has been called
        close_called = False
        
        def close_side_effect():
            nonlocal close_called
            close_called = True
        
        def get_socket_side_effect():
            if close_called:
                raise Exception("Connection closed")
            return mock_socket
        
        mock_telnet_instance.close.side_effect = close_side_effect
        mock_telnet_instance.get_socket.side_effect = get_socket_side_effect
        mock_socket.getsockopt.return_value = 1  # Valid socket before close
        
        self.telnet_conn.disconnect()
        
        mock_telnet_instance.close.assert_called_once()
        # Should log disconnection
        mock_logger.info.assert_called_once()

    def test_disconnect_failure(self):
        """Test disconnect raises error if connection cannot be closed."""
        mock_telnet_instance = MagicMock()
        self.telnet_conn.resulting_telnet_connection = mock_telnet_instance
        self.telnet_conn.destination_device = self.mock_device
        self.telnet_conn.destination_ip = self.destination_ip
        
        # Mock socket to always return True (connection stays active even after close)
        mock_socket = MagicMock()
        mock_socket.getsockopt.return_value = 1  # Always returns valid socket type
        mock_telnet_instance.get_socket.return_value = mock_socket
        
        with pytest.raises(ConnectionError):
            self.telnet_conn.disconnect()

    def test_write_credentials_success(self):
        """Test successful credential writing."""
        mock_telnet_instance = MagicMock()
        mock_telnet_instance.expect.return_value = (0, b"login:", b"")
        
        self.telnet_conn.resulting_telnet_connection = mock_telnet_instance
        
        self.telnet_conn._write_credentials([b"login:"], "testuser")
        
        mock_telnet_instance.write.assert_called_once_with(b"testuser\r")

    def test_write_credentials_no_match(self):
        """Test credential writing when no match found."""
        mock_telnet_instance = MagicMock()
        mock_telnet_instance.expect.return_value = (-1, None, b"no match")
        
        self.telnet_conn.resulting_telnet_connection = mock_telnet_instance
        
        with pytest.raises(EOFError):
            self.telnet_conn._write_credentials([b"login:"], "testuser")

    def test_write_credentials_no_connection(self):
        """Test credential writing when no connection object."""
        self.telnet_conn.resulting_telnet_connection = None
        
        # Should not raise an exception, just log an error
        self.telnet_conn._write_credentials([b"login:"], "testuser")

    def test_occupied_decorator(self):
        """Test the occupied decorator functionality for Telnet."""
        self.telnet_conn._is_occupied = True
        
        with pytest.raises(ConnectionRefusedError):
            self.telnet_conn.connect(self.mock_device, self.destination_ip)
