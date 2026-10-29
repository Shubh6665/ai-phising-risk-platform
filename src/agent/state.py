"""Typed state definition and deterministic escalation rules for the LangGraph agent."""

from typing import Any, Optional, TypedDict


class PhishingAnalysisState(TypedDict, total=False):
    """Working memory state passed through the LangGraph investigation workflow.

    The state maintains a strict boundary between:
    1. Pre-computed, immutable ML/NLP scoring and deterministic ensemble classification.
    2. Transient in-memory email content (never logged or persisted).
    3. Deterministic tool observations (URL structure, policy triage, knowledge search).
    4. Deterministic escalation flags (computed by formula, not LLM opinion).
    5. Future agent artifacts (grounded explanation & recommendations, Phase 8B).
    """

    # 1. Identifiers & In-Memory Email Data (Transient)
    request_id: str
    analysis_id: Optional[str]
    email_text: str
    email_subject: Optional[str]
    extracted_urls: list[str]

    # 2. Immutable Model & Ensemble Signals (Calculated in Phases 2–6)
    ml_probability: float
    nlp_probability: float
    risk_score: float
    classification: str
    rule_bonus: float
    extracted_features: dict[str, Any]

    # 3. Deterministic Tool Working Memory
    url_analysis: list[dict[str, Any]]
    policy_guidance: Optional[dict[str, Any]]
    retrieved_evidence: list[dict[str, Any]]
    evidence_already_retrieved: bool
    tool_outputs: list[dict[str, Any]]
    tool_errors: list[str]
    is_input_valid: bool

    # 4. Deterministic Escalation Governance
    requires_escalation: bool
    escalation_reason: Optional[str]

    # 5. LLM Generated Explanations (Phase 8C)
    explanation: Optional[str]
    recommendations: list[str]
    structured_explanation: Optional[dict[str, Any]]


def compute_deterministic_escalation(
    risk_score: float,
    ml_probability: float,
    nlp_probability: float,
) -> tuple[bool, Optional[str]]:
    """Determine whether an email requires mandatory human SOC analyst review or critical containment.

    Escalation is strictly governed by deterministic project rules, NOT LLM judgment:
    1. Critical Risk Tier (risk_score >= 80.0):
       Mandates immediate perimeter containment, mailbox purge, and high-priority SOC alert
       under NIST SP 800-61 Rev. 3 and CISA incident response guidance.
    2. High-Uncertainty Quarantine Tier (60.0 <= risk_score < 80.0):
       Places message in administrative quarantine, mandating secondary SOC analyst review.
    3. Statistical vs Deep Learning Model Divergence (abs(ml_probability - nlp_probability) > 0.30):
       Indicates contradictory signals between statistical features and transformer tokens.

    Low (< 40.0) and Medium (40.0 <= score < 60.0) tiers do not trigger operational escalation
    unless model divergence is detected.

    Returns:
        (requires_escalation, escalation_reason)
    """
    reasons: list[str] = []

    # Rule 1: Critical risk tier requires high-priority SOC containment alert
    if risk_score >= 80.0:
        reasons.append(
            f"Critical risk tier (score {risk_score:.1f} >= 80.0); "
            "mandates immediate perimeter containment, mailbox purge, and high-priority SOC alert."
        )
    # Rule 2: High risk triage band requires secondary SOC analyst review
    elif 60.0 <= risk_score < 80.0:
        reasons.append(
            f"High-uncertainty triage tier (score {risk_score:.1f} in 60.0–79.9); "
            "automated quarantine mandates secondary SOC analyst review."
        )

    # Rule 3: Significant model divergence indicating conflicting statistical signals
    prob_delta = abs(ml_probability - nlp_probability)
    if prob_delta > 0.30:
        reasons.append(
            f"Model disagreement: Classical ML ({ml_probability:.3f}) and Transformer NLP ({nlp_probability:.3f}) "
            f"diverge by {prob_delta:.3f} (> 0.30 threshold)."
        )

    if reasons:
        return True, " | ".join(reasons)
    return False, None


def create_initial_agent_state(
    request_id: str,
    email_text: str,
    ml_probability: float,
    nlp_probability: float,
    risk_score: float,
    classification: str,
    rule_bonus: float = 0.0,
    email_subject: Optional[str] = None,
    extracted_urls: Optional[list[str]] = None,
    extracted_features: Optional[dict[str, Any]] = None,
    analysis_id: Optional[str] = None,
    retrieved_evidence: Optional[list[dict[str, Any]]] = None,
) -> PhishingAnalysisState:
    """Construct an initial typed agent state populated with pre-computed signals."""
    requires_escalation, escalation_reason = compute_deterministic_escalation(
        risk_score=risk_score,
        ml_probability=ml_probability,
        nlp_probability=nlp_probability,
    )

    has_pre_retrieved = retrieved_evidence is not None

    return {
        "request_id": request_id,
        "analysis_id": analysis_id,
        "email_text": email_text,
        "email_subject": email_subject,
        "extracted_urls": list(extracted_urls) if extracted_urls else [],
        "ml_probability": ml_probability,
        "nlp_probability": nlp_probability,
        "risk_score": risk_score,
        "classification": classification,
        "rule_bonus": rule_bonus,
        "extracted_features": dict(extracted_features) if extracted_features else {},
        "url_analysis": [],
        "policy_guidance": None,
        "retrieved_evidence": list(retrieved_evidence) if retrieved_evidence else [],
        "evidence_already_retrieved": has_pre_retrieved,
        "tool_outputs": [],
        "tool_errors": [],
        "is_input_valid": True,
        "requires_escalation": requires_escalation,
        "escalation_reason": escalation_reason,
        "explanation": None,
        "recommendations": [],
        "structured_explanation": None,
    }

