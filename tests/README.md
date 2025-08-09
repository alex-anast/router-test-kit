# Tests

## Important Note

This directory contains unit and integration tests for the router-test-kit framework itself.

The framework was initially developed alongside comprehensive IPSec integration tests, but those have been moved to `../examples/advanced_ipsec_test/` to maintain a clear separation of concerns:

- `tests/` - Unit tests for the router-test-kit framework components
- `examples/advanced_ipsec_test/` - Advanced IPSec testing examples that showcase the framework's capabilities

## Current Test Structure

The `tests/` directory is organized as follows:

### Unit Tests (`unit/`)

Contains unit tests for individual components of the router-test-kit framework:

- `test_connection.py` - Tests for connection classes (SSH, Telnet)
- `test_device.py` - Tests for device classes (Linux, OneOS6, etc.)
- `test_static_utils.py` - Tests for utility functions
- `test_logger.py` - Tests for logging functionality
- `test_plugins.py` - Tests for plugin system

### Configuration Files

- `pytest.ini` - Pytest configuration settings
- `conftest.py` - Shared pytest fixtures and configuration

## Running Tests

To run the unit tests:

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_connection.py

# Run with coverage
pytest tests/unit/ --cov=src/router_test_kit
```

## Advanced Examples

For examples of using the router-test-kit framework in real-world scenarios, see the `examples/advanced_ipsec_test/` directory, which contains comprehensive IPSec testing examples that demonstrate the framework's capabilities with actual network devices.
