"""Deterministic security knowledge base search tool.

Wraps the Phase 7 ChromaDB semantic retriever in a typed agent tool interface.
Reuses SentenceTransformerEmbedder and the existing vector store collection.
"""

from typing import Any
from langchain_core.tools import tool

from src.agent.schemas import KnowledgeSearchChunk, KnowledgeSearchInput, KnowledgeSearchResult
from src.config import settings
from src.rag.embeddings import Embedder
from src.rag.retriever import search_knowledge_base


def search_security_knowledge(
    query: str,
    top_k: int = 3,
    embedder: Embedder | None = None,
) -> KnowledgeSearchResult:
    """Execute semantic retrieval over the security knowledge base and return typed results.

    Validates inputs, maps hits to KnowledgeSearchChunk models, and handles empty
    or failed retrievals explicitly without crashing.
    """
    if not isinstance(query, str) or not query.strip():
        return KnowledgeSearchResult(
            query=str(query),
            status="error",
            results_count=0,
            chunks=[],
            error_message="Query string must be non-empty and contain non-whitespace characters.",
        )

    clean_query = query.strip()
    k = max(1, min(10, int(top_k)))

    try:
        raw_hits = search_knowledge_base(
            query=clean_query,
            top_k=k,
            persist_dir=settings.CHROMA_PERSIST_DIR,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedder=embedder,
        )

        if not raw_hits:
            return KnowledgeSearchResult(
                query=clean_query,
                status="empty",
                results_count=0,
                chunks=[],
            )

        chunks: list[KnowledgeSearchChunk] = []
        for hit in raw_hits:
            sim = round(max(0.0, min(1.0, float(hit.get("similarity", 0.0)))), 4)
            chunks.append(
                KnowledgeSearchChunk(
                    chunk_id=hit["id"],
                    content=hit["content"],
                    similarity=sim,
                    document_name=hit.get("document_name") or "",
                    document_title=hit.get("document_title"),
                    heading=hit.get("heading"),
                    document_type=hit.get("document_type") or "source_backed_guidance",
                    source_attribution=hit.get("source_attribution") or "",
                    is_mock=bool(hit.get("is_mock", False)),
                )
            )

        return KnowledgeSearchResult(
            query=clean_query,
            status="retrieved",
            results_count=len(chunks),
            chunks=chunks,
        )

    except Exception as e:
        return KnowledgeSearchResult(
            query=clean_query,
            status="error",
            results_count=0,
            chunks=[],
            error_message=f"{type(e).__name__}: {str(e)}",
        )


@tool("knowledge_base_search", args_schema=KnowledgeSearchInput)
def knowledge_base_search_tool(query: str, top_k: int = 3) -> dict[str, Any]:
    """Retrieve authoritative threat patterns, phishing indicators, and incident response playbooks.

    Queries the curated security knowledge base grounded in NIST SP 800-61, CISA recommendations,
    APWG telemetry, and MITRE ATT&CK v20.0 techniques.
    """
    result = search_security_knowledge(query=query, top_k=top_k)
    return result.model_dump()

