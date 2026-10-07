import joblib
import numpy as np
import pandas as pd
import pytest
import sklearn
from sklearn.exceptions import NotFittedError
from sklearn.pipeline import Pipeline

from src.features.feature_pipeline import FEATURE_NAMES, extract_features
from src.models.baseline import create_baseline
from src.models.classifier import create_classifier
from src.models.registry import load_model, save_model


@pytest.fixture
def features():
    return extract_features(pd.DataFrame({
        "subject": ["Meeting", "URGENT"] * 12,
        "body": ["Team notes ready", "VERIFY account!!! http://192.0.2.1/"] * 12,
    }))


@pytest.mark.parametrize("factory", [create_baseline, create_classifier])
def test_round_trip_preserves_fitted_model_predictions_probabilities_and_order(factory, features, tmp_path):
    model = factory().fit(features, [0, 1] * 12)
    path = tmp_path / "ml" / "model.joblib"
    original = save_model(model, path, metadata={"configuration": "synthetic-test"})
    loaded = load_model(path)
    assert loaded.feature_names == FEATURE_NAMES
    assert loaded.metadata["classes"] == [0, 1]
    assert loaded.metadata["configuration"] == "synthetic-test"
    np.testing.assert_array_equal(loaded.predict(features), model.predict(features))
    np.testing.assert_array_equal(loaded.predict_proba(features), model.predict_proba(features))
    assert loaded.estimator.get_params().keys() == original.estimator.get_params().keys()
    if isinstance(model, Pipeline):
        assert isinstance(loaded.estimator, Pipeline)
        np.testing.assert_array_equal(loaded.estimator.named_steps["scaler"].mean_, model.named_steps["scaler"].mean_)
    with pytest.raises(FileExistsError):
        save_model(model, path)
    with pytest.raises(ValueError, match="names/order"):
        loaded.predict(features.loc[:, list(reversed(FEATURE_NAMES))])
    with pytest.raises(ValueError, match="names/order"):
        loaded.predict_proba(features.assign(source="metadata"))
    with pytest.raises(ValueError, match="finite"):
        loaded.predict(features.assign(word_count=np.nan))
    with pytest.raises(ValueError, match="numeric"):
        loaded.predict(features.assign(word_count="wrong"))


def test_rejects_unfitted_or_wrong_feature_schema(features, tmp_path):
    path = tmp_path / "model.joblib"
    with pytest.raises(NotFittedError):
        save_model(create_classifier(), path)
    model = create_classifier().fit(features.assign(source=0), [0, 1] * 12)
    with pytest.raises(ValueError, match="ten ordered"):
        save_model(model, path)
    assert not path.exists()


def test_rejects_incompatible_metadata(features, tmp_path):
    path = tmp_path / "model.joblib"
    model = create_classifier().fit(features, [0, 1] * 12)
    artifact = save_model(model, path)
    artifact.metadata["sklearn_version"] = "incompatible"
    joblib.dump(artifact, path)
    with pytest.raises(ValueError, match="scikit-learn version"):
        load_model(path)
    artifact.metadata["sklearn_version"] = sklearn.__version__
    original_fingerprints = artifact.metadata["feature_code_sha256"]
    artifact.metadata["feature_code_sha256"] = {}
    joblib.dump(artifact, path)
    with pytest.raises(ValueError, match="Cleaning/extraction code"):
        load_model(path)
    artifact.metadata["feature_code_sha256"] = original_fingerprints
    artifact.metadata["classes"] = [1, 0]
    joblib.dump(artifact, path)
    with pytest.raises(ValueError, match="class mapping"):
        load_model(path)
    artifact.metadata["classes"] = [0, 1]
    artifact.feature_names = tuple(reversed(FEATURE_NAMES))
    joblib.dump(artifact, path)
    with pytest.raises(ValueError, match="feature contract"):
        load_model(path)
