# Unit Tests

This directory contains unit tests for the router-test-kit package.

## Structure

- `test_static_utils.py` - Tests for pure utility functions
- Add other unit test modules as needed

## Running Tests

```bash
# Run all unit tests
pytest tests/unit

# Run with coverage
pytest tests/unit --cov=router_test_kit --cov-report=html

# Run specific test file
pytest tests/unit/test_static_utils.py
```
