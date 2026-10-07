"""Trusted-local persistence of fitted classical models and their feature contract."""

import hashlib
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted

from src.features.feature_pipeline import FEATURE_NAMES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "model_artifacts/ml/classical_model.joblib"
FEATURE_CONTRACT = "phase2-cleaned-subject-body-ten-numeric-features-v1"


def _feature_code_fingerprints() -> dict[str, str]:
    paths = (
        "src/data/loader.py", "src/data/preprocessor.py",
        "src/features/feature_pipeline.py", "src/features/text_features.py",
        "src/features/url_features.py",
    )
    return {path: hashlib.sha256((PROJECT_ROOT / path).read_bytes()).hexdigest() for path in paths}


@dataclass
class ClassicalModelArtifact:
    """Consumes Phase 2 numeric features, not raw emails. Includes an LR scaler if present."""

    estimator: Pipeline | RandomForestClassifier
    feature_names: tuple[str, ...]
    metadata: dict[str, Any]

    def _validate_features(self, features: pd.DataFrame) -> None:
        if tuple(features.columns) != self.feature_names:
            raise ValueError("Feature names/order must match the saved feature contract exactly")
        if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in features.dtypes):
            raise ValueError("Expected numeric features")
        if not np.isfinite(features.to_numpy(dtype=float)).all():
            raise ValueError("Features must be finite without missing values")

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        self._validate_features(features)
        return np.asarray(self.estimator.predict(features))

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        """Columns follow the class mapping stored in metadata, normally [0, 1]."""
        self._validate_features(features)
        return np.asarray(self.estimator.predict_proba(features))


def save_model(
    estimator: Pipeline | RandomForestClassifier,
    path: Path = DEFAULT_MODEL_PATH,
    *,
    metadata: dict[str, Any] | None = None,
) -> ClassicalModelArtifact:
    """Save a fitted estimator without overwriting an existing artifact."""
    check_is_fitted(estimator)
    if tuple(cast(Any, estimator).feature_names_in_) != FEATURE_NAMES:
        raise ValueError("Estimator must be fitted on the ten ordered Phase 2 features")
    artifact = ClassicalModelArtifact(
        estimator=estimator,
        feature_names=FEATURE_NAMES,
        metadata={
            **(metadata or {}),
            "schema_version": 1,
            "feature_contract": FEATURE_CONTRACT,
            "feature_code_sha256": _feature_code_fingerprints(),
            "python_version": platform.python_version(),
            "sklearn_version": sklearn.__version__,
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "joblib_version": joblib.__version__,
            "classes": np.asarray(estimator.classes_).tolist(),
        },
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        joblib.dump(artifact, stream, compress=3)
    return artifact


def load_model(path: Path = DEFAULT_MODEL_PATH) -> ClassicalModelArtifact:
    """Load ONLY trusted files: joblib can execute code before these checks run.

    Keep the same Phase 2 cleaning/extraction code and recorded runtime environment.
    This loader rejects incompatible sklearn versions rather than hiding warnings.
    """
    artifact = joblib.load(path)
    if not isinstance(artifact, ClassicalModelArtifact):
        raise TypeError("Expected a classical model artifact")
    if artifact.metadata.get("schema_version") != 1:
        raise ValueError("Unsupported artifact schema")
    if artifact.metadata.get("sklearn_version") != sklearn.__version__:
        raise ValueError("Artifact requires its recorded scikit-learn version")
    if artifact.metadata.get("feature_contract") != FEATURE_CONTRACT or artifact.feature_names != FEATURE_NAMES:
        raise ValueError("Artifact feature contract differs from the current Phase 2 contract")
    if artifact.metadata.get("feature_code_sha256") != _feature_code_fingerprints():
        raise ValueError("Cleaning/extraction code differs from the saved feature contract")
    check_is_fitted(artifact.estimator)
    if tuple(cast(Any, artifact.estimator).feature_names_in_) != artifact.feature_names:
        raise ValueError("Estimator feature order differs from saved metadata")
    if np.asarray(artifact.estimator.classes_).tolist() != artifact.metadata.get("classes"):
        raise ValueError("Estimator class mapping differs from saved metadata")
    return artifact
