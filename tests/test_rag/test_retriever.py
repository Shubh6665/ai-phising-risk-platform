"""Unit tests for indexing and retrieval using isolated test doubles."""

from pathlib import Path
import pytest

from src.rag.chunker import MarkdownChunker
from src.rag.embeddings import DummyEmbedder
from src.rag.indexer import index_knowledge_base
from src.rag.retriever import search_knowledge_base


@pytest.fixture
def dummy_embedder():
    return DummyEmbedder(dimension=64)


@pytest.fixture
def mock_kb_dir(tmp_path):
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()

    (kb_dir / "phishing_indicators.md").write_text(
        "# Phishing Indicators\n\n"
        "> **Sources**: NIST, CISA\n\n"
        "## 1. Domain Typosquatting\n\n"
        "Attackers register look-alike domains to deceive users.\n\n"
        "## 2. Urgency Cues\n\n"
        "Emails requesting immediate password reset or account verification.",
        encoding="utf-8",
    )

    (kb_dir / "security_policies.md").write_text(
        "# Internal Security Policies\n\n"
        "> [!IMPORTANT]\n> MOCK POLICY DOCUMENT\n\n"
        "## POL-SEC-101: Triage Actions\n\n"
        "Low risk emails are delivered normally. Critical risk emails are blocked.",
        encoding="utf-8",
    )
    return kb_dir


@pytest.fixture
def chroma_persist_dir(tmp_path):
    return tmp_path / "chroma_test_db"


def test_dummy_embedder_dimension_and_consistency(dummy_embedder):
    texts = ["Test query", "Another query", "Test query"]
    embs = dummy_embedder.encode(texts)
    assert len(embs) == 3
    assert len(embs[0]) == 64
    assert len(embs[1]) == 64
    # Deterministic equality for identical text
    assert embs[0] == embs[2]


def test_idempotent_indexing(mock_kb_dir, chroma_persist_dir, dummy_embedder):
    """Indexing twice with the same documents must not duplicate chunks."""
    col_name = "test_collection"

    # First run
    stats1 = index_knowledge_base(
        kb_dir=mock_kb_dir,
        persist_dir=chroma_persist_dir,
        collection_name=col_name,
        embedder=dummy_embedder,
    )
    assert stats1["document_count"] == 2
    assert stats1["chunk_count"] > 0
    first_count = stats1["total_collection_count"]
    assert first_count == stats1["chunk_count"]

    # Second run (must be idempotent)
    stats2 = index_knowledge_base(
        kb_dir=mock_kb_dir,
        persist_dir=chroma_persist_dir,
        collection_name=col_name,
        embedder=dummy_embedder,
    )
    assert stats2["document_count"] == 2
    assert stats2["chunk_count"] == stats1["chunk_count"]
    assert stats2["total_collection_count"] == first_count


def test_retriever_query_validation(chroma_persist_dir):
    with pytest.raises(ValueError, match="non-empty string"):
        search_knowledge_base("", persist_dir=chroma_persist_dir, collection_name="test_col")

    with pytest.raises(ValueError, match="non-empty string"):
        search_knowledge_base("   ", persist_dir=chroma_persist_dir, collection_name="test_col")

    with pytest.raises(ValueError, match="positive integer"):
        search_knowledge_base("valid query", top_k=0, persist_dir=chroma_persist_dir, collection_name="test_col")

    with pytest.raises(ValueError, match="positive integer"):
        search_knowledge_base("valid query", top_k=-5, persist_dir=chroma_persist_dir, collection_name="test_col")


def test_retriever_empty_collection(chroma_persist_dir, dummy_embedder):
    hits = search_knowledge_base(
        query="credential harvesting",
        top_k=3,
        persist_dir=chroma_persist_dir,
        collection_name="empty_test_col",
        embedder=dummy_embedder,
    )
    assert hits == []


def test_retriever_top_k_and_source_attribution(mock_kb_dir, chroma_persist_dir, dummy_embedder):
    col_name = "search_test_col"
    index_knowledge_base(
        kb_dir=mock_kb_dir,
        persist_dir=chroma_persist_dir,
        collection_name=col_name,
        embedder=dummy_embedder,
    )

    hits = search_knowledge_base(
        query="urgent account verification",
        top_k=2,
        persist_dir=chroma_persist_dir,
        collection_name=col_name,
        embedder=dummy_embedder,
    )

    assert len(hits) == 2
    for hit in hits:
        assert "id" in hit
        assert "content" in hit
        assert len(hit["content"]) > 0
        assert "distance" in hit
        assert "similarity" in hit
        assert "source_path" in hit
        assert "document_name" in hit
        assert "heading" in hit
        assert "document_type" in hit
        assert isinstance(hit["is_mock"], bool)
        assert "source_attribution" in hit

