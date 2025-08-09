# Examples

This directory contains examples demonstrating how to use the router-test-kit framework for various networking scenarios.

## Table of Contents

- [Examples](#examples)
  - [Table of Contents](#table-of-contents)
  - [Basic Examples](#basic-examples)
    - [Example 1: Simple Device Connection](#example-1-simple-device-connection)
    - [Example 2: Ping Between VMs](#example-2-ping-between-vms)
  - [Advanced Examples](#advanced-examples)
    - [Advanced IPSec Testing](#advanced-ipsec-testing)

## Basic Examples

### Example 1: Simple Device Connection

**File:** `example1_connect.py`

This example demonstrates the basic functionality of connecting to a device using SSH, checking the connection status, and disconnecting.

**Setup Requirements:**

- An Ubuntu Server VM accessible at IP 192.168.56.2
- SSH access with username/password: user/user

**Features Demonstrated:**

- Device registration with `LinuxDevice`
- Secure SSH connection using `SSHConnection`
- Connection status checking
- Proper disconnect handling

### Example 2: Ping Between VMs

**File:** `example2_ping_between_vms.py`

This example shows how to establish connections to multiple devices and test network connectivity between them.

**Setup Requirements:**

- Two Ubuntu Server VMs accessible at IPs 192.168.56.2 and 192.168.56.3
- SSH access with username/password: user/user

**Features Demonstrated:**

- Multiple device management
- SSH connections to multiple VMs
- Network connectivity testing with ping
- Packet loss analysis using `get_packet_loss`
- Proper cleanup and disconnection

## Advanced Examples

### Advanced IPSec Testing

**Directory:** `advanced_ipsec_test/`

Contains comprehensive examples showcasing the framework's capabilities for complex IPSec testing scenarios. This demonstrates real-world usage patterns and advanced features.

**Note:** These are showcase examples that require specific infrastructure and configuration files not included in the repository.

## Installation Note

All examples use direct imports from the router-test-kit package. Ensure you have installed the package in editable mode:

```bash
pip install -e .
```

This eliminates the need for any `sys.path` manipulation that was required in earlier versions.
