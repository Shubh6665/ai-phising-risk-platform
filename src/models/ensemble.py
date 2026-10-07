"""Ensemble risk scoring logic. Combines ML, NLP, and rules into a deterministic risk assessment."""

from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass(frozen=True)
class RiskAssessment:
    """The final deterministic output of the combined ensemble."""
    risk_score: float
    classification: str
    rule_bonus: float


def calculate_rule_bonus(rule_signals: Dict[str, bool]) -> float:
    """Return the plan-defined share of the 20-point deterministic rule bonus."""
    max_rules = len(rule_signals)
    if max_rules == 0:
        return 0.0
    active_rules = sum(1 for value in rule_signals.values() if value)
    return active_rules * (0.2 * 100 / max_rules)

def compute_risk_score(
    ml_probability: float,
    nlp_probability: float,
    rule_signals: Dict[str, bool],
) -> RiskAssessment:
    """Combine ML and NLP probabilities with deterministic rule signals.

    Risk score is an application-level score (0-100), NOT a calibrated probability.

    This preserves the conceptual formula currently printed in implementation_plan.md.
    That plan labels its weights and thresholds illustrative pending validation;
    this function must not be described as having experimentally validated them.
    """
    if not (0.0 <= ml_probability <= 1.0) or not (0.0 <= nlp_probability <= 1.0):
        raise ValueError("Probabilities must be strictly between 0.0 and 1.0")

    # Formula retained from the plan's conceptual example; it is not a claim of
    # experimentally tuned or validated weights.
    ml_weight = 0.4
    nlp_weight = 0.4
    rule_weight = 0.2

    # Calculate base score from statistical models
    base_score = (ml_probability * ml_weight + nlp_probability * nlp_weight) * 100

    # Calculate deterministic bonus from active rules
    rule_bonus = calculate_rule_bonus(rule_signals)

    risk_score = min(base_score + rule_bonus, 100.0)

    # Thresholds retained from the plan's conceptual example.
    if risk_score >= 80:
        classification = "Critical"
    elif risk_score >= 60:
        classification = "High"
    elif risk_score >= 40:
        classification = "Medium"
    else:
        classification = "Low"

    return RiskAssessment(
        risk_score=risk_score,
        classification=classification,
        rule_bonus=rule_bonus,
    )
