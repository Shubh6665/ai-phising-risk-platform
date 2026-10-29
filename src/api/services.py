"""Service layer for analysis API endpoint."""

import pandas as pd
from typing import Any, Callable
import structlog

from src.config import settings
from src.data.loader import build_email_text
from src.features.feature_pipeline import extract_features
from src.features.text_features import extract_text_features
from src.features.url_features import extract_url_features
from src.models.ensemble import compute_risk_score
from src.models.nlp_classifier import sample_probabilities
from src.db.repository import AnalysisRepository, hash_email_text

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
    def __init__(
        self,
        classical_model: Any,
        nlp_model: Any,
        nlp_tokenizer: Any,
        repository: AnalysisRepository | None = None,
        retriever: Callable[[str, int], list[dict[str, Any]]] | None = None,
    ):
        self.classical_model = classical_model
        self.nlp_model = nlp_model
        self.nlp_tokenizer = nlp_tokenizer
        self.repository = repository
        self.retriever = retriever

    def analyze_email(self, request_id: str, text: str, subject: str | None = None) -> dict:
        """Run preprocessing, model inference, ensemble risk scoring, and persistence."""
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

        # 6. Persist result when repository is present
        analysis_id = None
        if self.repository is not None:
            email_hash = hash_email_text(combined_text)
            record = self.repository.save_analysis_result(
                request_id=request_id,
                email_hash=email_hash,
                ml_probability=ml_prob,
                nlp_probability=nlp_prob,
                rule_bonus=assessment.rule_bonus,
                rule_signals=rule_signals,
                risk_score=assessment.risk_score,
                classification=assessment.classification,
            )
            analysis_id = str(record.id)

        # 7. Knowledge-base security evidence retrieval (Phase 7C)
        evidence: list[dict[str, Any]] = []
        evidence_status = "retrieved"

        if self.retriever is not None:
            try:
                raw_hits = self.retriever(combined_text, settings.RAG_TOP_K)
                if not raw_hits:
                    evidence_status = "empty"
                else:
                    evidence = [
                        {
                            "chunk_id": h["id"],
                            "content": h["content"],
                            "similarity": round(max(0.0, min(1.0, float(h.get("similarity", 0.0)))), 4),
                            "document_name": h.get("document_name") or "",
                            "document_title": h.get("document_title"),
                            "heading": h.get("heading"),
                            "document_type": h.get("document_type") or "source_backed_guidance",
                            "source_attribution": h.get("source_attribution") or "",
                            "is_mock": bool(h.get("is_mock", False)),
                        }
                        for h in raw_hits
                    ]
                    evidence_status = "retrieved"
            except Exception as e:
                logger.warning(
                    "rag_retrieval_failed",
                    request_id=request_id,
                    error_type=type(e).__name__,
                )
                evidence = []
                evidence_status = "unavailable"
        else:
            evidence_status = "disabled" if not settings.RAG_ENABLED else "unavailable"
        
        # Log success safely (without full email text, queries, or embeddings)
        logger.info(
            "analysis_completed",
            request_id=request_id,
            analysis_id=analysis_id,
            risk_score=assessment.risk_score,
            classification=assessment.classification,
            evidence_status=evidence_status,
            evidence_count=len(evidence),
        )
        
        return {
            "analysis_id": analysis_id,
            "request_id": request_id,
            "risk_score": assessment.risk_score,
            "classification": assessment.classification,
            "ml_probability": ml_prob,
            "nlp_probability": nlp_prob,
            "rule_bonus": assessment.rule_bonus,
            "evidence": evidence,
            "evidence_status": evidence_status,
        }
