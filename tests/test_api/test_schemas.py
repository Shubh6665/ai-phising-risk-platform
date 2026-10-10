"""Tests for Pydantic v2 request and response schemas.

These tests do NOT hit HTTP — they call Pydantic models directly.
This is important because schema validation logic should be independently
testable without needing a running server.

Concepts tested:
  - AnalyzeRequest: required fields, min_length, whitespace validator
  - AnalyzeResponse: field constraints (ge/le for probabilities/score)
  - ErrorResponse: minimal required fields
"""

import pytest
from pydantic import ValidationError

from src.api.schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse


class TestAnalyzeRequest:
    """AnalyzeRequest is the POST /api/v1/analyze body schema."""

    def test_valid_text_only(self):
        req = AnalyzeRequest(text="Please click here to verify your account.")
        assert req.text == "Please click here to verify your account."
        assert req.subject is None

    def test_valid_text_and_subject(self):
        req = AnalyzeRequest(text="Click here.", subject="Urgent: verify now")
        assert req.subject == "Urgent: verify now"

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(text="")
        # Pydantic error should mention the field
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) for e in errors)

    def test_whitespace_only_text_raises(self):
        """Our custom field_validator must reject whitespace-only strings."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(text="   \n\t  ")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) for e in errors)

    def test_missing_text_raises(self):
        with pytest.raises(ValidationError):
            AnalyzeRequest()  # type: ignore[call-arg]

    def test_subject_accepts_none_explicitly(self):
        req = AnalyzeRequest(text="Hello", subject=None)
        assert req.subject is None


class TestAnalyzeResponse:
    """AnalyzeResponse is what POST /api/v1/analyze returns."""

    def _valid_kwargs(self):
        return dict(
            request_id="abc-123",
            risk_score=72.5,
            classification="High",
            ml_probability=0.8,
            nlp_probability=0.85,
            rule_bonus=10.0,
        )

    def test_valid_response_constructs(self):
        resp = AnalyzeResponse(**self._valid_kwargs())
        assert resp.risk_score == 72.5
        assert resp.classification == "High"

    def test_risk_score_below_zero_raises(self):
        kwargs = {**self._valid_kwargs(), "risk_score": -1.0}
        with pytest.raises(ValidationError):
            AnalyzeResponse(**kwargs)

    def test_risk_score_above_100_raises(self):
        kwargs = {**self._valid_kwargs(), "risk_score": 100.1}
        with pytest.raises(ValidationError):
            AnalyzeResponse(**kwargs)

    def test_ml_probability_above_1_raises(self):
        kwargs = {**self._valid_kwargs(), "ml_probability": 1.01}
        with pytest.raises(ValidationError):
            AnalyzeResponse(**kwargs)

    def test_nlp_probability_below_0_raises(self):
        kwargs = {**self._valid_kwargs(), "nlp_probability": -0.01}
        with pytest.raises(ValidationError):
            AnalyzeResponse(**kwargs)

    def test_analysis_id_defaults_to_none(self):
        resp = AnalyzeResponse(**self._valid_kwargs())
        assert resp.analysis_id is None

    def test_analysis_id_can_be_set(self):
        resp = AnalyzeResponse(**self._valid_kwargs(), analysis_id="uuid-xyz")
        assert resp.analysis_id == "uuid-xyz"


class TestErrorResponse:
    def test_valid_error_response(self):
        err = ErrorResponse(error="validation_error", detail="text is required")
        assert err.error == "validation_error"
        assert err.request_id is None  # default

    def test_with_request_id(self):
        err = ErrorResponse(
            request_id="req-999", error="internal_error", detail="unexpected failure"
        )
        assert err.request_id == "req-999"
