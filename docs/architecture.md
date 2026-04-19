# Architecture Overview

Router Test Kit is structured around three abstractions: **Devices** (what you're testing), **Connections** (how you talk to them), and **Plugins** (how you extend either). This page walks through each layer and how they fit together.

---

## Devices

A `Device` is a plain data container that holds the credentials and identity of a network endpoint.

```
Device
├── LinuxDevice     – Linux/Unix hosts and VMs (default prompt: $)
├── OneOS6Device    – OneOS6 routers/switches   (default prompt: >)
│   └── RADIUSServer – RADIUS-authenticated Linux host
└── HostDevice      – local host (runs commands via subprocess, no network)
```

Device objects carry no connection logic. They expose:

- `username`, `password`, `hostname` – authentication info
- `DEFAULT_USERNAME`, `DEFAULT_PASSWORD`, `DEFAULT_PROMPT_SYMBOL` – class-level defaults

`Connection` decorators use `isinstance` checks against these classes to enforce that a method like `set_sudo()` is only called on a `LinuxDevice`, not on a `OneOS6Device`.

---

## Connections

`Connection` is an abstract base class (`abc.ABC`) that defines the interface every transport implementation must follow.

```
Connection (ABC)
├── SSHConnection              – paramiko-based SSH shell session
│   └── OneOS6SSHConnection    – SSHConnection + OneOS6Mixin CLI methods
├── TelnetConnection           – telnetlib-based Telnet session  ⚠ deprecated
│   └── OneOS6TelnetConnection – TelnetConnection + OneOS6Mixin CLI methods
└── TelnetCLIConnection        – Telnet hop via an existing TelnetConnection
```

### OneOS6Mixin — vendor-specific CLI methods

`OneOS6Mixin` provides six OneOS6-specific methods (`load_config`, `patch_config`, `unload_interface`, `unload_config`, `is_config_empty`, `reconfigure`) that are mixed into concrete connection classes via multiple inheritance:

- `OneOS6SSHConnection(OneOS6Mixin, SSHConnection)` — recommended for OneOS6 devices
- `OneOS6TelnetConnection(OneOS6Mixin, TelnetConnection)` — deprecated; prefer SSH

```python
from router_test_kit import OneOS6SSHConnection, OneOS6Device

device = OneOS6Device(username="admin", password="secret")
conn = OneOS6SSHConnection(timeout=30)
conn.connect(device, "10.0.0.1")
conn.load_config("/path/to/config.cfg")
conn.reconfigure()
```

### Connection lifecycle

```
device  = LinuxDevice(username="admin", password="secret")
conn    = SSHConnection(timeout=30)

conn.connect(device, "10.0.0.1")   # opens transport, sets prompt_symbol
conn.write_command("show version")  # sends command, reads until prompt
conn.disconnect()                   # closes transport, frees state
```

`SSHConnection` opens an interactive shell channel (not `exec_command`) so it can handle multi-step interactions like privilege escalation.

### Runtime decorators

Three decorator functions are defined inside `Connection` and used by subclasses:

| Decorator | Guards against |
|---|---|
| `@check_occupied` | method called while the connection is already in use by another thread or hop |
| `@check_device_type(type)` | method called on the wrong device type (e.g. calling `set_sudo` on an OneOS6 device) |
| `@check_connection` | method called before `connect()` has been called |

These are applied at the method level rather than subclass level, so each method explicitly declares what it requires. The checks raise `ConnectionRefusedError`, `TypeError`, or `ConnectionError` respectively.

### TelnetCLIConnection — Telnet hop

`TelnetCLIConnection` wraps an already-open `TelnetConnection` and issues a `telnet <ip>` command through it, acting as a second hop. On `disconnect()` / `exit()`, it writes `exit` to the shell and releases the parent connection back to available state.

```
host ──SSH──► router_A ──Telnet──► router_B
               TelnetConnection     TelnetCLIConnection
```

---

## Plugin system

The plugin system lets external packages register new device types without modifying the core library. Discovery uses Python's `importlib.metadata` entry points.

### Registration

External packages declare device classes in their `pyproject.toml`:

```toml
[project.entry-points."router_test_kit.devices"]
juniper = "rtk_plugin_juniper:JuniperDevice"
```

The registered class must inherit from `router_test_kit.device.Device`.

### Loading

`PluginManager` is a singleton. On `import router_test_kit`, `auto_load_plugins()` calls `PluginManager.get_instance().load_plugins()`, which:

1. Calls `importlib.metadata.entry_points().select(group="router_test_kit.devices")`
2. For each entry point: loads the class, validates it inherits `Device`, registers it by name
3. Built-in device types (`linux`, `oneos6`, `radius`, `host`) are registered first in `_register_builtin_devices()`

Plugin load failures are logged as warnings but do not prevent the package from importing.

### Usage

```python
from router_test_kit import get_plugin_manager

manager = get_plugin_manager()
devices = manager.get_available_devices()   # dict[str, type[Device]]

# Instantiate by name (if the plugin is installed)
juniper = devices["juniper"](username="admin", password="secret")
```

---

## End-to-end flow

```
1. Instantiate device:      device = LinuxDevice(username="admin", password="pw")
2. Instantiate connection:  conn   = SSHConnection(timeout=30)
3. Connect:                 conn.connect(device, "10.0.0.1")
                              └─ sets prompt_symbol from device.DEFAULT_PROMPT_SYMBOL
                              └─ flushes welcome banner
4. Execute commands:        output = conn.write_command("ip route show")
                              └─ sends bytes over the shell channel
                              └─ reads until prompt_symbol appears in recv buffer
5. Higher-level helpers:    conn.ping("10.0.0.2")   # wraps write_command
                            conn.set_sudo()           # checks device type first
6. Disconnect:              conn.disconnect()
                              └─ closes channel and transport
```

---

## Deprecations

**Telnet support** (`TelnetConnection`, `TelnetCLIConnection`) relies on the standard-library `telnetlib` module, which was removed in Python 3.13. Both classes emit a `DeprecationWarning` on instantiation. Prefer `SSHConnection` for all new code. See `CHANGELOG.md` at the repo root for the migration roadmap.

---

## Non-goals

- **Test orchestration** — Router Test Kit provides device fixtures. Test collection, parameterisation, and reporting are left to pytest.
- **Configuration management** — the library can push configs but doesn't store or diff them; that belongs in your test fixtures.
- **Async I/O** — all connection methods are synchronous. For concurrent device testing, use pytest-xdist or standard threading at the test layer.
