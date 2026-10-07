import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.evaluation.class_weight_experiment import (
    DELTA_METRICS,
    create_class_weight_variants,
    run_class_weight_experiment,
)
from src.features.feature_pipeline import extract_features
from src.models.baseline import create_baseline
from src.models.classifier import create_classifier


@pytest.fixture
def experiment_data():
    def emails(labels):
        return pd.DataFrame(
            {
                "subject": ["Meeting" if label == 0 else "URGENT" for label in labels],
                "body": ["Team notes ready" if label == 0 else "VERIFY account!!! http://192.0.2.1/" for label in labels],
                "label": labels,
            }
        )

    y_train = [0] * 24 + [1] * 16
    y_validation = [0, 1] * 4
    return extract_features(emails(y_train)), y_train, extract_features(emails(y_validation)), y_validation


def test_variants_change_only_class_weight_and_leave_factories_unchanged():
    variants = create_class_weight_variants()
    assert set(variants) == {"lr_unweighted", "lr_balanced", "rf_unweighted", "rf_balanced"}
    for family in ("lr", "rf"):
        original = variants[f"{family}_unweighted"]
        balanced = variants[f"{family}_balanced"]
        assert original is not balanced
        if isinstance(original, Pipeline):
            assert isinstance(balanced, Pipeline)
            assert original.named_steps["scaler"] is not balanced.named_steps["scaler"]
            assert original.named_steps["scaler"].get_params() == balanced.named_steps["scaler"].get_params()
            old = original.named_steps["classifier"].get_params()
            new = balanced.named_steps["classifier"].get_params()
        else:
            assert isinstance(balanced, RandomForestClassifier)
            old, new = original.get_params(), balanced.get_params()
        assert {key for key in old if old[key] != new[key]} == {"class_weight"}
        assert old["class_weight"] is None
        assert new["class_weight"] == "balanced"
    assert create_baseline().named_steps["classifier"].class_weight is None
    assert create_classifier().class_weight is None


def test_fits_use_only_training_rows_and_outputs_have_correct_deltas(monkeypatch, experiment_data):
    X_train, y_train, X_validation, y_validation = experiment_data
    before_train, before_validation = X_train.copy(), X_validation.copy()
    fits = []
    scaler_fit = StandardScaler.fit
    forest_fit = RandomForestClassifier.fit

    def fit_scaler(self, features, labels=None, sample_weight=None):
        assert features is X_train
        fits.append("scaler")
        return scaler_fit(self, features, labels, sample_weight=sample_weight)

    def fit_forest(self, features, labels, sample_weight=None):
        assert features is X_train
        assert labels is y_train
        fits.append("forest")
        return forest_fit(self, features, labels, sample_weight=sample_weight)

    monkeypatch.setattr(StandardScaler, "fit", fit_scaler)
    monkeypatch.setattr(RandomForestClassifier, "fit", fit_forest)
    result = run_class_weight_experiment(X_train, y_train, X_validation, y_validation)
    assert fits == ["scaler", "scaler", "forest", "forest"]
    assert result["balanced_class_weights_from_training"] == pytest.approx({"0": 40 / 48, "1": 40 / 32})
    for name, variant in result["variants"].items():
        assert variant["configuration"]["class_weight"] == ("balanced" if name.endswith("balanced") else None)
        metrics = variant["metrics"]
        assert set(metrics) == set(DELTA_METRICS) | {"confusion_matrix"}
        assert sum(map(sum, metrics["confusion_matrix"])) == len(y_validation)
        assert all(np.isfinite(metrics[metric]) and 0 <= metrics[metric] <= 1 for metric in DELTA_METRICS)
    for family in ("lr", "rf"):
        old = result["variants"][f"{family}_unweighted"]["metrics"]
        new = result["variants"][f"{family}_balanced"]["metrics"]
        for metric in DELTA_METRICS:
            assert result["balanced_minus_unweighted"][family][metric] == pytest.approx(new[metric] - old[metric])
    pd.testing.assert_frame_equal(X_train, before_train)
    pd.testing.assert_frame_equal(X_validation, before_validation)


def test_script_does_not_access_test_split(monkeypatch, experiment_data, capsys):
    from scripts import compare_class_weights

    X_train, y_train, X_validation, y_validation = experiment_data
    train = pd.DataFrame({"label": y_train})
    validation = pd.DataFrame({"label": y_validation})

    class NoTestAccess:
        @property
        def train(self):
            return train

        @property
        def validation(self):
            return validation

        @property
        def test(self):
            raise AssertionError("The class-weight experiment must not access test data")

    monkeypatch.setattr(compare_class_weights, "load_raw_emails", lambda: train)
    monkeypatch.setattr(compare_class_weights, "preprocess_emails", lambda data: data)
    monkeypatch.setattr(compare_class_weights, "split_emails", lambda data: NoTestAccess())

    def extract(data):
        if data is train:
            return X_train
        assert data is validation
        return X_validation

    calls = []

    def evaluate(features_train, labels_train, features_validation, labels_validation):
        assert features_train is X_train
        assert features_validation is X_validation
        assert labels_train == y_train
        assert labels_validation == y_validation
        calls.append(True)
        return {}

    monkeypatch.setattr(compare_class_weights, "extract_features", extract)
    monkeypatch.setattr(compare_class_weights, "run_class_weight_experiment", evaluate)
    compare_class_weights.main()
    assert calls == [True]
    assert '"held_out_test_features_extracted": false' in capsys.readouterr().out


def test_rejects_metadata_or_wrong_feature_order(experiment_data):
    X_train, y_train, X_validation, y_validation = experiment_data
    with pytest.raises(ValueError, match="ten Phase 2 features"):
        run_class_weight_experiment(X_train.assign(source="Enron"), y_train, X_validation, y_validation)
    with pytest.raises(ValueError, match="matching row counts"):
        run_class_weight_experiment(X_train, y_train[:-1], X_validation, y_validation)
