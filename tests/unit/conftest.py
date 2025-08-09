"""
Pytest configuration for unit tests.

This conftest.py is specific to unit tests and provides isolated configuration.
"""

import pytest


@pytest.fixture(autouse=True)
def setup_unit_test_environment():
    """Setup environment for unit tests."""
    # This fixture runs automatically for all unit tests
    # Add any common setup needed for unit tests here
    pass


# Add any unit-test specific fixtures below
