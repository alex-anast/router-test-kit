"""
Integration tests for SSHConnection transport layer.

These tests exercise the real paramiko SSH stack against a live OpenSSH
container (or an external server when RTK_SSH_* env vars are set).  They
replace the mock-heavy unit tests that previously tested the same happy paths
without real I/O.

Run with:
    docker compose -f docker-compose.test.yml up -d
    pytest tests/integration/ -v -m integration
"""

import pytest

from router_test_kit.connection import SSHConnection
from router_test_kit.device import LinuxDevice


@pytest.mark.integration
class TestSSHTransport:
    """Real-I/O tests for SSHConnection against a live SSH server."""

    @pytest.fixture(autouse=True)
    def _conn(self, ssh_server):
        """Provide a fresh SSHConnection for each test; auto-disconnect on teardown."""
        self.server = ssh_server
        self.device = LinuxDevice(
            username=ssh_server["username"],
            password=ssh_server["password"],
        )
        self.conn = SSHConnection(timeout=15)
        yield
        if self.conn.is_connected:
            self.conn.disconnect()

    # ── connect / disconnect ──────────────────────────────────────────────────

    def test_connect_returns_self(self):
        result = self.conn.connect(
            self.device, self.server["host"], port=self.server["port"]
        )
        assert result is self.conn

    def test_connect_sets_is_connected(self):
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        assert self.conn.is_connected is True

    def test_disconnect_clears_is_connected(self):
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        self.conn.disconnect()
        assert self.conn.is_connected is False

    def test_reconnect_after_disconnect(self):
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        self.conn.disconnect()
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        assert self.conn.is_connected is True

    # ── write_command ─────────────────────────────────────────────────────────

    def test_write_command_echo(self):
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        result = self.conn.write_command("echo hello_rtk")
        assert result is not None
        assert "hello_rtk" in result

    def test_write_command_multiple_sequential(self):
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        r1 = self.conn.write_command("echo first")
        r2 = self.conn.write_command("echo second")
        r3 = self.conn.write_command("echo third")
        assert r1 is not None and "first" in r1
        assert r2 is not None and "second" in r2
        assert r3 is not None and "third" in r3

    def test_write_command_returns_stdout(self):
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        result = self.conn.write_command("printf 'line1\\nline2\\n'")
        assert result is not None
        assert "line1" in result
        assert "line2" in result

    def test_write_command_with_env_variable(self):
        self.conn.connect(self.device, self.server["host"], port=self.server["port"])
        result = self.conn.write_command("echo $HOME")
        assert result is not None
        assert "/" in result  # HOME is always a path

    # ── error paths (real network errors, no mocks needed) ───────────────────

    def test_connect_wrong_password_raises(self):
        bad_device = LinuxDevice(
            username=self.server["username"], password="wrongpassword"
        )
        with pytest.raises(ConnectionAbortedError):
            self.conn.connect(bad_device, self.server["host"], port=self.server["port"])

    def test_connect_unreachable_port_raises(self):
        with pytest.raises(ConnectionAbortedError):
            self.conn.connect(self.device, "127.0.0.1", port=19999)
