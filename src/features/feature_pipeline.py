"""Combine stateless text and URL features for the same email sample."""

from typing import cast

import pandas as pd

from src.data.loader import build_email_text
from src.features.text_features import TEXT_FEATURE_NAMES, extract_text_features
from src.features.url_features import URL_FEATURE_NAMES, extract_url_features

FEATURE_NAMES = TEXT_FEATURE_NAMES + URL_FEATURE_NAMES


def extract_features(emails: pd.DataFrame) -> pd.DataFrame:
    """Return one numerical feature row per preprocessed email, in fixed order.

    Use separately for train/validation/test after the global split. Only
    subject/body are read; label/source and any extra columns are excluded by
    construction. There is no fit step or global statistic here.
    """
    dtypes = {
        name: "float64" if name in ("average_word_length", "uppercase_ratio") else "int64"
        for name in FEATURE_NAMES
    }
    if emails.empty:
        # Empty pandas columns may default to float: do not try to concatenate
        # them as strings; return the same numeric schema as a non-empty batch.
        return pd.DataFrame(columns=FEATURE_NAMES).astype(dtypes)

    subject = cast(pd.Series, emails["subject"])
    body = cast(pd.Series, emails["body"])
    combined_text = build_email_text(subject, body)
    features = [
        extract_text_features(text) | extract_url_features(text) for text in combined_text
    ]
    return pd.DataFrame.from_records(features, columns=FEATURE_NAMES).astype(dtypes)
