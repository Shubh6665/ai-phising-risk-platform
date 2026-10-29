"""Tests for the Phase 8B LangGraph investigation workflow."""

import socket
import urllib.request
from unittest.mock import patch
import pytest

from src.agent.graph import (
    build_investigation_graph,
    run_investigation,
)
from src.agent.state import create_initial_agent_state
from src.rag.embeddings import DummyEmbedder


def test_graph_compilation():
    """Verify that the investigation StateGraph compiles cleanly."""
    graph = build_investigation_graph()
    assert graph is not None


def test_graph_full_execution_flow():
    """Verify end-to-end sequential execution through all 5 nodes with valid state."""
    initial_state = create_initial_agent_state(
        request_id="req-test-graph-01",
        email_text="Please verify your banking profile at http://192.168.1.1:8080/login immediately.",
        email_subject="Urgent Security Alert",
        ml_probability=0.78,
        nlp_probability=0.82,
        risk_score=72.0,
        classification="High",
        rule_bonus=10.0,
        extracted_features={"url_count": 1},
        analysis_id="db-uuid-111",
    )

    fake_hits = [
        {
            "id": "attack_patterns_0_test",
            "content": "Adversaries leverage credential harvesting portals...",
            "distance": 0.15,
            "similarity": 0.92,
            "document_name": "attack_patterns.md",
            "document_title": "Attack Patterns",
            "heading": "2. MITRE ATT&CK Phishing Taxonomy",
            "document_type": "source_backed_guidance",
            "source_attribution": "MITRE ATT&CK v20.0 (October 13, 2026)",
            "is_mock": False,
        }
    ]

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchChunk, KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="retrieved",
            results_count=1,
            chunks=[KnowledgeSearchChunk(
                chunk_id="attack_patterns_0_test",
                content="Adversaries leverage credential harvesting portals...",
                similarity=0.92,
                document_name="attack_patterns.md",
                document_title="Attack Patterns",
                heading="2. MITRE ATT&CK Phishing Taxonomy",
                document_type="source_backed_guidance",
                source_attribution="MITRE ATT&CK v20.0 (October 13, 2026)",
                is_mock=False,
            )],
        )

        dummy_embedder = DummyEmbedder(dimension=384)
        final_state = run_investigation(initial_state, embedder=dummy_embedder)

        # 1. Verify preservation of pre-computed ML signals
        assert final_state["request_id"] == "req-test-graph-01"
        assert final_state["analysis_id"] == "db-uuid-111"
        assert final_state["risk_score"] == 72.0
        assert final_state["classification"] == "High"
        assert final_state["ml_probability"] == 0.78
        assert final_state["nlp_probability"] == 0.82
        assert final_state["rule_bonus"] == 10.0

        # 2. Verify URL analysis results
        assert len(final_state["url_analysis"]) == 1
        url_obs = final_state["url_analysis"][0]
        assert url_obs["url"] == "http://192.168.1.1:8080/login"
        assert url_obs["is_ip_literal"] is True
        assert url_obs["has_unusual_port"] is True
        assert url_obs["port"] == 8080

        # 3. Verify Policy guidance results
        assert final_state["policy_guidance"] is not None
        assert final_state["policy_guidance"]["classification"] == "High"
        assert "Automated Quarantine" in final_state["policy_guidance"]["triage_action"]

        # 4. Verify Retrieved Evidence
        assert len(final_state["retrieved_evidence"]) == 1
        assert final_state["retrieved_evidence"][0]["chunk_id"] == "attack_patterns_0_test"

        # 5. Verify Deterministic Escalation (High score: 72.0)
        assert final_state["requires_escalation"] is True
        assert "High-uncertainty triage tier" in final_state["escalation_reason"]

        # 6. Verify Tool Outputs Tracking
        tool_names = [t["tool"] for t in final_state["tool_outputs"]]
        assert "validate_input" in tool_names
        assert "knowledge_search" in tool_names
        assert "url_structure_analyzer" in tool_names
        assert "policy_lookup" in tool_names
        assert "aggregate_findings" in tool_names
        assert "explanation_generator" in tool_names
        assert len(final_state["tool_errors"]) == 0


def test_graph_invalid_input_conditional_branching():
    """Verify conditional edge skips tools and branches directly to aggregate_findings on errors."""
    # State with empty email_text and out-of-range risk_score
    invalid_state = {
        "request_id": "req-invalid-01",
        "email_text": "   ",  # whitespace only
        "risk_score": 150.0,  # invalid (> 100)
        "ml_probability": 0.5,
        "nlp_probability": 0.5,
        "classification": "Invalid",
        "tool_outputs": [],
        "tool_errors": [],
    }

    final_state = run_investigation(invalid_state)

    # Errors logged in tool_errors
    assert len(final_state["tool_errors"]) >= 2
    assert any("email_text" in err for err in final_state["tool_errors"])
    assert any("risk_score" in err for err in final_state["tool_errors"])

    # Tool outputs must only have validate_input and aggregate_findings
    tools_called = [t["tool"] for t in final_state["tool_outputs"]]
    assert tools_called == ["validate_input", "aggregate_findings"]
    assert "knowledge_search" not in tools_called
    assert "url_structure_analyzer" not in tools_called
    assert "policy_lookup" not in tools_called


def test_graph_critical_tier_escalation():
    """Verify that Critical risk scores (>= 80.0) trigger immediate containment escalation."""
    critical_state = create_initial_agent_state(
        request_id="req-critical-01",
        email_text="Wire transfer urgent instructions.",
        ml_probability=0.92,
        nlp_probability=0.94,
        risk_score=94.0,
        classification="Critical",
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="empty",
            results_count=0,
            chunks=[],
        )
        final_state = run_investigation(critical_state)

    assert final_state["requires_escalation"] is True
    assert "Critical risk tier" in final_state["escalation_reason"]
    assert final_state["policy_guidance"]["classification"] == "Critical"
    assert "Immediate Block" in final_state["policy_guidance"]["triage_action"]


def test_graph_low_tier_no_escalation():
    """Verify that Low risk scores with agreeing models do not trigger escalation."""
    low_state = create_initial_agent_state(
        request_id="req-low-01",
        email_text="Hey team, lunch at 12pm today?",
        ml_probability=0.05,
        nlp_probability=0.02,
        risk_score=5.0,
        classification="Low",
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="empty",
            results_count=0,
            chunks=[],
        )
        final_state = run_investigation(low_state)

    assert final_state["requires_escalation"] is False
    assert final_state["escalation_reason"] is None
    assert final_state["policy_guidance"]["classification"] == "Low"
    assert "Standard Delivery / Allow" in final_state["policy_guidance"]["triage_action"]


def test_graph_model_disagreement_escalation():
    """Verify that significant model divergence (> 0.30) triggers escalation regardless of score."""
    disagree_state = create_initial_agent_state(
        request_id="req-disagree-01",
        email_text="Please review attached invoice.",
        ml_probability=0.88,
        nlp_probability=0.12,  # Delta = 0.76 > 0.30
        risk_score=45.0,        # Medium score
        classification="Medium",
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="empty",
            results_count=0,
            chunks=[],
        )
        final_state = run_investigation(disagree_state)

    assert final_state["requires_escalation"] is True
    assert "Model disagreement" in final_state["escalation_reason"]


def test_graph_knowledge_base_empty_handling():
    """Verify empty vector store gracefully continues through all remaining nodes."""
    state = create_initial_agent_state(
        request_id="req-empty-kb",
        email_text="Check out https://test.org",
        ml_probability=0.3,
        nlp_probability=0.3,
        risk_score=30.0,
        classification="Low",
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="empty",
            results_count=0,
            chunks=[],
        )
        final_state = run_investigation(state)

    assert final_state["retrieved_evidence"] == []
    assert len(final_state["url_analysis"]) == 1
    assert final_state["policy_guidance"] is not None
    # Confirm knowledge_search tool recorded status="empty"
    kb_output = next(t for t in final_state["tool_outputs"] if t["tool"] == "knowledge_search")
    assert kb_output["status"] == "empty"


def test_graph_knowledge_base_error_handling():
    """Verify vector search exceptions are logged in tool_errors without halting workflow."""
    state = create_initial_agent_state(
        request_id="req-err-kb",
        email_text="Check out http://10.0.0.1",
        ml_probability=0.5,
        nlp_probability=0.5,
        risk_score=50.0,
        classification="Medium",
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="error",
            results_count=0,
            chunks=[],
            error_message="ChromaDB unavailable",
        )
        final_state = run_investigation(state)

    assert final_state["retrieved_evidence"] == []
    assert any("Knowledge search error: ChromaDB unavailable" in err for err in final_state["tool_errors"])
    # URL analyzer and policy lookup still completed successfully
    assert len(final_state["url_analysis"]) == 1
    assert final_state["policy_guidance"]["classification"] == "Medium"


def test_graph_offline_guarantee_no_network_access(monkeypatch):
    """Verify graph executes completely offline with zero network or DNS calls."""
    # Ensure offline mode by unsetting external API keys
    from src.config import settings
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", None)
    monkeypatch.setattr(settings, "GROQ_API_KEY", None)

    def guarded_connect(*args, **kwargs):
        pytest.fail("Network access attempted during LangGraph investigation execution!")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_connect)
    monkeypatch.setattr(urllib.request, "urlopen", guarded_connect)

    state = create_initial_agent_state(
        request_id="req-offline-01",
        email_text="Verify at http://192.168.1.1:8080/portal",
        ml_probability=0.65,
        nlp_probability=0.65,
        risk_score=65.0,
        classification="High",
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="empty",
            results_count=0,
            chunks=[],
        )
        final_state = run_investigation(state)

    assert final_state["requires_escalation"] is True
    assert len(final_state["url_analysis"]) == 1


def test_graph_no_raw_email_in_tool_outputs():
    """Verify tool_outputs audit trail does not leak the full raw email text."""
    secret_body = "CONFIDENTIAL INTERNAL DISCUSSION: do not share outside engineering"
    state = create_initial_agent_state(
        request_id="req-privacy-01",
        email_text=secret_body,
        ml_probability=0.1,
        nlp_probability=0.1,
        risk_score=10.0,
        classification="Low",
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="empty",
            results_count=0,
            chunks=[],
        )
        final_state = run_investigation(state)

    # Check that tool_outputs records do not contain secret_body
    for entry in final_state["tool_outputs"]:
        entry_str = str(entry)
        assert secret_body not in entry_str


def test_graph_with_injected_primary_llm():
    """Verify graph uses injected mock LLM and populates structured explanation without altering scores."""
    from unittest.mock import MagicMock
    from src.agent.schemas import InvestigationExplanation

    mock_llm = MagicMock()
    mock_struct = MagicMock()
    mock_explanation = InvestigationExplanation(
        summary="Phishing attempt detected with credential harvesting signals.",
        key_findings=["Insecure link to IP address"],
        risk_explanation="Risk score 75.0 warrants automated quarantine.",
        recommended_actions=["Quarantine message"],
        limitations=["Offline analysis only"],
        evidence_references=["chunk-1"],
        provider_used="google",
        generation_status="completed",
    )
    mock_struct.invoke.return_value = mock_explanation
    mock_llm.with_structured_output.return_value = mock_struct

    state = create_initial_agent_state(
        request_id="req-injected-llm",
        email_text="Please sign in at http://192.168.1.10/login",
        ml_probability=0.8,
        nlp_probability=0.7,
        risk_score=75.0,
        classification="High",
    )

    with patch("src.agent.graph.search_security_knowledge") as mock_search:
        from src.agent.schemas import KnowledgeSearchResult
        mock_search.return_value = KnowledgeSearchResult(
            query="test",
            status="empty",
            results_count=0,
            chunks=[],
        )
        final_state = run_investigation(state, primary_llm=mock_llm)

    assert final_state["explanation"] == mock_explanation.summary
    assert final_state["recommendations"] == ["Quarantine message"]
    assert final_state["structured_explanation"]["provider_used"] == "google"
    assert final_state["structured_explanation"]["generation_status"] == "completed"

    # Precomputed scores must remain 100% identical
    assert final_state["risk_score"] == 75.0
    assert final_state["classification"] == "High"
    assert final_state["ml_probability"] == 0.8
    assert final_state["nlp_probability"] == 0.7
    assert final_state["requires_escalation"] is True

