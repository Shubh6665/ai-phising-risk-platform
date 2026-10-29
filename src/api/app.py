"""FastAPI application factory."""

import os
import torch
import transformers
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
import structlog

from src.api.routes.health import router as health_router
from src.api.routes.analyze import router as analyze_router
from src.api.middleware import RequestIDAndLoggingMiddleware
from src.api.schemas import ErrorResponse
from src.models.registry import load_model, DEFAULT_MODEL_PATH
from src.config import settings
from src.db.session import create_db_engine, create_session_factory, init_db
from src.db.repository import DatabasePersistenceError
from src.rag.embeddings import SentenceTransformerEmbedder

logger = structlog.get_logger(__name__)

HF_REPOSITORY = "shubhsingh0700/phishing-risk-distilbert"
HF_REVISION = "0fa035f65ea98c94a33f24778c210695636efddd"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("application_startup")
    try:
        # 1. Load Classical ML Model (Random Forest)
        app.state.classical_model = load_model(DEFAULT_MODEL_PATH)
        logger.info("classical_model_loaded", path=str(DEFAULT_MODEL_PATH))
        
        # 2. Load DistilBERT (NLP) Model
        token = settings.HF_TOKEN
        if not token and os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
            from kaggle_secrets import UserSecretsClient
            token = UserSecretsClient().get_secret("HF_TOKEN")
            
        if not token:
            raise RuntimeError("HF_TOKEN is missing. Cannot load private DistilBERT model.")
            
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load Tokenizer
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            HF_REPOSITORY, revision=HF_REVISION, token=token, use_fast=True
        )
        tokenizer.truncation_side = "right"
        app.state.nlp_tokenizer = tokenizer
        
        # Load Model
        model = transformers.AutoModelForSequenceClassification.from_pretrained(
            HF_REPOSITORY, revision=HF_REVISION, token=token
        )
        model.to(device)
        model.eval()
        app.state.nlp_model = model
        
        logger.info(
            "nlp_model_loaded", 
            repository=HF_REPOSITORY, 
            revision=HF_REVISION,
            device=str(device)
        )

        # 3. Initialize Database Engine & Tables if configured
        if settings.DATABASE_URL:
            engine = create_db_engine(settings.DATABASE_URL)
            app.state.db_engine = engine
            app.state.db_session_factory = create_session_factory(engine)
            init_db(engine)
            logger.info("database_engine_initialized")
        else:
            app.state.db_engine = None
            app.state.db_session_factory = None
            logger.warning("database_url_not_configured")

        # 4. Initialize RAG Embedder if enabled and not already injected (e.g. by test doubles)
        if getattr(app.state, "rag_embedder", None) is None:
            if settings.RAG_ENABLED:
                try:
                    app.state.rag_embedder = SentenceTransformerEmbedder(settings.RAG_EMBEDDING_MODEL)
                    logger.info("rag_embedder_loaded", model=settings.RAG_EMBEDDING_MODEL)
                except Exception as e:
                    logger.warning("rag_embedder_load_failed", error=str(e))
                    app.state.rag_embedder = None
            else:
                app.state.rag_embedder = None
                logger.info("rag_retrieval_disabled_by_config")
        
    except Exception as e:
        logger.error("application_startup_failed", error=str(e))
        raise RuntimeError(f"Failed to initialize application startup: {e}") from e
        
    yield
    
    # Clean up database engine
    if getattr(app.state, "db_engine", None) is not None:
        app.state.db_engine.dispose()
        logger.info("database_engine_disposed")

    logger.info("application_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Phishing Risk Platform",
        description="Analyses email text using a Random Forest + DistilBERT ensemble and returns a deterministic risk score.",
        version="0.1.0",
        lifespan=lifespan,
        redirect_slashes=False,
    )
    
    # Add Middleware
    app.add_middleware(RequestIDAndLoggingMiddleware)

    # Register Exception Handlers
    @app.exception_handler(DatabasePersistenceError)
    async def database_persistence_exception_handler(
        request: Request, exc: DatabasePersistenceError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                request_id=request_id,
                error="database_error",
                detail="Failed to persist analysis result.",
            ).model_dump(),
        )
    
    # Register Routes
    app.include_router(health_router, tags=["Health"])
    app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])
    
    return app
