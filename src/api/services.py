"""Service layer for analysis API endpoint."""

import pandas as pd
from typing import Any
import structlog

from src.data.loader import build_email_text
from src.features.feature_pipeline import extract_features
from src.features.text_features import extract_text_features
from src.features.url_features import extract_url_features
from src.models.ensemble import compute_risk_score
from src.models.nlp_classifier import sample_probabilities

logger = structlog.get_logger(__name__)


def extract_rule_signals(email_text: str) -> dict[str, bool]:
    """Replicates Phase 5 rule extraction without duplicating evaluate_ensemble.py."""
    url_features = extract_url_features(email_text)
    text_features = extract_text_features(email_text)
    return {
        "has_suspicious_url": bool(url_features.get("has_ip_address_url", 0)),
        "urgency_language": bool(text_features.get("phishing_keyword_count", 0) > 0),
    }


class AnalysisService:
    def __init__(self, classical_model: Any, nlp_model: Any, nlp_tokenizer: Any):
        self.classical_model = classical_model
        self.nlp_model = nlp_model
        self.nlp_tokenizer = nlp_tokenizer

    def analyze_email(self, request_id: str, text: str, subject: str | None = None) -> dict:
        """Run preprocessing, model inference, and ensemble risk scoring."""
        # 1. Preprocess and combine text
        # DataFrame is needed for feature_pipeline's extract_features which expects 'subject' and 'body'
        df = pd.DataFrame([{"subject": subject or "", "body": text}])
        
        # We need the single combined string for NLP and rules
        # Use pandas Series as expected by build_email_text
        combined_text_series = build_email_text(df["subject"], df["body"])
        combined_text = combined_text_series.iloc[0]
        
        # 2. Extract classical ML features and get Random Forest probability
        features_df = extract_features(df)
        # Class 1 is phishing
        ml_prob = float(self.classical_model.predict_proba(features_df)[0][1])
        
        # 3. Get DistilBERT probability
        # sample_probabilities returns shape (1, 2)
        nlp_probs = sample_probabilities(
            self.nlp_model, 
            self.nlp_tokenizer, 
            [combined_text], 
            max_length=512, 
            batch_size=1
        )
        nlp_prob = float(nlp_probs[0][1])
        
        # 4. Extract rule signals
        rule_signals = extract_rule_signals(combined_text)
        
        # 5. Compute Phase 5 ensemble score
        assessment = compute_risk_score(ml_prob, nlp_prob, rule_signals)
        
        # Log success safely (without full email text)
        logger.info(
            "analysis_completed",
            risk_score=assessment.risk_score,
            classification=assessment.classification,
        )
        
        return {
            "request_id": request_id,
            "risk_score": assessment.risk_score,
            "classification": assessment.classification,
            "ml_probability": ml_prob,
            "nlp_probability": nlp_prob,
            "rule_bonus": assessment.rule_bonus,
        }
