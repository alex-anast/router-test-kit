"""
Unit tests for the plugin system.

This module contains comprehensive tests for the Router Test Kit plugin system,
including plugin discovery, loading, validation, and registration functionality.
"""

import unittest.mock as mock
import pytest
from typing import Type
import importlib.metadata

from router_test_kit.plugins import (
    PluginManager,
    PluginError,
    get_plugin_manager,
    auto_load_plugins
)
from router_test_kit.device import Device, LinuxDevice


class MockDevice(Device):
    """Mock device class for testing."""
    
    def __init__(self, username: str, password: str):
        super().__init__(username, password)


class InvalidDevice:
    """Invalid device class that doesn't inherit from Device."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


class TestPluginManager:
    """Test cases for PluginManager class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create a fresh plugin manager for each test
        PluginManager._instance = None
        self.manager = PluginManager()
    
    def test_singleton_pattern(self):
        """Test that PluginManager follows singleton pattern."""
        manager1 = PluginManager.get_instance()
        manager2 = PluginManager.get_instance()
        
        assert manager1 is manager2
        assert isinstance(manager1, PluginManager)
    
    def test_builtin_devices_registered(self):
        """Test that built-in devices are automatically registered."""
        devices = self.manager.get_available_devices()
        
        expected_devices = ["linux", "oneos6", "radius"]
        for device_name in expected_devices:
            assert device_name in devices
            assert issubclass(devices[device_name], Device)
        
        # HostDevice is special - it doesn't inherit from Device
        assert "host" in devices
    
    def test_manual_device_registration(self):
        """Test manual device registration."""
        self.manager.register_device("mock", MockDevice)
        
        devices = self.manager.get_available_devices()
        assert "mock" in devices
        assert devices["mock"] == MockDevice
    
    def test_manual_registration_invalid_device(self):
        """Test that registering invalid device raises error."""
        with pytest.raises(PluginError, match="must inherit from"):
            self.manager.register_device("invalid", InvalidDevice)
    
    def test_manual_registration_not_class(self):
        """Test that registering non-class raises error."""
        with pytest.raises(PluginError, match="must be a class"):
            self.manager.register_device("invalid", "not_a_class")
    
    def test_get_device_class_existing(self):
        """Test getting existing device class."""
        linux_class = self.manager.get_device_class("linux")
        assert linux_class == LinuxDevice
    
    def test_get_device_class_nonexistent(self):
        """Test getting non-existent device class returns None."""
        device_class = self.manager.get_device_class("nonexistent")
        assert device_class is None
    
    def test_create_device_success(self):
        """Test successful device creation."""
        device = self.manager.create_device("linux", "admin", "password")
        
        assert isinstance(device, LinuxDevice)
        assert device.username == "admin"
        assert device.password == "password"
    
    def test_create_device_unknown_type(self):
        """Test creating device with unknown type raises error."""
        with pytest.raises(PluginError, match="Unknown device type"):
            self.manager.create_device("unknown", "admin", "password")
    
    def test_create_device_with_kwargs(self):
        """Test device creation with additional keyword arguments."""
        self.manager.register_device("mock", MockDevice)
        device = self.manager.create_device("mock", "admin", "password")
        
        assert isinstance(device, MockDevice)
        assert device.username == "admin"
        assert device.password == "password"
    
    @mock.patch('router_test_kit.plugins.importlib.metadata.entry_points')
    def test_load_plugins_success(self, mock_entry_points):
        """Test successful plugin loading."""
        # Mock entry point
        mock_entry_point = mock.Mock()
        mock_entry_point.name = "test_device"
        mock_entry_point.load.return_value = MockDevice
        
        # Mock entry points selection
        mock_eps = mock.Mock()
        mock_eps.select.return_value = [mock_entry_point]
        mock_entry_points.return_value = mock_eps
        
        self.manager.load_plugins()
        
        # Verify plugin was loaded
        devices = self.manager.get_available_devices()
        assert "test_device" in devices
        assert devices["test_device"] == MockDevice
        
        # Verify plugin info
        info = self.manager.get_plugin_info()
        assert "test_device" in info["loaded_plugins"]
        assert info["loaded_count"] == 1
    
    @mock.patch('router_test_kit.plugins.importlib.metadata.entry_points')
    def test_load_plugins_invalid_device(self, mock_entry_points):
        """Test plugin loading with invalid device."""
        # Mock entry point with invalid device
        mock_entry_point = mock.Mock()
        mock_entry_point.name = "invalid_device"
        mock_entry_point.load.return_value = InvalidDevice
        
        # Mock entry points selection
        mock_eps = mock.Mock()
        mock_eps.select.return_value = [mock_entry_point]
        mock_entry_points.return_value = mock_eps
        
        self.manager.load_plugins()
        
        # Verify plugin failed to load
        info = self.manager.get_plugin_info()
        assert "invalid_device" in info["failed_plugins"]
        assert info["failed_count"] == 1
        
        # Verify device was not registered
        devices = self.manager.get_available_devices()
        assert "invalid_device" not in devices
    
    @mock.patch('router_test_kit.plugins.importlib.metadata.entry_points')
    def test_load_plugins_import_error(self, mock_entry_points):
        """Test plugin loading with import error."""
        # Mock entry point that raises ImportError
        mock_entry_point = mock.Mock()
        mock_entry_point.name = "broken_device"
        mock_entry_point.load.side_effect = ImportError("Module not found")
        
        # Mock entry points selection
        mock_eps = mock.Mock()
        mock_eps.select.return_value = [mock_entry_point]
        mock_entry_points.return_value = mock_eps
        
        self.manager.load_plugins()
        
        # Verify plugin failed to load
        info = self.manager.get_plugin_info()
        assert "broken_device" in info["failed_plugins"]
        assert info["failed_count"] == 1
    
    @mock.patch('router_test_kit.plugins.importlib.metadata.entry_points')
    def test_load_plugins_no_entry_points(self, mock_entry_points):
        """Test plugin loading when no entry points exist."""
        mock_entry_points.side_effect = Exception("No entry points")
        
        # Should not raise exception
        self.manager.load_plugins()
        
        # Only built-in devices should be available
        devices = self.manager.get_available_devices()
        builtin_devices = ["linux", "oneos6", "radius", "host"]
        assert len(devices) == len(builtin_devices)
    
    def test_get_plugin_info_initial_state(self):
        """Test plugin info in initial state."""
        info = self.manager.get_plugin_info()
        
        assert info["loaded_count"] == 0
        assert info["failed_count"] == 0
        assert info["total_devices"] == 4  # Built-in devices
        assert info["loaded_plugins"] == []
        assert info["failed_plugins"] == []
        assert len(info["registered_devices"]) == 4
    
    def test_clear_plugins(self):
        """Test clearing plugins resets to built-in devices."""
        # Add a custom device
        self.manager.register_device("custom", MockDevice)
        
        # Verify it was added
        devices = self.manager.get_available_devices()
        assert "custom" in devices
        assert len(devices) == 5
        
        # Clear plugins
        self.manager.clear_plugins()
        
        # Verify only built-in devices remain
        devices = self.manager.get_available_devices()
        assert "custom" not in devices
        assert len(devices) == 4
        
        # Verify counters are reset
        info = self.manager.get_plugin_info()
        assert info["loaded_count"] == 0
        assert info["failed_count"] == 0
    
    def test_override_existing_device(self):
        """Test overriding existing device registration."""
        original_devices = self.manager.get_available_devices()
        original_linux = original_devices["linux"]
        
        # Override with mock device
        with mock.patch('router_test_kit.plugins.logger') as mock_logger:
            self.manager.register_device("linux", MockDevice)
            mock_logger.warning.assert_called_with(
                "Overriding existing device registration: %s", "linux"
            )
        
        # Verify override worked
        devices = self.manager.get_available_devices()
        assert devices["linux"] == MockDevice
        assert devices["linux"] != original_linux


class TestPluginHelperFunctions:
    """Test cases for plugin helper functions."""
    
    def test_get_plugin_manager_singleton(self):
        """Test that get_plugin_manager returns singleton."""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, PluginManager)
    
    @mock.patch('router_test_kit.plugins.get_plugin_manager')  
    def test_auto_load_plugins(self, mock_get_manager):
        """Test auto_load_plugins function."""
        mock_manager = mock.Mock()
        mock_get_manager.return_value = mock_manager
        mock_manager.load_plugins.return_value = None
        mock_manager.get_plugin_info.return_value = {
            "loaded_count": 2,
            "failed_count": 0,
            "total_devices": 6
        }
        
        auto_load_plugins()
        
        mock_manager.load_plugins.assert_called_once()
        mock_manager.get_plugin_info.assert_called_once()


class TestPluginValidation:
    """Test cases for plugin validation functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        PluginManager._instance = None
        self.manager = PluginManager()
    
    def test_validate_plugin_success(self):
        """Test successful plugin validation."""
        # Should not raise exception
        self.manager._validate_plugin(MockDevice, "mock")
    
    def test_validate_plugin_not_class(self):
        """Test validation fails for non-class."""
        with pytest.raises(PluginError, match="must be a class"):
            self.manager._validate_plugin("not_a_class", "invalid")
    
    def test_validate_plugin_wrong_inheritance(self):
        """Test validation fails for wrong inheritance."""
        with pytest.raises(PluginError, match="must inherit from"):
            self.manager._validate_plugin(InvalidDevice, "invalid")
    
    def test_validate_plugin_missing_attributes(self):
        """Test validation warns about missing attributes."""
        class MinimalDevice(Device):
            pass
        
        with mock.patch('router_test_kit.plugins.logger') as mock_logger:
            self.manager._validate_plugin(MinimalDevice, "minimal")
            
            # Should warn about missing username and password
            warning_calls = mock_logger.warning.call_args_list
            assert len(warning_calls) >= 1  # At least one warning call


class TestPluginIntegration:
    """Integration tests for the plugin system."""
    
    def test_end_to_end_plugin_usage(self):
        """Test complete plugin workflow."""
        manager = PluginManager()
        
        # Register a custom device
        manager.register_device("test", MockDevice)
        
        # Create device instance
        device = manager.create_device("test", "admin", "secret")
        
        assert isinstance(device, MockDevice)
        assert device.username == "admin"
        assert device.password == "secret"
        
        # Verify device is available
        available = manager.get_available_devices()
        assert "test" in available
        assert available["test"] == MockDevice
