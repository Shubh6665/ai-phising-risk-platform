"""Stateless, offline lexical features from URLs present in one email."""

import ipaddress
import re
from urllib.parse import urlsplit

# Stop at text/HTML delimiters; strip common sentence punctuation afterwards.
_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_TRAILING_PUNCTUATION = ".,;:!?)]}"
URL_FEATURE_NAMES = (
    "url_count",
    "https_url_count",
    "max_url_length",
    "max_hostname_dot_count",
    "has_ip_address_url",
)


def extract_urls(email_text: str) -> list[str]:
    """Return parseable HTTP(S) URLs in text, in appearance order.

    This is lexical extraction only: never perform DNS lookups or HTTP calls.
    A malformed URL with no hostname is ignored. Trailing punctuation commonly
    attached to a URL in prose is removed; unusual URLs ending in those chars
    can be truncated (a known limitation of regex extraction).
    """
    urls = []
    for match in _URL_RE.finditer(email_text):
        url = match.group(0).rstrip(_TRAILING_PUNCTUATION)
        try:
            if urlsplit(url).hostname:
                urls.append(url)
        except ValueError:  # Invalid IPv6 address or malformed port/host.
            continue
    return urls


def extract_url_features(email_text: str) -> dict[str, int]:
    """Aggregate structural URL signals; return zeros if there is no URL."""
    urls = extract_urls(email_text)
    hostnames = [urlsplit(url).hostname for url in urls]
    has_ip = 0
    for hostname in hostnames:
        if hostname is None:
            continue
        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            continue
        has_ip = 1
        break
    return {
        "url_count": len(urls),
        "https_url_count": sum(url.lower().startswith("https://") for url in urls),
        "max_url_length": max((len(url) for url in urls), default=0),
        "max_hostname_dot_count": max((host.count(".") for host in hostnames if host), default=0),
        "has_ip_address_url": has_ip,
    }
