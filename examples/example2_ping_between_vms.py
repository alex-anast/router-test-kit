#!/usr/bin/env python3

"""
File: example2_ping_between_vms.py

This example assumes there are two Ubuntu Server VMs up and running.
See the README for specific details regarding the setup.
"""

from router_test_kit.device import LinuxDevice
from router_test_kit.connection import SSHConnection
from router_test_kit.static_utils import get_packet_loss


def main():
    """
    1. Connect to two VMs,
    2. Ping from VM1 to VM2,
    3. Check that the ping has been successful,
    4. Disconnect from both VMs.
    """

    # Register two LinuxDevice objects for the Ubuntu Servers
    print("Registering devices...")
    vm1 = LinuxDevice(username="user", password="user")
    print(f"Device 1 of type {vm1.type} registered.")
    vm2 = LinuxDevice(username="user", password="user")
    print(f"Device 2 of type {vm1.type} registered.")

    # Connect to the devices using telnet
    connection1 = SSHConnection(timeout=10) # Connection from Host to VM1
    connection1 = connection1.connect(
        destination_device=vm1,
        destination_ip="192.168.56.2",  # Assuming subnet /24
    )
    print(f"Connected to VM1: {connection1.is_connected}")

    connection2 = SSHConnection(timeout=10) # Connection from Host to VM2
    connection2 = connection2.connect(
        destination_device=vm2,
        destination_ip="192.168.56.3",  # Assuming subnet /24
    )
    print(f"Connected to VM2: {connection2.is_connected}")

    # Ping from VM1 to VM2
    print("Pinging from VM1 to VM2...")
    ping_response = connection1.ping(
        ip="192.168.56.3",  # IP address of VM2
        nbr_packets=3,
        ping_timeout=10,
    )
    print("Effort to ping from VM1 to VM2 complete.")

    # Check if the ping was successful
    print("Checking if ping has been successful...")
    packet_loss = get_packet_loss(ping_response)

    assert (packet_loss == '0'), f"Packet loss should be 0, but it is {packet_loss} instead."

    print("Ping has been successful. Disconnecting...")

    connection1.disconnect()
    connection2.disconnect()
    assert (connection1.is_connected is False and connection2.is_connected is False), \
        "Failed to disconnect from VMs."


if __name__ == "__main__":
    main()
