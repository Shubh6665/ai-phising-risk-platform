"""Reproducible 70/15/15 stratified split of preprocessed emails.

Call after deterministic cleaning and global deduplication. No feature
transformer is fitted here; train-fitted transformations belong to later phases.
"""

from dataclasses import dataclass
from typing import cast

import pandas as pd
from sklearn.model_selection import train_test_split

from src.data.loader import build_email_text


@dataclass(frozen=True)
class EmailSplits:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def split_emails(emails: pd.DataFrame, *, random_state: int = 42) -> EmailSplits:
    """Return train/validation/test at 70/15/15, stratified only by label.

    Input must already be globally cleaned and deduplicated. Source remains
    metadata in each output; it is NOT a stratification key or model input.
    The same seed makes the split reproducible on the same ordered input.
    """
    if emails.empty:
        raise ValueError("Cannot split an empty dataset")
    labels = cast(pd.Series, emails["label"])
    if not bool(labels.isin([0, 1]).all()) or labels.nunique() != 2:
        raise ValueError("Expected both binary labels 0 and 1 without missing values")
    subject = cast(pd.Series, emails["subject"])
    body = cast(pd.Series, emails["body"])
    if bool(build_email_text(subject, body).duplicated().any()):
        raise ValueError("Clean and globally deduplicate emails before splitting")

    train, remainder = cast(
        tuple[pd.DataFrame, pd.DataFrame],
        train_test_split(emails, test_size=0.30, stratify=labels, random_state=random_state),
    )
    remainder_labels = cast(pd.Series, remainder["label"])
    validation, test = cast(
        tuple[pd.DataFrame, pd.DataFrame],
        train_test_split(
            remainder, test_size=0.50, stratify=remainder_labels, random_state=random_state
        ),
    )
    return EmailSplits(
        train=train.reset_index(drop=True),
        validation=validation.reset_index(drop=True),
        test=test.reset_index(drop=True),
    )
