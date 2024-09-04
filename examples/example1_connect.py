#!/usr/bin/env python3

"""
File: example1_connect.py

This example assumes there is an Ubuntu Server VM up and running.
See the README for specific details regarding the setup.

TODO
"""

import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.device import LinuxDevice
from src.connection import TelnetConnection


def main():
    """
    Connect to a device using telnet, check status and disconnect.
    Assert the connection status on the way.
    """
    # Register a LinuxDevice object for the Ubuntu Server
    print("Registering device...")
    vm = LinuxDevice(username="user", password="user")
    print(f"Device of type {vm.type} registered.")

    # Connect to the device using telnet
    connection = TelnetConnection(timeout=10)
    connection = connection.connect(
        destination_device=vm,
        destination_ip="192.168.56.2",  # Assuming subnet /24
    )

    print(f"Connected to VM: {connection.is_connected}")
    assert(connection.is_connected), "Should have connected to device, check your setup."

    print("Disconnecting from device...")
    connection.disconnect()
    print(f"Connected to VM: {connection.is_connected}")

    assert(not connection.is_connected), "Should have disconnected from device."


if __name__ == "__main__":
    main()
