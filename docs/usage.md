# How to Use

This page walks through the everyday workflow: registering a device, opening a connection, running commands, and tearing the connection down. For design background (class hierarchy, plugin system) see [architecture.md](architecture.md); for how the test tiers relate to each other see [testing.md](testing.md).

## Core concepts

Two objects drive every test:

- **`device.Device`** — describes *what* you're talking to and carries the credentials. Pick the subclass that matches the target OS: `LinuxDevice`, `OneOS6Device`, `RADIUSServer`, or `HostDevice` (for local subprocess execution). External packages can register their own device types via the plugin system.
- **`connection.Connection`** — describes *how* you reach the device. `SSHConnection` is the recommended transport for all new code. `TelnetConnection` exists for legacy kit but emits a `DeprecationWarning` (the stdlib `telnetlib` module was removed in Python 3.13).

## Minimal SSH example

```python
from router_test_kit.connection import SSHConnection
from router_test_kit.device import LinuxDevice

device = LinuxDevice(username="user", password="password")
conn = SSHConnection(timeout=10).connect(device, "192.168.10.10")
try:
    output = conn.write_command("uname -a")
    print(output)
finally:
    conn.disconnect()
```

`connect()` returns `self`, so it chains cleanly off the constructor. `write_command()` returns the command's stdout as a string (or `None` if the channel is closed).

## Non-standard SSH ports

`SSHConnection.connect` takes an optional `port` parameter (default `22`). This is how the integration test suite points at the Docker OpenSSH container running on `2222` without any subclassing:

```python
conn = SSHConnection().connect(device, "127.0.0.1", port=2222)
```

## Telnet (legacy)

Only use this if you genuinely need it — it triggers a `DeprecationWarning` and requires Python `<3.13`:

```python
from router_test_kit.connection import TelnetConnection

conn = TelnetConnection(timeout=10).connect(device, "192.168.10.10")
```

For a second hop (e.g., host → router_A over Telnet → router_B over Telnet), see `TelnetCLIConnection` in [architecture.md](architecture.md#telnetcliconnection--telnet-hop). It is intentionally not re-exported from the package root because new code should not reach for it.

## Running end-to-end examples

- [`examples/example1_connect.py`](https://github.com/alex-anast/router-test-kit/blob/main/examples/example1_connect.py) — connect to a Linux VM over SSH, assert, disconnect.
- [`examples/example2_ping_between_vms.py`](https://github.com/alex-anast/router-test-kit/blob/main/examples/example2_ping_between_vms.py) — multi-hop connectivity check.
- [`examples/advanced_ipsec_test/`](https://github.com/alex-anast/router-test-kit/tree/main/examples/advanced_ipsec_test) — full IPSec verification flow against OneOS6 routers (Telnet-based, preserved as a legacy reference).

## Writing a pytest

```python
import pytest
from router_test_kit.connection import SSHConnection
from router_test_kit.device import LinuxDevice


@pytest.mark.integration
def test_host_reports_kernel(ssh_server):
    device = LinuxDevice(
        username=ssh_server["username"], password=ssh_server["password"]
    )
    conn = SSHConnection(timeout=10)
    conn.connect(device, ssh_server["host"], port=ssh_server["port"])
    try:
        assert "Linux" in (conn.write_command("uname -s") or "")
    finally:
        conn.disconnect()
```

The `ssh_server` fixture is provided by `tests/integration/conftest.py`; it spins up the Docker OpenSSH container on demand. Run only the integration tier with `pytest -m integration`; see [testing.md](testing.md) for the other tiers.
