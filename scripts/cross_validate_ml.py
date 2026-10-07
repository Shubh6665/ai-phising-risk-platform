"""Phase 3 Step 3: compare model stability within the training split only.

Run: .venv/bin/python -m scripts.cross_validate_ml
No held-out validation/test features, parameter search or artifact saving.
"""

import json

import sklearn

from src.data.loader import load_raw_emails
from src.data.preprocessor import preprocess_emails
from src.data.splitter import split_emails
from src.evaluation.cross_validation import evaluate_cross_validation
from src.features.feature_pipeline import FEATURE_NAMES, extract_features
from src.models.baseline import create_baseline
from src.models.classifier import create_classifier


def main() -> None:
    splits = split_emails(preprocess_emails(load_raw_emails()))
    X_train = extract_features(splits.train)
    y_train = splits.train["label"].tolist()
    assert tuple(X_train.columns) == FEATURE_NAMES
    results = {}
    for name, model in (("logistic_regression", create_baseline()), ("random_forest", create_classifier())):
        print(f"Running {name}: five training-only folds", flush=True)
        results[name] = evaluate_cross_validation(model, X_train, y_train)

    print(json.dumps(
        {
            "sklearn_version": sklearn.__version__,
            "training_rows": len(X_train),
            "training_label_counts": splits.train["label"].value_counts().sort_index().to_dict(),
            "feature_columns": list(X_train.columns),
            "cv_config": {
                "splitter": "StratifiedKFold", "n_splits": 5,
                "shuffle": True, "random_state": 42, "n_jobs": 1, "std_ddof": 0,
            },
            "results": results,
            "held_out_validation_features_extracted": False,
            "held_out_test_features_extracted": False,
            "artifact_saved": False,
        }, indent=2
    ))


if __name__ == "__main__":
    main()
