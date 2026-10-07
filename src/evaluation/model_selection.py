"""Select from recorded validation evidence, without fitting or test access."""

from collections.abc import Mapping
from math import isfinite

CANDIDATES = ("lr_unweighted", "lr_balanced", "rf_unweighted", "rf_balanced")
SELECTION_METRICS = ("f1", "recall", "roc_auc", "precision")
SELECTION_RULE = "Highest validation F1; exact ties: recall, ROC-AUC, precision, then name."


def select_classical_model(results: Mapping[str, Mapping[str, float]]) -> str:
    """Accuracy is not ranked; CV is supporting stability evidence, not a score."""
    if set(results) != set(CANDIDATES):
        raise ValueError("Expected the four previously measured classical candidates")
    for metrics in results.values():
        for name in SELECTION_METRICS:
            value = metrics.get(name)
            if value is None or not isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"Expected a finite {name} in [0, 1]")
    # Sorting gives an alphabetical tie-break when all ranked metrics are identical.
    return max(sorted(results), key=lambda name: tuple(results[name][m] for m in SELECTION_METRICS))
