"""Load the raw per-source phishing email CSVs into one DataFrame.

This module only loads, combines and de-duplicates. It deliberately does NOT
clean text (no lowercasing, no HTML removal, no stripping): that belongs to the
preprocessing step so that useful raw information is not silently lost here.
"""

from pathlib import Path

import pandas as pd

# <repo>/data/raw/archive
DEFAULT_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "archive"

# source name -> file name. Names are the file stems (including the dataset's
# own "SpamAssasin" spelling) so a source can always be traced to its file.
SOURCE_FILES: dict[str, str] = {
    "CEAS_08": "CEAS_08.csv",
    "Enron": "Enron.csv",
    "Ling": "Ling.csv",
    "Nazario": "Nazario.csv",
    "Nigerian_Fraud": "Nigerian_Fraud.csv",
    "SpamAssasin": "SpamAssasin.csv",
}

# Columns read from every file. sender / receiver / date / urls are never read:
# they exist in only some files, so they would identify the source rather than
# describe phishing (e.g. Nazario is 100% phishing).
REQUIRED_COLUMNS = ["subject", "body", "label"]

# Final columns. `source` is analysis metadata and must never be a model feature.
OUTPUT_COLUMNS = ["subject", "body", "label", "source"]

SUBJECT_BODY_SEPARATOR = "\n\n"


def load_raw_emails(raw_dir: Path = DEFAULT_RAW_DIR) -> pd.DataFrame:
    """Read the six source CSVs and return one DataFrame.

    Returns columns: subject, body, label (0 = legitimate, 1 = phishing/spam),
    source. Missing subject/body become "". No rows are dropped here.
    """
    raw_dir = Path(raw_dir)
    frames = []
    for source, file_name in SOURCE_FILES.items():
        path = raw_dir / file_name
        if not path.is_file():
            raise FileNotFoundError(f"Expected dataset file not found: {path}")

        frame = pd.read_csv(path, usecols=lambda c: c in REQUIRED_COLUMNS)
        missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
        if missing:
            raise ValueError(f"{file_name} is missing required columns: {missing}")

        if frame["label"].isna().any() or not frame["label"].isin([0, 1]).all():
            raise ValueError(f"{file_name} has labels other than 0/1 or missing labels")

        frame["subject"] = frame["subject"].fillna("")
        frame["body"] = frame["body"].fillna("")
        frame["source"] = source
        frames.append(frame[OUTPUT_COLUMNS])

    return pd.concat(frames, ignore_index=True)


def build_email_text(subject: pd.Series, body: pd.Series) -> pd.Series:
    """Combine subject and body into the single email text representation.

    This is the one place that defines the combined text, so training and
    (later) serving build it identically. It does not clean or normalize.
    """
    return subject + SUBJECT_BODY_SEPARATOR + body


def deduplicate_emails(emails: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate emails (same combined text), keeping the first.

    Safe to run before the train/val/test split: it only removes identical
    rows and learns nothing from the data. Comparison is exact and
    case-sensitive on purpose (normalizing first would be cleaning).
    """
    text = build_email_text(emails["subject"], emails["body"])
    return emails.loc[~text.duplicated(keep="first")].reset_index(drop=True)
