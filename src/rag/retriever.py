"""Semantic retrieval engine for knowledge base querying."""

from pathlib import Path
from typing import Any

from src.config import settings
from src.rag.embeddings import Embedder, SentenceTransformerEmbedder
from src.rag.indexer import get_chroma_client, get_or_create_collection


def search_knowledge_base(
    query: str,
    top_k: int = 3,
    persist_dir: str | Path | None = None,
    collection_name: str | None = None,
    embedder: Embedder | None = None,
) -> list[dict[str, Any]]:
    """Execute semantic similarity search over the persistent knowledge base.

    Returns structured chunk matches with distance, content, and metadata.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")

    collection = get_or_create_collection(persist_dir, collection_name)
    total_docs = collection.count()
    if total_docs == 0:
        return []

    if embedder is None:
        embedder = SentenceTransformerEmbedder(settings.RAG_EMBEDDING_MODEL)

    query_embeddings = embedder.encode([query])
    query_vector = query_embeddings[0]

    n_results = min(top_k, total_docs)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict[str, Any]] = []
    if not results or not results.get("ids") or not results["ids"][0]:
        return hits

    ids = results["ids"][0]
    docs = results["documents"][0] if results.get("documents") else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else []
    distances = results["distances"][0] if results.get("distances") else []

    for idx, chunk_id in enumerate(ids):
        doc_text = docs[idx] if idx < len(docs) else ""
        meta = metadatas[idx] if idx < len(metadatas) else {}
        dist = float(distances[idx]) if idx < len(distances) else 0.0

        # Cosine distance bounded [0, 2]; similarity = 1 - (dist / 2) or 1 / (1 + dist)
        similarity = max(0.0, 1.0 - (dist / 2.0))

        hits.append(
            {
                "id": chunk_id,
                "content": doc_text,
                "distance": dist,
                "similarity": similarity,
                "metadata": meta,
                "source_path": meta.get("source_path"),
                "document_name": meta.get("document_name"),
                "document_title": meta.get("document_title"),
                "document_type": meta.get("document_type"),
                "heading": meta.get("heading"),
                "is_mock": meta.get("is_mock", False),
                "source_attribution": meta.get("source_attribution"),
            }
        )

    return hits

