"""Unit tests for the database persistence layer using isolated SQLite in-memory."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.db.models import Base, AnalysisResult
from src.db.repository import AnalysisRepository, DatabasePersistenceError, hash_email_text
from src.db.session import create_session_factory, normalize_database_url


@pytest.fixture
def sqlite_engine():
    """Create an isolated, in-memory SQLite engine for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def session_factory(sqlite_engine):
    return create_session_factory(sqlite_engine)


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    yield session
    session.close()


def test_url_normalization():
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql://user:pass@host/db"
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql://user:pass@host/db"
    assert normalize_database_url("sqlite:///:memory:") == "sqlite:///:memory:"


def test_orm_table_and_model_creation(sqlite_engine):
    """Verify table creation, column types, and schema definition."""
    assert "analysis_results" in Base.metadata.tables
    table = Base.metadata.tables["analysis_results"]

    expected_cols = {
        "id",
        "request_id",
        "email_hash",
        "ml_probability",
        "nlp_probability",
        "rule_bonus",
        "rule_signals",
        "risk_score",
        "classification",
        "created_at",
    }
    assert set(table.columns.keys()) == expected_cols

    # Ensure raw text fields are NOT part of the schema
    assert "email_text" not in table.columns
    assert "email_subject" not in table.columns
    assert "body" not in table.columns
    assert "subject" not in table.columns


def test_session_lifecycle_and_cleanup(session_factory):
    """Verify session creation, transaction handling, and clean closure."""
    session = session_factory()
    res = session.execute(select(1)).scalar()
    assert res == 1
    session.close()
    assert session.get_transaction() is None


def test_successful_save_and_retrieval(db_session):
    """Verify save_analysis_result persists correct values and get_by_id retrieves them."""
    repo = AnalysisRepository(db_session)

    req_id = "req-test-uuid-001"
    raw_text = "Urgent: Your account has been compromised. Log in now!"
    email_hash = hash_email_text(raw_text)

    saved = repo.save_analysis_result(
        request_id=req_id,
        email_hash=email_hash,
        ml_probability=0.82,
        nlp_probability=0.88,
        rule_bonus=10.0,
        rule_signals={"has_suspicious_url": False, "urgency_language": True},
        risk_score=78.0,
        classification="High",
    )

    assert isinstance(saved.id, uuid.UUID)
    assert saved.request_id == req_id
    assert saved.email_hash == email_hash
    assert saved.ml_probability == 0.82
    assert saved.nlp_probability == 0.88
    assert saved.rule_bonus == 10.0
    assert saved.rule_signals == {"has_suspicious_url": False, "urgency_language": True}
    assert saved.risk_score == 78.0
    assert saved.classification == "High"
    assert isinstance(saved.created_at, datetime)

    # Retrieve by UUID
    retrieved = repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.request_id == req_id
    assert retrieved.email_hash == email_hash
    assert retrieved.risk_score == 78.0

    # Retrieve by string ID
    retrieved_by_str = repo.get_by_id(str(saved.id))
    assert retrieved_by_str is not None
    assert retrieved_by_str.id == saved.id

    # Retrieve invalid ID returns None
    assert repo.get_by_id("non-existent-uuid") is None
    assert repo.get_by_id(uuid.uuid4()) is None


def test_transaction_rollback_on_failure():
    """Verify that a database write failure rolls back the session and raises DatabasePersistenceError."""
    failing_session = MagicMock(spec=Session)
    failing_session.commit.side_effect = RuntimeError("Database write disk error")

    repo = AnalysisRepository(failing_session)

    with pytest.raises(DatabasePersistenceError) as exc_info:
        repo.save_analysis_result(
            request_id="req-fail-001",
            email_hash="hash001",
            ml_probability=0.5,
            nlp_probability=0.5,
            rule_bonus=0.0,
            rule_signals=None,
            risk_score=40.0,
            classification="Medium",
        )

    assert "Failed to persist analysis result" in str(exc_info.value)
    failing_session.rollback.assert_called_once()


def test_email_hashing_and_privacy():
    """Verify SHA-256 email hashing is deterministic, handles whitespace, and stores no raw text."""
    text1 = "Urgent: Please reset your password.\n\nThank you."
    text2 = "  Urgent:   Please reset your password. \n\nThank you.  "
    text3 = "Completely different text."

    hash1 = hash_email_text(text1)
    hash2 = hash_email_text(text2)
    hash3 = hash_email_text(text3)

    assert len(hash1) == 64
    # text1 and text2 normalize to the same content
    assert hash1 == hash2
    # different content yields a different hash
    assert hash1 != hash3

    # Verify model class has no raw content attributes
    model_attrs = [a for a in dir(AnalysisResult) if not a.startswith("_")]
    assert "email_text" not in model_attrs
    assert "subject" not in model_attrs
    assert "body" not in model_attrs

