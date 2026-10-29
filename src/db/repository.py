"""Persistence repository and email hashing utilities."""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
import structlog

from src.data.preprocessor import clean_text
from src.db.models import AnalysisResult

logger = structlog.get_logger(__name__)


def hash_email_text(text: str) -> str:
    """Compute SHA-256 hash of normalized email text for audit correlation.

    Normalized using preprocessor clean_text to ensure consistent hashing
    while never storing raw email body or subject.
    """
    normalized = clean_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DatabasePersistenceError(Exception):
    """Raised when persisting an analysis result fails."""
    pass


class AnalysisRepository:
    """Repository handling persistence and queries for AnalysisResult records."""

    def __init__(self, session: Session):
        self.session = session

    def save_analysis_result(
        self,
        *,
        request_id: str,
        email_hash: str,
        ml_probability: float,
        nlp_probability: float,
        rule_bonus: float,
        rule_signals: dict[str, Any] | None,
        risk_score: float,
        classification: str,
    ) -> AnalysisResult:
        """Persist analysis result in a single transaction with rollback on failure."""
        record = AnalysisResult(
            id=uuid.uuid4(),
            request_id=request_id,
            email_hash=email_hash,
            ml_probability=ml_probability,
            nlp_probability=nlp_probability,
            rule_bonus=rule_bonus,
            rule_signals=rule_signals,
            risk_score=risk_score,
            classification=classification,
            created_at=datetime.now(timezone.utc),
        )

        try:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return record
        except Exception as exc:
            self.session.rollback()
            # Log sanitized metadata only: no email content, no database credentials
            logger.error(
                "database_save_failed",
                error_type=type(exc).__name__,
                request_id=request_id,
            )
            raise DatabasePersistenceError("Failed to persist analysis result.") from exc

    def get_by_id(self, analysis_id: uuid.UUID | str) -> AnalysisResult | None:
        """Retrieve an AnalysisResult record by ID."""
        if isinstance(analysis_id, str):
            try:
                analysis_id = uuid.UUID(analysis_id)
            except ValueError:
                return None
        return self.session.scalar(
            select(AnalysisResult).where(AnalysisResult.id == analysis_id)
        )

