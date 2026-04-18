"""
Pytest configuration and shared fixtures for the advanced IPSec example tests.

These constants and fixtures mirror what a real deployment would configure.
Edit the values below to match your lab environment before running tests.
"""

import json
import os

import pytest

# ── ANSI colour codes ────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
NC = "\033[0m"  # No colour / reset

# ── Status strings ───────────────────────────────────────────────────────────
OK = "[  OK  ] "
NOK = "[ FAIL ] "
SKIPPED = "[ SKIP ] "

# ── Directory / file constants ───────────────────────────────────────────────
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
IPSEC_CFG_DIR_NAME = "configs_ipsec"
IPSEC_JSON_NAME = "ipsec.json"
BSA_DIR = "bsa"  # sub-directory inside configs_ipsec for BSA configs
SHOW_CRYPTO_DIR = "show_crypto"  # sub-directory for show-crypto reference data
RADIUS_CFG_DIR_NAME = "configs_radius"

# ── JSON test configuration ───────────────────────────────────────────────────
# Loaded once at import time so the module-level variable is available.
_json_path = os.path.join(ROOT_PATH, IPSEC_CFG_DIR_NAME, IPSEC_JSON_NAME)
try:
    with open(_json_path, encoding="utf-8") as _f:
        json_config: dict = json.load(_f)
except FileNotFoundError:
    json_config = {}

# ── Test parametrize data ────────────────────────────────────────────────────
# Each entry is (setup_marker: str, description: str, keywords: list[str]).
# Add your lab setups here; tests will be parametrized automatically.
TEST_SETUPS_GENERIC: list[tuple[str, str, list[str]]] = [
    # ("setup1", "Basic IKEv2 PSK tunnel", []),
    # ("setup2", "IKEv2 with RADIUS authentication", ["radius"]),
]

TEST_SETUPS_ALGORITHMS: list[tuple[str, str, list[str]]] = [
    # ("setup1-aes128", "AES-128 / SHA-256", []),
    # ("setup1-aes256", "AES-256 / SHA-384", []),
]


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture
def sudo_password() -> str:
    """Return the sudo password for the host running the test suite.

    Override via the ``SUDO_PASSWORD`` environment variable or edit this
    fixture directly for your lab environment.
    """
    return os.environ.get("SUDO_PASSWORD", "")
