# device.py


"""
This module contains the Device base class and its subclasses.
The devices hold information specific to the device, such as the username, password and hostname.
Actions are performed to a connection to the device, which is held in the Connection class.
Actions do not originate from the device.
"""

import logging
import subprocess
from abc import ABC
from typing import Optional

logger = logging.getLogger(__name__)


class Device(ABC):
    """
    Abstract base class for a device.

    Attributes:
        username (str): The username for the device. Default is None.
        password (str): The password for the device. Default is None.
        hostname (str): The hostname of the device. Default is None.
        _type (str): The type of the device. Default is "device".
    """

    # Default values to be overridden by subclasses
    DEFAULT_USERNAME: str = ""
    DEFAULT_PASSWORD: str = ""
    DEFAULT_PROMPT_SYMBOL: str = ""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username
        self.password = password
        self.hostname = None
        self._type = "device"

    @property
    def type(self) -> str:
        return self._type


class LinuxDevice(Device):
    DEFAULT_USERNAME = "user"
    DEFAULT_PASSWORD = "user"
    DEFAULT_PROMPT_SYMBOL = "$"  # Changes to '#' if root

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        username = username if username else self.DEFAULT_USERNAME
        password = password if password else self.DEFAULT_PASSWORD
        super().__init__(username, password)
        self._type = "linux"
        self.hostname = f"{self._type}-{username or self.DEFAULT_USERNAME}"


class RADIUSServer(LinuxDevice):
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        super().__init__(username, password)
        self.hostname = "radius-server"


class OneOS6Device(Device):
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "admin"
    DEFAULT_PROMPT_SYMBOL = "#"

    # To be extended by use-case with more interfaces
    PHYSICAL_INTERFACES_LIST = [
        "gigabitethernet",
        "fastethernet",
    ]

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        username = username if username else self.DEFAULT_USERNAME
        password = password if password else self.DEFAULT_PASSWORD
        super().__init__(username, password)
        self._type = "oneos"
        self.hostname = "localhost"


class HostDevice:
    @staticmethod
    def write_command(command: str, print_response: bool = False, quiet: bool = False) -> Optional[str]:
        """
        Execute a command on the local host system.
        
        Args:
            command: The command to execute
            print_response: Whether to log successful command execution
            quiet: Whether to suppress error logging
            
        Returns:
            Command output if successful, None otherwise
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
