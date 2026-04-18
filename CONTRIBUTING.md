# Contributing to Router Test Kit

Thank you for your interest in contributing to Router Test Kit! This guide will help you get started with development and ensure that your contributions align with the project's standards.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Security Guidelines](#security-guidelines)

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Local Development Environment

1. **Clone the repository:**

   ```bash
   git clone https://github.com/alex-anast/router-test-kit.git
   cd router-test-kit
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the package with development dependencies:**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Install and enable pre-commit hooks:**

   ```bash
   pip install pre-commit
   pre-commit install
   ```

5. **Verify the installation:**

   ```bash
   pytest tests/unit/ -v
   ```

## Code Standards

Router Test Kit follows modern Python best practices and coding standards.

### Code Quality Tools

We use several tools to maintain code quality:

- **Ruff**: For linting and code formatting
- **MyPy**: For static type checking
- **Pytest**: For testing

### Formatting and Linting

Before submitting any code, ensure it passes our quality checks:

```bash
# Format code with ruff
ruff format src/ tests/

# Check for linting issues
ruff check src/ tests/

# Run type checking
mypy src/router_test_kit/
```

### Type Hints

All public functions and methods must include comprehensive type hints:

```python
def connect(self, destination_device: Device, destination_ip: str) -> Connection:
    \"\"\"Establish connection to device.
    
    Args:
        destination_device: Target device with credentials
        destination_ip: IP address of the device
        
    Returns:
        Connection instance for method chaining
        
    Raises:
        ConnectionAbortedError: If connection fails
    \"\"\"
    # Implementation here
```

### Docstring Standards

Use Google-style docstrings for all public classes and functions:

```python
def example_function(param1: str, param2: int = 10) -> bool:
    \"\"\"Brief description of the function.
    
    Longer description if needed, explaining the purpose and behavior
    of the function in more detail.
    
    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter with default value
        
    Returns:
        Description of the return value
        
    Raises:
        ValueError: Description of when this exception is raised
        ConnectionError: Description of when this exception is raised
        
    Example:
        ```python
        result = example_function("test", param2=20)
        if result:
            print("Success!")
        ```
    \"\"\"
```

## Testing

The test suite has three tiers. See [docs/testing.md](docs/testing.md) for the full explanation.

### Tier 1 — Unit tests (no Docker required)

```bash
pytest tests/unit/ -v
pytest tests/unit/ --cov=src/router_test_kit --cov-report=term
```

### Tier 2 — Integration tests (Docker required)

```bash
docker compose -f docker-compose.test.yml up -d
pytest tests/integration/ -v -m integration
docker compose -f docker-compose.test.yml down -v
```

### Tier 3 — Hardware tests

```bash
RTK_HARDWARE_LAB=1 pytest -m hardware
```

Hardware tests are skipped by default. Set `RTK_HARDWARE_LAB=1` to enable them.

### Writing Tests

#### Test Structure

- Unit tests go in `tests/unit/` — use mocks only for edge cases and error paths, not happy paths.
- Integration tests go in `tests/integration/` — exercise real I/O (SSH container, etc.), mark with `@pytest.mark.integration`.
- Hardware tests — mark with `@pytest.mark.hardware`; require `RTK_HARDWARE_LAB=1`.
- Follow the naming convention: `test_<module_name>.py`

#### Test Requirements

1. **Prefer real I/O over mocks for happy paths** — mock only where a real server would be impractical (timing-sensitive edge cases, error injection).
2. **Test Edge Cases**: Include error scenarios and boundary conditions.
3. **Clear Test Names**: Use descriptive test method names.

#### Example — Integration test

```python
import pytest
from router_test_kit.connection import SSHConnection
from router_test_kit.device import LinuxDevice

@pytest.mark.integration
class TestSSHTransport:
    def test_write_command_echo(self, ssh_server):
        device = LinuxDevice(username=ssh_server["username"], password=ssh_server["password"])
        conn = SSHConnection(timeout=15)
        conn.connect(device, ssh_server["host"], port=ssh_server["port"])
        result = conn.write_command("echo hello")
        assert "hello" in result
        conn.disconnect()
            
            # Assertions
            assert result is not None
            mock_ssh.return_value.connect.assert_called_once()
```

### Test Coverage

Add tests for new functionality. Run `pytest tests/unit/ --cov=src/router_test_kit` to check coverage.

## Documentation

### API Documentation

API documentation is auto-generated from docstrings using mkdocstrings. Ensure your docstrings are complete and accurate.

### Building Documentation

To build and preview documentation locally:

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

### Documentation Guidelines

1. **Keep Examples Current**: Ensure code examples work with the current API
2. **Include Security Notes**: Highlight security considerations
3. **Migration Guides**: Document breaking changes and migration paths
4. **Clear Structure**: Use consistent formatting and organization

## Submitting Changes

### Workflow

1. **Create a Feature Branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes:**
   - Follow the code standards above
   - Include comprehensive tests
   - Update documentation as needed

3. **Run Quality Checks:**

   ```bash
   # Format and lint
   ruff format src/ tests/
   ruff check src/ tests/
   
   # Type checking
   mypy src/router_test_kit/
   
   # Run tests
   python -m pytest tests/unit/ --cov=src/router_test_kit
   ```

4. **Commit Your Changes:**

   ```bash
   git add .
   git commit -m "feat: add new SSH connection feature"
   ```

5. **Push and Create Pull Request:**

   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use conventional commit messages:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/modifications
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

Examples:

```bash
feat: add SSH connection timeout configuration
fix: resolve memory leak in connection pooling
docs: update API documentation for device module
test: add comprehensive SSH connection tests
```

### Pull Request Guidelines

1. **Clear Description**: Explain what changes you made and why
2. **Link Issues**: Reference any related GitHub issues
3. **Test Evidence**: Include test results and coverage reports
4. **Breaking Changes**: Clearly document any breaking changes
5. **Security Impact**: Note any security implications

## Security Guidelines

### Security First Development

1. **Secure by Default**: Use SSH instead of Telnet for all new code
2. **Input Validation**: Validate all user inputs and command parameters
3. **Error Handling**: Don't expose sensitive information in error messages
4. **Dependencies**: Keep dependencies updated and audit for vulnerabilities

### Reporting Security Issues

Please report security vulnerabilities privately by emailing the maintainers. Do not create public GitHub issues for security problems.

### Security Review Checklist

Before submitting code:

- [ ] No hardcoded credentials or secrets
- [ ] Proper input validation and sanitization
- [ ] Secure communication protocols (SSH over Telnet)
- [ ] Error messages don't leak sensitive information
- [ ] Dependencies are up-to-date and secure

## Code Review Process

### What We Look For

1. **Correctness**: Does the code work as intended?
2. **Quality**: Is the code well-structured and maintainable?
3. **Testing**: Are there adequate tests with good coverage?
4. **Documentation**: Are docstrings and comments clear and helpful?
5. **Security**: Are there any security concerns?
6. **Performance**: Are there any performance implications?

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: [alex-anast.github.io/router-test-kit](https://alex-anast.github.io/router-test-kit/)
- **Code**: Look at existing tests for usage examples

Thank you for contributing to Router Test Kit!
