"""Tests for the deterministic security knowledge base search tool."""

from unittest.mock import patch
import pytest

from src.agent.tools.knowledge_search import (
    search_security_knowledge,
    knowledge_base_search_tool,
)
from src.rag.embeddings import DummyEmbedder


def test_knowledge_search_successful_retrieval():
    """Verify successful semantic search transforms raw hits into typed chunks."""
    fake_hits = [
        {
            "id": "attack_patterns_1_abcd1234",
            "content": "Adversaries send spearphishing emails containing malicious attachments...",
            "distance": 0.2,
            "similarity": 0.9,
            "document_name": "attack_patterns.md",
            "document_title": "Attack Patterns",
            "heading": "2. MITRE ATT&CK Phishing Taxonomy",
            "document_type": "source_backed_guidance",
            "source_attribution": "MITRE ATT&CK v20.0 (October 13, 2026)",
            "is_mock": False,
        }
    ]

    with patch("src.agent.tools.knowledge_search.search_knowledge_base", return_value=fake_hits) as mock_search:
        dummy_embedder = DummyEmbedder(dimension=384)
        res = search_security_knowledge(
            query="spearphishing attachment",
            top_k=2,
            embedder=dummy_embedder,
        )

        assert res.status == "retrieved"
        assert res.results_count == 1
        assert len(res.chunks) == 1
        chunk = res.chunks[0]
        assert chunk.chunk_id == "attack_patterns_1_abcd1234"
        assert chunk.similarity == 0.9
        assert chunk.document_name == "attack_patterns.md"
        assert chunk.document_type == "source_backed_guidance"
        assert chunk.source_attribution == "MITRE ATT&CK v20.0 (October 13, 2026)"
        assert chunk.is_mock is False

        mock_search.assert_called_once()


def test_knowledge_search_empty_query_validation():
    """Verify empty or whitespace-only queries return error status without crashing."""
    res_empty = search_security_knowledge("")
    assert res_empty.status == "error"
    assert "Query string must be non-empty" in res_empty.error_message

    res_ws = search_security_knowledge("   ")
    assert res_ws.status == "error"


def test_knowledge_search_empty_index_handling():
    """Verify that an empty vector store gracefully returns empty status."""
    with patch("src.agent.tools.knowledge_search.search_knowledge_base", return_value=[]):
        res = search_security_knowledge("credential harvesting")
        assert res.status == "empty"
        assert res.results_count == 0
        assert res.chunks == []
        assert res.error_message is None


def test_knowledge_search_exception_graceful_degradation():
    """Verify that vector store or embedding exceptions return error status."""
    with patch(
        "src.agent.tools.knowledge_search.search_knowledge_base",
        side_effect=RuntimeError("ChromaDB connection timeout"),
    ):
        res = search_security_knowledge("phishing indicators")
        assert res.status == "error"
        assert res.results_count == 0
        assert "RuntimeError" in res.error_message


def test_knowledge_search_langchain_tool():
    """Verify LangChain tool wrapper returns expected dictionary."""
    fake_hits = [
        {
            "id": "indicators_0_123456",
            "content": "Urgency cues induce cognitive overload in recipients...",
            "distance": 0.1,
            "similarity": 0.95,
            "document_name": "phishing_indicators.md",
            "document_title": "Phishing Indicators",
            "heading": "1. Social Engineering Indicators",
            "document_type": "source_backed_guidance",
            "source_attribution": "CISA Secure Our World",
            "is_mock": False,
        }
    ]

    with patch("src.agent.tools.knowledge_search.search_knowledge_base", return_value=fake_hits):
        raw = knowledge_base_search_tool.invoke({"query": "urgency indicators", "top_k": 1})
        assert isinstance(raw, dict)
        assert raw["status"] == "retrieved"
        assert raw["results_count"] == 1
        assert raw["chunks"][0]["document_name"] == "phishing_indicators.md"

