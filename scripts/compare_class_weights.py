"""Phase 3 Step 4: controlled class-weight comparisons, validation only.

Run: .venv/bin/python -m scripts.compare_class_weights
No held-out test features, CV rerun, threshold tuning or model artifacts.
"""

import json

import sklearn

from src.data.loader import load_raw_emails
from src.data.preprocessor import preprocess_emails
from src.data.splitter import split_emails
from src.evaluation.class_weight_experiment import run_class_weight_experiment
from src.features.feature_pipeline import extract_features


def main() -> None:
    splits = split_emails(preprocess_emails(load_raw_emails()))
    X_train = extract_features(splits.train)
    X_validation = extract_features(splits.validation)
    results = run_class_weight_experiment(
        X_train, splits.train["label"].tolist(),
        X_validation, splits.validation["label"].tolist(),
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
            "experiment": results,
            "held_out_test_features_extracted": False,
            "artifact_saved": False,
        }, indent=2
    ))


if __name__ == "__main__":
    main()
