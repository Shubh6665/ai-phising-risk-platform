"""Tests for Phase 8D: LangGraph investigation agent integration into FastAPI analysis endpoint."""

import socket
import urllib.request
import uuid
from unittest.mock import MagicMock, patch
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
    get_investigation_graph,
)
from src.api.schemas import AnalyzeResponse
from src.agent.graph import build_investigation_graph
from src.agent.schemas import InvestigationExplanation
from src.config import settings
from src.db.models import Base, AnalysisResult
from src.db.repository import DatabasePersistenceError
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
            "source_attribution": "MITRE ATT&CK Framework v20.0",
        },
        {
            "id": "security_policies_002_def987654321",
            "content": "Out-of-band verification is recommended for all high-risk account updates.",
            "distance": 0.52,
            "similarity": 0.740,
            "source_path": "data/knowledge_base/security_policies.md",
            "document_name": "security_policies.md",
            "document_title": "Project Triage Guidance and Recommended Security Controls",
            "document_type": "source_backed_guidance",
            "heading": "Out-of-Band Verification",
            "is_mock": False,
            "source_attribution": "CISA Phishing Guidance; NIST SP 800-61 Rev. 3",
        },
    ]


@pytest.fixture
def agent_test_app(test_db_session, monkeypatch):
    """FastAPI test app configured for offline execution without live API keys."""
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", None)
    monkeypatch.setattr(settings, "GROQ_API_KEY", None)

    app = create_app()
    app.dependency_overrides[get_classical_model] = lambda: DummyClassicalModel()
    app.dependency_overrides[get_nlp_model] = lambda: DummyNLPModel()
    app.dependency_overrides[get_nlp_tokenizer] = lambda: DummyTokenizer()
    app.dependency_overrides[get_db] = lambda: test_db_session
    return app


# --- Tests ---


def test_analyze_with_agent_findings_and_explanation(
    agent_test_app, mock_sample_probabilities, sample_evidence_hits, test_db_session
):
    """Verify successful end-to-end analysis returning scoring, evidence, URL analysis, and explanation."""
    agent_test_app.dependency_overrides[get_rag_retriever] = (
        lambda: lambda query, top_k=3: sample_evidence_hits
    )

    # Injected mock LLM
    mock_llm = MagicMock()
    mock_struct = MagicMock()
    mock_explanation = InvestigationExplanation(
        summary="Phishing attempt detected with IP-literal host and urgency language.",
        key_findings=["Direct IP literal hostname detected", "High probability across classical and NLP models"],
        risk_explanation="Composite risk score 82.0 places message in Critical tier.",
        recommended_actions=["Enforce perimeter blocklist", "Advise recipient of potential compromise"],
        limitations=["Offline analysis only"],
        evidence_references=["attack_patterns_001_abc123456789"],
        provider_used="google",
        generation_status="completed",
    )
    mock_struct.invoke.return_value = mock_explanation
    mock_llm.with_structured_output.return_value = mock_struct

    # Build graph with injected mock LLM
    custom_graph = build_investigation_graph(
        embedder=DummyEmbedder(dimension=384),
        primary_llm=mock_llm,
    )
    agent_test_app.dependency_overrides[get_investigation_graph] = lambda: custom_graph

    with TestClient(agent_test_app) as client:
        payload = {
            "text": "URGENT: Verify your account immediately at http://192.168.1.100:8080/auth",
            "subject": "Immediate Action Required",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()

        # 1. Classical and NLP inference remains intact
        assert data["ml_probability"] == 0.8
        assert data["nlp_probability"] == 0.85
        assert data["rule_bonus"] > 0
        assert data["risk_score"] > 80.0
        assert data["classification"] == "Critical"
        assert data["analysis_id"] is not None

        # 2. Database persistence intact
        persisted = test_db_session.scalar(
            select(AnalysisResult).where(AnalysisResult.id == uuid.UUID(data["analysis_id"]))
        )
        assert persisted is not None
        assert persisted.risk_score == data["risk_score"]

        # 3. Retrieved security evidence intact
        assert data["evidence_status"] == "retrieved"
        assert len(data["evidence"]) == 2

        # 4. Deterministic escalation
        assert data["requires_escalation"] is True
        assert "Critical risk tier" in data["escalation_reason"]

        # 5. URL observations
        assert len(data["url_analysis"]) == 1
        url_obs = data["url_analysis"][0]
        assert url_obs["hostname"] == "192.168.1.100"
        assert url_obs["port"] == 8080
        assert url_obs["is_ip_literal"] is True
        assert url_obs["has_unusual_port"] is True

        # 6. Structured explanation
        explanation = data["explanation"]
        assert explanation is not None
        assert explanation["summary"] == mock_explanation.summary
        assert explanation["provider_used"] == "google"
        assert explanation["generation_status"] == "completed"
        assert len(explanation["recommended_actions"]) == 2


def test_analyze_reuses_pre_retrieved_evidence_without_duplicate_search(
    agent_test_app, mock_sample_probabilities, sample_evidence_hits
):
    """Verify that knowledge-base search is performed once by retriever and reused by the graph."""
    agent_test_app.dependency_overrides[get_rag_retriever] = (
        lambda: lambda query, top_k=3: sample_evidence_hits
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_graph_search:
        with TestClient(agent_test_app) as client:
            payload = {
                "text": "Please check http://login.bank.com to confirm wire details.",
                "subject": "Wire Transfer Notice",
            }
            response = client.post("/api/v1/analyze", json=payload)
            assert response.status_code == 200

            # The graph's search_security_knowledge must NOT be called because evidence was reused!
            mock_graph_search.assert_not_called()

            data = response.json()
            assert len(data["evidence"]) == 2
            assert data["evidence_status"] == "retrieved"


def test_analyze_with_empty_rag_results(
    agent_test_app, mock_sample_probabilities
):
    """Verify behavior when RAG retriever returns empty results."""
    agent_test_app.dependency_overrides[get_rag_retriever] = (
        lambda: lambda query, top_k=3: []
    )

    with TestClient(agent_test_app) as client:
        payload = {
            "text": "Hello, meeting is scheduled for tomorrow at 3pm.",
            "subject": "Tomorrow's Schedule",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["evidence"] == []
        assert data["evidence_status"] == "empty"
        # Explanation still generated gracefully
        assert data["explanation"] is not None
        assert data["explanation"]["generation_status"] in ["completed", "degraded"]


def test_analyze_with_retrieval_failure_recovers_gracefully(
    agent_test_app, mock_sample_probabilities
):
    """Verify that vector search exception in retriever does not fail analysis."""
    def failing_retriever(query, top_k=3):
        raise RuntimeError("ChromaDB vector store connection refused")

    agent_test_app.dependency_overrides[get_rag_retriever] = lambda: failing_retriever

    with TestClient(agent_test_app) as client:
        payload = {
            "text": "Urgent update required at http://10.0.0.1/verify",
            "subject": "Password Reset",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["evidence_status"] == "unavailable"
        assert data["evidence"] == []
        assert data["risk_score"] > 0
        assert data["analysis_id"] is not None
        # Explanation still generated via degraded generator
        assert data["explanation"] is not None


def test_analyze_both_llm_providers_fail_deterministic_degraded_explanation(
    agent_test_app, mock_sample_probabilities, sample_evidence_hits
):
    """Verify graceful fallback to deterministic degraded explanation when LLM providers fail."""
    agent_test_app.dependency_overrides[get_rag_retriever] = (
        lambda: lambda query, top_k=3: sample_evidence_hits
    )

    failing_llm = MagicMock()
    failing_llm.with_structured_output.side_effect = RuntimeError("Provider 429 Quota Exceeded")

    graph = build_investigation_graph(
        embedder=DummyEmbedder(dimension=384),
        primary_llm=failing_llm,
        fallback_llm=failing_llm,
    )
    agent_test_app.dependency_overrides[get_investigation_graph] = lambda: graph

    with TestClient(agent_test_app) as client:
        payload = {
            "text": "Click here to login: http://phish-site.org/auth",
            "subject": "Security Review Required",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        exp = data["explanation"]
        assert exp is not None
        assert exp["generation_status"] == "degraded"
        assert exp["provider_used"] is None
        assert "Automated recommended operational action is:" in exp["summary"]
        assert len(exp["recommended_actions"]) > 0


def test_analyze_graph_invocation_exception_recovers_gracefully(
    agent_test_app, mock_sample_probabilities, test_db_session
):
    """Verify that unexpected graph invocation exception does not fail analysis or drop DB persistence."""
    failing_graph = MagicMock()
    failing_graph.invoke.side_effect = RuntimeError("Fatal graph state recursion")
    agent_test_app.dependency_overrides[get_investigation_graph] = lambda: failing_graph

    with TestClient(agent_test_app) as client:
        payload = {
            "text": "Urgent alert: http://192.168.0.1 needs your credentials.",
            "subject": "Urgent Alert",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["risk_score"] > 0
        assert data["analysis_id"] is not None

        # Confirm persisted in DB
        persisted = test_db_session.scalar(
            select(AnalysisResult).where(AnalysisResult.id == uuid.UUID(data["analysis_id"]))
        )
        assert persisted is not None

        # Recovered explanation marked degraded
        assert data["explanation"] is not None
        assert data["explanation"]["generation_status"] == "degraded"


def test_analyze_database_failure_returns_500_before_agent(
    agent_test_app, mock_sample_probabilities
):
    """Verify that database persistence failure is not swallowed and aborts with 500."""
    with patch(
        "src.db.repository.AnalysisRepository.save_analysis_result",
        side_effect=DatabasePersistenceError("Database down"),
    ):
        with TestClient(agent_test_app) as client:
            payload = {
                "text": "Suspicious email text content.",
                "subject": "Test",
            }
            response = client.post("/api/v1/analyze", json=payload)
            assert response.status_code == 500

            err = response.json()
            assert err["error"] == "database_error"
            assert err["detail"] == "Failed to persist analysis result."


def test_analyze_response_backwards_compatibility(
    agent_test_app, mock_sample_probabilities
):
    """Verify that clients consuming only Phase 6/7 fields can validate without error."""
    with TestClient(agent_test_app) as client:
        payload = {
            "text": "Standard routine invoice email.",
            "subject": "Monthly Invoice",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Verify all existing Phase 6/7 fields are present and valid
        assert "request_id" in data
        assert "risk_score" in data
        assert "classification" in data
        assert "ml_probability" in data
        assert "nlp_probability" in data
        assert "rule_bonus" in data
        assert "analysis_id" in data
        assert "evidence" in data
        assert "evidence_status" in data


def test_analyze_no_raw_email_leakage(
    agent_test_app, mock_sample_probabilities, test_db_session
):
    """Verify that raw email body text is never leaked into explanations or database records."""
    canary = "CANARY_SECRET_TOKEN_DO_NOT_LEAK_999888777"
    with TestClient(agent_test_app) as client:
        payload = {
            "text": f"Your confidential passcode is {canary}. Visit http://auth.example.com",
            "subject": "Secret Password Update",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        explanation = data.get("explanation") or {}
        # Canary must not appear in summary or key findings
        assert canary not in explanation.get("summary", "")
        for finding in explanation.get("key_findings", []):
            assert canary not in finding

        # Confirm database only persisted hash, not raw email text
        persisted = test_db_session.scalar(
            select(AnalysisResult).where(AnalysisResult.id == uuid.UUID(data["analysis_id"]))
        )
        assert persisted is not None
        assert len(persisted.email_hash) == 64


def test_analyze_independent_sequential_requests(
    agent_test_app, mock_sample_probabilities
):
    """Verify sequential requests maintain independent request IDs and analysis states."""
    with TestClient(agent_test_app) as client:
        res1 = client.post("/api/v1/analyze", json={"text": "Email 1 with http://one.com", "subject": "Subject 1"})
        res2 = client.post("/api/v1/analyze", json={"text": "Email 2 with http://two.com", "subject": "Subject 2"})

        assert res1.status_code == 200
        assert res2.status_code == 200

        data1 = res1.json()
        data2 = res2.json()

        assert data1["request_id"] != data2["request_id"]
        assert data1["analysis_id"] != data2["analysis_id"]
        assert data1["url_analysis"][0]["hostname"] == "one.com"
        assert data2["url_analysis"][0]["hostname"] == "two.com"


def test_analyze_offline_guarantee_no_network_access(
    agent_test_app, mock_sample_probabilities, monkeypatch
):
    """Verify zero socket network calls occur during offline API execution."""
    real_socket_connect = socket.socket.connect

    def blocked_connect(self, *args, **kwargs):
        raise AssertionError("Unexpected network call intercepted during offline analysis!")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)

    with TestClient(agent_test_app) as client:
        payload = {
            "text": "Check out http://10.0.0.1:8080/dashboard now.",
            "subject": "Offline System Check",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] > 0
        assert len(data["url_analysis"]) == 1
        assert data["explanation"] is not None

