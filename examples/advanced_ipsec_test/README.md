# Advanced IPSec Test Example

This directory contains an advanced example showcasing the capabilities of the router-test-kit framework for IPSec testing. This example was originally developed alongside the framework and demonstrates real-world usage patterns.

## Important Note

This is an **example/showcase only**. The tests are not runnable in a typical environment because they require:

1. Specific network infrastructure (VMs or physical devices)
2. Custom JSON configuration files with device credentials and IPs
3. Pytest fixtures for configuration management

The code is preserved here to demonstrate the framework's capabilities and serve as a reference for similar implementations.

## Contents

- `test_ipsec.py` - Comprehensive IPSec test suite showing various test scenarios
- `configs_ipsec/` - Directory for IPSec configuration files (not included for security)

## Design Overview

This example demonstrates:

- **Pytest Integration**: Uses pytest framework with custom fixtures for configuration management
- **JSON Configuration**: Reads device configurations from JSON files
- **Multi-Device Testing**: Tests IPSec connectivity between multiple devices
- **Real-World Scenarios**: Various IPSec setups and configurations

## Usage Pattern

When running (in an appropriate environment), tests would be executed with:

```bash
# Run specific test setups
pytest -k "setup1" test_ipsec.py
pytest -k "setup2" test_ipsec.py

# Run all IPSec tests
pytest test_ipsec.py -v
```

## Framework Features Demonstrated

This example showcases many router-test-kit features:

- Device management and connection handling
- SSH/Telnet connection types
- Command execution and output parsing
- Network connectivity testing
- Configuration management
- Error handling and logging

## Moving to Production

To adapt this example for your environment:

1. Create appropriate JSON configuration files
2. Set up the required network infrastructure
3. Modify device IPs and credentials
4. Adjust test scenarios for your specific requirements

This serves as a comprehensive reference for implementing complex network testing scenarios with the router-test-kit framework.
