#!/usr/bin/env python3

"""
File: example1_connect.py

This example assumes there is an Ubuntu Server VM up and running.
See the README for specific details regarding the setup.
"""

from router_test_kit.device import LinuxDevice
from router_test_kit.connection import SSHConnection


def main():
    """
    Connect to a device using SSH, check status and disconnect.
    Assert the connection status on the way.
    """
    # Register a LinuxDevice object for the Ubuntu Server
    print("Registering device...")
    vm = LinuxDevice(username="user", password="user")
    print(f"Device of type {vm.type} registered.")

    # Connect to the device using SSH (secure connection)
    connection = SSHConnection(timeout=10)
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
