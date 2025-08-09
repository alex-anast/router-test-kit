# Router Test Kit

[![Build Status](https://github.com/alex-anast/router-test-kit/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/alex-anast/router-test-kit/actions)
[![Coverage](https://codecov.io/gh/alex-anast/router-test-kit/branch/main/graph/badge.svg)](https://codecov.io/gh/alex-anast/router-test-kit)
[![PyPI version](https://img.shields.io/pypi/v/router-test-kit)](https://pypi.org/project/router-test-kit/)
[![Python Support](https://img.shields.io/pypi/pyversions/router-test-kit)](https://pypi.org/project/router-test-kit/)
[![License](https://img.shields.io/github/license/alex-anast/router-test-kit)](https://github.com/alex-anast/router-test-kit/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://alex-anast.github.io/router-test-kit/)

🚀 **A professional-grade Python framework for automated network device testing**

Router Test Kit provides a simple, secure, and comprehensive solution for testing virtual and physical routers, network devices, and Linux systems. Built with security-first principles and modern Python practices.

## ✨ Key Features

- 🔒 **Security First**: SSH-based connections with modern authentication
- 🌐 **Multi-Device Support**: OneOS6 routers, Cisco devices, Linux systems, RADIUS servers
- 🧪 **Test-Driven**: Comprehensive test suite with >90% coverage
- 📚 **Professional Documentation**: Auto-generated API docs with examples
- 🔄 **CI/CD Ready**: GitHub Actions integration for automated testing
- 🎯 **Type-Safe**: Full type hints for better development experience
- 🐍 **Modern Python**: Support for Python 3.8 through 3.12

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Supported Devices](#supported-devices)
- [Security](#security)
- [Examples](#examples)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Quick Start

```python
from router_test_kit.device import LinuxDevice
from router_test_kit.connection import SSHConnection

# Create device and establish secure connection
device = LinuxDevice(username="admin", password="secure_pass")
conn = SSHConnection().connect(device, "192.168.1.100")

# Execute commands and verify results
result = conn.exec("ip route show")
print(f"Routes: {result}")

# Clean up
conn.disconnect()
```

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install router-test-kit
```

## 🔧 Basic Usage

### Simple Device Connection

```python
from router_test_kit.device import LinuxDevice
from router_test_kit.connection import SSHConnection

# Create a device with credentials
device = LinuxDevice(username="admin", password="secure_password")

# Establish SSH connection
with SSHConnection() as conn:
    conn.connect(device, "192.168.1.100")
    
    # Execute commands
    result = conn.exec("ls -la")
    print(result)
    
    # Connection automatically closed
```

### Advanced Network Testing

```python
from router_test_kit.device import OneOS6Device, RADIUSServer
from router_test_kit.static_utils import ping, print_banner

# Setup test environment
router = OneOS6Device(username="admin", password="router_pass")
radius = RADIUSServer(username="radius_admin", password="radius_pass")

# Execute network tests
print_banner("Network Connectivity Test")
loss_rate = ping(source_device=router, target_ip="192.168.1.1", count=10)
print(f"Packet loss: {loss_rate}%")
```

## 🌐 Supported Devices

| Device Type | Protocol | Authentication | Status |
|-------------|----------|----------------|--------|
| **Linux Systems** | SSH/Telnet | Password/Key | ✅ Full Support |
| **OneOS6 Routers** | SSH/Telnet | Password | ✅ Full Support |
| **Cisco Devices** | SSH/Telnet | Password | ✅ Compatible |
| **RADIUS Servers** | SSH | Password | ✅ Specialized Support |
| **Generic Hosts** | Local | N/A | ✅ Host Commands |

## 🔒 Security

Router Test Kit prioritizes security in network testing:

- **SSH First**: Default to secure SSH connections over insecure Telnet
- **Credential Management**: Secure handling of authentication credentials
- **Input Validation**: Comprehensive validation of all user inputs
- **Error Handling**: Secure error messages that don't leak sensitive information
- **Dependency Security**: Regular security audits of all dependencies

### Security Best Practices

```python
# ✅ Recommended: Use SSH connections
conn = SSHConnection()

# ⚠️  Use only when SSH is not available
conn = TelnetConnection()  # Consider security implications

# 🔒 Use environment variables for credentials
import os
device = LinuxDevice(
    username=os.getenv("DEVICE_USERNAME"),
    password=os.getenv("DEVICE_PASSWORD")
)
```

## 📖 Examples

### Quick Examples

- **[Basic Connection](./examples/example1_connect.py)**: Simple device connection and command execution
- **[Network Testing](./examples/example2_ping_between_vms.py)**: Inter-VM connectivity testing
- **[Advanced IPSec](./tests/test_ipsec.py)**: Comprehensive IPSec tunnel testing

### Real-World Use Cases

```python
# Network topology validation
def validate_network_topology():
    devices = [
        LinuxDevice("admin", "pass") for _ in range(3)
    ]
    
    # Test connectivity matrix
    for i, source in enumerate(devices):
        for j, target in enumerate(devices):
            if i != j:
                loss = ping(source, f"192.168.1.{j+1}")
                assert loss < 5, f"High packet loss: {loss}%"

# Router configuration testing
def test_router_config():
    router = OneOS6Device("admin", "config_pass")
    
    with SSHConnection() as conn:
        conn.connect(router, "192.168.1.1")
        
        # Load test configuration
        conn.load_config("test_config.txt")
        
        # Verify configuration
        result = conn.exec("show running-config")
        assert "test_interface" in result
        
        # Cleanup
        conn.unload_config()
```

## 📚 Documentation

- **[API Reference](https://alex-anast.github.io/router-test-kit/api/)**: Complete API documentation
- **[User Guide](https://alex-anast.github.io/router-test-kit/usage/)**: Detailed usage examples
- **[Installation Guide](https://alex-anast.github.io/router-test-kit/installation/)**: Setup instructions
- **[Contributing Guide](./CONTRIBUTING.md)**: Development guidelines

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Quick Development Setup

```bash
git clone https://github.com/alex-anast/router-test-kit.git
cd router-test-kit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov ruff mypy mkdocs mkdocs-material

# Run tests
python -m pytest tests/unit/ -v

# Run linting
ruff check src/ tests/
ruff format src/ tests/

# Build documentation
mkdocs serve
```

### Contributing Areas

- 🐛 **Bug Reports**: Help us identify and fix issues
- 🚀 **New Features**: Add support for new device types or protocols
- 📖 **Documentation**: Improve guides and API documentation  
- 🧪 **Testing**: Expand test coverage and add integration tests
- 🔒 **Security**: Security audits and improvements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the network testing and automation community
- Inspired by the need for simple, secure router testing
- Special thanks to all contributors and users

## 📊 Project Stats

- **🐍 Python**: 3.8+ support
- **📦 Dependencies**: Minimal, security-focused
- **🧪 Tests**: >90% coverage
- **📚 Documentation**: Auto-generated from code
- **🔄 CI/CD**: Automated testing and deployment

---

**Ready to automate your network testing?** [Install Router Test Kit](https://pypi.org/project/router-test-kit/) and start building reliable network tests today!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
