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

- Python 3.8 or higher
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
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Or using conda
   conda create -n router-test-kit python=3.12
   conda activate router-test-kit
   ```

3. **Install the package in development mode:**

   ```bash
   pip install -e .
   ```

4. **Install development dependencies:**

   ```bash
   pip install pytest pytest-cov ruff mypy mkdocs mkdocs-material mkdocstrings[python]
   ```

5. **Verify the installation:**

   ```bash
   python -m pytest tests/unit/ -v
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

### Running Tests

Execute the full test suite:

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run with coverage report
python -m pytest tests/unit/ --cov=src/router_test_kit --cov-report=term

# Run specific test file
python -m pytest tests/unit/test_connection.py -v
```

### Writing Tests

#### Test Structure

- Unit tests go in `tests/unit/`
- Integration tests go in `tests/integration/`
- Follow the naming convention: `test_<module_name>.py`

#### Test Requirements

1. **Comprehensive Coverage**: Aim for >90% code coverage
2. **Mock External Dependencies**: Use `unittest.mock` for external services
3. **Test Edge Cases**: Include error scenarios and boundary conditions
4. **Clear Test Names**: Use descriptive test method names

#### Example Test Structure

```python
import unittest.mock as mock
import pytest
from router_test_kit.connection import SSHConnection

class TestSSHConnection:
    \"\"\"Test cases for SSHConnection class.\"\"\"
    
    def test_connect_success(self):
        \"\"\"Test successful SSH connection establishment.\"\"\"
        with mock.patch('paramiko.SSHClient') as mock_ssh:
            # Setup mocks
            mock_ssh.return_value.connect.return_value = None
            
            # Test the functionality
            conn = SSHConnection()
            result = conn.connect(mock_device, "192.168.1.1")
            
            # Assertions
            assert result is not None
            mock_ssh.return_value.connect.assert_called_once()
```

### Test Coverage Requirements

- **Minimum Coverage**: 85% overall
- **Critical Modules**: 95% for connection.py and device.py
- **New Features**: 100% coverage for all new code

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

### Review Timeline

- Most PRs are reviewed within 2-3 business days
- Complex changes may take longer
- Security-related changes are prioritized

## Getting Help

If you need help or have questions:

1. **GitHub Discussions**: For general questions and feature discussions
2. **GitHub Issues**: For bug reports and feature requests
3. **Documentation**: Check the API documentation and examples
4. **Code**: Look at existing tests for examples

## Recognition

Contributors who make significant improvements to the project will be recognized in:

- The project README
- Release notes
- Documentation acknowledgments

Thank you for contributing to Router Test Kit! Your efforts help make network testing more reliable and secure for everyone.
