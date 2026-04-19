"""
Integration tests for Linux-specific SSH command paths.

Tests exercise real command paths in connection.py against the live SSH container:
    - is_root property (whoami output)
    - _get_interfaces (ip a output)
    - _get_interface named/unnamed lookups
    - polymorphic ping() via LinuxDevice.ping_command()

Run with:
    docker compose -f docker-compose.test.yml up -d
    pytest tests/integration/ -v -m integration
"""

import pytest

from router_test_kit.connection import SSHConnection
from router_test_kit.device import LinuxDevice


@pytest.mark.integration
class TestSSHLinuxCommands:
    """Real-I/O tests for Linux-command paths against a live SSH server."""

    @pytest.fixture(autouse=True)
    def _conn(self, ssh_server):
        """Provide a connected SSHConnection for each test; auto-disconnect on teardown."""
        self.server = ssh_server
        self.device = LinuxDevice(
            username=ssh_server["username"],
            password=ssh_server["password"],
        )
        self.conn = SSHConnection(timeout=15)
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        yield
        if self.conn.is_connected:
            self.conn.disconnect()

    def test_is_root_returns_false_for_nonroot_user(self):
        """is_root property returns False when SSH user is not root (testuser)."""
        assert self.conn.is_root is False

    def test_get_interfaces_returns_nonempty_list(self):
        """_get_interfaces() returns a non-empty list of interface entries."""
        interfaces = self.conn._get_interfaces()
        assert isinstance(interfaces, list)
        assert len(interfaces) > 0
        # Each entry should contain interface metadata (number: name: pattern)
        assert any(": " in line for line in interfaces)

    def test_get_interface_named_lo_returns_matching_line(self):
        """_get_interface('lo') returns a non-None string containing 'lo'."""
        line = self.conn._get_interface("lo")
        assert line is not None
        assert "lo" in line

    def test_get_interface_nonexistent_returns_none(self):
        """_get_interface with an unknown interface name returns None."""
        assert self.conn._get_interface("doesnotexist0") is None

    def test_ping_polymorphic_dispatch_to_localhost(self):
        """ping() delegates to LinuxDevice.ping_command() and returns real output."""
        output = self.conn.ping("127.0.0.1", nbr_packets=1)
        assert output is not None
        assert "127.0.0.1" in output

    def test_ping_before_connect_raises_connection_error(self):
        """_check_connection guard raises ConnectionError when called before connect."""
        fresh_conn = SSHConnection(timeout=15)
        with pytest.raises(ConnectionError):
            fresh_conn.ping("127.0.0.1")

    def test_check_device_type_mismatch_raises_value_error(self):
        """_check_device_type guard raises ValueError when device type does not match."""
        from router_test_kit.device import OneOS6Device

        fresh_conn = SSHConnection(timeout=15)
        fresh_conn.destination_device = OneOS6Device()  # type: ignore[assignment]
        with pytest.raises(ValueError, match="available only for linux"):
            fresh_conn.set_sudo()

    def test_check_device_type_not_connected_raises_connection_error(self):
        """_check_device_type guard raises ConnectionError when device type matches but not connected."""
        fresh_conn = SSHConnection(timeout=15)
        fresh_conn.destination_device = LinuxDevice(
            username=self.server["username"], password=self.server["password"]
        )
        with pytest.raises(ConnectionError):
            fresh_conn.set_sudo()

    def test_set_interface_ip_nonroot_raises_permission_error(self):
        """_check_device_type guard raises PermissionError when is_root=True but user is not root."""
        with pytest.raises(PermissionError):
            self.conn.set_interface_ip("eth0", "10.0.0.1")

    def test_flush_deep_runs_without_raising(self):
        """flush_deep() drains SSH channel with retry logic and does not raise."""
        self.conn.write_command("echo ready")
        self.conn.flush_deep(time_interval=0.1, retries_timeout=5)
