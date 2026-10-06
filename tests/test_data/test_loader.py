import pandas as pd
import pytest

from src.data.loader import (
    OUTPUT_COLUMNS,
    SOURCE_FILES,
    build_email_text,
    deduplicate_emails,
    load_raw_emails,
)


def write_sources(raw_dir, overrides=None):
    """Write one tiny CSV per source. Some files get the extra metadata columns
    (sender/urls) that the real files have, to prove the loader drops them."""
    overrides = overrides or {}
    for i, (source, file_name) in enumerate(SOURCE_FILES.items()):
        rows = overrides.get(
            source,
            {"subject": [f"subj {i}"], "body": [f"body {i}"], "label": [i % 2]},
        )
        frame = pd.DataFrame(rows)
        if source in ("CEAS_08", "Nazario"):
            frame["sender"] = "someone@example.com"
            frame["urls"] = 1
        frame.to_csv(raw_dir / file_name, index=False)


def test_load_returns_only_expected_columns_with_source(tmp_path):
    write_sources(tmp_path)
    emails = load_raw_emails(tmp_path)

    assert list(emails.columns) == OUTPUT_COLUMNS
    assert len(emails) == len(SOURCE_FILES)
    assert set(emails["source"]) == set(SOURCE_FILES)
    for dropped in ("sender", "receiver", "date", "urls"):
        assert dropped not in emails.columns


def test_missing_subject_and_body_become_empty_strings(tmp_path):
    write_sources(
        tmp_path,
        {"Enron": {"subject": [None, "hi"], "body": ["text", None], "label": [0, 1]}},
    )
    emails = load_raw_emails(tmp_path)
    enron = emails[emails["source"] == "Enron"]

    assert enron["subject"].tolist() == ["", "hi"]
    assert enron["body"].tolist() == ["text", ""]
    assert not emails[["subject", "body"]].isna().any().any()


def test_loader_does_not_clean_raw_text(tmp_path):
    raw_body = "URGENT!! Visit <b>http://Example.com</b>  now"
    write_sources(
        tmp_path, {"Ling": {"subject": ["Hi"], "body": [raw_body], "label": [1]}}
    )
    emails = load_raw_emails(tmp_path)

    assert emails.loc[emails["source"] == "Ling", "body"].iloc[0] == raw_body


def test_missing_file_raises(tmp_path):
    write_sources(tmp_path)
    (tmp_path / SOURCE_FILES["Ling"]).unlink()
    with pytest.raises(FileNotFoundError):
        load_raw_emails(tmp_path)


def test_missing_required_column_raises(tmp_path):
    write_sources(tmp_path)
    pd.DataFrame({"subject": ["a"], "label": [0]}).to_csv(
        tmp_path / SOURCE_FILES["Enron"], index=False
    )
    with pytest.raises(ValueError, match="missing required columns"):
        load_raw_emails(tmp_path)


def test_invalid_label_raises(tmp_path):
    write_sources(
        tmp_path, {"Ling": {"subject": ["a"], "body": ["b"], "label": [2]}}
    )
    with pytest.raises(ValueError, match="labels"):
        load_raw_emails(tmp_path)


def test_build_email_text_is_exact_and_unnormalized():
    text = build_email_text(pd.Series(["Hello", ""]), pd.Series(["World", "Body"]))
    assert text.tolist() == ["Hello\n\nWorld", "\n\nBody"]


def test_deduplicate_removes_exact_duplicates_across_sources_keeping_first():
    emails = pd.DataFrame(
        {
            "subject": ["a", "a", "b"],
            "body": ["x", "x", "x"],
            "label": [1, 1, 0],
            "source": ["Enron", "CEAS_08", "Ling"],
        }
    )
    deduped = deduplicate_emails(emails)

    assert len(deduped) == 2
    assert deduped["source"].tolist() == ["Enron", "Ling"]
    assert deduped.index.tolist() == [0, 1]


def test_deduplicate_is_exact_not_normalized_and_does_not_mutate_input():
    emails = pd.DataFrame(
        {
            "subject": ["Hi", "hi"],
            "body": ["Body", "Body"],
            "label": [0, 0],
            "source": ["Enron", "Enron"],
        }
    )
    before = emails.copy()
    deduped = deduplicate_emails(emails)

    assert len(deduped) == 2  # different case => different email
    pd.testing.assert_frame_equal(emails, before)
