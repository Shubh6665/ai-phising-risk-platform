"""FastAPI application factory."""

import os
import torch
import transformers
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
import structlog

from src.api.routes.health import router as health_router
from src.api.routes.analyze import router as analyze_router
from src.api.middleware import RequestIDAndLoggingMiddleware
from src.models.registry import load_model, DEFAULT_MODEL_PATH
from src.config import settings

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
        
    except Exception as e:
        logger.error("application_startup_failed", error=str(e))
        raise RuntimeError(f"Failed to load models during startup: {e}") from e
        
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
    
    # Add Middleware
    app.add_middleware(RequestIDAndLoggingMiddleware)
    
    # Register Routes
    app.include_router(health_router, tags=["Health"])
    app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])
    
    return app
