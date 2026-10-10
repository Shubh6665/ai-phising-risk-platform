"""FastAPI application factory.

Design decisions:
- create_app() factory function instead of a module-level `app` instance.
  This makes the app trivially testable: each test can call create_app()
  independently, and we can pass in different settings/state if needed.

- lifespan() context manager (not the deprecated @app.on_event hooks).
  FastAPI 0.93+ recommends lifespan because it makes startup/shutdown a
  single coherent block. In later sub-steps we'll load ML models here.

- Routers registered with api_router prefix keeps versioning clean.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

import structlog

from src.api.routes.health import router as health_router
from src.api.schemas import ErrorResponse

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: runs startup logic before yield, shutdown after.

    Sub-step A–E: nothing to load yet — that comes in sub-step F when we wire
    in the ML models.  The stub is here so tests already exercise the correct
    lifespan path and we never have to restructure later.
    """
    logger.info("application_startup", environment="api")
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns a fresh FastAPI instance every time it is called.  This is
    intentional: the test suite calls this once per test session (via a
    fixture) and the production server calls it once at process start.
    """
    app = FastAPI(
        title="AI Phishing Risk Platform",
        description=(
            "Analyses email text using a Random Forest + DistilBERT ensemble "
            "and returns a deterministic risk score."
        ),
        version="0.1.0",
        lifespan=lifespan,
        # Disable automatic redirect for trailing slashes — avoids silent 307s
        # that can confuse clients and hide route mismatches in tests.
        redirect_slashes=False,
    )

    # Register routers
    app.include_router(health_router, tags=["Health"])

    # Global exception handlers are added in later sub-steps (middleware phase).
    # For now, FastAPI's own 422 validation error responses are sufficient.

    return app
