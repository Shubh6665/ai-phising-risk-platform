import json
from types import SimpleNamespace

import pandas as pd
import pytest

from src.data import nlp_dataset
from src.data.loader import SOURCE_FILES


def test_adapter_exposes_only_development_text_and_preserves_metadata_boundary(monkeypatch, tmp_path):
    for name in SOURCE_FILES.values():
        (tmp_path / name).write_text("subject,body,label\n")
    train = pd.DataFrame({"subject": ["Meeting", "URGENT"], "body": ["team notes", "verify account"], "label": [0, 1], "source": ["metadata", "metadata"]})
    validation = train.iloc[::-1].reset_index(drop=True)
    # Test subject/body deliberately absent: adapter must not build test text.
    test = pd.DataFrame({"label": [0, 1]})
    monkeypatch.setattr(nlp_dataset, "load_raw_emails", lambda path: train)
    monkeypatch.setattr(nlp_dataset, "preprocess_emails", lambda frame: frame)
    seen = []

    def split(frame, *, random_state):
        seen.append(random_state)
        return SimpleNamespace(train=train, validation=validation, test=test)

    monkeypatch.setattr(nlp_dataset, "split_emails", split)
    data = nlp_dataset.load_nlp_development_data(tmp_path)
    assert seen == [42]
    assert data.train_text == ["Meeting\n\nteam notes", "URGENT\n\nverify account"]
    assert data.train_labels == [0, 1] and data.validation_labels == [1, 0]
    assert not hasattr(data, "test_text") and not hasattr(data, "test_labels")
    assert all("metadata" not in text for text in data.train_text)
    assert data.manifest["counts"] == {"train": 2, "validation": 2, "test": 2}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data.manifest))
    nlp_dataset.verify_data_manifest(data.manifest, path)
    changed = {**data.manifest, "split_seed": 43}
    with pytest.raises(ValueError, match="different"):
        nlp_dataset.verify_data_manifest(changed, path)


def test_ordered_partition_hash_detects_text_label_and_order_changes():
    original = nlp_dataset._partition_sha256(["a", "b"], [0, 1])
    assert original != nlp_dataset._partition_sha256(["b", "a"], [1, 0])
    assert original != nlp_dataset._partition_sha256(["a", "b"], [1, 0])
    assert original != nlp_dataset._partition_sha256(["aa", "b"], [0, 1])
    with pytest.raises(ValueError):
        nlp_dataset._partition_sha256(["a"], [])
