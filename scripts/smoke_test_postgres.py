"""Smoke test verifying schema creation, write, read, and cleanup against live PostgreSQL."""

import sys
import uuid
from sqlalchemy import select, text

from src.config import settings
from src.db.models import AnalysisResult
from src.db.repository import AnalysisRepository, hash_email_text
from src.db.session import create_db_engine, create_session_factory, init_db


def run_postgres_smoke_test() -> bool:
    print("[1/6] Checking DATABASE_URL configuration...")
    if not settings.DATABASE_URL:
        print("ERROR: DATABASE_URL is not set.")
        return False

    print("[2/6] Connecting to live PostgreSQL database...")
    try:
        engine = create_db_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print("  -> PostgreSQL connection established successfully.")
    except Exception as exc:
        print(f"ERROR: Live PostgreSQL connectivity failed: {type(exc).__name__}: {exc}")
        return False

    print("[3/6] Ensuring tables exist via init_db...")
    try:
        init_db(engine)
        print("  -> Schema initialized successfully.")
    except Exception as exc:
        print(f"ERROR: Schema initialization failed: {type(exc).__name__}: {exc}")
        return False

    session_factory = create_session_factory(engine)
    session = session_factory()

    smoke_request_id = f"smoke-test-neon-{uuid.uuid4()}"
    synthetic_text = "Synthetic smoke test content for live Neon DB verification."
    email_hash = hash_email_text(synthetic_text)
    record_id: uuid.UUID | None = None

    try:
        print("[4/6] Persisting synthetic test record...")
        repo = AnalysisRepository(session)
        record = repo.save_analysis_result(
            request_id=smoke_request_id,
            email_hash=email_hash,
            ml_probability=0.75,
            nlp_probability=0.80,
            rule_bonus=5.0,
            rule_signals={"synthetic_smoke_signal": True},
            risk_score=67.0,
            classification="Medium",
        )
        record_id = record.id
        print(f"  -> Record saved with ID: {record_id}")

        print("[5/6] Verifying record retrieval and fields...")
        retrieved = repo.get_by_id(record_id)
        if retrieved is None:
            print("ERROR: Failed to retrieve saved record by ID.")
            return False

        assert retrieved.request_id == smoke_request_id
        assert retrieved.email_hash == email_hash
        assert retrieved.risk_score == 67.0
        assert retrieved.classification == "Medium"
        assert retrieved.rule_signals == {"synthetic_smoke_signal": True}
        print("  -> Record fields verified successfully.")

        print("[6/6] Cleaning up synthetic test record...")
        session.delete(retrieved)
        session.commit()

        # Confirm cleanup
        verified_gone = repo.get_by_id(record_id)
        if verified_gone is not None:
            print("ERROR: Test record was not removed cleanly.")
            return False
        print("  -> Synthetic test record cleaned up safely.")

    except Exception as exc:
        session.rollback()
        print(f"ERROR: Smoke test execution failed: {type(exc).__name__}: {exc}")
        return False
    finally:
        session.close()
        engine.dispose()

    print("PostgreSQL smoke test PASSED.")
    return True


if __name__ == "__main__":
    success = run_postgres_smoke_test()
    sys.exit(0 if success else 1)
