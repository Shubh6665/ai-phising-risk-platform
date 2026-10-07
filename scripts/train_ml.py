"""Reproduce Phase 3 Step 1: fit Logistic Regression and evaluate validation only.

Run from the repo with: .venv/bin/python -m scripts.train_ml
No test features are extracted; no model artifact is saved.
"""

import json
import warnings

import sklearn
from sklearn.exceptions import ConvergenceWarning

from src.data.loader import load_raw_emails
from src.data.preprocessor import preprocess_emails
from src.data.splitter import split_emails
from src.evaluation.metrics import compute_classification_metrics
from src.features.feature_pipeline import extract_features
from src.models.baseline import create_baseline


def main() -> None:
    splits = split_emails(preprocess_emails(load_raw_emails()))
    X_train = extract_features(splits.train)
    X_validation = extract_features(splits.validation)
    y_train = splits.train["label"].tolist()
    y_validation = splits.validation["label"].tolist()

    model = create_baseline()
    # A non-converged fit must be diagnosed, not quietly reported as a valid run.
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(X_train, y_train)

    predictions = model.predict(X_validation)
    positive_index = list(model.classes_).index(1)
    probabilities = model.predict_proba(X_validation)[:, positive_index]
    metrics = compute_classification_metrics(
        y_validation, predictions.tolist(), probabilities.tolist()
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
            "scaler_training_samples": int(model.named_steps["scaler"].n_samples_seen_),
            "classifier_config": model.named_steps["classifier"].get_params(),
            "convergence_iterations": model.named_steps["classifier"].n_iter_.tolist(),
            "validation_metrics": metrics,
            "test_features_extracted": False,
            "artifact_saved": False,
        }, indent=2
    ))


if __name__ == "__main__":
    main()
