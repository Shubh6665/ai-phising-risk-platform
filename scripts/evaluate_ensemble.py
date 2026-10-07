"""Genuine Phase 5 evaluation on the reconstructed Phase 2 validation split.

This script has no synthetic-prediction fallback. It writes a report only after
the pinned private DistilBERT artifact returns real probabilities for every row.
"""

import hashlib
import json
import os
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch
import transformers
from dotenv import load_dotenv
from torch.utils.data import DataLoader, Dataset

from src.data.loader import DEFAULT_RAW_DIR, build_email_text, load_raw_emails
from src.data.preprocessor import preprocess_emails
from src.data.splitter import split_emails
from src.evaluation.metrics import compute_classification_metrics
from src.features.feature_pipeline import extract_features
from src.features.text_features import extract_text_features
from src.features.url_features import extract_url_features
from src.models.ensemble import compute_risk_score
from src.models.registry import DEFAULT_MODEL_PATH, load_model

HF_REPOSITORY = "shubhsingh0700/phishing-risk-distilbert"
HF_REVISION = "0fa035f65ea98c94a33f24778c210695636efddd"
HF_TOKEN_ENVIRONMENT_VARIABLE = "HF_TOKEN"
VALIDATION_ROW_COUNT = 12_337
MAX_LENGTH = 512


class IndexedTextDataset(Dataset[tuple[int, str]]):
    def __init__(self, texts: Sequence[str]) -> None:
        self.texts = list(texts)

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, index: int) -> tuple[int, str]:
        return index, self.texts[index]


def require_hf_token() -> str:
    """Return a process-only Hub token, or fail before evaluation begins."""
    # The project keeps local secrets in ignored .env files.  Existing exported
    # environment values win because load_dotenv does not override by default.
    load_dotenv()
    token = os.environ.get(HF_TOKEN_ENVIRONMENT_VARIABLE)
    if not token and os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
        try:
            from kaggle_secrets import UserSecretsClient
        except ImportError as error:
            raise RuntimeError("Kaggle Secrets is unavailable in this Kaggle runtime") from error
        token = UserSecretsClient().get_secret(HF_TOKEN_ENVIRONMENT_VARIABLE)
    if not token:
        raise RuntimeError(
            "Cannot run genuine Phase 5 evaluation: the pinned private Hugging Face "
            f"model requires {HF_TOKEN_ENVIRONMENT_VARIABLE} in the process environment. "
            "Provide a read token outside this repository; do not put it in source, docs, "
            "Git, or command history."
        )
    return token


def validation_row_ids(texts: Sequence[str]) -> list[str]:
    """Create non-reversible IDs that make the shared inference order auditable."""
    return [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in texts]


def verify_probability_alignment(
    expected_row_ids: Sequence[str],
    ml_row_ids: Sequence[str],
    nlp_row_ids: Sequence[str],
    ml_probabilities: Sequence[float],
    nlp_probabilities: Sequence[float],
) -> None:
    """Fail closed unless both model arrays cover the exact validation rows."""
    expected_length = len(expected_row_ids)
    if expected_length != VALIDATION_ROW_COUNT:
        raise ValueError(
            f"Expected {VALIDATION_ROW_COUNT} Phase 2 validation rows, got {expected_length}"
        )
    if len(ml_probabilities) != expected_length or len(nlp_probabilities) != expected_length:
        raise ValueError("ML and NLP probability arrays must both match validation-row count")
    if list(ml_row_ids) != list(expected_row_ids) or list(nlp_row_ids) != list(expected_row_ids):
        raise ValueError("ML and NLP probability arrays do not share the validation row order")
    for name, probabilities in (("ML", ml_probabilities), ("NLP", nlp_probabilities)):
        values = np.asarray(probabilities, dtype=float)
        if not np.isfinite(values).all() or not ((0.0 <= values) & (values <= 1.0)).all():
            raise ValueError(f"{name} probabilities must be finite values in [0, 1]")


def predict_distilbert_probabilities(texts: Sequence[str], token: str) -> tuple[list[str], list[float]]:
    """Use dynamic padding, right truncation, max_length=512, and input order."""
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        HF_REPOSITORY, revision=HF_REVISION, token=token
    )
    tokenizer.truncation_side = "right"
    model = transformers.AutoModelForSequenceClassification.from_pretrained(
        HF_REPOSITORY, revision=HF_REVISION, token=token
    )
    model.eval()
    row_ids = validation_row_ids(texts)
    predicted_row_ids: list[str] = []
    probabilities: list[float] = []
    for indices, batch in DataLoader(IndexedTextDataset(texts), batch_size=64, shuffle=False):
        with torch.no_grad():
            inputs = tokenizer(
                list(batch), padding=True, truncation=True, max_length=MAX_LENGTH,
                return_tensors="pt",
            )
            probabilities.extend(torch.softmax(model(**inputs).logits, dim=1)[:, 1].tolist())
        predicted_row_ids.extend(row_ids[int(index)] for index in indices.tolist())
    return predicted_row_ids, probabilities


def extract_rule_signals(email_text: str) -> dict[str, bool]:
    url_features = extract_url_features(email_text)
    text_features = extract_text_features(email_text)
    return {
        "has_suspicious_url": bool(url_features.get("has_ip_address_url", 0)),
        "urgency_language": bool(text_features.get("phishing_keyword_count", 0) > 0),
    }


def parse_arguments() -> Namespace:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-data-dir", type=Path, default=Path(os.environ.get("PHISHING_RAW_DATA_DIR", DEFAULT_RAW_DIR)),
        help="Directory containing the six Phase 2 raw CSV files; attach it as a Kaggle Input.",
    )
    parser.add_argument(
        "--classical-model-path", type=Path,
        default=Path(os.environ.get("PHISHING_CLASSICAL_MODEL_PATH", DEFAULT_MODEL_PATH)),
        help="Trusted saved Random Forest joblib artifact; attach it as a separate Kaggle Input.",
    )
    parser.add_argument(
        "--report-path", type=Path,
        default=Path(os.environ.get("PHASE5_REPORT_PATH", "docs/ensemble-step5-report.json")),
        help="New report location; an existing report is never overwritten.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    token = require_hf_token()
    if arguments.report_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {arguments.report_path}")
    splits = split_emails(preprocess_emails(load_raw_emails(arguments.raw_data_dir)), random_state=42)
    validation = splits.validation
    texts = build_email_text(validation["subject"], validation["body"]).tolist()
    labels = validation["label"].tolist()
    row_ids = validation_row_ids(texts)

    random_forest = load_model(arguments.classical_model_path)
    ml_probabilities = random_forest.predict_proba(extract_features(validation))[:, 1].tolist()
    nlp_row_ids, nlp_probabilities = predict_distilbert_probabilities(texts, token)
    verify_probability_alignment(row_ids, row_ids, nlp_row_ids, ml_probabilities, nlp_probabilities)

    risk_scores: list[float] = []
    classifications: list[str] = []
    categories = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    samples: list[dict[str, Any]] = []
    sample_indices = {0, len(texts) // 4, len(texts) // 2, 3 * len(texts) // 4, len(texts) - 1}
    for index, (ml_probability, nlp_probability, text) in enumerate(
        zip(ml_probabilities, nlp_probabilities, texts, strict=True)
    ):
        rules = extract_rule_signals(text)
        assessment = compute_risk_score(ml_probability, nlp_probability, rules)
        risk_scores.append(assessment.risk_score)
        classifications.append(assessment.classification)
        categories[assessment.classification] += 1
        if index in sample_indices:
            samples.append({
                "validation_row_index": index,
                "row_id_sha256": row_ids[index],
                "random_forest_probability": round(ml_probability, 6),
                "distilbert_probability": round(nlp_probability, 6),
                "rule_signals": rules,
                "rule_bonus": round(assessment.rule_bonus, 2),
                "risk_score": round(assessment.risk_score, 2),
                "category": assessment.classification,
            })

    predictions = [0 if category == "Low" else 1 for category in classifications]
    report = {
        "evaluation_scope": "Phase 2 validation split only; held-out test split not accessed",
        "test_evaluated": False,
        "validation_rows": len(validation),
        "split_seed": 42,
        "probability_alignment": {
            "verified": True,
            "row_count": len(row_ids),
            "row_order": "shared validation order; transformer DataLoader shuffle=False",
        },
        "model_inputs": {
            "classical": {"kind": "saved Random Forest artifact", "path": str(arguments.classical_model_path)},
            "nlp": {"repository": HF_REPOSITORY, "revision": HF_REVISION},
            "tfidf": "not an ensemble input under implementation_plan.md",
        },
        "ensemble_formula": "(ml_probability * 0.4 + nlp_probability * 0.4) * 100 + rule_bonus; capped at 100",
        "thresholds": {"Low": "< 40", "Medium": ">= 40", "High": ">= 60", "Critical": ">= 80"},
        "ensemble_metrics": compute_classification_metrics(labels, predictions, [score / 100 for score in risk_scores]),
        "risk_category_distribution": categories,
        "risk_score_stats": {"min": min(risk_scores), "max": max(risk_scores), "mean": float(np.mean(risk_scores))},
        "sample_cases": samples,
    }
    arguments.report_path.parent.mkdir(parents=True, exist_ok=True)
    arguments.report_path.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Phase 5 report: {arguments.report_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
