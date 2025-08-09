"""
Plugin system for Router Test Kit.

This module provides a plugin architecture that allows external packages to register
new device types without modifying the core library code. The system uses Python's
entry points mechanism for automatic plugin discovery and registration.

Security Notice:
    Plugin loading can execute arbitrary code. Only install plugins from trusted sources.
    The plugin system validates that registered plugins inherit from the Device base class.

Example:
    External plugin registration in setup.py or pyproject.toml:
    
    [project.entry-points."router_test_kit.devices"]
    juniper = "rtk_plugin_juniper:JuniperDevice"
    fortinet = "rtk_plugin_fortinet:FortinetDevice"

Author: Router Test Kit Development Team
License: MIT
"""

import logging
import importlib.metadata
from typing import Dict, Type, Optional, List, Any
from abc import ABC

from .device import Device

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Raised when plugin loading or validation fails."""
    pass


class PluginManager:
    """
    Manages plugin discovery, loading, and registration for Router Test Kit.
    
    The PluginManager uses Python's entry points system to automatically discover
    and load device plugins from installed packages. Plugins must inherit from
    the Device base class and be properly registered in their package metadata.
    
    Attributes:
        _registered_devices: Dictionary mapping device names to device classes
        _loaded_plugins: Set of successfully loaded plugin names
        
    Example:
        ```python
        from router_test_kit.plugins import PluginManager
        
        # Get the global plugin manager instance
        manager = PluginManager.get_instance()
        
        # Load all available plugins
        manager.load_plugins()
        
        # Get available device types
        devices = manager.get_available_devices()
        print(f"Available devices: {list(devices.keys())}")
        
        # Create a device instance
        if "juniper" in devices:
            juniper_class = devices["juniper"]
            device = juniper_class(username="admin", password="secret")
        ```
    """
    
    _instance: Optional['PluginManager'] = None
    
    def __init__(self) -> None:
        """Initialize the plugin manager."""
        self._registered_devices: Dict[str, Type[Device]] = {}
        self._loaded_plugins: List[str] = []
        self._failed_plugins: List[str] = []
        
        # Register built-in devices
        self._register_builtin_devices()
    
    @classmethod
    def get_instance(cls) -> 'PluginManager':
        """
        Get the singleton instance of the plugin manager.
        
        Returns:
            PluginManager: The global plugin manager instance
            
        Example:
            ```python
            manager = PluginManager.get_instance()
            manager.load_plugins()
            ```
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _register_builtin_devices(self) -> None:
        """Register built-in device types from the core library."""
        from .device import LinuxDevice, OneOS6Device, RADIUSServer, HostDevice
        
        builtin_devices = {
            "linux": LinuxDevice,
            "oneos6": OneOS6Device,
            "radius": RADIUSServer,
            "host": HostDevice,  # Special case: doesn't inherit from Device
        }
        
        for name, device_class in builtin_devices.items():
            self._registered_devices[name] = device_class
            logger.debug(f"Registered built-in device: {name}")
    
    def load_plugins(self, group_name: str = "router_test_kit.devices") -> None:
        """
        Load all available plugins from the specified entry point group.
        
        Args:
            group_name: Entry point group name for device plugins
            
        Raises:
            PluginError: If plugin loading fails critically
            
        Example:
            ```python
            manager = PluginManager.get_instance()
            
            # Load default device plugins
            manager.load_plugins()
            
            # Load from custom entry point group
            manager.load_plugins("my_company.network_devices")
            ```
        """
        logger.info(f"Loading plugins from entry point group: {group_name}")
        
        try:
            entry_points = importlib.metadata.entry_points()
            device_plugins = entry_points.select(group=group_name)
        except Exception as e:
            logger.warning(f"Failed to discover entry points: {e}")
            return
        
        for entry_point in device_plugins:
            try:
                self._load_single_plugin(entry_point)
            except Exception as e:
                error_msg = f"Failed to load plugin '{entry_point.name}': {e}"
                logger.error(error_msg)
                self._failed_plugins.append(entry_point.name)
    
    def _load_single_plugin(self, entry_point) -> None:
        """
        Load and validate a single plugin from an entry point.
        
        Args:
            entry_point: Entry point object representing the plugin
            
        Raises:
            PluginError: If plugin validation fails
        """
        plugin_name = entry_point.name
        
        try:
            # Load the plugin class
            device_class = entry_point.load()
            
            # Validate the plugin
            self._validate_plugin(device_class, plugin_name)
            
            # Register the plugin
            self._registered_devices[plugin_name] = device_class
            self._loaded_plugins.append(plugin_name)
            
            logger.info(f"Successfully loaded plugin: {plugin_name} -> {device_class.__name__}")
            
        except ImportError as e:
            raise PluginError(f"Cannot import plugin '{plugin_name}': {e}")
        except Exception as e:
            raise PluginError(f"Plugin loading failed for '{plugin_name}': {e}")
    
    def _validate_plugin(self, device_class: Any, plugin_name: str) -> None:
        """
        Validate that a plugin meets the requirements.
        
        Args:
            device_class: The device class to validate
            plugin_name: Name of the plugin for error reporting
            
        Raises:
            PluginError: If validation fails
        """
        # Check if it's a class
        if not isinstance(device_class, type):
            raise PluginError(f"Plugin '{plugin_name}' must be a class, got {type(device_class)}")
        
        # Special case for HostDevice which doesn't inherit from Device
        if plugin_name == "host":
            logger.debug("Plugin '%s' validation passed (special case)", plugin_name)
            return
        
        # Check inheritance from Device
        if not issubclass(device_class, Device):
            raise PluginError(
                f"Plugin '{plugin_name}' class {device_class.__name__} "
                f"must inherit from router_test_kit.device.Device"
            )
        
        # Check required attributes/methods
        required_attrs = ['username', 'password']
        for attr in required_attrs:
            if not hasattr(device_class, attr):
                logger.warning(
                    "Plugin '%s' missing recommended attribute: %s", plugin_name, attr
                )
        
        logger.debug("Plugin '%s' validation passed", plugin_name)
    
    def register_device(self, name: str, device_class: Any) -> None:
        """
        Manually register a device class.
        
        Args:
            name: Unique name for the device type
            device_class: Device class that inherits from Device
            
        Raises:
            PluginError: If device registration fails
            
        Example:
            ```python
            class CustomDevice(Device):
                def __init__(self, username: str, password: str):
                    super().__init__(username, password)
            
            manager = PluginManager.get_instance()
            manager.register_device("custom", CustomDevice)
            ```
        """
        try:
            self._validate_plugin(device_class, name)
            
            if name in self._registered_devices:
                logger.warning("Overriding existing device registration: %s", name)
            
            self._registered_devices[name] = device_class
            logger.info("Manually registered device: %s -> %s", name, device_class.__name__)
            
        except Exception as e:
            raise PluginError(f"Failed to register device '{name}': {e}") from e
    
    def get_available_devices(self) -> Dict[str, Type[Device]]:
        """
        Get all registered device types.
        
        Returns:
            Dictionary mapping device names to device classes
            
        Example:
            ```python
            manager = PluginManager.get_instance()
            devices = manager.get_available_devices()
            
            for name, device_class in devices.items():
                print(f"{name}: {device_class.__name__}")
            ```
        """
        return self._registered_devices.copy()
    
    def get_device_class(self, name: str) -> Optional[Type[Device]]:
        """
        Get a specific device class by name.
        
        Args:
            name: Name of the device type
            
        Returns:
            Device class if found, None otherwise
            
        Example:
            ```python
            manager = PluginManager.get_instance()
            linux_class = manager.get_device_class("linux")
            
            if linux_class:
                device = linux_class("admin", "password")
            ```
        """
        return self._registered_devices.get(name)
    
    def create_device(self, device_type: str, username: str, password: str, **kwargs) -> Device:
        """
        Create a device instance of the specified type.
        
        Args:
            device_type: Name of the registered device type
            username: Device username
            password: Device password
            **kwargs: Additional arguments passed to device constructor
            
        Returns:
            Device instance of the specified type
            
        Raises:
            PluginError: If device type is not found or creation fails
            
        Example:
            ```python
            manager = PluginManager.get_instance()
            
            # Create a Linux device
            linux_device = manager.create_device("linux", "admin", "pass")
            
            # Create with additional parameters
            oneos6_device = manager.create_device(
                "oneos6", 
                "admin", 
                "pass",
                enable_password="enable_pass"
            )
            ```
        """
        device_class = self.get_device_class(device_type)
        
        if device_class is None:
            available = list(self._registered_devices.keys())
            raise PluginError(
                f"Unknown device type: {device_type}. "
                f"Available types: {available}"
            )
        
        try:
            return device_class(username=username, password=password, **kwargs)
        except Exception as e:
            raise PluginError(f"Failed to create {device_type} device: {e}") from e
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Get information about loaded plugins and registration status.
        
        Returns:
            Dictionary with plugin loading statistics and status
            
        Example:
            ```python
            manager = PluginManager.get_instance()
            info = manager.get_plugin_info()
            
            print(f"Loaded plugins: {info['loaded_count']}")
            print(f"Failed plugins: {info['failed_plugins']}")
            ```
        """
        return {
            "loaded_count": len(self._loaded_plugins),
            "failed_count": len(self._failed_plugins),
            "total_devices": len(self._registered_devices),
            "loaded_plugins": self._loaded_plugins.copy(),
            "failed_plugins": self._failed_plugins.copy(),
            "registered_devices": list(self._registered_devices.keys())
        }
    
    def clear_plugins(self) -> None:
        """
        Clear all registered plugins and reload built-in devices.
        
        This method is primarily intended for testing purposes.
        
        Example:
            ```python
            manager = PluginManager.get_instance()
            manager.clear_plugins()  # Reset to built-in devices only
            ```
        """
        self._registered_devices.clear()
        self._loaded_plugins.clear()
        self._failed_plugins.clear()
        self._register_builtin_devices()
        logger.info("Cleared all plugins and reloaded built-in devices")


# Global plugin manager instance
_plugin_manager = None


def get_plugin_manager() -> PluginManager:
    """
    Get the global plugin manager instance.
    
    This is a convenience function for accessing the plugin manager.
    
    Returns:
        PluginManager: The global plugin manager instance
        
    Example:
        ```python
        from router_test_kit.plugins import get_plugin_manager
        
        manager = get_plugin_manager()
        manager.load_plugins()
        
        # Create a device using the plugin system
        device = manager.create_device("linux", "admin", "password")
        ```
    """
    # Use module-level variable instead of global
    return PluginManager.get_instance()


def auto_load_plugins() -> None:
    """
    Automatically load all available plugins.
    
    This function should be called during package initialization to ensure
    all plugins are available when the package is imported.
    
    Example:
        ```python
        from router_test_kit.plugins import auto_load_plugins
        
        # Load all plugins automatically
        auto_load_plugins()
        ```
    """
    manager = get_plugin_manager()
    manager.load_plugins()
    
    info = manager.get_plugin_info()
    logger.info(
        "Plugin loading complete: %d plugins loaded, %d failed, %d devices available",
        info['loaded_count'], info['failed_count'], info['total_devices']
    )
