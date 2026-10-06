import pandas as pd
import pytest

from src.data.loader import build_email_text
from src.data.splitter import split_emails


def emails_fixture(n=200):
    return pd.DataFrame(
        {
            "subject": [f"subject {i}" for i in range(n)],
            "body": [f"body {i}" for i in range(n)],
            "label": [0] * (n // 2) + [1] * (n // 2),
            "source": ["Enron" if i % 2 else "CEAS_08" for i in range(n)],
        }
    )


def test_split_sizes_and_label_balance():
    splits = split_emails(emails_fixture())
    assert (len(splits.train), len(splits.validation), len(splits.test)) == (140, 30, 30)
    for part in (splits.train, splits.validation, splits.test):
        assert part["label"].value_counts().to_dict() == {0: len(part) // 2, 1: len(part) // 2}
        assert list(part.columns) == ["subject", "body", "label", "source"]
        assert part.index.tolist() == list(range(len(part)))


def test_no_duplicate_emails_or_missing_rows_across_splits():
    emails = emails_fixture()
    splits = split_emails(emails)
    groups = [
        set(build_email_text(part["subject"], part["body"]))
        for part in (splits.train, splits.validation, splits.test)
    ]
    assert all(not groups[i] & groups[j] for i, j in ((0, 1), (0, 2), (1, 2)))
    assert set.union(*groups) == set(build_email_text(emails["subject"], emails["body"]))


def test_same_seed_reproduces_all_splits_without_mutating_input():
    emails = emails_fixture()
    before = emails.copy(deep=True)
    a = split_emails(emails, random_state=7)
    b = split_emails(emails, random_state=7)
    for x, y in zip((a.train, a.validation, a.test), (b.train, b.validation, b.test)):
        pd.testing.assert_frame_equal(x, y)
    pd.testing.assert_frame_equal(emails, before)


def test_split_rejects_unsanitized_duplicates():
    emails = emails_fixture()
    emails.loc[1, ["subject", "body"]] = emails.loc[0, ["subject", "body"]]
    with pytest.raises(ValueError, match="deduplicate"):
        split_emails(emails)


def test_split_rejects_missing_class_and_empty_input():
    with pytest.raises(ValueError, match="empty"):
        split_emails(emails_fixture(0))
    with pytest.raises(ValueError, match="both binary labels"):
        split_emails(emails_fixture().query("label == 0"))


def test_source_remains_metadata_not_a_stratification_key():
    emails = emails_fixture()
    emails.loc[emails["source"] == "Enron", "label"] = 1
    splits = split_emails(emails)
    # The procedure preserves rows with both source names; it only stratifies label.
    assert set(splits.train["source"]) == {"CEAS_08", "Enron"}
    assert set(splits.validation["source"]) == {"CEAS_08", "Enron"}
    assert set(splits.test["source"]) == {"CEAS_08", "Enron"}
