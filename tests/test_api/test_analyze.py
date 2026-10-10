"""Tests for the analyze API endpoint and middleware."""

import pytest
import numpy as np

from src.api.app import create_app
from src.api.dependencies import get_classical_model, get_nlp_model, get_nlp_tokenizer

# --- Test Doubles ---

class DummyClassicalModel:
    def predict_proba(self, features):
        # Always return 80% phishing probability
        return np.array([[0.2, 0.8]])


class DummyNLPModel:
    pass  # We'll mock sample_probabilities in the service via monkeypatch, or we can just mock it here.


class DummyTokenizer:
    pass


# We need to mock sample_probabilities in src.api.services because it does real torch inference
@pytest.fixture
def mock_sample_probabilities(monkeypatch):
    def mock_sample(model, tokenizer, texts, max_length, batch_size):
        # Always return 85% phishing probability
        return np.array([[0.15, 0.85]])
    
    monkeypatch.setattr("src.api.services.sample_probabilities", mock_sample)


@pytest.fixture
def test_app():
    app = create_app()
    app.dependency_overrides[get_classical_model] = lambda: DummyClassicalModel()
    app.dependency_overrides[get_nlp_model] = lambda: DummyNLPModel()
    app.dependency_overrides[get_nlp_tokenizer] = lambda: DummyTokenizer()
    return app


@pytest.fixture
def test_client(test_app):
    from fastapi.testclient import TestClient
    with TestClient(test_app) as client:
        yield client


# --- Tests ---

def test_analyze_endpoint_success(test_client, mock_sample_probabilities):
    payload = {
        "text": "URGENT: Click here to verify your account immediately!",
        "subject": "Account Suspended"
    }
    
    response = test_client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "request_id" in data
    assert data["ml_probability"] == 0.8
    assert data["nlp_probability"] == 0.85
    
    # Text contains "URGENT", so urgency_language should be True.
    # We expect rule_bonus > 0.
    assert data["rule_bonus"] > 0
    assert data["risk_score"] > (0.8 * 0.4 + 0.85 * 0.4) * 100
    assert data["classification"] in ["Low", "Medium", "High", "Critical"]


def test_analyze_endpoint_requires_text(test_client):
    payload = {"subject": "No text body"}
    response = test_client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422


def test_request_id_middleware_generates_id(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_request_id_middleware_preserves_id(test_client):
    custom_id = "test-custom-id-12345"
    response = test_client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id


def test_analyze_endpoint_propagates_request_id(test_client, mock_sample_probabilities):
    custom_id = "analyze-req-999"
    payload = {"text": "Hello"}
    response = test_client.post(
        "/api/v1/analyze", 
        json=payload, 
        headers={"X-Request-ID": custom_id}
    )
    
    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id
    
    # Check that it's also in the response body payload
    data = response.json()
    assert data["request_id"] == custom_id
