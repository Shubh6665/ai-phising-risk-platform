import socket

from src.features.url_features import URL_FEATURE_NAMES, extract_url_features, extract_urls


def test_no_url_yields_zeros():
    assert extract_urls("No links here, or just www.example.com") == []
    assert extract_url_features("No links here") == dict.fromkeys(URL_FEATURE_NAMES, 0)


def test_multiple_urls_and_trailing_prose_punctuation():
    text = "Click (https://login.mail.example/path?x=1), or http://192.0.2.1/act!"
    assert extract_urls(text) == [
        "https://login.mail.example/path?x=1",
        "http://192.0.2.1/act",
    ]
    features = extract_url_features(text)
    assert tuple(features) == URL_FEATURE_NAMES
    assert features == {
        "url_count": 2,
        "https_url_count": 1,
        "max_url_length": len("https://login.mail.example/path?x=1"),
        "max_hostname_dot_count": 3,
        "has_ip_address_url": 1,
    }


def test_ip_is_hostname_only_not_query_or_path():
    features = extract_url_features("https://safe.example/?next=http://192.0.2.1")
    assert features["has_ip_address_url"] == 0
    assert features["url_count"] == 1


def test_ipv6_and_domain_dots_are_structural_not_risk_labels():
    features = extract_url_features("HTTPS://[2001:db8::1]/reset https://sub.example.org/")
    assert features["has_ip_address_url"] == 1
    assert features["max_hostname_dot_count"] == 2
    assert features["https_url_count"] == 2


def test_malformed_url_does_not_crash_or_count():
    assert extract_url_features("http:// https://[not-an-ip/path") == dict.fromkeys(
        URL_FEATURE_NAMES, 0
    )


def test_url_extraction_does_not_contact_any_host(monkeypatch):
    def deny_network(*args, **kwargs):
        raise AssertionError("URL extraction must not use the network")

    monkeypatch.setattr(socket, "getaddrinfo", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)

    features = extract_url_features("https://example.org/login http://192.0.2.1/reset")
    assert features["url_count"] == 2
    assert features["has_ip_address_url"] == 1


def test_html_href_target_preserved_by_preprocessor_is_detectable():
    from src.data.preprocessor import clean_text

    cleaned = clean_text('<a href="https://example.org/login">verify</a>')
    assert extract_urls(cleaned) == ["https://example.org/login"]
