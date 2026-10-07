"""Freeze selection from recorded evidence, refit development data, test once.

Run once: .venv/bin/python -m scripts.finalize_classical_ml
An existing artifact or final report blocks accidental repeat test evaluation.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.data.loader import load_raw_emails
from src.data.preprocessor import preprocess_emails
from src.data.splitter import split_emails
from src.evaluation.class_weight_experiment import create_class_weight_variants
from src.evaluation.metrics import compute_classification_metrics
from src.evaluation.model_selection import SELECTION_RULE, select_classical_model
from src.features.feature_pipeline import extract_features
from src.models.registry import DEFAULT_MODEL_PATH, PROJECT_ROOT, load_model, save_model

EVIDENCE_PATH = PROJECT_ROOT / "docs/classical_ml_development.json"
REPORT_PATH = DEFAULT_MODEL_PATH.with_name("classical_model_final_evaluation.json")


def finalize_classical_ml(
    evidence_path: Path = EVIDENCE_PATH,
    artifact_path: Path = DEFAULT_MODEL_PATH,
    report_path: Path = REPORT_PATH,
) -> dict:
    """Test is accessed only after frozen selection, refit and development round-trip check.

    If a run fails, the reserved report is intentionally retained. Investigate its
    state before doing anything else; never delete it just to rerun test evaluation.
    """
    evidence = json.loads(evidence_path.read_text())
    selected = select_classical_model(evidence["validation_metrics"])
    if artifact_path.exists() or report_path.exists():
        raise FileExistsError("Final artifact/report already exists; do not repeat held-out evaluation")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x") as stream:
        json.dump({"status": "reserved", "selected_model": selected, "selection_rule": SELECTION_RULE}, stream)

    splits = split_emails(preprocess_emails(load_raw_emails()))
    development = pd.concat([splits.train, splits.validation], ignore_index=True)
    X_development = extract_features(development)
    y_development = development["label"].tolist()
    model = create_class_weight_variants()[selected]
    model.fit(X_development, y_development)
    classifier = model.named_steps["classifier"] if isinstance(model, Pipeline) else model
    configuration = classifier.get_params()
    artifact = save_model(model, artifact_path, metadata={
        "selected_model": selected,
        "configuration": configuration,
        "selection_rule": SELECTION_RULE,
        "development_rows": len(development),
        "split_seed": 42,
        "development_evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
    })
    loaded = load_model(artifact_path)
    probe = X_development.iloc[:128]
    np.testing.assert_array_equal(artifact.predict(probe), loaded.predict(probe))
    np.testing.assert_array_equal(artifact.predict_proba(probe), loaded.predict_proba(probe))

    # First test access: configuration is frozen, refitted, saved and checked.
    X_test = extract_features(splits.test)
    y_test = splits.test["label"].tolist()
    predictions = loaded.predict(X_test)
    probabilities = loaded.predict_proba(X_test)
    positive_index = loaded.metadata["classes"].index(1)
    final_metrics = compute_classification_metrics(
        y_test, predictions.tolist(), probabilities[:, positive_index].tolist()
    )
    report = {
        "status": "complete",
        "selected_model": selected,
        "selection_rule": SELECTION_RULE,
        "configuration": configuration,
        "artifact_metadata": loaded.metadata,
        "development_rows": len(development),
        "development_label_counts": development["label"].value_counts().sort_index().to_dict(),
        "test_rows": len(X_test),
        "test_label_counts": splits.test["label"].value_counts().sort_index().to_dict(),
        "feature_names": list(loaded.feature_names),
        "validation_metrics_before_refit": evidence["validation_metrics"][selected],
        "training_only_cv_before_refit": evidence["training_only_cv"][selected],
        "final_test_metrics": final_metrics,
        "test_evaluation_count": 1,
        "round_trip_check": {"rows": len(probe), "partition": "development", "exact_predictions": True, "exact_probabilities": True},
        "artifact_path": str(artifact_path.relative_to(PROJECT_ROOT)) if artifact_path.is_relative_to(PROJECT_ROOT) else str(artifact_path),
        "artifact_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    print(json.dumps(finalize_classical_ml(), indent=2))


if __name__ == "__main__":
    main()
