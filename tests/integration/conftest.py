"""
Pytest fixtures for integration tests.

Integration tests run against real services (Docker containers or external
servers) rather than mocks.  The session-scoped `ssh_server` fixture manages
the container lifecycle automatically, unless the caller already has a server
running (detected via RTK_SSH_* environment variables).

Environment variables:
    RTK_SSH_HOST        Override host (default: localhost via Docker)
    RTK_SSH_PORT        Override port (default: 2222)
    RTK_SSH_USER        Override username (default: testuser)
    RTK_SSH_PASSWORD    Override password (default: testpass)
    RTK_HARDWARE_LAB    Set to "1" to run @pytest.mark.hardware tests
"""

import os
import socket
import subprocess
import time
from collections.abc import Generator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
COMPOSE_FILE = REPO_ROOT / "docker-compose.test.yml"

_DEFAULT_HOST = "localhost"
_DEFAULT_PORT = 2222
_DEFAULT_USERNAME = "testuser"
_DEFAULT_PASSWORD = "testpass"

_DEFAULT = {
    "host": _DEFAULT_HOST,
    "port": _DEFAULT_PORT,
    "username": _DEFAULT_USERNAME,
    "password": _DEFAULT_PASSWORD,
}

_ENV_OVERRIDE = all(
    os.environ.get(k)
    for k in ("RTK_SSH_HOST", "RTK_SSH_PORT", "RTK_SSH_USER", "RTK_SSH_PASSWORD")
)


def _wait_for_port(host: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(
        f"SSH server at {host}:{port} did not become ready within {timeout}s"
    )


@pytest.fixture(scope="session")
def ssh_server() -> Generator[dict, None, None]:
    """
    Yields connection info dict for the test SSH server.

    Starts a Docker container if RTK_SSH_* env vars are not all set.
    Tears it down after the session ends.
    """
    if _ENV_OVERRIDE:
        yield {
            "host": os.environ["RTK_SSH_HOST"],
            "port": int(os.environ["RTK_SSH_PORT"]),
            "username": os.environ["RTK_SSH_USER"],
            "password": os.environ["RTK_SSH_PASSWORD"],
        }
        return

    subprocess.run(
        ["docker-compose", "-f", str(COMPOSE_FILE), "up", "-d"],
        check=True,
        capture_output=True,
    )
    try:
        _wait_for_port(_DEFAULT_HOST, _DEFAULT_PORT)
        # Extra settle time for sshd to finish initialising inside the container
        time.sleep(2)
        yield dict(_DEFAULT)
    finally:
        subprocess.run(
            ["docker-compose", "-f", str(COMPOSE_FILE), "down", "-v"],
            capture_output=True,
        )


def pytest_collection_modifyitems(config, items):
    """Auto-skip @pytest.mark.hardware tests unless RTK_HARDWARE_LAB=1."""
    if os.environ.get("RTK_HARDWARE_LAB") == "1":
        return
    skip = pytest.mark.skip(reason="Set RTK_HARDWARE_LAB=1 to run hardware tests")
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip)
