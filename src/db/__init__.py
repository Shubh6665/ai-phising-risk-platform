"""Database package exposing models, session utilities, and repositories."""

from src.db.models import Base, AnalysisResult
from src.db.session import (
    create_db_engine,
    create_session_factory,
    init_db,
    get_db,
    normalize_database_url,
)
from src.db.repository import (
    AnalysisRepository,
    DatabasePersistenceError,
    hash_email_text,
)

__all__ = [
    "Base",
    "AnalysisResult",
    "create_db_engine",
    "create_session_factory",
    "init_db",
    "get_db",
    "normalize_database_url",
    "AnalysisRepository",
    "DatabasePersistenceError",
    "hash_email_text",
]

