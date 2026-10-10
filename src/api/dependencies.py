"""Dependency injection for the API."""

from fastapi import Request

def get_classical_model(request: Request):
    """Retrieve the loaded Random Forest model from app state."""
    return request.app.state.classical_model

def get_nlp_model(request: Request):
    """Retrieve the loaded DistilBERT model from app state."""
    return request.app.state.nlp_model

def get_nlp_tokenizer(request: Request):
    """Retrieve the DistilBERT tokenizer from app state."""
    return request.app.state.nlp_tokenizer
