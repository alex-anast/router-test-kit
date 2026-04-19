# Connection API

The connection module provides network connection management capabilities for communicating with remote devices.

**Recommended transport:** `SSHConnection` for Linux/Unix devices, `OneOS6SSHConnection` for OneOS6 routers.

**Deprecated:** `TelnetConnection` and `TelnetCLIConnection` rely on `telnetlib` (removed in Python 3.13). Migrate to SSH equivalents.

**OneOS6 support:** `OneOS6Mixin` provides vendor-specific CLI methods (`load_config`, `patch_config`, `unload_interface`, `unload_config`, `is_config_empty`, `reconfigure`). These are available through `OneOS6SSHConnection` and `OneOS6TelnetConnection`.

::: router_test_kit.connection
    options:
      show_root_heading: false
      show_source: true
      group_by_category: true
      members_order: source
      show_category_heading: true
