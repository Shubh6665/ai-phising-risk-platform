"""Tests for Phase 7 Sub-step A: Security Knowledge Base curation and formatting."""

import re
from pathlib import Path
import pytest

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
    """Verify that authoritative documents reference real public security bodies."""
    phishing_doc = (KB_DIR / "phishing_indicators.md").read_text(encoding="utf-8")
    assert "NIST" in phishing_doc
    assert "CISA" in phishing_doc
    assert "APWG" in phishing_doc
    assert "https://www.cisa.gov" in phishing_doc or "https://csrc.nist.gov" in phishing_doc

    attack_doc = (KB_DIR / "attack_patterns.md").read_text(encoding="utf-8")
    assert "MITRE ATT&CK" in attack_doc
    assert "OWASP" in attack_doc
    assert "T1566" in attack_doc
    assert "https://attack.mitre.org" in attack_doc


def test_mock_documents_are_explicitly_labeled_fictional():
    """Verify mock policies and incident response playbooks are clearly declared fictional."""
    for mock_doc in ["security_policies.md", "incident_response.md"]:
        content = (KB_DIR / mock_doc).read_text(encoding="utf-8")
        assert (
            "MOCK" in content or "fictional" in content.lower()
        ), f"{mock_doc} missing explicit fictional disclaimer"
        assert (
            "demonstration" in content.lower() or "project" in content.lower()
        ), f"{mock_doc} should indicate it was created for demonstration/project"


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
