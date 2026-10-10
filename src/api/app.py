"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
import structlog

from src.api.routes.health import router as health_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("application_startup")
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Phishing Risk Platform",
        description="Analyses email text using a Random Forest + DistilBERT ensemble and returns a deterministic risk score.",
        version="0.1.0",
        lifespan=lifespan,
        redirect_slashes=False,
    )
    app.include_router(health_router, tags=["Health"])
    return app
