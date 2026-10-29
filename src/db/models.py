"""SQLAlchemy ORM models for database persistence."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, String, JSON, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy models."""
    pass


class AnalysisResult(Base):
    """Persisted email risk analysis result.

    Privacy rules:
    - Does NOT store raw email body, subject, or tokens.
    - Stores a SHA-256 hash of the normalized email text for correlation/audit.
    """
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique primary key UUID for the analysis record.",
    )
    request_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="API Request ID for distributed tracing and request correlation.",
    )
    email_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="SHA-256 hash of the normalized email content (no raw text stored).",
    )
    ml_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Random Forest phishing probability (0.0 to 1.0).",
    )
    nlp_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="DistilBERT phishing probability (0.0 to 1.0).",
    )
    rule_bonus: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Deterministic rule bonus added to the base score.",
    )
    rule_signals: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        doc="JSON object containing extracted heuristic rule signals.",
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Final composite application risk score (0.0 to 100.0).",
    )
    classification: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Risk tier: Low, Medium, High, or Critical.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="UTC timestamp when the analysis was performed and persisted.",
    )

