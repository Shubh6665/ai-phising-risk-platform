"""Dependency injection for the API."""

from typing import Any, Callable
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.config import settings
from src.db.session import get_db
from src.db.repository import AnalysisRepository
from src.rag.embeddings import Embedder
from src.rag.retriever import search_knowledge_base


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


def get_rag_embedder(request: Request) -> Embedder | None:
    """Retrieve the pre-initialized RAG embedder from app state."""
    return getattr(request.app.state, "rag_embedder", None)


def get_rag_retriever(
    embedder: Embedder | None = Depends(get_rag_embedder),
) -> Callable[[str, int], list[dict[str, Any]]] | None:
    """Factory dependency providing a configured knowledge-base retriever callable."""
    if not settings.RAG_ENABLED or embedder is None:
        return None

    def _retriever(query: str, top_k: int = settings.RAG_TOP_K) -> list[dict[str, Any]]:
        return search_knowledge_base(
            query=query,
            top_k=top_k,
            persist_dir=settings.CHROMA_PERSIST_DIR,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedder=embedder,
        )

    return _retriever
