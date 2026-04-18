# Testing

The test suite is organised in three tiers. Each tier has a clear contract about what it needs and what it proves.

---

## Tier 1 — Unit tests

```
pytest tests/unit/
```

No network access. No Docker. Mocks are used only where genuinely necessary:

- **Validators and parsers** (`is_valid_ip`, `get_packet_loss`, regex helpers) — pure logic, no I/O.
- **Edge cases and error paths** — connection guard decorators, channel-closed states, socket errors. These are easier to simulate with a controlled mock than to reproduce deterministically with a real server.
- **State machines** — `flush`, `flush_deep`, channel buffer draining. Timing-sensitive; mocks let tests be deterministic.

Everything that is *not* an edge case or error path belongs in Tier 2.

---

## Tier 2 — Integration tests (Docker)

```bash
# Start the SSH server once per session
docker compose -f docker-compose.test.yml up -d

# Run the integration suite
pytest tests/integration/ -v -m integration

# Tear down
docker compose -f docker-compose.test.yml down -v
```

These tests connect to a real OpenSSH server running in a local container (`linuxserver/openssh-server`). They prove:

- `SSHConnection.connect` performs the full TLS + auth handshake
- `write_command` sends bytes over the wire and reads real shell output
- `disconnect` actually closes the socket
- Wrong passwords produce real `AuthenticationException` errors
- Unreachable hosts produce real `socket.error`

Container is started once per `pytest` session by the session-scoped `ssh_server` fixture in `tests/integration/conftest.py`. If you already have an SSH server running, override the fixture by setting all four environment variables:

```bash
RTK_SSH_HOST=myserver RTK_SSH_PORT=22 RTK_SSH_USER=admin RTK_SSH_PASSWORD=secret \
  pytest tests/integration/ -m integration
```

---

## Tier 3 — Hardware tests

```bash
RTK_HARDWARE_LAB=1 pytest -m hardware
```

Tests marked `@pytest.mark.hardware` require a real OneOS6 device on the network. They are **skipped by default** — both locally and in CI. Set `RTK_HARDWARE_LAB=1` to enable them.

No hardware tests are currently in the repository. This tier is scaffolded for when the connection layer is refactored to expose a `OneOS6Connection` class that can be exercised against real kit.

---

## Running the full suite locally

```bash
# 1. Create and activate a virtual environment (first time only)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install pre-commit
pre-commit install

# 2. Unit tests (fast, no Docker required)
pytest tests/unit/

# 3. Integration tests (requires Docker)
docker compose -f docker-compose.test.yml up -d
pytest tests/integration/ -m integration
docker compose -f docker-compose.test.yml down -v

# 4. Full coverage report
pytest tests/ --cov=src --cov-report=term-missing
```

---

## CI

GitHub Actions runs two test jobs in parallel on every push/PR:

| Job | Runs on | What it tests |
|---|---|---|
| `test` | Python 3.9 – 3.12 matrix | Unit tests only — no Docker |
| `integration` | Python 3.12, ubuntu-latest | Tier 2 tests against a Docker SSH container |
