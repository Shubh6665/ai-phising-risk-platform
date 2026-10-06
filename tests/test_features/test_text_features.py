import pytest

from src.features.text_features import TEXT_FEATURE_NAMES, extract_text_features


def test_text_features_count_words_case_punctuation_and_keywords():
    features = extract_text_features("URGENT!!! Verify your account. Click to VERIFY.")
    assert tuple(features) == TEXT_FEATURE_NAMES
    assert features["word_count"] == 7
    assert features["average_word_length"] == pytest.approx(36 / 7)
    assert features["uppercase_ratio"] == pytest.approx(14 / 36)
    assert features["exclamation_count"] == 3
    assert features["phishing_keyword_count"] == 5


def test_keywords_use_whole_words_not_substrings():
    features = extract_text_features("accounting clickable urgently account! suspended")
    assert features["phishing_keyword_count"] == 2


def test_empty_and_punctuation_only_are_safe():
    for text in ("", "?! 123"):
        features = extract_text_features(text)
        assert features["uppercase_ratio"] == 0.0
        assert features["phishing_keyword_count"] == 0
    assert extract_text_features("")["word_count"] == 0
    assert extract_text_features("")["average_word_length"] == 0.0
    assert extract_text_features("?! 123")["exclamation_count"] == 1
