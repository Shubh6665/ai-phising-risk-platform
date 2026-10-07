# Learning Notes: Ensemble and Risk Scoring

## Phase 5 status

The initial Phase 5 report was invalid because it substituted a noisy copy of
the Random Forest probabilities when the private DistilBERT artifact could not
be accessed. It was removed and its metrics must not be cited. No genuine
ensemble validation metrics are recorded until the pinned private Hugging Face
model can be loaded and every model input is real.

`scripts/evaluate_ensemble.py` now fails closed unless the process has an
`HF_TOKEN` environment variable with read access to
`shubhsingh0700/phishing-risk-distilbert` revision
`0fa035f65ea98c94a33f24778c210695636efddd`. The token is never stored in the
tracked repository, documentation, or command history. The project's ignored
`.env` mechanism may supply it to the evaluation process.

For Kaggle, attach the six raw CSVs and trusted `classical_model.joblib` as
separate private Inputs. Run `scripts/evaluate_ensemble.py` with
`--raw-data-dir`, `--classical-model-path`, and a new writable `--report-path`.
The evaluator may obtain `HF_TOKEN` from Kaggle Secrets. It never substitutes
predictions, never accesses `splits.test`, and refuses to overwrite a report.

## GPU inference placement

`model.eval()` changes dropout/batch-normalization behavior, but it does not
move model weights to a GPU. The Phase 5 evaluator explicitly selects
`torch.device("cuda" if torch.cuda.is_available() else "cpu")`, calls
`model.to(device)`, and moves each tokenized batch to that same device before
calling the model. On a Kaggle GPU session it prints CUDA availability, the
selected device, actual model-parameter device, and GPU name, then fails if
the model is not on CUDA. Batch size defaults to 8 and is configurable via
`--inference-batch-size`; dynamic padding limits each batch to its longest
email rather than always allocating 512 tokens.

## Why Ensemble Models Are Useful
In earlier phases, we trained classical ML models (Random Forest) that leverage explicit linguistic and structural features, as well as an NLP transformer (DistilBERT) that captures deep contextual relationships in the raw text. Ensembles are powerful because they combine multiple diverse models to produce a result that is typically more robust and accurate than any single constituent model. By bringing together the orthogonal signals (structured metadata vs. unstructured context), the ensemble mitigates individual model blindspots.

## Probability-Level Combination vs. Metric-Level Comparison
Metric-level comparison (e.g., comparing F1 or Accuracy between models) simply tells us which model performs best globally on a test dataset. However, it doesn't give us a way to utilize the strengths of all models simultaneously on a *per-email* basis.

Probability-level combination actually takes the continuous prediction outputs (probabilities) of multiple models for a specific instance, scales them by given weights, and fuses them into a single score. This means if the NLP model is slightly uncertain (e.g., 0.6 probability) but the classical ML model sees clear structural indicators of phishing (e.g., 0.9 probability), their combination yields a stronger aggregate signal than choosing just one model beforehand.

## How Weighted Averaging Works
Weighted averaging applies a specific fractional multiplier to each model's output before summing them. The conceptual example in `implementation_plan.md` uses:
- **ML Probability Weight:** 0.4
- **NLP Probability Weight:** 0.4
- **Rule Bonus Weight:** 0.2

For a given email, the base score is `(ML_prob * 0.4 + NLP_prob * 0.4) * 100`. This scales the 0.0-1.0 probability range up to a 0-80 range. The remaining 20 points are reserved for a deterministic "rule bonus" derived from hardcoded rules (e.g., detecting an IP address as a URL or finding urgency language).

## Why the Application Risk Score is Separated from Probability
A raw machine learning probability is a mathematical construct optimizing log-loss or cross-entropy during training. It is often uncalibrated and lacks intuitive meaning for end users.
We derive an **Application Risk Score (0-100)** to abstract away the underlying statistical artifacts. This score is a UX decision:
- It makes the system's output interpretable.
- It seamlessly incorporates non-probabilistic signals (like rule-based bonuses).
- **Importantly, we do not claim this score is a calibrated probability.** Without formal calibration (e.g., Platt scaling, Isotonic Regression), calling it a probability would be statistically misleading.

## How Deterministic Thresholds Work
We convert the 0-100 risk score into a discrete categorical label using deterministic thresholds. The thresholds enforce strict, auditable cutoffs:
- **Critical:** Score $\geq$ 80
- **High:** Score $\geq$ 60
- **Medium:** Score $\geq$ 40
- **Low:** Score $<$ 40

Deterministic thresholds ensure stable escalation routing and policy enforcement later in the application.

## Validation Evaluation and Leakage Checks
The eventual ensemble evaluation is restricted to the Phase 2 `validation` split.
- **Validation Evaluation:** All model hyperparameters (and ensemble logic) must be tuned against a dataset distinct from the test set to avoid over-optimistic generalization estimates. The final `test` set remains held-out.
- **Leakage Prevention:** Just like in prior phases, any feature extractor must only be fitted on the `training` set. The validation pipeline transforms the validation data strictly using those pre-fit artifacts. For the ensemble, it is crucial that the same validation examples are fed to both models in identical deterministic order to ensure the combined probabilities correspond to the same underlying email.

## Current limitation

The plan calls its formula illustrative and says weights and thresholds should
be determined after individual-model validation. This project retains the shown
formula without calling it experimentally validated. No Phase 6 work starts
from this correction.

## Phase 5 measured validation result

The real Kaggle run completed on the Phase 2 seed-42 validation partition only:
**12,337 rows**, `test_evaluated=false`. The immutable measurement artifact is
[`docs/ensemble-step5-report.json`](../ensemble-step5-report.json). It recorded
Tesla T4 / `cuda:0` DistilBERT inference, the saved Random Forest artifact, the
pinned private model revision, `max_length=512`, right truncation, dynamic
padding, `shuffle=False`, and batch size 8. It also verified that the Random
Forest and DistilBERT probability arrays both had 12,337 values in identical
validation-row order and were all in `[0, 1]`.

| Metric | Measured ensemble validation value |
|---|---:|
| Accuracy | 0.9928669854908 |
| Precision | 0.9900621118012423 |
| Recall | 0.99625 |
| F1 | 0.9931464174454828 |
| ROC-AUC | 0.9984230777328617 |

Confusion matrix order is `[[TN, FP], [FN, TP]]`: `[[5873, 64], [24, 6376]]`.
Risk categories were Low 5,897; Medium 1,020; High 4,123; Critical 1,297. Risk
score minimum/mean/maximum were 0.21780749035699695, 43.38746897382866, and
97.67155129224194. These are validation observations, not production claims.

## Interview explanation: what is actually fused

An ensemble must combine **per-row probabilities**, not the aggregate accuracy
or F1 values of its component models. Accuracy and F1 each summarize an entire
dataset after a thresholding decision; averaging them would neither create a
prediction for one email nor have a valid probabilistic meaning. Here each email
instead contributes its Random Forest and DistilBERT phishing probabilities:

```text
base_score = (ml_probability * 0.4 + nlp_probability * 0.4) * 100
rule_bonus = active_rules * (0.2 * 100 / max_rules)
risk_score = min(base_score + rule_bonus, 100)
```

The two current deterministic rules are `has_suspicious_url` and
`urgency_language`; so each active rule contributes 10 points and both consume
the full 20-point bonus. The mapping is Low `<40`, Medium `>=40`, High `>=60`,
and Critical `>=80`. This makes the result explainable and stable, but the
0–100 score is an application risk score—not a calibrated chance of phishing.

## Alignment and leakage lesson

The model arrays can be combined only when entry `i` from each model refers to
the same email. The evaluator therefore reconstructs the deterministic Phase 2
validation split, derives stable row IDs from its combined email text, keeps the
transformer `DataLoader` at `shuffle=False`, and rejects unequal row order,
length, non-finite values, or probabilities outside `[0,1]`. The test split is
not read. This protects the aggregation from row-mismatch bugs; it does not
remove the existing broader limitations of random-split source/template
shortcuts or 512-token right truncation, which can discard late email content.

## What the result does and does not show

The ensemble need not beat DistilBERT on every metric to be useful: it gives a
deterministic risk construction that exposes both learned and rule signals.
Validation performance does not establish real-world phishing generalization.
The historical mixed labels, possible near-duplicate templates, source style,
lack of source-disjoint/temporal evaluation, and truncation limitation remain
important interview caveats.
