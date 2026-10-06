"""Stateless numerical features from one email's combined subject and body."""

import re

# Predefined domain terms, not learned from the dataset. Matches whole words only.
PHISHING_TERMS = ("verify", "account", "urgent", "click", "suspended")
_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
_PHISHING_TERMS_RE = re.compile(
    r"\b(?:" + "|".join(PHISHING_TERMS) + r")\b", re.IGNORECASE
)
TEXT_FEATURE_NAMES = (
    "word_count",
    "average_word_length",
    "uppercase_ratio",
    "exclamation_count",
    "phishing_keyword_count",
)


def extract_text_features(email_text: str) -> dict[str, int | float]:
    """Count visible text patterns without fitting a vocabulary or mutating input.

    Uppercase ratio uses alphabetic characters as denominator; no letters and
    no words both yield zero rather than NaN or a division error. Keyword count
    counts occurrences, including repeated terms, with case-insensitive word
    boundaries ("account" in "accounting" is not a match).
    """
    words = _WORD_RE.findall(email_text)
    letters = [char for char in email_text if char.isalpha()]
    return {
        "word_count": len(words),
        "average_word_length": sum(map(len, words)) / len(words) if words else 0.0,
        "uppercase_ratio": (
            sum(char.isupper() for char in letters) / len(letters) if letters else 0.0
        ),
        "exclamation_count": email_text.count("!"),
        "phishing_keyword_count": len(_PHISHING_TERMS_RE.findall(email_text)),
    }
