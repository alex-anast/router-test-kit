"""
Router Test Kit - A comprehensive framework for network device testing.

This package provides a flexible and extensible framework for testing routers,
network devices, and Linux systems with support for multiple connection types
and device protocols.

Key Features:
    - Multiple device type support (Linux, OneOS6, RADIUS, Host)
    - Secure SSH and Telnet connections
    - Plugin architecture for extensibility
    - Comprehensive testing utilities
    - Type-safe API with full type hints

Quick Start:
    ```python
    from router_test_kit.device import LinuxDevice
    from router_test_kit.connection import SSHConnection
    
    # Create device and establish connection
    device = LinuxDevice(username="admin", password="secure_pass")
    
    with SSHConnection() as conn:
        conn.connect(device, "192.168.1.100")
        result = conn.exec("ip route show")
        print(f"Routes: {result}")
    ```

Plugin System:
    The package supports plugins for extending device support:
    
    ```python
    from router_test_kit.plugins import get_plugin_manager
    
    manager = get_plugin_manager()
    manager.load_plugins()
    
    # Use plugin-provided device types
    device = manager.create_device("juniper", "admin", "password")
    ```

Author: Router Test Kit Development Team
License: MIT
Version: 0.2.0
"""

import logging

# Set up basic logging configuration
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Package metadata
__version__ = "0.2.0"
__author__ = "Router Test Kit Development Team"
__license__ = "MIT"
__email__ = "anastasioyaa@gmail.com"

# Import main classes for convenience
from .device import Device, LinuxDevice, OneOS6Device, RADIUSServer, HostDevice
from .connection import Connection, SSHConnection, TelnetConnection
from .static_utils import print_banner, ping, get_packet_loss, is_valid_ip
from .plugins import get_plugin_manager, auto_load_plugins, PluginManager, PluginError

# Auto-load plugins when package is imported
try:
    auto_load_plugins()
except (ImportError, AttributeError, PluginError) as e:
    # Don't fail package import if plugin loading fails
    logging.getLogger(__name__).warning("Plugin auto-loading failed: %s", e)

# Define public API
__all__ = [
    # Core classes
    "Device",
    "LinuxDevice", 
    "OneOS6Device",
    "RADIUSServer",
    "HostDevice",
    "Connection",
    "SSHConnection",
    "TelnetConnection",
    
    # Utilities
    "print_banner",
    "ping",
    "get_packet_loss",
    "is_valid_ip",
    
    # Plugin system
    "PluginManager",
    "PluginError",
    "get_plugin_manager",
    "auto_load_plugins",
    
    # Metadata
    "__version__",
    "__author__",
    "__license__",
    "__email__",
]