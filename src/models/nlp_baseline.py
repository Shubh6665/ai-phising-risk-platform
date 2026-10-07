"""Phase 4 Step 1: cleaned email text → train-fitted TF-IDF → LR."""

from collections.abc import Sequence

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


class EmailTextInput(TransformerMixin, BaseEstimator):
    """Flat string sequences validate karo; metadata DataFrame ko text mat samjho.

    Cleaning already Phase 2 mein hoti hai. Yeh stateless guard text change nahi
    karta; pandas Series caller explicitly .tolist() se pass kare.
    """

    def fit(self, texts: Sequence[str], y=None):
        self.transform(texts)
        return self

    def transform(self, texts: Sequence[str]) -> Sequence[str]:
        if isinstance(texts, (str, bytes)) or not isinstance(texts, (list, tuple)):
            raise TypeError("Cleaned email strings ki flat list/tuple expected hai")
        if not all(isinstance(text, str) for text in texts):
            raise TypeError("Har email string honi chahiye; missing/non-text values allowed nahi")
        return texts


def create_nlp_baseline() -> Pipeline:
    """Unfitted text-only pipeline; caller fit sirf original training split par kare.

    Validation/test inference fitted vocabulary/IDF reuse karti hai. Lowercasing
    vectorizer-specific hai; Phase 2 text aur handcrafted features unchanged hain.
    """
    return Pipeline([
        ("text_input", EmailTextInput()),
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            analyzer="word",
            ngram_range=(1, 2),
            min_df=2,
            max_df=1.0,
            max_features=None,
            stop_words=None,
            token_pattern=r"(?u)\b\w\w+\b",
            norm="l2",
            use_idf=True,
            smooth_idf=True,
            sublinear_tf=False,
            dtype=np.float64,
        )),
        ("classifier", LogisticRegression(
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            tol=1e-4,
            fit_intercept=True,
            class_weight=None,
            random_state=42,
        )),
    ])
