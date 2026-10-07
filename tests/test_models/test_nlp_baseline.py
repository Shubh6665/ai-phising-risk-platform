import json

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse
from sklearn.feature_extraction.text import TfidfVectorizer

from src.models.nlp_baseline import create_nlp_baseline


@pytest.fixture
def training_data():
    texts = [
        "Team meeting agenda project", "Team meeting schedule project",
        "Team project notes meeting", "Team meeting agenda notes",
        "URGENT verify account password", "urgent verify account suspended",
        "verify account password urgent", "urgent account verify password",
    ]
    return texts, [0, 0, 0, 0, 1, 1, 1, 1]


def test_initial_configuration_is_untuned_and_has_no_scaler():
    model = create_nlp_baseline()
    assert list(model.named_steps) == ["text_input", "tfidf", "classifier"]
    vectorizer = model.named_steps["tfidf"]
    assert vectorizer.ngram_range == (1, 2)
    assert vectorizer.min_df == 2 and vectorizer.max_df == 1.0
    assert vectorizer.max_features is None and vectorizer.stop_words is None
    assert vectorizer.lowercase and vectorizer.norm == "l2" and vectorizer.smooth_idf
    assert vectorizer.use_idf and not vectorizer.sublinear_tf
    classifier = model.named_steps["classifier"]
    assert classifier.C == 1.0 and classifier.solver == "lbfgs"
    assert classifier.max_iter == 1000 and classifier.tol == 1e-4
    assert classifier.fit_intercept and classifier.class_weight is None
    assert classifier.random_state == 42


def test_train_fit_builds_ordered_sparse_vocabulary_and_preserves_input(training_data):
    texts, labels = training_data
    before = texts.copy()
    model = create_nlp_baseline().fit(texts, labels)
    vectorizer = model.named_steps["tfidf"]
    matrix = model[:-1].transform(texts)
    assert issparse(matrix)
    assert matrix.shape == (8, len(vectorizer.vocabulary_))
    assert matrix.dtype == np.float64
    assert "verify account" in vectorizer.vocabulary_
    assert "urgent" in vectorizer.vocabulary_ and "URGENT" not in vectorizer.vocabulary_
    assert "schedule" not in vectorizer.vocabulary_  # min_df=2 excludes singleton.
    for name, position in vectorizer.vocabulary_.items():
        assert vectorizer.get_feature_names_out()[position] == name
    np.testing.assert_allclose(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel(), 1.0)
    assert texts == before


def test_validation_transform_and_predictions_never_refit(training_data, monkeypatch):
    texts, labels = training_data
    fits = []
    original = TfidfVectorizer.fit_transform

    def fit_transform(self, documents, y=None):
        assert documents is texts
        fits.append(True)
        return original(self, documents, y)

    monkeypatch.setattr(TfidfVectorizer, "fit_transform", fit_transform)
    model = create_nlp_baseline().fit(texts, labels)
    vectorizer = model.named_steps["tfidf"]
    vocabulary, idf = vectorizer.vocabulary_.copy(), vectorizer.idf_.copy()
    validation = ["validationonly verify account", "validationonly project meeting"]
    matrix = model[:-1].transform(validation)
    assert issparse(matrix) and matrix.shape[1] == len(vocabulary)
    assert model.predict(validation).shape == (2,)
    probabilities = model.predict_proba(validation)
    assert probabilities.shape == (2, 2)
    assert np.isfinite(probabilities).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0)
    np.testing.assert_array_equal(model.classes_, [0, 1])
    assert vectorizer.vocabulary_ == vocabulary and "validationonly" not in vocabulary
    np.testing.assert_array_equal(vectorizer.idf_, idf)
    assert fits == [True]


def test_reproducibility_and_empty_or_unseen_text(training_data):
    texts, labels = training_data
    first, second = create_nlp_baseline().fit(texts, labels), create_nlp_baseline().fit(texts, labels)
    validation = ["verify account", "project meeting", "", "unknownxyz"]
    assert first.named_steps["tfidf"].vocabulary_ == second.named_steps["tfidf"].vocabulary_
    np.testing.assert_array_equal(first.predict(validation), second.predict(validation))
    np.testing.assert_array_equal(first.predict_proba(validation), second.predict_proba(validation))
    assert first[:-1].transform(validation[2:]).nnz == 0
    assert np.isfinite(first.predict_proba(validation)).all()


@pytest.mark.parametrize("invalid", [
    "single string", [None], [123], [["nested"]],
    {"body": "verify", "label": 1}, pd.DataFrame({"body": ["verify"], "source": ["metadata"]}),
])
def test_rejects_non_text_schema_during_fit_and_inference(invalid, training_data):
    texts, labels = training_data
    with pytest.raises(TypeError):
        create_nlp_baseline().fit(invalid, [1])
    fitted = create_nlp_baseline().fit(texts, labels)
    with pytest.raises(TypeError):
        fitted.predict_proba(invalid)


def test_empty_training_vocabulary_fails_clearly():
    with pytest.raises(ValueError, match="empty vocabulary"):
        create_nlp_baseline().fit(["", ""], [0, 1])


def test_script_uses_original_train_and_validation_only(monkeypatch, capsys):
    from scripts import train_nlp_baseline as script

    train = pd.DataFrame({
        "subject": ["Meeting", "URGENT"] * 4,
        "body": ["team project agenda", "verify account password"] * 4,
        "label": [0, 1] * 4,
        "source": ["source_should_not_be_a_token"] * 8,
    })
    validation = pd.DataFrame({
        "subject": ["Meeting", "URGENT"],
        "body": ["validationonly team", "validationonly verify account"],
        "label": [0, 1],
        "source": ["validation_metadata"] * 2,
    })

    class NoTestAccess:
        @property
        def train(self):
            return train

        @property
        def validation(self):
            return validation

        @property
        def test(self):
            raise AssertionError("Is step mein held-out test access allowed nahi")

    original = TfidfVectorizer.fit_transform
    fits = []

    def fit_transform(self, documents, y=None):
        assert documents == (train["subject"] + "\n\n" + train["body"]).tolist()
        fits.append(True)
        result = original(self, documents, y)
        assert "validationonly" not in self.vocabulary_
        assert "source_should_not_be_a_token" not in self.vocabulary_
        return result

    monkeypatch.setattr(TfidfVectorizer, "fit_transform", fit_transform)
    monkeypatch.setattr(script, "load_raw_emails", lambda: train)
    monkeypatch.setattr(script, "preprocess_emails", lambda data: data)
    monkeypatch.setattr(script, "split_emails", lambda data: NoTestAccess())
    script.main()
    report = json.loads(capsys.readouterr().out)
    assert fits == [True]
    assert report["training_matrix"]["shape"][0] == 8
    assert report["validation_matrix"]["shape"][0] == 2
    assert report["training_matrix"]["sparse"] and report["validation_matrix"]["sparse"]
    assert report["test_split_accessed"] is False and report["artifact_saved"] is False
    assert set(report["comparison"]) == {"lr_unweighted", "rf_unweighted"}
