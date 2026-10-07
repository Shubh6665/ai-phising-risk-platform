import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError

from src.features.feature_pipeline import FEATURE_NAMES, extract_features
from src.models.classifier import create_classifier


@pytest.fixture(scope="module")
def training_data():
    emails = pd.DataFrame(
        {
            "subject": [f"Meeting {i}" for i in range(20)] + [f"URGENT {i}" for i in range(20)],
            "body": ["The team report is ready" for _ in range(20)]
            + ["VERIFY account!!! http://192.0.2.1/login" for _ in range(20)],
        }
    )
    return extract_features(emails), np.array([0] * 20 + [1] * 20)


@pytest.fixture(scope="module")
def fitted_classifier(training_data):
    X_train, y_train = training_data
    return create_classifier().fit(X_train, y_train)


def test_initial_configuration_and_unfitted_state(training_data):
    model = create_classifier()
    assert model.n_estimators == 200
    assert model.max_depth == 12
    assert model.min_samples_leaf == 5
    assert model.max_features == "sqrt"
    assert model.bootstrap is True
    assert model.random_state == 42
    assert model.class_weight is None
    assert model.n_jobs == 1
    with pytest.raises(NotFittedError):
        model.predict(training_data[0])


def test_prediction_and_importance_match_feature_schema(training_data, fitted_classifier):
    X_train, _ = training_data
    model = fitted_classifier
    predictions = model.predict(X_train)
    probabilities = model.predict_proba(X_train)
    assert predictions.shape == (len(X_train),)
    assert set(predictions).issubset({0, 1})
    np.testing.assert_array_equal(model.classes_, [0, 1])
    np.testing.assert_array_equal(model.feature_names_in_, FEATURE_NAMES)
    assert probabilities.shape == (len(X_train), 2)
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0)
    assert model.feature_importances_.shape == (len(FEATURE_NAMES),)
    assert (model.feature_importances_ >= 0).all()
    assert model.feature_importances_.sum() == pytest.approx(1.0)
    assert all(tree.get_depth() <= 12 for tree in model.estimators_)


def test_same_seed_reproduces_predictions_and_importances(training_data, fitted_classifier):
    X_train, y_train = training_data
    another = create_classifier().fit(X_train, y_train)
    np.testing.assert_array_equal(
        another.predict_proba(X_train), fitted_classifier.predict_proba(X_train)
    )
    np.testing.assert_array_equal(another.feature_importances_, fitted_classifier.feature_importances_)


def test_prediction_does_not_refit_trees(training_data, fitted_classifier):
    X_train, _ = training_data
    nodes = [tree.tree_.node_count for tree in fitted_classifier.estimators_]
    importance = fitted_classifier.feature_importances_.copy()
    validation = X_train.iloc[[0]].copy()
    validation["word_count"] = 1_000_000
    fitted_classifier.predict(validation)
    fitted_classifier.predict_proba(validation)
    assert nodes == [tree.tree_.node_count for tree in fitted_classifier.estimators_]
    np.testing.assert_array_equal(importance, fitted_classifier.feature_importances_)


def test_feature_order_is_enforced(training_data, fitted_classifier):
    X_train, _ = training_data
    with pytest.raises(ValueError, match="feature names"):
        fitted_classifier.predict(X_train[list(reversed(X_train.columns))])
