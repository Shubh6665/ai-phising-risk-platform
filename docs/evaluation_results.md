# Classical ML evaluation results — Phase 3

These are measured results, not estimates. Positive class **1** combines phishing/spam;
class **0** is legitimate. See [learning notes](learning/ml-evaluation.md) for full methodology,
all experiments, per-fold CV scores, feature importance and limitations.

## Data and evaluation boundaries

Six per-source CSVs: **82,486 raw rows**, **82,249 after deterministic cleaning/exact deduplication**.
Seed-42 stratified split: **57,574 train / 12,337 validation / 12,338 test** (70/15/15).
Ten deterministic features; no `source`, `label`, sender/receiver/date or precomputed URL features.

- Validation selected the model using existing experiments.
- Training-only five-fold stratified CV measured stability, not final test performance.
- A fresh selected estimator was fitted on **69,911 train+validation rows**.
- The selected estimator was evaluated **once** on the held-out test, after selection/refitting.
- No test-driven tuning, new search, CV rerun, weighting rerun, NLP or ensemble work.

## Development validation results (before final refit)

| Candidate | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| LR None | 0.718651212 | 0.727725082 | 0.731250000 | 0.729483283 | 0.784671657 |
| LR balanced | 0.708356975 | 0.743991641 | 0.667500000 | 0.703673200 | 0.783113946 |
| RF None | 0.864796952 | 0.903341289 | 0.827968750 | 0.864014349 | 0.941323559 |
| RF balanced | 0.864715895 | 0.906233900 | 0.824531250 | 0.863454144 | 0.940899786 |

Selection rule: highest validation **F1**, exact ties **recall → ROC-AUC → precision → ascending
candidate name**. Accuracy does not rank candidates. **Unweighted RF selected**: highest F1,
stronger recall/F1/AUC than weighted RF, and stronger precision/recall/F1/AUC than LR.
Balancing produced 408 extra misses for LR and 22 for RF, while reducing alarms by 281 and 21.
Keep `class_weight=None`. This is a project policy, not a measured universal cost optimum.
Recorded development evidence: [`classical_ml_development.json`](classical_ml_development.json).

## Training-only CV stability (unweighted baselines, before refit)

Five stratified shuffled folds, seed 42, SD `ddof=0`. Weighted variants were not cross-validated.

| Metric | LR mean ± SD | RF mean ± SD |
|---|---:|---:|
| Accuracy | 0.7187099079 ± 0.0031381334 | 0.8687601938 ± 0.0018449263 |
| Precision | 0.7265830496 ± 0.0036320090 | 0.9072753762 ± 0.0026204631 |
| Recall | 0.7339871627 ± 0.0045912485 | 0.8320554536 ± 0.0023652752 |
| F1 | 0.7302560221 ± 0.0030774985 | 0.8680357341 ± 0.0018515066 |
| ROC-AUC | 0.7841766771 ± 0.0013744862 | 0.9425990056 ± 0.0013890773 |

These SDs are neither confidence intervals nor proof of real-world robustness.

## Selected model and local artifact

RandomForestClassifier: `n_estimators=200`, `criterion="gini"`, `max_depth=12`,
`min_samples_leaf=5`, `min_samples_split=2`, `max_features="sqrt"`, `bootstrap=True`,
`class_weight=None`, `random_state=42`, `n_jobs=1`; other defaults unchanged. No scaler.
Refit labels: **33,644 legitimate / 36,267 phishing-spam**.

Artifact: `model_artifacts/ml/classical_model.joblib` (gitignored).
Run report: `model_artifacts/ml/classical_model_final_evaluation.json` (gitignored).
Artifact SHA-256: `0fe95d47acb45a4caab6d600d6266b27efb44746e61e61e6a8e738337e9ffcc0`.

Saved fitted estimator, ordered feature schema, class mapping, configuration, runtime versions,
and feature-code hashes. Predictions and probabilities matched **exactly** before/after loading
on **128 development rows**. Only trusted artifacts may be loaded: joblib unpickling can execute
code. Keep matching code/environment; the model consumes Phase 2 numeric matrices, not raw emails.
Python 3.12.15; sklearn 1.9.1; NumPy 2.5.3; pandas 3.0.6; joblib 1.6.0.

## ONE final held-out test result

Command executed once: `.venv/bin/python -m scripts.finalize_classical_ml`.
An existing final artifact/report prevents accidental rerun; no test-driven change followed.
Test: **12,338 rows**, **5,938 legitimate / 6,400 phishing-spam**.

| Metric | Final test |
|---|---:|
| Accuracy | 0.8674015237477711 |
| Precision | 0.9067622950819673 |
| Recall | 0.8296875 |
| F1 | 0.866514360313316 |
| ROC-AUC | 0.9416939494568879 |

Confusion matrix: `[[5392, 546], [1090, 5310]]`, ordered `[[TN, FP], [FN, TP]]`.
**546 false alarms; 1,090 missed positives** (17.03125% of actual positives).

Test results are close to the earlier validation results, but different data and refitting prevent
attributing small differences to an improvement. The saved model trained on validation rows:
its subsequent validation predictions are not independent development-evaluation evidence.

## Limitations

Random partitions can share source-format/style shortcuts and near-duplicate templates. Excluding
`source` does not remove source effects; exact deduplication does not remove near-duplicates.
Labels mix phishing/spam/fraud, data are historical, and no source-disjoint/temporal evaluation,
calibration, security cost study or live deployment validation occurred. This result is **not
evidence of production-level generalization**. The final test must not be recycled for future tuning.
