# device.py


"""
This module contains the Device base class and its subclasses.
The devices hold information specific to the device, such as the username, password and hostname.
Actions are performed to a connection to the device, which is held in the Connection class.
Actions do not originate from the device.
"""


import logging
import subprocess
from abc import ABC, abstractmethod
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

    def __init__(self, username: Optional[str]=None, password: Optional[str]=None):
        self.username = username
        self.password = password
        self.hostname = None
        self._type = "device"

    @property
    def type(self) -> str:
        return self._type

    @property
    @abstractmethod
    def DEFAULT_USERNAME(self):
        pass

    @property
    @abstractmethod
    def DEFAULT_PASSWORD(self):
        pass

    @property
    @abstractmethod
    def DEFAULT_PROMPT_SYMBOL(self):
        pass


class LinuxDevice(Device):
    DEFAULT_USERNAME = 'user'
    DEFAULT_PASSWORD = 'user'
    DEFAULT_PROMPT_SYMBOL = '$'  # Changes to '#' if root

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        username = username if username else self.DEFAULT_USERNAME
        password = password if password else self.DEFAULT_PASSWORD
        super().__init__(username, password)
        self._type = "linux"
        self.hostname = f"{self._type}-{username or self.DEFAULT_USERNAME}"


class RADIUSServer(LinuxDevice):
    def __init__(self, username: Optional[str]=None, password: Optional[str]=None):
        super().__init__(username, password)
        self.hostname = "radius-server"


class OneOS6Device(Device):
    DEFAULT_USERNAME = 'admin'
    DEFAULT_PASSWORD = 'admin'
    DEFAULT_PROMPT_SYMBOL = '#'

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


class HostDevice():
    @staticmethod
    def write_command(command: str, print_response=False, quiet=False) -> Optional[str]:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        responses = []
        if process.returncode != 0 and not quiet:
            logger.error(f"Error executing command: {command}")
            logger.error(f"Error message: {stderr.decode()}")
        else:
            response = stdout.decode()
            if print_response and not quiet:
                logger.debug(f"Command executed successfully: {command}")
                logger.debug(f"Output: {response}")
        responses.append(stdout.decode()) if stdout else None
        responses.append(stderr.decode()) if stderr else None
        return '\n'.join(responses) if responses else None
