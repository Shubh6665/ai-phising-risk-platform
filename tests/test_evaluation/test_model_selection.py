import json
from pathlib import Path

import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from src.evaluation.model_selection import CANDIDATES, select_classical_model


def scores():
    return {name: {"f1": 0.7, "recall": 0.7, "precision": 0.7, "roc_auc": 0.8, "accuracy": 0.99} for name in CANDIDATES}


@pytest.mark.parametrize("winner", CANDIDATES)
def test_selection_is_driven_by_evidence_not_model_name(winner):
    results = scores()
    results[winner]["f1"] = 0.8
    results[winner]["accuracy"] = 0.1
    assert select_classical_model(results) == winner


def test_ties_prioritize_recall_then_auc_then_precision():
    results = scores()
    results["lr_balanced"]["recall"] = 0.8
    assert select_classical_model(results) == "lr_balanced"
    results["rf_balanced"]["recall"] = 0.8
    results["rf_balanced"]["roc_auc"] = 0.9
    assert select_classical_model(results) == "rf_balanced"
    results["rf_unweighted"].update(recall=0.8, roc_auc=0.9, precision=0.9)
    assert select_classical_model(results) == "rf_unweighted"


def test_rejects_missing_candidates_or_invalid_measurements():
    results = scores()
    with pytest.raises(ValueError, match="four"):
        select_classical_model({"rf_unweighted": results["rf_unweighted"]})
    for invalid in (float("nan"), float("inf"), -0.1, 1.1):
        results["lr_unweighted"]["f1"] = invalid
        with pytest.raises(ValueError, match="finite"):
            select_classical_model(results)


def test_recorded_evidence_selects_unweighted_rf():
    root = Path(__file__).resolve().parents[2]
    recorded = json.loads((root / "docs/classical_ml_development.json").read_text())
    assert select_classical_model(recorded["validation_metrics"]) == "rf_unweighted"


def test_finalization_refits_development_then_evaluates_once_and_blocks_repeat(monkeypatch, tmp_path):
    from scripts import finalize_classical_ml as script

    def emails(count):
        return pd.DataFrame({
            "subject": ["Meeting", "URGENT"] * count,
            "body": ["Team notes", "VERIFY account!!! https://example.com/"] * count,
            "label": [0, 1] * count,
            "source": ["synthetic"] * (2 * count),
        })

    train, validation, test = emails(20), emails(4), emails(5)
    state = {"fits": 0, "saved": False, "loaded": False, "evaluations": 0}
    real_fit = RandomForestClassifier.fit
    real_save, real_load, real_metrics = script.save_model, script.load_model, script.compute_classification_metrics

    def fit(self, features, labels, **kwargs):
        assert len(features) == len(train) + len(validation)
        assert labels == train["label"].tolist() + validation["label"].tolist()
        assert self.class_weight is None and self.n_estimators == 200 and self.max_depth == 12
        state["fits"] += 1
        return real_fit(self, features, labels, **kwargs)

    def save(*args, **kwargs):
        result = real_save(*args, **kwargs)
        state["saved"] = True
        return result

    def load(*args, **kwargs):
        result = real_load(*args, **kwargs)
        state["loaded"] = True
        return result

    def metrics(*args):
        state["evaluations"] += 1
        return real_metrics(*args)

    class GuardedSplits:
        @property
        def train(self):
            return train

        @property
        def validation(self):
            return validation

        @property
        def test(self):
            assert state["fits"] == 1 and state["saved"] and state["loaded"]
            return test

    monkeypatch.setattr(RandomForestClassifier, "fit", fit)
    monkeypatch.setattr(script, "load_raw_emails", lambda: train)
    monkeypatch.setattr(script, "preprocess_emails", lambda value: value)
    monkeypatch.setattr(script, "split_emails", lambda value: GuardedSplits())
    monkeypatch.setattr(script, "save_model", save)
    monkeypatch.setattr(script, "load_model", load)
    monkeypatch.setattr(script, "compute_classification_metrics", metrics)
    artifact_path, report_path = tmp_path / "model.joblib", tmp_path / "report.json"
    report = script.finalize_classical_ml(artifact_path=artifact_path, report_path=report_path)
    assert report["test_evaluation_count"] == state["evaluations"] == 1
    assert report["development_rows"] == 48 and report["test_rows"] == 10
    assert report["round_trip_check"]["exact_probabilities"] is True
    assert json.loads(report_path.read_text())["status"] == "complete"
    with pytest.raises(FileExistsError, match="do not repeat"):
        script.finalize_classical_ml(artifact_path=artifact_path, report_path=report_path)
    assert state["fits"] == state["evaluations"] == 1
