"""Tests for Phase 8C LLM provider abstraction, fallback, and grounded explanations."""

from unittest.mock import MagicMock, patch
import pytest

from src.agent.llm import (
    build_minimized_investigation_prompt,
    generate_deterministic_degraded_explanation,
    generate_investigation_explanation,
    get_fallback_llm,
    get_primary_llm,
    sanitize_url_observations,
)
from src.agent.schemas import InvestigationExplanation
from src.agent.state import create_initial_agent_state
from src.config import settings


@pytest.fixture
def sample_investigation_state():
    """Fixture providing a realistic completed investigation state."""
    state = create_initial_agent_state(
        request_id="req-test-llm-01",
        email_text="Please sign in at https://secure-portal.com/login?token=dummy_sample_token_xyz to verify your account.",
        email_subject="Urgent: Account Verification Required",
        ml_probability=0.88,
        nlp_probability=0.84,
        risk_score=78.0,
        classification="High",
        rule_bonus=10.0,
        analysis_id="uuid-db-test-01",
    )
    state["url_analysis"] = [
        {
            "url": "https://secure-portal.com/login?token=dummy_sample_token_xyz",
            "scheme": "https",
            "hostname": "secure-portal.com",
            "port": 443,
            "path": "/login",
            "query": "token=dummy_sample_token_xyz",
            "is_ip_literal": False,
            "has_userinfo": False,
            "has_punycode": False,
            "has_unusual_port": False,
            "subdomain_depth": 0,
            "indicator_count": 1,
            "suspicious_indicators": ["Sensitive authentication/account keywords found in path or query: login"],
        }
    ]
    state["policy_guidance"] = {
        "risk_score": 78.0,
        "classification": "High",
        "score_range": "60.0 – 79.9",
        "triage_action": "Automated Quarantine / Security Analyst Review",
        "technical_handling": "Divert message to quarantine.",
        "recommended_controls": [
            "Quarantine message payload.",
            "Mandate secondary SOC analyst inspection.",
        ],
        "source_attribution": "CISA Phishing Guidance; NIST SP 800-61 Rev. 3",
        "is_project_triage_choice": True,
    }
    state["retrieved_evidence"] = [
        {
            "chunk_id": "attack_patterns_0_abc",
            "document_name": "attack_patterns.md",
            "heading": "2. MITRE ATT&CK Phishing Taxonomy",
            "source_attribution": "MITRE ATT&CK v20.0",
            "content": "Adversaries leverage spearphishing links to direct victims to credential harvesting portals.",
            "similarity": 0.94,
        }
    ]
    return state


def test_provider_initialization_without_keys(monkeypatch):
    """Verify that get_primary_llm and get_fallback_llm return None when API keys are unset."""
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", None)
    monkeypatch.setattr(settings, "GROQ_API_KEY", None)

    assert get_primary_llm() is None
    assert get_fallback_llm() is None

    # Dummy placeholder keys should also evaluate to None
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "your_google_api_key_here")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "your_groq_api_key_here")

    assert get_primary_llm() is None
    assert get_fallback_llm() is None


def test_input_minimization_and_url_sanitization(sample_investigation_state):
    """Verify prompt minimizes input and strips sensitive query tokens and raw body text."""
    prompt = build_minimized_investigation_prompt(sample_investigation_state)

    # 1. Sensitive tokens in URLs must be completely absent
    assert "dummy_sample_token_xyz" not in prompt
    assert "?token=" not in prompt

    # 2. Raw email body text must NOT be included in prompt
    assert "Please sign in at https://secure-portal.com" not in prompt

    # 3. Sanitized structural indicators and scores must be present
    assert "secure-portal.com" in prompt
    assert "78.0" in prompt
    assert "High" in prompt
    assert "attack_patterns_0_abc" in prompt


def test_primary_provider_success(sample_investigation_state):
    """Verify primary provider (Google) generates structured explanation successfully."""
    expected_explanation = InvestigationExplanation(
        summary="High-risk phishing attempt with credential harvesting indicators.",
        key_findings=["Sensitive login keywords in URL", "High Random Forest score (0.8800)"],
        risk_explanation="The message was scored at 78.0 due to strong phishing signals.",
        recommended_actions=["Automated quarantine", "Analyst header review"],
        limitations=["Offline URL parsing only"],
        evidence_references=["attack_patterns_0_abc"],
        provider_used="google",
        generation_status="completed",
    )

    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = expected_explanation
    mock_llm.with_structured_output.return_value = mock_structured

    result = generate_investigation_explanation(
        state=sample_investigation_state,
        primary_llm=mock_llm,
        fallback_llm=None,
    )

    assert result.provider_used == "google"
    assert result.generation_status == "completed"
    assert result.summary == expected_explanation.summary
    assert "attack_patterns_0_abc" in result.evidence_references


def test_fallback_provider_success_when_primary_fails(sample_investigation_state):
    """Verify fallback provider (Groq) triggers when primary provider raises an exception."""
    failing_primary = MagicMock()
    mock_failing_struct = MagicMock()
    mock_failing_struct.invoke.side_effect = RuntimeError("Google API RateLimit 429")
    failing_primary.with_structured_output.return_value = mock_failing_struct

    fallback_explanation = InvestigationExplanation(
        summary="Fallback generated: Suspicious email quarantined.",
        key_findings=["Non-standard link structure"],
        risk_explanation="Score 78.0 mandates quarantine under NIST SP 800-61.",
        recommended_actions=["Review message in admin quarantine"],
        limitations=["LLM fallback used"],
        evidence_references=["attack_patterns_0_abc"],
        provider_used="groq",
        generation_status="fallback",
    )

    mock_groq = MagicMock()
    mock_groq_struct = MagicMock()
    mock_groq_struct.invoke.return_value = fallback_explanation
    mock_groq.with_structured_output.return_value = mock_groq_struct

    result = generate_investigation_explanation(
        state=sample_investigation_state,
        primary_llm=failing_primary,
        fallback_llm=mock_groq,
    )

    assert result.provider_used == "groq"
    assert result.generation_status == "fallback"
    assert "Fallback generated" in result.summary


def test_both_providers_fail_graceful_degradation(sample_investigation_state):
    """Verify deterministic degraded explanation is generated when both providers fail."""
    failing_primary = MagicMock()
    failing_primary.with_structured_output.return_value.invoke.side_effect = RuntimeError("Google 500")

    failing_groq = MagicMock()
    failing_groq.with_structured_output.return_value.invoke.side_effect = TimeoutError("Groq Timeout")

    result = generate_investigation_explanation(
        state=sample_investigation_state,
        primary_llm=failing_primary,
        fallback_llm=failing_groq,
    )

    assert result.provider_used is None
    assert result.generation_status == "degraded"
    assert "Automated recommended operational action is: Automated Quarantine" in result.summary
    assert any("Generative LLM narrative unavailable" in lim for lim in result.limitations)
    assert "attack_patterns_0_abc" in result.evidence_references


def test_llm_generation_disabled_by_config(sample_investigation_state, monkeypatch):
    """Verify deterministic explanation is returned with status 'disabled' when LLM_ENABLED is False."""
    monkeypatch.setattr(settings, "LLM_ENABLED", False)

    result = generate_investigation_explanation(sample_investigation_state)

    assert result.provider_used is None
    assert result.generation_status == "disabled"
    assert "78.0" in result.summary


def test_deterministic_degraded_explanation_output_shape(sample_investigation_state):
    """Verify generate_deterministic_degraded_explanation populates all required fields."""
    degraded = generate_deterministic_degraded_explanation(sample_investigation_state, status="degraded")

    assert isinstance(degraded, InvestigationExplanation)
    assert len(degraded.summary) > 10
    assert len(degraded.key_findings) >= 3
    assert len(degraded.recommended_actions) >= 1
    assert degraded.provider_used is None
    assert degraded.generation_status == "degraded"

