"""Shared pytest fixtures for the test_api package.

Why a conftest.py here?
  pytest automatically discovers conftest.py files and makes their fixtures
  available to all tests in the same directory and below.

  Putting the `client` fixture here (rather than in each test file) means:
    - all test_api tests share the same app creation logic
    - if the creation logic changes, we fix it in one place

TestClient vs AsyncClient:
  FastAPI ships with two options:
    - TestClient (from starlette) — synchronous, wraps the ASGI app in a
      thread so you can write plain `def` tests.  Simpler for most cases.
    - AsyncClient (from httpx) — async, requires `pytest-asyncio`.

  For sub-steps A–E we use TestClient because the endpoints are synchronous
  and the overhead of async is not needed yet.  We'll switch to AsyncClient
  when we add async DB operations.

Key concept — why `with TestClient(app) as client`?
  The `with` block triggers the lifespan context manager (startup/shutdown).
  Without it, lifespan events are NOT fired and we'd miss any startup logic.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture(scope="session")
def app():
    """Create a single FastAPI app instance for the entire test session.

    scope="session" means pytest creates this once and reuses it.
    This is fine for stateless tests. If tests mutated app state we'd
    use scope="function" instead.
    """
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    """Synchronous TestClient that exercises the full ASGI lifespan.

    The `with` statement is required: it triggers startup/shutdown hooks.
    """
    with TestClient(app) as c:
        yield c
