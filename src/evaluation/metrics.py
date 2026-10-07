"""Binary phishing metrics; positive class is label 1 (phishing/spam)."""

from collections.abc import Sequence

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_classification_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    phishing_probabilities: Sequence[float],
) -> dict[str, float | list[list[int]]]:
    """Compute metrics without fitting anything.

    Matrix order is [[TN, FP], [FN, TP]]. ROC-AUC uses class-1 probabilities,
    not thresholded labels, and requires both classes in y_true. Precision/F1
    are defined as zero if the model never predicts a positive class.
    """
    # The runtime API accepts zero_division=0; inferred types in this installed
    # sklearn release incorrectly narrow the parameter to its string default.
    return {
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),  # type: ignore[arg-type]
        "recall": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),  # type: ignore[arg-type]
        "f1": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),  # type: ignore[arg-type]
        "roc_auc": float(roc_auc_score(y_true, phishing_probabilities)),
    }
