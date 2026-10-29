"""Dependency injection for the API."""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.repository import AnalysisRepository


def get_classical_model(request: Request):
    """Retrieve the loaded Random Forest model from app state."""
    return request.app.state.classical_model


def get_nlp_model(request: Request):
    """Retrieve the loaded DistilBERT model from app state."""
    return request.app.state.nlp_model


def get_nlp_tokenizer(request: Request):
    """Retrieve the DistilBERT tokenizer from app state."""
    return request.app.state.nlp_tokenizer


def get_analysis_repository(db: Session = Depends(get_db)) -> AnalysisRepository:
    """Retrieve request-scoped AnalysisRepository bound to active database session."""
    return AnalysisRepository(db)
