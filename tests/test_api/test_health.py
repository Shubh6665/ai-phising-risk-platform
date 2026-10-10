"""Tests for GET /health.

What we're verifying:
  1. The endpoint returns HTTP 200.
  2. The response body matches the HealthResponse schema.
  3. The `status` field is exactly "ok".
  4. The `version` field is a non-empty string.

Each test is intentionally small.  A single test that checks everything at
once is hard to debug when it fails.  Small, focused tests tell you exactly
what broke.
"""

import pytest


class TestHealthEndpoint:
    """Group health tests in a class for clear organisation in the test output."""

    def test_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_content_type_is_json(self, client):
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]

    def test_status_is_ok(self, client):
        response = client.get("/health")
        body = response.json()
        assert body["status"] == "ok"

    def test_version_is_present(self, client):
        response = client.get("/health")
        body = response.json()
        assert isinstance(body["version"], str)
        assert len(body["version"]) > 0

    def test_response_schema_fields(self, client):
        """Response must contain exactly the fields defined by HealthResponse."""
        response = client.get("/health")
        body = response.json()
        assert set(body.keys()) == {"status", "version"}

    def test_unknown_route_returns_404(self, client):
        """Sanity check: unknown routes should 404, not silently match /health."""
        response = client.get("/does-not-exist")
        assert response.status_code == 404
