"""Initial Random Forest on the existing ten deterministic email features."""

from sklearn.ensemble import RandomForestClassifier


def create_classifier() -> RandomForestClassifier:
    """Return an unfitted, reproducible forest; fit on training data only.

    Limits are an initial complexity budget, not validation-selected settings.
    Trees use feature ordering rather than distance, so scaling is not required.
    """
    return RandomForestClassifier(
        n_estimators=200,
        criterion="gini",
        max_depth=12,
        min_samples_split=2,
        min_samples_leaf=5,
        max_features="sqrt",
        bootstrap=True,
        class_weight=None,
        random_state=42,
        n_jobs=1,
    )
