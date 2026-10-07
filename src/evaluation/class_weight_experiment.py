"""Controlled None-vs-balanced comparisons on supplied train/validation data."""

import warnings
from collections.abc import Sequence
from typing import cast

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.pipeline import Pipeline
from sklearn.utils.class_weight import compute_class_weight

from src.evaluation.metrics import compute_classification_metrics
from src.features.feature_pipeline import FEATURE_NAMES
from src.models.baseline import create_baseline
from src.models.classifier import create_classifier

DELTA_METRICS = ("accuracy", "precision", "recall", "f1", "roc_auc")


def create_class_weight_variants() -> dict[str, Pipeline | RandomForestClassifier]:
    """Create separate unfitted variants; the baseline factories are unchanged."""
    lr = create_baseline()
    rf = create_classifier()
    return {
        "lr_unweighted": lr,
        "lr_balanced": cast(Pipeline, clone(lr)).set_params(classifier__class_weight="balanced"),
        "rf_unweighted": rf,
        "rf_balanced": cast(RandomForestClassifier, clone(rf)).set_params(class_weight="balanced"),
    }


def run_class_weight_experiment(
    X_train: pd.DataFrame,
    y_train: Sequence[int],
    X_validation: pd.DataFrame,
    y_validation: Sequence[int],
) -> dict:
    """Fit four controlled variants on train only and report validation metrics.

    No dataset loader, held-out test access, threshold choice, CV or serialization
    is performed here. Returns measurements/configuration, not fitted estimators.
    """
    if tuple(X_train.columns) != FEATURE_NAMES or tuple(X_validation.columns) != FEATURE_NAMES:
        raise ValueError("Expected only the ten Phase 2 features in their fixed order")
    if len(X_train) != len(y_train) or len(X_validation) != len(y_validation):
        raise ValueError("Features and labels must have matching row counts")

    class_weights = compute_class_weight(
        class_weight="balanced", classes=np.array([0, 1]), y=np.asarray(y_train)
    )
    results = {}
    for name, model in create_class_weight_variants().items():
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model.fit(X_train, y_train)
        predictions = np.asarray(model.predict(X_validation), dtype=np.int64)
        probabilities = np.asarray(model.predict_proba(X_validation), dtype=np.float64)
        positive_index = list(model.classes_).index(1)
        assert predictions.shape == (len(y_validation),)
        classifier = model.named_steps["classifier"] if isinstance(model, Pipeline) else model
        results[name] = {
            "configuration": classifier.get_params(),
            "metrics": compute_classification_metrics(
                y_validation, cast(list[int], predictions.tolist()),
                probabilities[:, positive_index].tolist(),
            ),
        }

    deltas = {}
    for family in ("lr", "rf"):
        original = results[f"{family}_unweighted"]["metrics"]
        weighted = results[f"{family}_balanced"]["metrics"]
        deltas[family] = {
            metric: cast(float, weighted[metric]) - cast(float, original[metric])
            for metric in DELTA_METRICS
        }
    return {
        "balanced_class_weights_from_training": {
            "0": float(class_weights[0]), "1": float(class_weights[1])
        },
        "variants": results,
        "balanced_minus_unweighted": deltas,
    }
