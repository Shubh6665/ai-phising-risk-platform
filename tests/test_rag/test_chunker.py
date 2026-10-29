"""Unit tests for the markdown chunking engine."""

from pathlib import Path
import pytest

from src.rag.chunker import DocumentChunk, MarkdownChunker


@pytest.fixture
def chunker():
    return MarkdownChunker(max_chunk_chars=300, chunk_overlap_chars=50)


def test_chunk_empty_document(chunker, tmp_path):
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("", encoding="utf-8")
    assert chunker.chunk_document(empty_file) == []
    assert chunker.chunk_document(empty_file, content="   \n\n  ") == []


def test_chunk_short_document(chunker, tmp_path):
    doc_path = tmp_path / "short_guidance.md"
    content = "# Short Title\n\nThis is a short single paragraph."
    doc_path.write_text(content, encoding="utf-8")

    chunks = chunker.chunk_document(doc_path)
    assert len(chunks) == 1
    chunk = chunks[0]
    assert isinstance(chunk, DocumentChunk)
    assert "short single paragraph" in chunk.content
    assert chunk.metadata["document_name"] == "short_guidance.md"
    assert chunk.metadata["document_title"] == "Short Title"
    assert chunk.metadata["document_type"] == "authoritative"
    assert not chunk.metadata["is_mock"]
    assert chunk.metadata["chunk_index"] == 0


def test_deterministic_chunking_and_stable_ids(tmp_path):
    doc_path = tmp_path / "phishing_indicators.md"
    content = (
        "# Phishing Indicators\n\n"
        "> **Sources**: NIST, CISA\n\n"
        "## 1. Urgency Tactics\n\n"
        "Urgency is frequently used in phishing attacks to force immediate panic.\n\n"
        "## 2. Link Deception\n\n"
        "Links with numerical IP addresses or misspelled brand domains are deceptive."
    )
    doc_path.write_text(content, encoding="utf-8")

    chunker1 = MarkdownChunker(max_chunk_chars=400, chunk_overlap_chars=50)
    chunker2 = MarkdownChunker(max_chunk_chars=400, chunk_overlap_chars=50)

    chunks1 = chunker1.chunk_document(doc_path)
    chunks2 = chunker2.chunk_document(doc_path)

    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.id == c2.id
        assert c1.content == c2.content
        assert c1.metadata == c2.metadata


def test_mock_document_type_detection(chunker, tmp_path):
    mock_path = tmp_path / "mock_policies.md"
    content = "# Internal Policies\n\n> [!IMPORTANT]\n> **MOCK POLICY DOCUMENT**\n\n## POL-101\n\nPolicy text."
    mock_path.write_text(content, encoding="utf-8")

    chunks = chunker.chunk_document(mock_path)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.metadata["is_mock"] is True
        assert chunk.metadata["document_type"] == "mock"


def test_source_backed_guidance_with_policy_disclaimer_is_not_mock(chunker, tmp_path):
    doc_path = tmp_path / "security_policies.md"
    content = (
        "# Project Triage Guidance\n\n"
        "> [!NOTE]\n"
        "> **PROJECT TRIAGE GUIDANCE — NOT AN ORGANIZATION-APPROVED SECURITY POLICY**\n\n"
        "> **Sources**: CISA, NIST\n\n"
        "## 1. Scope\n\n"
        "This is source-backed technical guidance for email triage."
    )
    doc_path.write_text(content, encoding="utf-8")

    chunks = chunker.chunk_document(doc_path)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.metadata["is_mock"] is False
        assert chunk.metadata["document_type"] == "authoritative"
        assert "CISA, NIST" in chunk.metadata["source_attribution"]


def test_long_document_splitting_with_overlap(tmp_path):
    doc_path = tmp_path / "long_doc.md"
    # Create multiple paragraphs that exceed max_chunk_chars (200)
    p1 = "Paragraph one with specific security content that is descriptive and detailed. " * 3
    p2 = "Paragraph two with another set of indicators and attack patterns discussed. " * 3
    content = f"# Title\n\n## Big Section\n\n{p1}\n\n{p2}"
    doc_path.write_text(content, encoding="utf-8")

    chunker = MarkdownChunker(max_chunk_chars=220, chunk_overlap_chars=40)
    chunks = chunker.chunk_document(doc_path)

    assert len(chunks) > 1
    # Verify sequential chunk indices
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["chunk_index"] == i
        assert len(chunk.content) > 0


def test_invalid_chunker_parameters():
    with pytest.raises(ValueError, match="strictly greater"):
        MarkdownChunker(max_chunk_chars=100, chunk_overlap_chars=100)

    with pytest.raises(ValueError, match="strictly greater"):
        MarkdownChunker(max_chunk_chars=100, chunk_overlap_chars=150)

    with pytest.raises(ValueError, match="cannot be negative"):
        MarkdownChunker(max_chunk_chars=100, chunk_overlap_chars=-10)
