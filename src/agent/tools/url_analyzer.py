"""Deterministic URL structure analyzer tool.

Performs offline lexical and structural inspection of URLs without making
network connections, DNS lookups, or HTTP requests.
"""

import ipaddress
import re
from typing import Any
from urllib.parse import urlsplit

from langchain_core.tools import tool

from src.agent.schemas import URLAnalyzerInput, URLObservation
from src.features.url_features import extract_urls

_SUSPICIOUS_PATH_KEYWORDS = re.compile(
    r"\b(login|signin|verify|verification|update|secure|account|banking|password|credential|wallet|auth|token)\b",
    re.IGNORECASE,
)
_HEX_ENCODING_RE = re.compile(r"%[0-9a-fA-F]{2}")


def analyze_url_structure(url: str) -> URLObservation:
    """Analyze the lexical and structural properties of a single URL offline.

    No network requests, DNS queries, or external resources are touched.
    Structural anomalies are flagged in `suspicious_indicators`.
    """
    if not isinstance(url, str) or not url.strip():
        return URLObservation(
            url=str(url),
            scheme="",
            hostname=None,
            suspicious_indicators=["Empty or whitespace URL string"],
            indicator_count=1,
            notes="Malformed URL: string is empty or invalid.",
        )

    clean_url = url.strip()
    suspicious_indicators: list[str] = []

    try:
        parsed = urlsplit(clean_url)
    except Exception as e:
        return URLObservation(
            url=clean_url,
            scheme="",
            hostname=None,
            suspicious_indicators=[f"URL parser exception: {type(e).__name__}"],
            indicator_count=1,
            notes="Malformed URL could not be parsed by RFC 3986 parser.",
        )

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc
    path = parsed.path
    query = parsed.query
    hostname = parsed.hostname
    port = parsed.port

    # 1. Scheme analysis
    if scheme == "http":
        suspicious_indicators.append("Insecure cleartext HTTP scheme used")
    elif scheme not in ("http", "https", "mailto"):
        suspicious_indicators.append(f"Uncommon or non-web scheme: '{scheme}'")

    # 2. Hostname missing check
    if not hostname:
        suspicious_indicators.append("Missing or malformed hostname")
        return URLObservation(
            url=clean_url,
            scheme=scheme,
            hostname=None,
            port=port,
            path=path,
            query=query,
            suspicious_indicators=suspicious_indicators,
            indicator_count=len(suspicious_indicators),
            url_length=len(clean_url),
            notes="Malformed URL: scheme present but no valid hostname could be resolved.",
        )

    hostname_lower = hostname.lower()

    # 3. IP Literal check (IPv4 / IPv6)
    is_ip = False
    ip_type = None
    try:
        ip_obj = ipaddress.ip_address(hostname_lower)
        is_ip = True
        ip_type = "ipv4" if isinstance(ip_obj, ipaddress.IPv4Address) else "ipv6"
        suspicious_indicators.append(f"Literal {ip_type.upper()} address used as hostname instead of a domain name")
    except ValueError:
        is_ip = False
        ip_type = None

    # 4. Userinfo (@ symbol in netloc) check
    # Attackers frequently use http://legit.example.com@attacker.com to deceive human readers
    has_userinfo = "@" in netloc
    if has_userinfo:
        suspicious_indicators.append("User-info credentials syntax ('@') present in URL authority segment")

    # 5. Punycode / IDN homograph check
    has_punycode = "xn--" in hostname_lower
    if has_punycode:
        suspicious_indicators.append("Internationalized domain name Punycode prefix ('xn--') detected in hostname")

    # 6. Port inspection
    has_unusual_port = False
    if port is not None:
        if (scheme == "http" and port != 80) or (scheme == "https" and port != 443):
            has_unusual_port = True
            suspicious_indicators.append(f"Non-standard web port ({port}) specified")

    # 7. Subdomain depth calculation (for domain names, not IP literals)
    subdomain_depth = 0
    if not is_ip:
        dots = hostname_lower.count(".")
        # Typical domain has 1 dot (example.com) or 2 (example.co.uk). > 3 dots suggests nested subdomains
        if dots > 0:
            subdomain_depth = max(0, dots - 1)
        if dots >= 4:
            suspicious_indicators.append(f"Excessive domain label nesting ({dots + 1} labels / {dots} dots)")

    # 8. Path & Query heuristics
    if _HEX_ENCODING_RE.search(clean_url):
        suspicious_indicators.append("Percent-encoded characters detected in URL")

    full_target_str = f"{path}?{query}"
    matched_keywords = set(_SUSPICIOUS_PATH_KEYWORDS.findall(full_target_str))
    if matched_keywords:
        suspicious_indicators.append(
            f"Sensitive authentication/account keywords found in path or query: {', '.join(sorted(matched_keywords))}"
        )

    # 9. Excessive length check (> 120 chars)
    url_len = len(clean_url)
    if url_len > 120:
        suspicious_indicators.append(f"Abnormally long URL length ({url_len} characters)")

    return URLObservation(
        url=clean_url,
        scheme=scheme,
        hostname=hostname,
        port=port,
        path=path,
        query=query,
        is_ip_literal=is_ip,
        ip_type=ip_type,
        has_userinfo=has_userinfo,
        has_punycode=has_punycode,
        has_unusual_port=has_unusual_port,
        subdomain_depth=subdomain_depth,
        url_length=url_len,
        suspicious_indicators=suspicious_indicators,
        indicator_count=len(suspicious_indicators),
        notes=(
            "Indicators represent structural anomalies and must be correlated with threat intelligence; "
            "presence of an indicator does not alone confirm maliciousness."
        ),
    )


def analyze_urls_in_text(email_text: str) -> list[URLObservation]:
    """Extract all HTTP(S) URLs from email text and run structural analysis on each."""
    urls = extract_urls(email_text)
    return [analyze_url_structure(u) for u in urls]


@tool("url_structure_analyzer", args_schema=URLAnalyzerInput)
def url_structure_analyzer_tool(url: str) -> dict[str, Any]:
    """Inspect the structural and lexical characteristics of a single URL offline.

    Checks for IP literal hosts, userinfo '@' tricks, Punycode (xn--), non-standard ports,
    excessive subdomain depth, and suspicious path tokens without making any network calls.
    """
    observation = analyze_url_structure(url)
    return observation.model_dump()

