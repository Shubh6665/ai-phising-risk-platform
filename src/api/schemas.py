"""Pydantic v2 request and response schemas."""

from pydantic import BaseModel, Field, field_validator, ConfigDict


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


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., description="UUID identifying this API request.")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Ensemble risk score 0–100.")
    classification: str = Field(..., description="Risk tier: Low / Medium / High / Critical.")
    ml_probability: float = Field(..., ge=0.0, le=1.0, description="Random Forest P(phishing).")
    nlp_probability: float = Field(..., ge=0.0, le=1.0, description="DistilBERT P(phishing).")
    rule_bonus: float = Field(..., ge=0.0, description="Deterministic rule contribution.")
    analysis_id: str | None = Field(default=None, description="Persisted analysis record UUID.")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str | None = Field(default=None, description="Request ID if available.")
    error: str = Field(..., description="Short error type label.")
    detail: str = Field(..., description="Human-readable description.")
