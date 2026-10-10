"""Pydantic v2 request and response schemas for the Phishing Risk API.

Why Pydantic for schemas?
  FastAPI uses Pydantic models as the single source of truth for:
    1. Request validation  — FastAPI reads the model, auto-parses JSON, and
       returns a 422 if any field is missing or the wrong type.
    2. Response serialisation — FastAPI validates the return value against the
       response_model before sending it to the client.
    3. OpenAPI documentation — FastAPI generates /docs and /openapi.json
       automatically from these models.

  This means we define the contract once and get validation + docs for free.

Schema design principles used here:
  - Every field has a type annotation AND a Field() with a description.
    This makes the auto-generated /docs readable without extra work.
  - Immutable response models (model_config frozen=True) prevent accidental
    mutation after construction.
  - No Optional fields unless a value is genuinely absent in a real response.
"""

from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Returned by GET /health."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(..., description="Always 'ok' while the process is alive.")
    version: str = Field(..., description="Application version string.")


# ---------------------------------------------------------------------------
# Analysis request
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Body of POST /api/v1/analyze.

    Only `text` is required.  `subject` is optional because not all email
    sources expose the subject separately; the feature pipeline handles the
    None case.
    """

    text: str = Field(
        ...,
        min_length=1,
        description=(
            "The email body text to analyse.  Must be non-empty.  "
            "Do not include authentication headers or raw MIME."
        ),
    )
    subject: str | None = Field(
        default=None,
        description="Optional email subject line.",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must contain at least one non-whitespace character")
        return value


# ---------------------------------------------------------------------------
# Analysis response
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    """Returned by POST /api/v1/analyze.

    Field mapping to Phase 5 ensemble output:
      risk_score      — compute_risk_score() → RiskAssessment.risk_score
      classification  — RiskAssessment.classification  (Low/Medium/High/Critical)
      ml_probability  — Random Forest P(phishing)
      nlp_probability — DistilBERT P(phishing)
      rule_bonus      — RiskAssessment.rule_bonus  (deterministic rule contribution)
      analysis_id     — UUID stored in PostgreSQL (added in sub-step G)
      request_id      — Propagated from request middleware (added in sub-step F)
    """

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., description="UUID identifying this API request.")
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Ensemble risk score 0–100 (not a calibrated probability).",
    )
    classification: str = Field(
        ...,
        description="Risk tier: Low / Medium / High / Critical.",
    )
    ml_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Random Forest P(phishing), 0–1.",
    )
    nlp_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="DistilBERT P(phishing), 0–1.",
    )
    rule_bonus: float = Field(
        ...,
        ge=0.0,
        description="Deterministic rule contribution added to the base score.",
    )
    analysis_id: str | None = Field(
        default=None,
        description="UUID of the persisted analysis record (null before DB is wired).",
    )


# ---------------------------------------------------------------------------
# Error response
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Returned for 4xx/5xx errors."""

    model_config = ConfigDict(frozen=True)

    request_id: str | None = Field(
        default=None,
        description="Request ID if available.",
    )
    error: str = Field(..., description="Short error type label.")
    detail: str = Field(..., description="Human-readable description.")
