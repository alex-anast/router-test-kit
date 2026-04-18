# Router Test Kit

[![CI](https://github.com/alex-anast/router-test-kit/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/alex-anast/router-test-kit/actions)
[![PyPI version](https://img.shields.io/pypi/v/router-test-kit)](https://pypi.org/project/router-test-kit/)
[![Python](https://img.shields.io/badge/python-3.9%20–%203.12-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/alex-anast/router-test-kit)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://alex-anast.github.io/router-test-kit/)

A Python framework for automated testing of network devices — OneOS6 routers, Cisco-compatible devices, Linux hosts, and RADIUS servers — over SSH and Telnet. Device types are registered via Python entry points, so external packages can contribute new device types without modifying the core library.

## Installation

```bash
pip install router-test-kit
```

## Testing

Three-tier test strategy: **unit** (mocks, no Docker) → **integration** (real SSH via Docker) → **hardware** (real OneOS6 devices, opt-in). See [docs/testing.md](docs/testing.md) for setup and usage.

## Quick start

```python
from router_test_kit.device import LinuxDevice
from router_test_kit.connection import SSHConnection

device = LinuxDevice(username="admin", password="secret")
conn = SSHConnection(timeout=10).connect(device, "192.168.1.100")
try:
    output = conn.write_command("ip route show")
    print(output)
finally:
    conn.disconnect()
```

`SSHConnection.connect` accepts an optional `port` (default `22`), so non-standard SSH ports work without any subclassing:

```python
conn = SSHConnection().connect(device, "192.168.1.100", port=2222)
```

## Supported devices

| Device type | Class | Transport |
|---|---|---|
| Linux / Unix host | `LinuxDevice` | SSH, Telnet |
| OneOS6 router | `OneOS6Device` | SSH, Telnet |
| RADIUS server | `RADIUSServer` | SSH |
| Local host | `HostDevice` | subprocess |

**Note:** Telnet support uses the standard-library `telnetlib` module, which was removed in Python 3.13. This package requires Python `>=3.9,<3.13` until a replacement lands. `TelnetConnection` emits a `DeprecationWarning` on instantiation — prefer `SSHConnection` where possible.

## Plugin system

New device types are registered via Python entry points. To add a device type from an external package, declare it in the package's `pyproject.toml`:

```toml
[project.entry-points."router_test_kit.devices"]
juniper = "rtk_plugin_juniper:JuniperDevice"
```

The class must inherit from `router_test_kit.device.Device`. At import time, `router_test_kit` auto-discovers and loads all registered plugins.

```python
from router_test_kit import get_plugin_manager

manager = get_plugin_manager()
devices = manager.get_available_devices()  # includes built-ins + plugins

juniper = manager.create_device("juniper", username="admin", password="secret")
```

## Examples

- [`examples/example1_connect.py`](examples/example1_connect.py) — basic device connection
- [`examples/example2_ping_between_vms.py`](examples/example2_ping_between_vms.py) — inter-VM connectivity testing
- [`examples/advanced_ipsec_test/`](examples/advanced_ipsec_test/) — IPSec tunnel verification on OneOS6

## Documentation

Full API reference and usage guide: [alex-anast.github.io/router-test-kit](https://alex-anast.github.io/router-test-kit/)

Design overview (device hierarchy, connection abstraction, plugin discovery): [docs/architecture.md](docs/architecture.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding conventions, and the release process.

```bash
git clone https://github.com/alex-anast/router-test-kit.git
cd router-test-kit
pip install -e ".[dev]"
python -m pytest tests/unit/ -v
ruff check src/ tests/
```

## License

MIT — see [LICENSE](LICENSE).
