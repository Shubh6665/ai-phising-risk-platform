"""Database engine, session factory, and session dependency."""

from collections.abc import Generator
from typing import Any

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.db.models import Base


def normalize_database_url(url: str) -> str:
    """Normalize database connection URL for SQLAlchemy 2.x and PostgreSQL.

    - Replaces legacy postgres:// scheme with postgresql://
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def create_db_engine(url: str, **kwargs: Any) -> Engine:
    """Create a new SQLAlchemy engine with safe production defaults.

    Uses pool_pre_ping=True by default to guard against dropped connections.
    """
    normalized_url = normalize_database_url(url)
    engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}
    engine_kwargs.update(kwargs)
    return create_engine(normalized_url, **engine_kwargs)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a thread-safe session factory bound to the given engine."""
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def init_db(engine: Engine) -> None:
    """Idempotently create tables that do not already exist.

    Never drops or resets existing tables or data.
    """
    Base.metadata.create_all(bind=engine)


# Global lazy session factory for standalone/CLI usage when configured
_lazy_engine: Engine | None = None
_lazy_session_factory: sessionmaker[Session] | None = None


def get_global_session_factory() -> sessionmaker[Session]:
    """Retrieve or lazily initialize the global session factory from settings.

    Explicitly raises RuntimeError if DATABASE_URL is not configured.
    Does NOT silently fall back to SQLite in application runtime.
    """
    global _lazy_engine, _lazy_session_factory
    if _lazy_session_factory is None:
        if not settings.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not configured. Database persistence requires a configured database."
            )
        _lazy_engine = create_db_engine(settings.DATABASE_URL)
        _lazy_session_factory = create_session_factory(_lazy_engine)
    return _lazy_session_factory


def get_db(request: Request) -> Generator[Session, None, None]:
    """Request-scoped SQLAlchemy session generator for FastAPI dependency injection.

    Uses the session factory attached to app.state during lifespan startup.
    Falls back to the lazily initialized global factory if app.state is unavailable.
    """
    session_factory = getattr(request.app.state, "db_session_factory", None)
    if session_factory is None:
        session_factory = get_global_session_factory()

    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()
