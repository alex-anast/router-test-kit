# How to Use

Assuming that the prerequisites are met and the installation has been successful, you can start using the test framework right away.

## Examples

For examples, see the `./examples/example1_connect.py` and `./examples/example2_ping_between_vms.py` files.
For a very thorough example showcasing the full capabilities of the test framework, see `./tests/test_ipsec.py`.

## Core Parts of any Test

The two most important parts of writing a network setup test are:

- `device.py::Device` class: As in the real world, you have to let the test know that you are connection from a `HostDevice` to a destination device that can be any of the children classes: `LinuxDevice`, `RadiusServer`, `OneOS6Device`, etc.

- `connection.py::Connection` class: The connection from the host device to the destination device. For the time being, only one connection is supported, the `TelnetConnection`. Alongside this, for the case where you need to connect to a device and from there, to jump to a third device, use the `TelnetCLIConnection` class. This includes several protection mechanisms for the connections to work well together as a group.

### Script Example

The steps that should be taken for establishing and killing a connection are given below:

```python
# Register device(s)
vm = LinuxDevice(username="user", password="password")

# Create a `connection` instance
my_connection = TelnetConnection(timeout=10)

# Connect to the device using telnet
connection = connection.connect(
    destination_device=vm,
    destination_ip="192.168.10.10",
)

# Perform actions, like ping, execute command on device etc.

# Close the connection
connection.disconnect()
```
