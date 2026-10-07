"""Classical Logistic Regression baseline on the Phase 2 numerical features."""

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def create_baseline() -> Pipeline:
    """Return an unfitted scaler/classifier pipeline.

    Caller must fit on training features/labels ONLY. During predict/predict_proba,
    the pipeline transforms inputs with the training-fitted scaler, without refitting.
    """
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    solver="lbfgs",
                    max_iter=1000,
                    tol=1e-4,
                    fit_intercept=True,
                    class_weight=None,
                    random_state=42,
                ),
            ),
        ]
    )
