import pytest

from src.evaluation.metrics import compute_classification_metrics


def test_metrics_use_phishing_as_positive_and_probability_for_auc():
    result = compute_classification_metrics([0, 0, 1, 1], [0, 1, 0, 1], [0.1, 0.8, 0.3, 0.9])
    assert result["confusion_matrix"] == [[1, 1], [1, 1]]
    assert result["accuracy"] == pytest.approx(0.5)
    assert result["precision"] == pytest.approx(0.5)
    assert result["recall"] == pytest.approx(0.5)
    assert result["f1"] == pytest.approx(0.5)
    assert result["roc_auc"] == pytest.approx(0.75)  # hard labels would give 0.5


def test_no_positive_predictions_have_explicit_zero_precision_and_f1():
    result = compute_classification_metrics([0, 1], [0, 0], [0.2, 0.2])
    assert result["confusion_matrix"] == [[1, 0], [1, 0]]
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0
    assert result["roc_auc"] == pytest.approx(0.5)
