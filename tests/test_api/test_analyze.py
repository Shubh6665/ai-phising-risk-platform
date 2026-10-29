"""Tests for the analyze API endpoint, database persistence, and middleware."""

import uuid
import numpy as np
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.dependencies import (
    get_classical_model,
    get_nlp_model,
    get_nlp_tokenizer,
    get_analysis_repository,
)
from src.db.models import Base, AnalysisResult
from src.db.repository import AnalysisRepository, DatabasePersistenceError, hash_email_text
from src.db.session import get_db

# --- Test Doubles ---


class DummyClassicalModel:
    def predict_proba(self, features):
        # Always return 80% phishing probability
        return np.array([[0.2, 0.8]])


class DummyNLPModel:
    pass


class DummyTokenizer:
    pass


@pytest.fixture
def mock_sample_probabilities(monkeypatch):
    def mock_sample(model, tokenizer, texts, max_length, batch_size):
        # Always return 85% phishing probability
        return np.array([[0.15, 0.85]])

    monkeypatch.setattr("src.api.services.sample_probabilities", mock_sample)


@pytest.fixture
def test_db_session():
    """Isolated in-memory SQLite database session for API unit tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_app(test_db_session):
    app = create_app()
    app.dependency_overrides[get_classical_model] = lambda: DummyClassicalModel()
    app.dependency_overrides[get_nlp_model] = lambda: DummyNLPModel()
    app.dependency_overrides[get_nlp_tokenizer] = lambda: DummyTokenizer()
    app.dependency_overrides[get_db] = lambda: test_db_session
    return app


@pytest.fixture
def test_client(test_app):
    with TestClient(test_app) as client:
        yield client


# --- Tests ---


def test_analyze_endpoint_success(test_client, test_db_session, mock_sample_probabilities):
    payload = {
        "text": "URGENT: Click here to verify your account immediately!",
        "subject": "Account Suspended",
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

    # Verify persisted analysis ID is returned
    assert data["analysis_id"] is not None
    record_uuid = uuid.UUID(data["analysis_id"])

    # Verify record in database matches response
    persisted = test_db_session.scalar(
        select(AnalysisResult).where(AnalysisResult.id == record_uuid)
    )
    assert persisted is not None
    assert persisted.request_id == data["request_id"]
    assert persisted.ml_probability == data["ml_probability"]
    assert persisted.nlp_probability == data["nlp_probability"]
    assert persisted.rule_bonus == data["rule_bonus"]
    assert persisted.risk_score == data["risk_score"]
    assert persisted.classification == data["classification"]

    # Verify email hash was persisted rather than raw email text
    expected_hash = hash_email_text(
        f"{payload['subject']}\n\n{payload['text']}"
    )
    assert persisted.email_hash == expected_hash


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


def test_analyze_endpoint_propagates_request_id(
    test_client, test_db_session, mock_sample_probabilities
):
    custom_id = "analyze-req-999"
    payload = {"text": "Hello, this is a legitimate message."}
    response = test_client.post(
        "/api/v1/analyze",
        json=payload,
        headers={"X-Request-ID": custom_id},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id

    data = response.json()
    assert data["request_id"] == custom_id

    # Verify record in database has the propagated request ID
    record_uuid = uuid.UUID(data["analysis_id"])
    persisted = test_db_session.scalar(
        select(AnalysisResult).where(AnalysisResult.id == record_uuid)
    )
    assert persisted is not None
    assert persisted.request_id == custom_id


def test_analyze_endpoint_database_failure_returns_sanitized_500(
    test_app, mock_sample_probabilities
):
    """When database persistence fails, an error response is returned instead of 200."""
    class FailingRepository(AnalysisRepository):
        def save_analysis_result(self, **kwargs):
            raise DatabasePersistenceError("Simulated database failure during insert.")

    # Override repository with failing repository
    test_app.dependency_overrides[get_analysis_repository] = lambda: FailingRepository(None)

    with TestClient(test_app) as client:
        custom_id = "fail-req-500"
        response = client.post(
            "/api/v1/analyze",
            json={"text": "Suspicious email text"},
            headers={"X-Request-ID": custom_id},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["request_id"] == custom_id
        assert data["error"] == "database_error"
        assert data["detail"] == "Failed to persist analysis result."
        # Ensure raw internal traceback or database credentials are NOT in the payload
        assert "password" not in str(data).lower()
        assert "traceback" not in str(data).lower()
