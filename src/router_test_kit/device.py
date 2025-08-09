"""Device Management Module.

This module provides device abstraction classes that represent different types of
network devices and hosts. Each device class encapsulates device-specific information
such as credentials, hostnames, and device type characteristics.

The module implements a device hierarchy with an abstract base class and concrete
implementations for different device types:

- Device (ABC): Abstract base class defining the device interface
- LinuxDevice: Represents Linux-based network devices and hosts
- OneOS6Device: Represents OneOS6 router/switch devices  
- RADIUSServer: Specialized Linux device for RADIUS authentication
- HostDevice: Utility class for executing commands on the local host

Classes:
    Device: Abstract base class for all device types
    LinuxDevice: Linux/Unix-based device implementation
    OneOS6Device: OneOS6 network device implementation
    RADIUSServer: RADIUS server device (extends LinuxDevice)
    HostDevice: Local host command execution utility

Example:
    Basic device usage:
    
    ```python
    from router_test_kit.device import LinuxDevice, OneOS6Device
    
    # Create different device types
    linux_vm = LinuxDevice(username="admin", password="secret")
    router = OneOS6Device(username="admin", password="admin")
    
    # Device types are automatically set
    print(linux_vm.type)  # "linux"
    print(router.type)    # "oneos"
    ```

Note:
    Device objects store connection credentials but do not manage connections
    themselves. Connections are handled by the Connection classes which use
    Device objects to obtain authentication information.
"""

import logging
import subprocess
from abc import ABC
from typing import Optional

logger = logging.getLogger(__name__)


class Device(ABC):
    """Abstract base class for network devices and hosts.
    
    This class provides a common interface for all device types, storing essential
    information such as credentials, hostname, and device type. Device objects are
    used by Connection classes to obtain authentication information and device-specific
    characteristics.
    
    Each device subclass defines default values for username, password, and prompt
    symbols that are appropriate for that device type. These defaults can be
    overridden during instantiation.
    
    Attributes:
        username (Optional[str]): Authentication username for the device
        password (Optional[str]): Authentication password for the device  
        hostname (Optional[str]): Network hostname or identifier
        type (str): Device type identifier (read-only property)
        
    Class Attributes:
        DEFAULT_USERNAME (str): Default username for this device type
        DEFAULT_PASSWORD (str): Default password for this device type
        DEFAULT_PROMPT_SYMBOL (str): Default command prompt symbol
        
    Example:
        This is an abstract class and cannot be instantiated directly:
        
        ```python
        # Use concrete implementations instead
        device = LinuxDevice(username="admin", password="secret")
        print(device.type)  # "linux"
        ```
        
    Note:
        Device objects are passive containers for device information. They do not
        establish or manage network connections. Use Connection classes for actual
        network communication.
    """

    # Default values to be overridden by subclasses
    DEFAULT_USERNAME: str = ""
    DEFAULT_PASSWORD: str = ""
    DEFAULT_PROMPT_SYMBOL: str = ""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """Initialize a new device instance.
        
        Args:
            username: Authentication username. Uses class default if None.
            password: Authentication password. Uses class default if None.
            
        Note:
            This is an abstract class and should not be instantiated directly.
            Use concrete implementations like LinuxDevice or OneOS6Device.
        """
        self.username = username
        self.password = password
        self.hostname = None
        self._type = "device"

    @property
    def type(self) -> str:
        """Get the device type identifier.
        
        Returns:
            str: Device type string (e.g., "linux", "oneos")
        """
        return self._type


class LinuxDevice(Device):
    """Linux/Unix-based device implementation.
    
    Represents Linux, Unix, or other POSIX-compatible devices and virtual machines.
    This class is commonly used for Linux-based network appliances, virtual machines,
    and general-purpose Linux hosts.
    
    The class provides appropriate defaults for Linux systems:
    - Default username: "user"
    - Default password: "user"  
    - Default prompt: "$" (changes to "#" for root)
    
    Attributes:
        All attributes inherited from Device class, plus:
        hostname (str): Auto-generated hostname in format "linux-{username}"
        
    Example:
        ```python
        # Use defaults
        vm = LinuxDevice()
        print(vm.username)  # "user"
        print(vm.hostname)  # "linux-user"
        
        # Custom credentials
        vm = LinuxDevice(username="admin", password="secret")
        print(vm.hostname)  # "linux-admin"
        ```
    """
    DEFAULT_USERNAME = "user"
    DEFAULT_PASSWORD = "user"
    DEFAULT_PROMPT_SYMBOL = "$"  # Changes to '#' if root

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """Initialize a Linux device.
        
        Args:
            username: Linux username. Defaults to "user" if None.
            password: Linux password. Defaults to "user" if None.
        """
        username = username if username else self.DEFAULT_USERNAME
        password = password if password else self.DEFAULT_PASSWORD
        super().__init__(username, password)
        self._type = "linux"
        self.hostname = f"{self._type}-{username or self.DEFAULT_USERNAME}"


class RADIUSServer(LinuxDevice):
    """RADIUS authentication server device.
    
    Specialized Linux device for RADIUS (Remote Authentication Dial-In User Service)
    servers. Inherits all Linux device functionality but uses a specific hostname
    identifier for RADIUS services.
    
    This class is typically used in network testing scenarios that require
    authentication services for devices like routers and switches.
    
    Example:
        ```python
        radius = RADIUSServer(username="radius_admin", password="secret")
        print(radius.hostname)  # "radius-server"
        print(radius.type)      # "linux"
        ```
    """
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """Initialize a RADIUS server device.
        
        Args:
            username: RADIUS server admin username. Defaults to "user" if None.
            password: RADIUS server admin password. Defaults to "user" if None.
        """
        super().__init__(username, password)
        self.hostname = "radius-server"


class OneOS6Device(Device):
    """OneOS6 network device implementation.
    
    Represents OneOS6-based routers and switches. OneOS6 is a network operating
    system commonly used in enterprise routing and switching equipment.
    
    The class provides appropriate defaults for OneOS6 devices:
    - Default username: "admin"
    - Default password: "admin"
    - Default prompt: "#" (privileged mode)
    
    Attributes:
        All attributes inherited from Device class, plus:
        PHYSICAL_INTERFACES_LIST (List[str]): Supported interface types
        
    Class Attributes:
        PHYSICAL_INTERFACES_LIST: List of supported physical interface types
        that can be extended based on specific device models
        
    Example:
        ```python
        # Use defaults
        router = OneOS6Device()
        print(router.username)  # "admin"
        print(router.type)      # "oneos"
        
        # Check supported interfaces
        print(router.PHYSICAL_INTERFACES_LIST)
        # ["gigabitethernet", "fastethernet"]
        ```
        
    Note:
        The PHYSICAL_INTERFACES_LIST can be extended in subclasses to support
        additional interface types for specific OneOS6 device models.
    """
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "admin"
    DEFAULT_PROMPT_SYMBOL = "#"

    # To be extended by use-case with more interfaces
    PHYSICAL_INTERFACES_LIST = [
        "gigabitethernet",
        "fastethernet",
    ]

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """Initialize a OneOS6 device.
        
        Args:
            username: OneOS6 admin username. Defaults to "admin" if None.
            password: OneOS6 admin password. Defaults to "admin" if None.
        """
        username = username if username else self.DEFAULT_USERNAME
        password = password if password else self.DEFAULT_PASSWORD
        super().__init__(username, password)
        self._type = "oneos"
        self.hostname = "localhost"


class HostDevice:
    """Local host command execution utility.
    
    This class provides static methods for executing shell commands on the local
    host system. It's designed for scenarios where tests need to run commands
    on the host machine running the test suite.
    
    The class uses the modern subprocess.run API with proper error handling,
    timeout support, and flexible output management.
    
    Example:
        ```python
        # Basic command execution
        result = HostDevice.write_command("echo 'Hello World'")
        print(result)  # "Hello World"
        
        # With error handling
        result = HostDevice.write_command("nonexistent_command", quiet=True)
        print(result)  # None (command failed)
        
        # With logging
        result = HostDevice.write_command("ls -la", print_response=True)
        # Logs command execution details
        ```
        
    Note:
        All methods are static since this class doesn't maintain state.
        Commands are executed with a 30-second timeout by default.
    """
    
    @staticmethod
    def write_command(command: str, print_response: bool = False, quiet: bool = False) -> Optional[str]:
        """Execute a shell command on the local host system.
        
        Executes the specified command using subprocess.run with proper error
        handling and timeout support. Returns combined stdout/stderr output
        or None if the command fails.
        
        Args:
            command: Shell command to execute
            print_response: Whether to log successful command execution details
            quiet: Whether to suppress error logging for failed commands
            
        Returns:
            Combined command output (stdout + stderr) if successful, None if failed
            
        Raises:
            None: All exceptions are caught and handled internally
            
        Example:
            ```python
            # Simple command
            output = HostDevice.write_command("date")
            
            # Command with error handling
            output = HostDevice.write_command("ping -c 1 nonexistent.host", quiet=True)
            if output is None:
                print("Command failed")
            ```
            
        Note:
            Commands are executed with shell=True, so shell features like pipes
            and redirects are supported. A 30-second timeout is enforced.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=False  # Don't raise exception on non-zero exit
            )

            if result.returncode != 0:
                if not quiet:
                    logger.error("Error executing command: %s", command)
                    logger.error("Error message: %s", result.stderr)
                return None

            if print_response and not quiet:
                logger.debug("Command executed successfully: %s", command)
                logger.debug("Output: %s", result.stdout)

            # Return combined output (stdout + stderr) if available
            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(result.stderr)

            return "\n".join(output_parts) if output_parts else None

        except subprocess.TimeoutExpired:
            if not quiet:
                logger.error("Command timed out: %s", command)
            return None
        except OSError:
            if not quiet:
                logger.exception("Failed to execute command: %s", command)
            return None
