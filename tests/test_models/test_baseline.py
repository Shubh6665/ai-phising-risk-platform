import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError

from src.features.feature_pipeline import extract_features
from src.models.baseline import create_baseline


@pytest.fixture
def training_data():
    emails = pd.DataFrame(
        {
            "subject": ["Meeting", "Lunch", "Notes", "Hello", "URGENT", "Verify", "Account", "Click"],
            "body": [
                "See you tomorrow", "How about lunch", "The report is ready", "Thanks for your help",
                "CLICK!!! http://192.0.2.1/login", "verify account now!!!",
                "account suspended! http://example.org/reset", "URGENT verify account!",
            ],
        }
    )
    return extract_features(emails), np.array([0, 0, 0, 0, 1, 1, 1, 1])


def test_baseline_configuration_and_unfitted_state(training_data):
    model = create_baseline()
    classifier = model.named_steps["classifier"]
    assert classifier.C == 1.0
    assert classifier.solver == "lbfgs"
    assert classifier.max_iter == 1000
    assert classifier.class_weight is None
    with pytest.raises(NotFittedError):
        model.predict(training_data[0])


def test_scaler_fits_only_training_and_predict_never_refits(training_data):
    X_train, y_train = training_data
    model = create_baseline().fit(X_train, y_train)
    scaler = model.named_steps["scaler"]
    np.testing.assert_allclose(scaler.mean_, X_train.mean().to_numpy())
    assert scaler.n_samples_seen_ == len(X_train)
    mean_before, scale_before = scaler.mean_.copy(), scaler.scale_.copy()
    validation = X_train.iloc[[0]].copy()
    validation["word_count"] = 1_000_000  # conspicuously unlike the training distribution
    model.predict(validation)
    model.predict_proba(validation)
    np.testing.assert_array_equal(scaler.mean_, mean_before)
    np.testing.assert_array_equal(scaler.scale_, scale_before)
    assert scaler.n_samples_seen_ == len(X_train)


def test_predict_returns_labels_and_normalized_probabilities(training_data):
    X_train, y_train = training_data
    model = create_baseline().fit(X_train, y_train)
    predictions = model.predict(X_train)
    probabilities = model.predict_proba(X_train)
    assert predictions.shape == (len(X_train),)
    assert set(predictions).issubset({0, 1})
    np.testing.assert_array_equal(model.classes_, [0, 1])
    assert probabilities.shape == (len(X_train), 2)
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0)


def test_prediction_requires_the_same_feature_order(training_data):
    X_train, y_train = training_data
    model = create_baseline().fit(X_train, y_train)
    with pytest.raises(ValueError, match="feature names"):
        model.predict(X_train[list(reversed(X_train.columns))])
