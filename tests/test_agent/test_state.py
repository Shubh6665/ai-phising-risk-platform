"""Tests for agent state, schemas, and deterministic escalation rules."""

import pytest
from src.agent.schemas import (
    URLAnalyzerInput,
    URLObservation,
    PolicyLookupInput,
    PolicyGuidanceResult,
    KnowledgeSearchInput,
    KnowledgeSearchResult,
)
from src.agent.state import (
    PhishingAnalysisState,
    compute_deterministic_escalation,
    create_initial_agent_state,
)


def test_deterministic_escalation_rules():
    """Test deterministic escalation conditions based on risk score and model divergence."""
    # Case 1: Low risk, agreement -> No escalation
    esc, reason = compute_deterministic_escalation(risk_score=20.0, ml_probability=0.2, nlp_probability=0.25)
    assert esc is False
    assert reason is None

    # Case 2: High uncertainty tier (60 <= score < 80) -> Mandatory escalation
    esc, reason = compute_deterministic_escalation(risk_score=68.5, ml_probability=0.68, nlp_probability=0.69)
    assert esc is True
    assert "High-uncertainty triage tier" in reason

    # Case 3: Medium score but significant model disagreement (> 0.30) -> Mandatory escalation
    esc, reason = compute_deterministic_escalation(risk_score=45.0, ml_probability=0.85, nlp_probability=0.15)
    assert esc is True
    assert "Model disagreement" in reason

    # Case 4: Critical score (> 80), model agreement -> No uncertainty escalation
    esc, reason = compute_deterministic_escalation(risk_score=92.0, ml_probability=0.95, nlp_probability=0.91)
    assert esc is False
    assert reason is None

    # Case 5: Both High uncertainty AND model disagreement
    esc, reason = compute_deterministic_escalation(risk_score=65.0, ml_probability=0.85, nlp_probability=0.45)
    assert esc is True
    assert "High-uncertainty triage tier" in reason
    assert "Model disagreement" in reason


def test_create_initial_agent_state():
    """Test full initial agent state population with immutability of ML signals."""
    state = create_initial_agent_state(
        request_id="req-agent-001",
        email_text="Please click here to update your credentials immediately.",
        email_subject="Urgent: Account Suspended",
        extracted_urls=["https://phish.example.com/login"],
        ml_probability=0.82,
        nlp_probability=0.88,
        risk_score=85.0,
        classification="Critical",
        rule_bonus=5.0,
        extracted_features={"url_count": 1, "urgency_score": 3},
        analysis_id="uuid-1234-5678",
    )

    assert state["request_id"] == "req-agent-001"
    assert state["analysis_id"] == "uuid-1234-5678"
    assert state["email_subject"] == "Urgent: Account Suspended"
    assert state["extracted_urls"] == ["https://phish.example.com/login"]
    assert state["risk_score"] == 85.0
    assert state["classification"] == "Critical"
    assert state["ml_probability"] == 0.82
    assert state["nlp_probability"] == 0.88
    assert state["rule_bonus"] == 5.0
    assert state["extracted_features"]["url_count"] == 1
    assert state["url_analysis"] == []
    assert state["policy_guidance"] is None
    assert state["retrieved_evidence"] == []
    assert state["tool_outputs"] == []
    assert state["tool_errors"] == []
    assert state["requires_escalation"] is False
    assert state["explanation"] is None
    assert state["recommendations"] == []


def test_agent_schema_validations():
    """Test Pydantic validation rules on agent tool input schemas."""
    # Valid inputs
    url_input = URLAnalyzerInput(url="https://example.com")
    assert url_input.url == "https://example.com"

    policy_input = PolicyLookupInput(risk_score=55.5)
    assert policy_input.risk_score == 55.5

    kb_input = KnowledgeSearchInput(query="MITRE T1566 spearphishing", top_k=5)
    assert kb_input.top_k == 5

    # Invalid URL (empty string)
    with pytest.raises(ValueError):
        URLAnalyzerInput(url="")

    # Invalid policy risk score (< 0 or > 100)
    with pytest.raises(ValueError):
        PolicyLookupInput(risk_score=-5.0)
    with pytest.raises(ValueError):
        PolicyLookupInput(risk_score=105.0)

    # Invalid KB search input (empty query or out-of-range top_k)
    with pytest.raises(ValueError):
        KnowledgeSearchInput(query="")
    with pytest.raises(ValueError):
        KnowledgeSearchInput(query="test", top_k=0)
    with pytest.raises(ValueError):
        KnowledgeSearchInput(query="test", top_k=20)

