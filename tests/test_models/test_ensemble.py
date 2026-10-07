import importlib.util
from pathlib import Path

import pytest

from src.models.ensemble import compute_risk_score, RiskAssessment


def _load_evaluator_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "evaluate_ensemble.py"
    spec = importlib.util.spec_from_file_location("evaluate_ensemble", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_compute_risk_score_invalid_probabilities():
    """Probabilities must be within [0.0, 1.0]."""
    with pytest.raises(ValueError):
        compute_risk_score(-0.1, 0.5, {})
    with pytest.raises(ValueError):
        compute_risk_score(0.5, 1.1, {})

def test_compute_risk_score_zero_rules_gives_no_bonus():
    """If no rules exist, base score is ml*40 + nlp*40."""
    result = compute_risk_score(0.5, 0.5, {})
    assert result.risk_score == 40.0
    assert result.classification == "Medium"

def test_compute_risk_score_deterministic_thresholds():
    """Test exact boundaries for risk categories."""
    assert compute_risk_score(0.0, 0.0, {}).classification == "Low"      # 0
    assert compute_risk_score(1.0, 0.0, {}).classification == "Medium"   # 40
    assert compute_risk_score(1.0, 0.5, {}).classification == "High"     # 60
    assert compute_risk_score(1.0, 1.0, {}).classification == "Critical" # 80

def test_compute_risk_score_with_active_rules():
    """Rules should provide proportional bonus."""
    rules = {"has_suspicious_url": True, "urgency_language": False}
    # ml=0, nlp=0 -> base = 0.
    # 1 out of 2 rules -> bonus = 1 * (0.2 * 100 / 2) = 10.0
    result = compute_risk_score(0.0, 0.0, rules)
    assert result.risk_score == 10.0

    rules["urgency_language"] = True
    # 2 out of 2 rules -> bonus = 2 * (0.2 * 100 / 2) = 20.0
    result = compute_risk_score(0.0, 0.0, rules)
    assert result.risk_score == 20.0

def test_compute_risk_score_cap_at_100():
    """Risk score should never exceed 100."""
    rules = {"has_suspicious_url": True, "urgency_language": True}
    # Base score = 80, rule bonus = 20 -> total 100
    assert compute_risk_score(1.0, 1.0, rules).risk_score == 100.0


def test_phase5_evaluator_requires_an_environment_token(monkeypatch):
    evaluator = _load_evaluator_module()
    monkeypatch.setattr(evaluator, "load_dotenv", lambda: False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="HF_TOKEN"):
        evaluator.require_hf_token()


def test_phase5_evaluator_rejects_misaligned_probability_arrays():
    evaluator = _load_evaluator_module()
    row_ids = ["row"] * evaluator.VALIDATION_ROW_COUNT
    with pytest.raises(ValueError, match="both match validation-row count"):
        evaluator.verify_probability_alignment(row_ids, row_ids, row_ids, [0.5] * len(row_ids), [0.5])


def test_phase5_evaluator_rejects_different_model_row_order():
    evaluator = _load_evaluator_module()
    row_ids = [str(index) for index in range(evaluator.VALIDATION_ROW_COUNT)]
    reversed_ids = list(reversed(row_ids))
    probabilities = [0.5] * len(row_ids)
    with pytest.raises(ValueError, match="do not share the validation row order"):
        evaluator.verify_probability_alignment(
            row_ids, row_ids, reversed_ids, probabilities, probabilities
        )
