"""Compare initial LR and RF on the exact same train/validation feature matrices.

Run: .venv/bin/python -m scripts.compare_classical_ml
No test features, threshold tuning, weight experiments or artifact serialization.
"""

import json
import warnings
from typing import cast

import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning

from src.data.loader import load_raw_emails
from src.data.preprocessor import preprocess_emails
from src.data.splitter import split_emails
from src.evaluation.metrics import compute_classification_metrics
from src.features.feature_pipeline import FEATURE_NAMES, extract_features
from src.models.baseline import create_baseline
from src.models.classifier import create_classifier


def main() -> None:
    splits = split_emails(preprocess_emails(load_raw_emails()))
    X_train = extract_features(splits.train)
    X_validation = extract_features(splits.validation)
    y_train = splits.train["label"].tolist()
    y_validation = splits.validation["label"].tolist()
    assert tuple(X_train.columns) == tuple(X_validation.columns) == FEATURE_NAMES
    assert "source" not in X_train and "label" not in X_train

    baseline = create_baseline()
    forest = create_classifier()
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        baseline.fit(X_train, y_train)
    forest.fit(X_train, y_train)

    results = {}
    for name, model in (("logistic_regression", baseline), ("random_forest", forest)):
        positive_index = list(model.classes_).index(1)
        predictions = np.asarray(model.predict(X_validation), dtype=np.int64)
        probabilities = np.asarray(model.predict_proba(X_validation), dtype=np.float64)
        assert predictions.shape == (len(y_validation),)
        results[name] = compute_classification_metrics(
            y_validation,
            cast(list[int], predictions.tolist()),
            probabilities[:, positive_index].tolist(),
        )

    importances = sorted(
        zip(X_train.columns, forest.feature_importances_), key=lambda item: item[1], reverse=True
    )
    print(json.dumps(
        {
            "sklearn_version": sklearn.__version__,
            "split_seed": 42,
            "training_rows": len(X_train),
            "validation_rows": len(X_validation),
            "training_label_counts": splits.train["label"].value_counts().sort_index().to_dict(),
            "validation_label_counts": splits.validation["label"].value_counts().sort_index().to_dict(),
            "feature_columns": list(X_train.columns),
            "rf_config": forest.get_params(),
            "lr_config": baseline.named_steps["classifier"].get_params(),
            "validation_metrics": results,
            "rf_feature_importance_mdi": {name: float(value) for name, value in importances},
            "test_features_extracted": False,
            "artifact_saved": False,
        }, indent=2
    ))


if __name__ == "__main__":
    main()
