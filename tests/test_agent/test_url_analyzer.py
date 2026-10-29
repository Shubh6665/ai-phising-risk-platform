"""Tests for the deterministic offline URL structure analyzer tool."""

import socket
import urllib.request
import pytest

from src.agent.tools.url_analyzer import (
    analyze_url_structure,
    analyze_urls_in_text,
    url_structure_analyzer_tool,
)


def test_standard_legitimate_url_inspection():
    """Verify normal legitimate HTTPS URL has no structural anomalies."""
    obs = analyze_url_structure("https://www.example.com/about/team")
    assert obs.scheme == "https"
    assert obs.hostname == "www.example.com"
    assert obs.port is None
    assert obs.is_ip_literal is False
    assert obs.has_userinfo is False
    assert obs.has_punycode is False
    assert obs.has_unusual_port is False
    assert obs.subdomain_depth == 1  # 'www'
    assert obs.indicator_count == 0
    assert len(obs.suspicious_indicators) == 0


def test_ip_literal_hostnames():
    """Verify IPv4 and IPv6 literal hostnames are detected as structural anomalies."""
    # IPv4 literal host
    v4 = analyze_url_structure("http://192.168.1.100:8080/login")
    assert v4.is_ip_literal is True
    assert v4.ip_type == "ipv4"
    assert v4.has_unusual_port is True
    assert v4.port == 8080
    assert any("Literal IPV4 address" in ind for ind in v4.suspicious_indicators)
    assert any("Non-standard web port (8080)" in ind for ind in v4.suspicious_indicators)
    assert any("Insecure cleartext HTTP" in ind for ind in v4.suspicious_indicators)
    assert any("Sensitive authentication/account keywords" in ind for ind in v4.suspicious_indicators)

    # IPv6 literal host
    v6 = analyze_url_structure("https://[2001:db8::1]/secure/account")
    assert v6.is_ip_literal is True
    assert v6.ip_type == "ipv6"
    assert any("Literal IPV6 address" in ind for ind in v6.suspicious_indicators)


def test_userinfo_at_symbol_deception():
    """Verify @ user-info credential syntax in authority is flagged."""
    obs = analyze_url_structure("https://legit-bank.com@attacker-harvest.ru/verify")
    assert obs.has_userinfo is True
    assert obs.hostname == "attacker-harvest.ru"
    assert any("User-info credentials syntax ('@')" in ind for ind in obs.suspicious_indicators)
    assert any("Sensitive authentication/account keywords" in ind for ind in obs.suspicious_indicators)


def test_punycode_homograph_detection():
    """Verify internationalized domain name Punycode (xn--) prefix is flagged."""
    obs = analyze_url_structure("https://xn--pple-43d.com/signin")
    assert obs.has_punycode is True
    assert any("Punycode prefix ('xn--')" in ind for ind in obs.suspicious_indicators)


def test_excessive_subdomain_nesting():
    """Verify high dot count / deep subdomain nesting is flagged."""
    obs = analyze_url_structure("https://login.portal.update.billing.client.attacker.com/index.html")
    assert obs.subdomain_depth >= 4
    assert any("Excessive domain label nesting" in ind for ind in obs.suspicious_indicators)


def test_percent_encoded_and_long_url():
    """Verify percent-encoding and abnormally long URLs are flagged."""
    long_url = "https://example.com/path?" + ("param=" + "%20%2f" * 30)
    obs = analyze_url_structure(long_url)
    assert obs.url_length > 120
    assert any("Percent-encoded characters" in ind for ind in obs.suspicious_indicators)
    assert any("Abnormally long URL" in ind for ind in obs.suspicious_indicators)


def test_malformed_and_edge_case_urls():
    """Verify malformed and empty URLs are handled safely without crashing."""
    # Empty string
    empty = analyze_url_structure("")
    assert empty.hostname is None
    assert empty.indicator_count > 0

    # Whitespace
    ws = analyze_url_structure("   ")
    assert ws.hostname is None

    # Missing hostname
    nohost = analyze_url_structure("http:///path/to/page")
    assert nohost.hostname is None
    assert any("Missing or malformed hostname" in ind for ind in nohost.suspicious_indicators)

    # Non-web scheme
    ftp = analyze_url_structure("ftp://ftp.example.com/files")
    assert any("Uncommon or non-web scheme" in ind for ind in ftp.suspicious_indicators)


def test_offline_guarantee_no_network_access(monkeypatch):
    """Verify that analyzing URLs makes absolutely zero network or DNS calls."""
    def guarded_connect(*args, **kwargs):
        pytest.fail("Network access attempted during offline URL analysis!")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_connect)
    monkeypatch.setattr(urllib.request, "urlopen", guarded_connect)

    # Run analysis over a suite of tricky URLs
    urls = [
        "https://www.google.com",
        "http://192.168.1.1:8080/admin",
        "https://user:pass@phish.net/login",
        "https://xn--e1afmkfd.xn--p1ai/test",
    ]
    for u in urls:
        obs = analyze_url_structure(u)
        assert obs.url == u


def test_analyze_urls_in_text():
    """Verify extraction and batch analysis of multiple URLs from an email body."""
    body = (
        "Dear customer, please review our policy at https://example.com/policy. "
        "Alternatively, sign in directly at http://10.0.0.1/login to resolve this."
    )
    observations = analyze_urls_in_text(body)
    assert len(observations) == 2
    assert observations[0].hostname == "example.com"
    assert observations[1].hostname == "10.0.0.1"
    assert observations[1].is_ip_literal is True


def test_langchain_tool_invocation():
    """Verify LangChain tool wrapper conforms to expected tool calling interface."""
    raw = url_structure_analyzer_tool.invoke({"url": "http://192.168.1.1/login"})
    assert isinstance(raw, dict)
    assert raw["url"] == "http://192.168.1.1/login"
    assert raw["is_ip_literal"] is True
    assert raw["indicator_count"] >= 2
    assert "Indicators represent structural anomalies" in raw["notes"]

