"""Stratified cross-validation confined to a caller-supplied training split."""

import warnings
from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate

CV_METRIC_NAMES = ("accuracy", "precision", "recall", "f1", "roc_auc")


def evaluate_cross_validation(
    estimator: BaseEstimator,
    X_train: pd.DataFrame,
    y_train: Sequence[int],
) -> dict:
    """Measure a fresh clone of estimator per fold; never pre-fit a transformer.

    This function has no dataset loader or held-out split argument. Pass the
    existing LR pipeline intact so its scaler is fitted only inside each fold.
    The original estimator is not fitted or mutated. Scores are descriptive:
    standard deviation uses ddof=0 over the five fold-validation measurements.
    """
    if len(X_train) != len(y_train):
        raise ValueError("Training features and labels must have equal row counts")
    labels, counts = np.unique(y_train, return_counts=True)
    if not np.array_equal(labels, [0, 1]) or counts.min() < 5:
        raise ValueError("Five-fold CV requires both labels 0/1 with at least five rows each")

    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    fold_indices = list(splitter.split(X_train, y_train))
    scoring = {
        "accuracy": "accuracy",
        "precision": make_scorer(precision_score, pos_label=1, zero_division=0),
        "recall": make_scorer(recall_score, pos_label=1, zero_division=0),
        "f1": make_scorer(f1_score, pos_label=1, zero_division=0),
        "roc_auc": make_scorer(roc_auc_score, response_method="predict_proba"),
    }
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        # sklearn accepts "raise"; inferred typing sees only the float default.
        scores = cross_validate(
            estimator, X_train, y_train, scoring=scoring, cv=fold_indices,
            n_jobs=1, error_score="raise", return_train_score=False,  # type: ignore[arg-type]
        )

    # sklearn calls fold-validation scores "test_*". These are NOT scores on
    # the project's held-out test set; all fold indices come from X_train.
    folds = [
        {
            "fold": i + 1,
            "training_rows": len(train_indices),
            "fold_validation_rows": len(validation_indices),
            **{metric: float(scores[f"test_{metric}"][i]) for metric in CV_METRIC_NAMES},
        }
        for i, (train_indices, validation_indices) in enumerate(fold_indices)
    ]
    summary = {
        metric: {
            "mean": float(np.mean(scores[f"test_{metric}"])),
            "std": float(np.std(scores[f"test_{metric}"], ddof=0)),
        }
        for metric in CV_METRIC_NAMES
    }
    return {"folds": folds, "summary": summary}
