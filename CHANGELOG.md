# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `OneOS6Mixin` holding all OneOS6-specific CLI methods (`load_config`, `patch_config`, `unload_interface`, `unload_config`, `is_config_empty`, `reconfigure`).
- `OneOS6SSHConnection(OneOS6Mixin, SSHConnection)` — recommended transport for OneOS6 devices over SSH.
- `OneOS6TelnetConnection(OneOS6Mixin, TelnetConnection)` — Telnet variant (deprecated; prefer SSH).
- Both new classes exported from `router_test_kit` and listed in `__all__`.
- `Device.ping_command(ip, count, timeout)` abstract method; overridden in `LinuxDevice`, `OneOS6Device`, and `HostDevice`. Plugin-provided device types get ping support by implementing one method.
- Pre-commit hooks (`.pre-commit-config.yaml`) running `ruff` (lint + format with auto-fix) and `mypy` on every commit.
- `examples/advanced_ipsec_test/conftest.py` providing colour codes, path constants, parametrize data, and a `sudo_password` fixture so the legacy IPSec example is runnable out of the box.
- Architecture overview page (`docs/architecture.md`) describing the Device / Connection / Plugin abstractions, linked from the README and MkDocs nav.

### Changed
- `Connection.connect()` signature normalized across all transports: `(device, ip, port: Optional[int] = None)`. Each transport resolves its own default port internally (SSH → 22, Telnet → 23). Fixes Liskov substitution violation.
- `Connection.ping()` replaced with a polymorphic implementation that delegates to `device.ping_command()`; removes the hardcoded `if device.type == "oneos"` branch.
- `HostDevice` is now a proper `Device` subclass (was a standalone class). The special-case bypass in `PluginManager._validate_plugin` is removed.
- OneOS6-specific CLI methods removed from `Connection` base class — use `OneOS6SSHConnection` / `OneOS6TelnetConnection` instead.
- Python compatibility is now capped at `<3.13` while `telnetlib` is the Telnet backend.
- Legacy IPSec example (`examples/advanced_ipsec_test/test_ipsec.py`) now imports from the installed `router_test_kit` package instead of the removed `src.*` layout and the `sys.path.insert` hack.
- Python version badge in README replaced with a static `3.9 – 3.12` badge reflecting `requires-python`.
- `docs/usage.md` rewritten to match the current SSH-first API, document the optional `port` parameter, and cross-link the testing tiers.
- README and package docstring Quick Start snippets replaced: both showed a non-existent `with SSHConnection() as conn: … conn.exec(...)` API; now use the actual `connect().write_command()` flow.
- `ruff` / `mypy` lower bounds in `[dev]` extras tightened to `>=0.9.0` / `>=1.14.1` to match the pre-commit pins.

### Deprecated
- `TelnetConnection` and `TelnetCLIConnection` emit a `DeprecationWarning` on instantiation. Migrate to `SSHConnection` for future compatibility.

### Removed
- `Connection.hping3()` — no callers found in tests or examples.
- Six OneOS6-specific methods from `Connection` base (`load_config`, `patch_config`, `unload_interface`, `unload_config`, `is_config_empty`, `reconfigure`). Migrate to `OneOS6SSHConnection` / `OneOS6TelnetConnection`.

### Fixed
- `reboot_device()` in `static_utils` called `get_packet_loss(vm_ip)` (passing an IP string) instead of `get_packet_loss(ping(vm_ip))`. Packet loss comparison also fixed from `== 0` (int) to `== "0"` (str, matching `get_packet_loss` return type).
- All `mypy` errors in `src/` resolved: proper `Optional` annotations on `Connection` attributes, module-level guard decorators with `Callable[..., Any]` typing, `assert` guards before `Optional` attribute access, and targeted `# type: ignore[attr-defined]` comments for OneOS6-only attribute access reached under `@_check_device_type("oneos")`.
- All `ruff` lint violations resolved across `src/`, `tests/`, and `examples/` (UP035/UP006, E402, B904, E722, B024, B017, F841, I001, B007, E741).
- `setup_logger()` is now idempotent — repeat calls no longer attach duplicate file handlers.
- `Connection.is_root` used byte-string patterns (`rb"\$"`, `b"#"`) in `write_command`, which raised `TypeError` when used via `SSHConnection` (response is decoded to `str`). Fixed to use string patterns (`r"\$"`, `"#"`).

### Added (coverage lift)
- Integration tests for Linux-command paths against the real SSH container (`tests/integration/test_ssh_linux_commands.py`): `is_root`, `_get_interfaces`, `_get_interface`, and polymorphic `ping()`.
- Integration tests for connection-lifecycle error paths: `_check_occupied` guard, `_check_connection` guard via `write_command` before connect, and `flush()` after a real command.
- Codecov reporting split into `unit` and `integration` flags for per-tier visibility.

### Changed (coverage lift)
- Coverage threshold enforced at 80% via `[tool.coverage.report] fail_under = 80`.
- Deprecated `TelnetConnection` and `TelnetCLIConnection` excluded from coverage measurement via `exclude_also` (scheduled for removal when Python 3.13 drops `telnetlib`).

## [0.2.0] - 2025-08-09

### Added
- Plugin system for extensible device support using Python entry points
  - Automatic plugin discovery and loading via `importlib.metadata`
  - Device validation with inheritance checking
  - Singleton `PluginManager` for centralized control
  - Support for external package device extensions
- Automated release pipeline: GitHub releases on version tags, PyPI trusted publishing, release notes from git history

### Changed
- Modular plugin-based architecture for extensibility
- Standardised logging format across all modules
- Enhanced CI/CD workflow with security scanning and automated releases

## [0.1.0] - 2024-09-05

### Added
- Initial release of Router Test Kit
- SSH and Telnet connection management with automatic retry
- Device abstraction: `LinuxDevice`, `OneOS6Device`, `RADIUSServer`, `HostDevice`
- Network utilities: ping, packet loss parsing, IP validation, SCP transfer
- MkDocs documentation site deployed to GitHub Pages
- CI/CD pipeline with GitHub Actions
- PyPI package publishing via `pyproject.toml`
