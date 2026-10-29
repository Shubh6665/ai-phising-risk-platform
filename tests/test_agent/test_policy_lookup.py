"""Tests for the deterministic policy and triage lookup tool."""

import pytest

from src.agent.tools.policy_lookup import (
    lookup_policy_guidance,
    policy_triage_lookup_tool,
)


def test_policy_lookup_low_tier():
    """Verify Low risk tier (0.0 to 39.9) returns Standard Delivery."""
    for score in [0.0, 15.5, 39.9]:
        res = lookup_policy_guidance(score)
        assert res.classification == "Low"
        assert res.score_range == "0.0 – 39.9"
        assert "Standard Delivery / Allow" in res.triage_action
        assert "NIST SP 800-177" in res.source_attribution
        assert res.is_project_triage_choice is True
        assert "NOT AN ORGANIZATION-APPROVED SECURITY POLICY" in res.disclaimer


def test_policy_lookup_medium_tier():
    """Verify Medium risk tier (40.0 to 59.9) returns Defensive Delivery."""
    for score in [40.0, 50.0, 59.9]:
        res = lookup_policy_guidance(score)
        assert res.classification == "Medium"
        assert res.score_range == "40.0 – 59.9"
        assert "Warning Injected" in res.triage_action
        assert any("out-of-band" in c.lower() for c in res.recommended_controls)
        assert "CISA Secure Our World" in res.source_attribution


def test_policy_lookup_high_tier():
    """Verify High risk tier (60.0 to 79.9) returns Automated Quarantine."""
    for score in [60.0, 70.0, 79.9]:
        res = lookup_policy_guidance(score)
        assert res.classification == "High"
        assert res.score_range == "60.0 – 79.9"
        assert "Automated Quarantine" in res.triage_action
        assert any("phishing-resistant mfa" in c.lower() for c in res.recommended_controls)
        assert "MITRE ATT&CK T1566" in res.source_attribution


def test_policy_lookup_critical_tier():
    """Verify Critical risk tier (80.0 to 100.0) returns Immediate Block."""
    for score in [80.0, 92.5, 100.0]:
        res = lookup_policy_guidance(score)
        assert res.classification == "Critical"
        assert res.score_range == "80.0 – 100.0"
        assert "Immediate Block" in res.triage_action
        assert any("blocklist" in c.lower() for c in res.recommended_controls)
        assert "NIST SP 800-61 Rev. 3" in res.source_attribution


def test_policy_lookup_boundary_and_invalid_inputs():
    """Verify out-of-range scores and invalid types raise appropriate exceptions."""
    with pytest.raises(ValueError):
        lookup_policy_guidance(-0.1)

    with pytest.raises(ValueError):
        lookup_policy_guidance(100.1)

    with pytest.raises(TypeError):
        lookup_policy_guidance("eighty")  # type: ignore


def test_policy_lookup_langchain_tool():
    """Verify LangChain tool wrapper returns expected dictionary."""
    raw = policy_triage_lookup_tool.invoke({"risk_score": 75.0})
    assert isinstance(raw, dict)
    assert raw["classification"] == "High"
    assert "Automated Quarantine" in raw["triage_action"]
    assert raw["is_project_triage_choice"] is True
    assert "NOT AN ORGANIZATION-APPROVED SECURITY POLICY" in raw["disclaimer"]

