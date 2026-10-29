"""Pydantic v2 request and response schemas."""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from src.agent.schemas import InvestigationExplanation, URLObservation


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str = Field(..., description="Always 'ok' while the process is alive.")
    version: str = Field(..., description="Application version string.")


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Email body text to analyse.")
    subject: str | None = Field(default=None, description="Optional email subject.")

    @field_validator("text")
    @classmethod
    def text_must_not_be_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must contain at least one non-whitespace character")
        return value


class SecurityEvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(..., description="Deterministic chunk identifier.")
    content: str = Field(..., description="Extracted knowledge-base guidance excerpt.")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score [0.0, 1.0].")
    document_name: str = Field(..., description="Source document file name.")
    document_title: str | None = Field(default=None, description="Document title.")
    heading: str | None = Field(default=None, description="Section heading hierarchy.")
    document_type: str = Field(..., description="Classification: source_backed_guidance, mock, etc.")
    source_attribution: str = Field(..., description="Official standard or issuing body attribution.")
    is_mock: bool = Field(default=False, description="Whether this evidence contains synthetic mock material.")


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., description="UUID identifying this API request.")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Ensemble risk score 0–100.")
    classification: str = Field(..., description="Risk tier: Low / Medium / High / Critical.")
    ml_probability: float = Field(..., ge=0.0, le=1.0, description="Random Forest P(phishing).")
    nlp_probability: float = Field(..., ge=0.0, le=1.0, description="DistilBERT P(phishing).")
    rule_bonus: float = Field(..., ge=0.0, description="Deterministic rule contribution.")
    analysis_id: str | None = Field(default=None, description="Persisted analysis record UUID.")
    evidence: list[SecurityEvidenceItem] = Field(
        default_factory=list,
        description="Retrieved security knowledge-base evidence relevant to this email.",
    )
    evidence_status: str = Field(
        default="retrieved",
        description="Evidence retrieval status: 'retrieved', 'empty', 'unavailable', or 'disabled'.",
    )
    requires_escalation: bool = Field(
        default=False,
        description="Whether deterministic triage rules mandate human analyst or containment escalation.",
    )
    escalation_reason: str | None = Field(
        default=None,
        description="Reason for deterministic escalation if required.",
    )
    url_analysis: list[URLObservation] = Field(
        default_factory=list,
        description="Offline lexical analysis of URLs found in the email body.",
    )
    explanation: InvestigationExplanation | None = Field(
        default=None,
        description="Structured investigation explanation, grounded findings, and defensive recommendations "
                    "(advisory only; platform does not execute containment actions).",
    )


class ErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str | None = Field(default=None, description="Request ID if available.")
    error: str = Field(..., description="Short error type label.")
    detail: str = Field(..., description="Human-readable description.")
