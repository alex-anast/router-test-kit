# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pre-commit hooks (`.pre-commit-config.yaml`) running `ruff` (lint + format with auto-fix) and `mypy` on every commit.
- `examples/advanced_ipsec_test/conftest.py` providing colour codes, path constants, parametrize data, and a `sudo_password` fixture so the legacy IPSec example is runnable out of the box.
- Architecture overview page (`docs/architecture.md`) describing the Device / Connection / Plugin abstractions, linked from the README and MkDocs nav.

### Changed
- Python compatibility is now capped at `<3.13` while `telnetlib` is the Telnet backend.
- Legacy IPSec example (`examples/advanced_ipsec_test/test_ipsec.py`) now imports from the installed `router_test_kit` package instead of the removed `src.*` layout and the `sys.path.insert` hack.
- Python version badge in README replaced with a static `3.9 – 3.12` badge reflecting `requires-python`.
- `docs/usage.md` rewritten to match the current SSH-first API, document the optional `port` parameter, and cross-link the testing tiers.
- README and package docstring Quick Start snippets replaced: both showed a non-existent `with SSHConnection() as conn: … conn.exec(...)` API; now use the actual `connect().write_command()` flow.
- `ruff` / `mypy` lower bounds in `[dev]` extras tightened to `>=0.9.0` / `>=1.14.1` to match the pre-commit pins.

### Deprecated
- `TelnetConnection` and `TelnetCLIConnection` emit a `DeprecationWarning` on instantiation. Migrate to `SSHConnection` for future compatibility.

### Fixed
- All `mypy` errors in `src/` resolved: proper `Optional` annotations on `Connection` attributes, module-level guard decorators with `Callable[..., Any]` typing, `assert` guards before `Optional` attribute access, and targeted `# type: ignore[attr-defined]` comments for OneOS6-only attribute access reached under `@_check_device_type("oneos")`.
- All `ruff` lint violations resolved across `src/`, `tests/`, and `examples/` (UP035/UP006, E402, B904, E722, B024, B017, F841, I001, B007, E741).
- `setup_logger()` is now idempotent — repeat calls no longer attach duplicate file handlers.

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
