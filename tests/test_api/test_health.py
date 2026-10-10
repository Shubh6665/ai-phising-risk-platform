"""Tests for GET /health."""


class TestHealthEndpoint:
    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_content_type_is_json(self, client):
        assert "application/json" in client.get("/health").headers["content-type"]

    def test_status_is_ok(self, client):
        assert client.get("/health").json()["status"] == "ok"

    def test_version_is_present(self, client):
        version = client.get("/health").json()["version"]
        assert isinstance(version, str) and len(version) > 0

    def test_response_schema_fields(self, client):
        assert set(client.get("/health").json().keys()) == {"status", "version"}

    def test_unknown_route_returns_404(self, client):
        assert client.get("/does-not-exist").status_code == 404
