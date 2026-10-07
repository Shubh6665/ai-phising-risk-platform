"""TF-IDF + LR train/validation experiment; test/artifact access nahi.

Run: .venv/bin/python -m scripts.train_nlp_baseline
"""

import json
import warnings
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import sklearn
from scipy.sparse import issparse
from sklearn.exceptions import ConvergenceWarning

from src.data.loader import build_email_text, load_raw_emails
from src.data.preprocessor import preprocess_emails
from src.data.splitter import split_emails
from src.evaluation.metrics import compute_classification_metrics
from src.models.nlp_baseline import create_nlp_baseline

DEVELOPMENT_EVIDENCE_PATH = Path(__file__).resolve().parents[1] / "docs/classical_ml_development.json"


def main() -> None:
    splits = split_emails(preprocess_emails(load_raw_emails()))
    train_text = build_email_text(
        cast(pd.Series, splits.train["subject"]), cast(pd.Series, splits.train["body"])
    ).tolist()
    validation_text = build_email_text(
        cast(pd.Series, splits.validation["subject"]), cast(pd.Series, splits.validation["body"])
    ).tolist()
    train_labels = splits.train["label"].tolist()
    validation_labels = splits.validation["label"].tolist()
    model = create_nlp_baseline()
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(train_text, train_labels)

    vectorizer = model.named_steps["tfidf"]
    classifier = model.named_steps["classifier"]
    # Training representation measure karo, phir memory release karke validation transform karo.
    training_matrix = vectorizer.transform(train_text)
    training_summary = {
        "shape": list(training_matrix.shape), "nnz": int(training_matrix.nnz),
        "dtype": str(training_matrix.dtype), "sparse": bool(issparse(training_matrix)),
    }
    del training_matrix
    validation_matrix = vectorizer.transform(validation_text)
    predictions = np.asarray(classifier.predict(validation_matrix))
    probabilities = np.asarray(classifier.predict_proba(validation_matrix))
    positive_index = list(classifier.classes_).index(1)
    metrics = compute_classification_metrics(
        validation_labels, predictions.tolist(), probabilities[:, positive_index].tolist()
    )
    evidence = json.loads(DEVELOPMENT_EVIDENCE_PATH.read_text())["validation_metrics"]
    comparison = {
        name: {
            "recorded_validation_metrics": evidence[name],
            "tfidf_minus_handcrafted": {
                metric: cast(float, metrics[metric]) - evidence[name][metric]
                for metric in ("accuracy", "precision", "recall", "f1", "roc_auc")
            },
        }
        for name in ("lr_unweighted", "rf_unweighted")
    }
    vectorizer_config = vectorizer.get_params()
    vectorizer_config["dtype"] = np.dtype(vectorizer_config["dtype"]).name
    print(json.dumps({
        "sklearn_version": sklearn.__version__,
        "split_seed": 42,
        "training_rows": len(train_text),
        "validation_rows": len(validation_text),
        "training_label_counts": splits.train["label"].value_counts().sort_index().to_dict(),
        "validation_label_counts": splits.validation["label"].value_counts().sort_index().to_dict(),
        "tfidf_configuration": vectorizer_config,
        "lr_configuration": classifier.get_params(),
        "lr_iterations": classifier.n_iter_.tolist(),
        "vocabulary_size": len(vectorizer.vocabulary_),
        "training_matrix": training_summary,
        "validation_matrix": {
            "shape": list(validation_matrix.shape), "nnz": int(validation_matrix.nnz),
            "dtype": str(validation_matrix.dtype), "sparse": bool(issparse(validation_matrix)),
        },
        "validation_metrics": metrics,
        "comparison": comparison,
        "test_split_accessed": False,
        "artifact_saved": False,
    }, indent=2))


if __name__ == "__main__":
    main()
