"""Remote NLP run ke liye unchanged Phase 2 flow aur reproducible data identity."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pandas as pd

from src.data.loader import SOURCE_FILES, build_email_text, load_raw_emails
from src.data.preprocessor import preprocess_emails
from src.data.splitter import split_emails


@dataclass(frozen=True)
class NLPDevelopmentData:
    train_text: list[str]
    train_labels: list[int]
    validation_text: list[str]
    validation_labels: list[int]
    manifest: dict


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _partition_sha256(texts: list[str], labels: list[int]) -> str:
    digest = hashlib.sha256()
    for text, label in zip(texts, labels, strict=True):
        encoded = text.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(bytes([label]))
    return digest.hexdigest()


def load_nlp_development_data(raw_dir: Path) -> NLPDevelopmentData:
    """Test text expose nahi hota; counts audit hain, model evaluation nahi."""
    raw_dir = Path(raw_dir)
    raw = load_raw_emails(raw_dir)
    cleaned = preprocess_emails(raw)
    splits = split_emails(cleaned, random_state=42)
    train_text = build_email_text(
        cast(pd.Series, splits.train["subject"]), cast(pd.Series, splits.train["body"])
    ).tolist()
    validation_text = build_email_text(
        cast(pd.Series, splits.validation["subject"]), cast(pd.Series, splits.validation["body"])
    ).tolist()
    train_labels = splits.train["label"].astype(int).tolist()
    validation_labels = splits.validation["label"].astype(int).tolist()
    manifest = {
        "schema_version": 1,
        "split_seed": 42,
        "raw_rows": len(raw),
        "cleaned_rows": len(cleaned),
        "raw_csv_sha256": {name: _file_sha256(raw_dir / name) for name in SOURCE_FILES.values()},
        "counts": {"train": len(splits.train), "validation": len(splits.validation), "test": len(splits.test)},
        "label_counts": {
            name: {str(label): int(count) for label, count in frame["label"].value_counts().sort_index().items()}
            for name, frame in (("train", splits.train), ("validation", splits.validation), ("test", splits.test))
        },
        "ordered_text_label_sha256": {
            "train": _partition_sha256(train_text, train_labels),
            "validation": _partition_sha256(validation_text, validation_labels),
        },
    }
    return NLPDevelopmentData(train_text, train_labels, validation_text, validation_labels, manifest)


def verify_data_manifest(actual: dict, reference_path: Path) -> None:
    """Counts alone enough nahi: exact CSVs aur ordered train/validation membership verify karo."""
    if actual != json.loads(Path(reference_path).read_text()):
        raise ValueError("Dataset/split local reference se different hai; training start mat karo")
