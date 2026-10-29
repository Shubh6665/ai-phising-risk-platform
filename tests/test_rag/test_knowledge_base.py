"""Tests for Phase 7 Knowledge Base curation, source attribution, and triage alignment."""

import re
from pathlib import Path
import pytest

from src.rag.chunker import MarkdownChunker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = PROJECT_ROOT / "data/knowledge_base"

REQUIRED_DOCUMENTS = [
    "phishing_indicators.md",
    "attack_patterns.md",
    "security_policies.md",
    "incident_response.md",
]


def test_required_documents_exist():
    """Verify all four required knowledge base documents exist on disk."""
    assert KB_DIR.is_dir(), f"Knowledge base directory {KB_DIR} does not exist"
    for doc_name in REQUIRED_DOCUMENTS:
        doc_path = KB_DIR / doc_name
        assert doc_path.is_file(), f"Missing required document: {doc_name}"


@pytest.mark.parametrize("doc_name", REQUIRED_DOCUMENTS)
def test_documents_are_valid_utf8_and_non_empty(doc_name):
    """Verify all documents are clean UTF-8 and contain substantial content."""
    doc_path = KB_DIR / doc_name
    content = doc_path.read_text(encoding="utf-8")
    assert len(content.strip()) > 500, f"{doc_name} is unexpectedly short"
    # Ensure no null bytes or binary corruption
    assert "\x00" not in content


def test_authoritative_documents_source_attribution():
    """Verify that all knowledge base documents reference real public security standards."""
    phishing_doc = (KB_DIR / "phishing_indicators.md").read_text(encoding="utf-8")
    assert "NIST" in phishing_doc
    assert "CISA" in phishing_doc
    assert "APWG" in phishing_doc
    assert "https://www.cisa.gov" in phishing_doc
    assert "https://csrc.nist.gov" in phishing_doc

    attack_doc = (KB_DIR / "attack_patterns.md").read_text(encoding="utf-8")
    assert "MITRE ATT&CK" in attack_doc
    assert "OWASP" in attack_doc
    assert "T1566" in attack_doc
    assert "v20" in attack_doc
    assert "https://attack.mitre.org" in attack_doc

    policy_doc = (KB_DIR / "security_policies.md").read_text(encoding="utf-8")
    assert "CISA" in policy_doc
    assert "NIST" in policy_doc
    assert "SP 800-61" in policy_doc or "SP 800-177" in policy_doc
    assert "https://www.cisa.gov" in policy_doc or "https://csrc.nist.gov" in policy_doc

    ir_doc = (KB_DIR / "incident_response.md").read_text(encoding="utf-8")
    assert "NIST" in ir_doc
    assert "SP 800-61 Rev. 3" in ir_doc
    assert "CISA" in ir_doc
    assert "https://csrc.nist.gov/pubs/sp/800/61/r3/final" in ir_doc


def test_guidance_distinguishes_project_triage_from_approved_organizational_policy():
    """Verify triage and IR documents clarify they are reference guidance, not approved policies."""
    policies_doc = (KB_DIR / "security_policies.md").read_text(encoding="utf-8")
    assert "NOT AN ORGANIZATION-APPROVED SECURITY POLICY" in policies_doc
    assert "ensemble" in policies_doc.lower() or "src/models/ensemble.py" in policies_doc
    assert "not standards" in policies_doc.lower() or "not thresholds mandated" in policies_doc.lower()

    ir_doc = (KB_DIR / "incident_response.md").read_text(encoding="utf-8")
    assert "NOT AN ORGANIZATION-APPROVED INCIDENT RESPONSE PLAN" in ir_doc
    assert "executive leadership" in ir_doc.lower() or "legal counsel" in ir_doc.lower()


def test_knowledge_base_documents_have_correct_mock_status():
    """Ensure source-backed reference guidance is not falsely tagged as mock."""
    chunker = MarkdownChunker()
    for doc_name in REQUIRED_DOCUMENTS:
        doc_path = KB_DIR / doc_name
        chunks = chunker.chunk_document(doc_path)
        assert len(chunks) > 0, f"No chunks generated for {doc_name}"
        for chunk in chunks:
            assert chunk.metadata["is_mock"] is False, f"{doc_name} should not be marked as mock"
            assert chunk.metadata["document_type"] == "source_backed_guidance"
            assert "Fictional Project Policy" not in chunk.metadata["source_attribution"]


def test_no_secrets_or_private_credentials_in_knowledge_base():
    """Ensure no API keys, tokens, or credentials were inadvertently committed."""
    secret_patterns = [
        re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"),
        re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"hf_[a-zA-Z0-9]{34}"),
        re.compile(r"postgres(ql)?://[^:\s]+:[^@\s]+@"),
    ]

    for doc_name in REQUIRED_DOCUMENTS:
        content = (KB_DIR / doc_name).read_text(encoding="utf-8")
        for pattern in secret_patterns:
            matches = pattern.findall(content)
            assert not matches, f"Potential credential found in {doc_name}: {matches}"


def test_document_structure_has_markdown_headings():
    """Verify documents have structured markdown headers for future chunking."""
    for doc_name in REQUIRED_DOCUMENTS:
        content = (KB_DIR / doc_name).read_text(encoding="utf-8")
        h2_headings = [line for line in content.splitlines() if line.startswith("## ")]
        assert len(h2_headings) >= 3, f"{doc_name} should contain at least 3 major sections (##)"


def test_policy_thresholds_match_ensemble_classification():
    """Ensure guidance tiers align with Phase 5 ensemble thresholds."""
    policies_doc = (KB_DIR / "security_policies.md").read_text(encoding="utf-8")
    assert "0.0 – 39.9" in policies_doc
    assert "40.0 – 59.9" in policies_doc
    assert "60.0 – 79.9" in policies_doc
    assert "80.0 – 100.0" in policies_doc

    ir_doc = (KB_DIR / "incident_response.md").read_text(encoding="utf-8")
    assert "0.0 – 39.9" in ir_doc
    assert "40.0 – 59.9" in ir_doc
    assert "60.0 – 79.9" in ir_doc
    assert "80.0 – 100.0" in ir_doc
