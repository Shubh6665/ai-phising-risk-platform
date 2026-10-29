"""Tests for Phase 7C: FastAPI RAG integration, evidence metadata, and degraded retrieval behavior."""

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
    get_rag_retriever,
    get_rag_embedder,
)
from src.api.schemas import SecurityEvidenceItem, AnalyzeResponse
from src.config import settings
from src.db.models import Base, AnalysisResult
from src.db.session import get_db
from src.rag.embeddings import DummyEmbedder


# --- Test Doubles ---


class DummyClassicalModel:
    def predict_proba(self, features):
        return np.array([[0.2, 0.8]])


class DummyNLPModel:
    pass


class DummyTokenizer:
    pass


@pytest.fixture
def mock_sample_probabilities(monkeypatch):
    def mock_sample(model, tokenizer, texts, max_length, batch_size):
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
def sample_evidence_hits():
    return [
        {
            "id": "attack_patterns_001_abc123456789",
            "content": "Credential harvesting portals mirror enterprise login screens (MITRE T1566.002).",
            "distance": 0.45,
            "similarity": 0.775,
            "source_path": "data/knowledge_base/attack_patterns.md",
            "document_name": "attack_patterns.md",
            "document_title": "Attack Patterns and Threat Actor Tactics",
            "document_type": "source_backed_guidance",
            "heading": "Profile A: Credential Harvesting and AiTM",
            "is_mock": False,
            "source_attribution": "MITRE ATT&CK Framework, OWASP",
        },
        {
            "id": "security_policies_002_def987654321",
            "content": "Out-of-band verification is required for all urgent wire transfer requests.",
            "distance": 0.52,
            "similarity": 0.740,
            "source_path": "data/knowledge_base/security_policies.md",
            "document_name": "security_policies.md",
            "document_title": "Project Triage Guidance and Recommended Security Controls",
            "document_type": "source_backed_guidance",
            "heading": "Out-of-Band Verification for Financial and Executive Requests",
            "is_mock": False,
            "source_attribution": "CISA Phishing Guidance, NIST SP 800-61 Rev. 3",
        },
    ]


@pytest.fixture
def rag_test_app(test_db_session):
    app = create_app()
    app.dependency_overrides[get_classical_model] = lambda: DummyClassicalModel()
    app.dependency_overrides[get_nlp_model] = lambda: DummyNLPModel()
    app.dependency_overrides[get_nlp_tokenizer] = lambda: DummyTokenizer()
    app.dependency_overrides[get_db] = lambda: test_db_session
    return app


# --- Tests ---


def test_analyze_with_retrieved_security_evidence(
    rag_test_app, mock_sample_probabilities, sample_evidence_hits, test_db_session
):
    """Successful analysis returns both model scoring and retrieved security evidence."""
    rag_test_app.dependency_overrides[get_rag_retriever] = (
        lambda: lambda query, top_k=3: sample_evidence_hits
    )

    with TestClient(rag_test_app) as client:
        payload = {
            "text": "URGENT: Please verify your credentials at http://login-update.com",
            "subject": "Action Required: Account Verification",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()

        # 1. Verify model scoring and classification are intact
        assert data["ml_probability"] == 0.8
        assert data["nlp_probability"] == 0.85
        assert data["rule_bonus"] > 0
        assert data["risk_score"] > 0
        assert data["classification"] in ["Low", "Medium", "High", "Critical"]
        assert data["analysis_id"] is not None

        # 2. Verify database persistence is intact
        persisted = test_db_session.scalar(
            select(AnalysisResult).where(AnalysisResult.id == uuid.UUID(data["analysis_id"]))
        )
        assert persisted is not None
        assert persisted.risk_score == data["risk_score"]

        # 3. Verify retrieved security evidence structure
        assert data["evidence_status"] == "retrieved"
        assert len(data["evidence"]) == 2

        hit1 = data["evidence"][0]
        assert hit1["chunk_id"] == "attack_patterns_001_abc123456789"
        assert "Credential harvesting portals" in hit1["content"]
        assert hit1["similarity"] == 0.775
        assert hit1["document_name"] == "attack_patterns.md"
        assert hit1["document_type"] == "source_backed_guidance"
        assert hit1["heading"] == "Profile A: Credential Harvesting and AiTM"
        assert hit1["is_mock"] is False
        assert hit1["source_attribution"] == "MITRE ATT&CK Framework, OWASP"

        hit2 = data["evidence"][1]
        assert hit2["chunk_id"] == "security_policies_002_def987654321"
        assert hit2["document_type"] == "source_backed_guidance"
        assert hit2["is_mock"] is False


def test_analyze_when_rag_is_disabled(
    rag_test_app, mock_sample_probabilities, monkeypatch
):
    """When RAG_ENABLED is false, analysis succeeds with evidence_status='disabled'."""
    monkeypatch.setattr(settings, "RAG_ENABLED", False)

    with TestClient(rag_test_app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={"text": "Review the attached invoice for payment."},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["evidence_status"] == "disabled"
        assert data["evidence"] == []
        assert data["risk_score"] > 0
        assert data["classification"] in ["Low", "Medium", "High", "Critical"]


def test_analyze_when_retriever_is_unavailable(
    rag_test_app, mock_sample_probabilities
):
    """When retriever is None (e.g. embedder failed to load), evidence_status is 'unavailable'."""
    rag_test_app.dependency_overrides[get_rag_retriever] = lambda: None

    with TestClient(rag_test_app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={"text": "Hello, here is the weekly project update."},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["evidence_status"] == "unavailable"
        assert data["evidence"] == []
        assert data["risk_score"] > 0


def test_analyze_when_knowledge_base_is_empty(
    rag_test_app, mock_sample_probabilities
):
    """When knowledge base returns zero chunks, evidence_status is 'empty' without failing."""
    rag_test_app.dependency_overrides[get_rag_retriever] = lambda: lambda query, top_k=3: []

    with TestClient(rag_test_app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={"text": "Checking out the document."},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["evidence_status"] == "empty"
        assert data["evidence"] == []
        assert data["risk_score"] > 0


def test_analyze_gracefully_degrades_on_retriever_exception(
    rag_test_app, mock_sample_probabilities
):
    """When ChromaDB/retriever raises an unexpected error, analysis completes with evidence_status='unavailable'."""
    def failing_retriever(query, top_k=3):
        raise RuntimeError("ChromaDB connection or I/O failure.")

    rag_test_app.dependency_overrides[get_rag_retriever] = lambda: failing_retriever

    with TestClient(rag_test_app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={"text": "Password reset required immediately."},
        )
        assert response.status_code == 200
        data = response.json()

        # The core risk assessment must succeed even when optional retrieval fails
        assert data["evidence_status"] == "unavailable"
        assert data["evidence"] == []
        assert data["risk_score"] > 0
        assert data["analysis_id"] is not None


def test_security_evidence_schema_validations():
    """Ensure SecurityEvidenceItem enforces correct constraints and types."""
    valid_item = SecurityEvidenceItem(
        chunk_id="chk_001_123456",
        content="Guidance excerpt.",
        similarity=0.85,
        document_name="attack_patterns.md",
        document_title="Attack Patterns",
        heading="2. Taxonomy",
        document_type="source_backed_guidance",
        source_attribution="MITRE ATT&CK",
        is_mock=False,
    )
    assert valid_item.similarity == 0.85
    assert not valid_item.is_mock

    # Invalid similarity score (> 1.0)
    with pytest.raises(Exception):
        SecurityEvidenceItem(
            chunk_id="chk_001_123456",
            content="Excerpt",
            similarity=1.5,
            document_name="attack_patterns.md",
            document_type="source_backed_guidance",
            source_attribution="MITRE",
        )

    # Invalid similarity score (< 0.0)
    with pytest.raises(Exception):
        SecurityEvidenceItem(
            chunk_id="chk_001_123456",
            content="Excerpt",
            similarity=-0.1,
            document_name="attack_patterns.md",
            document_type="source_backed_guidance",
            source_attribution="MITRE",
        )

