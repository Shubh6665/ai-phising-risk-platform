"""Shared pytest fixtures for the test_api package."""

import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    with TestClient(app) as c:
        yield c
