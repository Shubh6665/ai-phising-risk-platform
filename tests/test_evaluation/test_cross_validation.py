import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from src.evaluation.cross_validation import CV_METRIC_NAMES, evaluate_cross_validation
from src.features.feature_pipeline import extract_features
from src.models.baseline import create_baseline
from src.models.classifier import create_classifier


@pytest.fixture
def training_data():
    emails = pd.DataFrame(
        {
            "subject": [f"Meeting {i}" if i % 2 == 0 else f"URGENT {i}" for i in range(50)],
            "body": ["Team report ready" if i % 2 == 0 else "VERIFY account!!! http://192.0.2.1/" for i in range(50)],
        }
    )
    return extract_features(emails), [i % 2 for i in range(50)]


@pytest.mark.parametrize("factory", [create_baseline, create_classifier])
def test_five_folds_reproducible_metric_structure_and_summaries(factory, training_data):
    X, y = training_data
    result = evaluate_cross_validation(factory(), X, y)
    repeat = evaluate_cross_validation(factory(), X, y)
    assert result == repeat
    assert set(result) == {"folds", "summary"}
    assert len(result["folds"]) == 5
    for i, fold in enumerate(result["folds"], start=1):
        assert fold["fold"] == i
        assert fold["training_rows"] == 40
        assert fold["fold_validation_rows"] == 10
        assert set(fold) == set(CV_METRIC_NAMES) | {"fold", "training_rows", "fold_validation_rows"}
        assert all(0 <= fold[metric] <= 1 for metric in CV_METRIC_NAMES)
    assert set(result["summary"]) == set(CV_METRIC_NAMES)
    for metric in CV_METRIC_NAMES:
        values = [fold[metric] for fold in result["folds"]]
        assert set(result["summary"][metric]) == {"mean", "std"}
        assert result["summary"][metric]["mean"] == pytest.approx(np.mean(values))
        assert result["summary"][metric]["std"] == pytest.approx(np.std(values, ddof=0))


def test_lr_scaler_is_fitted_independently_inside_each_training_fold(monkeypatch, training_data):
    X, y = training_data
    fit_records = []
    original_fit = StandardScaler.fit

    def record_fit(self, features, labels=None, sample_weight=None):
        output = original_fit(self, features, labels, sample_weight=sample_weight)
        fit_records.append((features.copy(), self.mean_.copy()))
        return output

    monkeypatch.setattr(StandardScaler, "fit", record_fit)
    model = create_baseline()
    evaluate_cross_validation(model, X, y)
    expected_folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(X, y))
    assert len(fit_records) == 5
    for (actual_X, actual_mean), (train_indices, validation_indices) in zip(fit_records, expected_folds):
        expected_X = X.iloc[train_indices]
        pd.testing.assert_frame_equal(actual_X, expected_X)
        np.testing.assert_allclose(actual_mean, expected_X.mean().to_numpy())
        assert set(actual_X.index).isdisjoint(X.iloc[validation_indices].index)
    assert not hasattr(model.named_steps["scaler"], "mean_")  # caller's model stays unfitted


def test_script_never_accesses_held_out_splits(monkeypatch, training_data, capsys):
    from scripts import cross_validate_ml

    X, y = training_data
    train = pd.DataFrame({"subject": ["x"] * 50, "body": ["y"] * 50, "label": y})

    class TrainingOnlySplits:
        @property
        def train(self):
            return train

        @property
        def validation(self):
            raise AssertionError("Held-out validation must not enter CV")

        @property
        def test(self):
            raise AssertionError("Held-out test must not enter CV")

    monkeypatch.setattr(cross_validate_ml, "load_raw_emails", lambda: train)
    monkeypatch.setattr(cross_validate_ml, "preprocess_emails", lambda rows: rows)
    monkeypatch.setattr(cross_validate_ml, "split_emails", lambda rows: TrainingOnlySplits())

    def extract_only_training(rows):
        assert rows is train
        return X

    calls = []

    def evaluate_only_training(model, features, labels):
        assert features is X
        assert labels == y
        calls.append(model)
        return {"folds": [], "summary": {}}

    monkeypatch.setattr(cross_validate_ml, "extract_features", extract_only_training)
    monkeypatch.setattr(cross_validate_ml, "evaluate_cross_validation", evaluate_only_training)
    cross_validate_ml.main()
    assert len(calls) == 2
    assert '"held_out_test_features_extracted": false' in capsys.readouterr().out


def test_cv_rejects_insufficient_class_counts_and_misaligned_rows(training_data):
    X, y = training_data
    with pytest.raises(ValueError, match="equal row counts"):
        evaluate_cross_validation(create_baseline(), X, y[:-1])
    with pytest.raises(ValueError, match="at least five"):
        evaluate_cross_validation(create_baseline(), X.iloc[:8], y[:8])
