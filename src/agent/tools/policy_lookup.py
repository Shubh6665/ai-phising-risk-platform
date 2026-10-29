"""Deterministic policy and triage guidance lookup tool.

Maps application composite risk scores to project triage actions, operational
handling tiers, and recommended technical controls aligned with the Phase 5
ensemble thresholds and the Phase 7 knowledge base.
"""

from typing import Any
from langchain_core.tools import tool

from src.agent.schemas import PolicyGuidanceResult, PolicyLookupInput


_POLICY_TIERS = {
    "Low": {
        "score_range": "0.0 – 39.9",
        "triage_action": "Standard Delivery / Allow",
        "technical_handling": (
            "Deliver message to recipient mailbox without modification or latency. "
            "Record analysis ID, model probabilities, and text hash in audit storage."
        ),
        "recommended_controls": [
            "Maintain standard email gateway hygiene (SPF, DKIM, DMARC alignment).",
            "Retain analysis telemetry for model performance and drift monitoring.",
        ],
        "source_attribution": "CISA Phishing Guidance; NIST SP 800-177 Rev. 1",
    },
    "Medium": {
        "score_range": "40.0 – 59.9",
        "triage_action": "Defensive Delivery / Warning Injected",
        "technical_handling": (
            "Deliver message to recipient mailbox with an informational warning banner prepended. "
            "Advise out-of-band verification and offer one-click user reporting."
        ),
        "recommended_controls": [
            "Prepend external sender / suspicious language warning banner.",
            "Advise recipient to independently verify sender identity via established out-of-band channels.",
            "Provide one-click phishing reporting feature (CISA Secure Our World).",
            "Enable click-time link protection and URL re-writing where supported.",
        ],
        "source_attribution": "CISA Secure Our World; NIST SP 800-61 Rev. 3",
    },
    "High": {
        "score_range": "60.0 – 79.9",
        "triage_action": "Automated Quarantine / Security Analyst Review",
        "technical_handling": (
            "Divert message from standard delivery stream into administrative quarantine repository. "
            "Notify recipient that message is under security review. Prioritize in SOC queue."
        ),
        "recommended_controls": [
            "Quarantine message payload to stop initial access at Phase One (CISA Phishing Guidance).",
            "Mandate secondary SOC analyst inspection of headers, sandboxed attachments, and extracted IOCs.",
            "Verify phishing-resistant MFA (FIDO2/WebAuthn) enrollment for targeted recipients.",
        ],
        "source_attribution": "CISA Phishing Guidance; NIST SP 800-61 Rev. 3; MITRE ATT&CK T1566",
    },
    "Critical": {
        "score_range": "80.0 – 100.0",
        "triage_action": "Immediate Block / Perimeter Containment / High-Priority Alert",
        "technical_handling": (
            "Immediately suppress and drop message payload across all mailboxes. "
            "Update edge blocklists with sender domains, originating IPs, and embedded URLs."
        ),
        "recommended_controls": [
            "Immediate perimeter domain, IP, and URL blocklist enforcement.",
            "Enterprise mailbox purge using message body hash and normalized subject.",
            "Terminate active user sessions and revoke OAuth tokens if links were clicked.",
            "Initiate incident containment under NIST SP 800-61 Rev. 3 Respond function.",
        ],
        "source_attribution": "NIST SP 800-61 Rev. 3; CISA Incident Response Plan Basics; MITRE ATT&CK T1566",
    },
}

_PROJECT_DISCLAIMER = (
    "PROJECT TRIAGE GUIDANCE — NOT AN ORGANIZATION-APPROVED SECURITY POLICY. "
    "The numerical risk thresholds (0.0–100.0) and tier classifications are technical design choices "
    "of this project's ensemble architecture (src/models/ensemble.py). They are not standards mandated "
    "by NIST or CISA. Deploying organizations must formally author and approve their own enterprise policies."
)


def lookup_policy_guidance(risk_score: float) -> PolicyGuidanceResult:
    """Retrieve operational triage action and defensive controls for a given risk score.

    Uses the project's Phase 5 ensemble thresholds:
    - Low: 0.0 – 39.9
    - Medium: 40.0 – 59.9
    - High: 60.0 – 79.9
    - Critical: 80.0 – 100.0
    """
    if not isinstance(risk_score, (int, float)):
        raise TypeError("risk_score must be a float or integer")
    if not (0.0 <= float(risk_score) <= 100.0):
        raise ValueError(f"risk_score ({risk_score}) must be between 0.0 and 100.0")

    score = float(risk_score)

    if score >= 80.0:
        tier = "Critical"
    elif score >= 60.0:
        tier = "High"
    elif score >= 40.0:
        tier = "Medium"
    else:
        tier = "Low"

    data = _POLICY_TIERS[tier]

    return PolicyGuidanceResult(
        risk_score=score,
        classification=tier,
        score_range=data["score_range"],
        triage_action=data["triage_action"],
        technical_handling=data["technical_handling"],
        recommended_controls=data["recommended_controls"],
        source_attribution=data["source_attribution"],
        is_project_triage_choice=True,
        disclaimer=_PROJECT_DISCLAIMER,
    )


@tool("policy_triage_lookup", args_schema=PolicyLookupInput)
def policy_triage_lookup_tool(risk_score: float) -> dict[str, Any]:
    """Retrieve operational triage actions and technical defensive controls for a risk score.

    Returns the technical handling actions (allow, warning, quarantine, block) and recommended
    defensive controls from NIST SP 800-61 and CISA guidelines for the given risk tier.
    """
    result = lookup_policy_guidance(risk_score)
    return result.model_dump()

