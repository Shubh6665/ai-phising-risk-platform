# Model evaluation results — Phase 3 + Phase 4 Step 1

Yeh actual measured results hain, estimates nahi. Positive class **1** phishing/spam mix hai;
class **0** legitimate hai. Neeche original Phase 3 sections historical records hain; last
section Phase 4 Step 1 ka validation-only NLP experiment hai. Classical methodology ke liye
[ML learning notes](learning/ml-evaluation.md), aur text baseline ke liye
[NLP learning notes](learning/nlp-transformers.md) dekho.

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

## Phase 4 Step 1 — TF-IDF + LR, validation-only NLP baseline

Existing Phase 2 cleaning/dedup/split unchanged hai. Training **57,574**, validation **12,337**;
input existing `subject + "\n\n" + body` representation hai. `source`/`label` text features nahi.
**NLP Step 1 mein test split access/evaluate nahi hua.** Phase 3 ka final test result is comparison
mein use nahi kiya, aur selected classical artifact unchanged hai.

### Fixed initial configuration aur actual matrix sizes

TF-IDF: word unigrams+bigrams `(1, 2)`, `lowercase=True`, `min_df=2`, `max_df=1.0`,
`max_features=None`, `stop_words=None`, default two-or-more-character Unicode token pattern,
raw TF (`binary=False`, `sublinear_tf=False`), smoothed IDF, L2 normalization, `float64`.
Vocabulary/IDF sirf train par fit; validation sirf transformed. No additional scaler.

LR: `C=1.0`, `solver="lbfgs"`, `max_iter=1000`, `tol=1e-4`, `fit_intercept=True`,
`class_weight=None`, `random_state=42`, effective L2; remaining defaults unchanged.
Python 3.12.15, sklearn 1.9.1. LR **18 iterations** mein converge hua. No tuning/weight experiment.

- Vocabulary: **1,064,372** terms.
- Training sparse matrix: **`(57574, 1064372)`**, **16,962,766** nonzero entries.
- Validation sparse matrix: **`(12337, 1064372)`**, **3,478,829** nonzero entries.
- Dono matrices `float64`, sparse; dense conversion nahi hui.
- No NLP model artifact save/commit hua.

Command: `.venv/bin/python -m scripts.train_nlp_baseline`.
Measured run mein numerical-library thread counts one rakhe to avoid oversubscription;
exact environment-prefixed command NLP learning notes mein recorded hai.

### Actual validation results

| Metric | TF-IDF + LR validation |
|---|---:|
| Accuracy | 0.9850855151171274 |
| Precision | 0.9844139650872819 |
| Recall | 0.986875 |
| F1 | 0.9856429463171036 |
| ROC-AUC | 0.9987274717870978 |

Confusion matrix `[[TN, FP], [FN, TP]]`: **`[[5837, 100], [84, 6316]]`**.
**100 false alarms, 84 missed phishing/spam examples**.

### Separate same-validation comparison — Phase 3 train-only baselines

Historical unweighted LR/RF measurements reuse kiye, rerun nahi. Final saved RF use nahi kiya:
woh validation par bhi refitted hai, so independent validation comparison ke liye unsuitable hai.

| Representation/model | Accuracy | Precision | Recall | F1 | ROC-AUC | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Handcrafted LR | 0.718651212 | 0.727725082 | 0.731250000 | 0.729483283 | 0.784671657 | 1,751 | 1,720 |
| Handcrafted RF | 0.864796952 | 0.903341289 | 0.827968750 | 0.864014349 | 0.941323559 | 567 | 1,101 |
| TF-IDF LR | 0.985085515 | 0.984413965 | 0.986875000 | 0.985642946 | 0.998727472 | 100 | 84 |

TF-IDF-minus-handcrafted deltas, 0–1 metric scale:

| Metric | vs LR | vs RF |
|---|---:|---:|
| Accuracy | +0.266434303 | +0.120288563 |
| Precision | +0.256688883 | +0.081072676 |
| Recall | +0.255625000 | +0.158906250 |
| F1 | +0.256159664 | +0.121628598 |
| ROC-AUC | +0.214055815 | +0.057403913 |

Vs LR **1,651 fewer false alarms / 1,636 fewer misses**; vs RF **467 fewer alarms / 1,017 fewer
misses**. Is validation distribution par lexical text representation help karti hai: all metrics
higher hain, both FP/FN lower hain. Yeh one-metric-only superiority claim nahi hai.

Lekin ten handcrafted columns vs 1,064,372 learned lexical columns **same feature space nahi**;
RF comparison mein model family bhi different hai. Source-style shortcuts, near-duplicate/template
effects, case-normalized text collisions, mixed labels aur historical data high scores ko inflate
kar sakte hain. No source-disjoint/temporal study, calibrated probabilities, NLP CV/test evaluation,
serving benchmark ya production-generalization proof. Existing classical model replace nahi kiya.

## Phase 4 Step 2 — DistilBERT fine-tuning results

Kaggle GPU fine-tuning is now complete. The notebook `notebooks/02_nlp_training.ipynb` was executed with a two-source strategy (project source from GitHub `main`, data from Kaggle Input).

### Actual configuration and token length decision

- **Tokenizer/Truncation**: Pretrained `distilbert-base-uncased` tokenizer. Right truncation, dynamic padding.
- **Max length**: `512` (selected to comfortably fit T4 16GB memory while minimizing truncation).
- **Truncation impact**: Even at 512 tokens, **24.77% of training documents exceed this length and are truncated**. This means a quarter of the emails lose their later tokens (e.g. trailing URLs, signatures).
- **Training**: 3 epochs, learning rate `2e-5`, weight decay `0.01`, batch 8 with gradient accumulation 2 (effective batch 16), seed 42, FP16. Epoch-wise validation and save, best checkpoint by validation F1 restored.

### Actual validation results

| Metric | DistilBERT validation |
|---|---:|
| Accuracy | 0.994731 |
| Precision | 0.994536 |
| Recall | 0.995313 |
| F1 | 0.994924 |
| ROC-AUC | 0.999773 |
| Validation Loss | 0.031694 |
| Training Loss | 0.041000 |

Confusion matrix `[[TN, FP], [FN, TP]]`: **`[[5902, 35], [30, 6370]]`**.
**35 false alarms, 30 missed phishing/spam examples**.

*(Note: Validation loss increased from `0.0254` at Epoch 1 to `0.0317` at Epoch 3, indicating loss overfitting, although validation F1 improved slightly. The best checkpoint by F1 was saved.)*

*(Note: The test set was **NOT** evaluated.)*

### Hugging Face Artifacts

- **Repository**: `shubhsingh0700/phishing-risk-distilbert` (Private)
- **Revision**: `0fa035f65ea98c94a33f24778c210695636efddd`
- **Verification**: Both local reload and Hugging Face reload equivalence tests passed exactly.

### Limitations

- **Truncation**: 24.77% of training documents are truncated, discarding potentially crucial semantic information at the end of long emails.
- **Shortcut Risks**: The high validation scores (F1 ~0.995) must be viewed skeptically. Random splits can share source-specific stylistic shortcuts or near-duplicate templates. This result does not guarantee that the model has learned robust phishing semantics for live production use, and no temporal/source-disjoint evaluation was performed.
- **Scope note**: These are Phase 4 transformer results. Phase 5 ensemble validation is documented separately below; FastAPI, RAG, LangGraph, and held-out test evaluation remain out of scope here.

## Phase 5 — Ensemble and application risk score, validation-only

Measured evidence: [`ensemble-step5-report.json`](ensemble-step5-report.json). This
report is the immutable record for this run; the values below are transcribed from
it, not recomputed. The Kaggle evaluation used a Tesla T4 with DistilBERT on
`cuda:0`, the saved Random Forest artifact, and the pinned private model
`shubhsingh0700/phishing-risk-distilbert` at revision
`0fa035f65ea98c94a33f24778c210695636efddd`.

### Scope and inference contract

- Phase 2 validation partition only: **12,337 rows**, deterministic seed **42**.
- `test_evaluated: false`; the held-out test split was not accessed.
- Real per-row Random Forest and DistilBERT class-1 probabilities were used;
  TF-IDF was not an ensemble input.
- DistilBERT used `max_length=512`, right truncation, dynamic per-batch padding,
  `shuffle=False`, and batch size **8**.
- Probability alignment was verified: both arrays had 12,337 valid probabilities
  in the shared deterministic validation-row order.

### Exact aggregation and categories

```text
base_score = (ml_probability * 0.4 + nlp_probability * 0.4) * 100
rule_bonus = active_rules * (0.2 * 100 / max_rules)
risk_score = min(base_score + rule_bonus, 100)
```

The current deterministic rules are `has_suspicious_url` and `urgency_language`.
With these two rules, each active rule contributes 10 points and both contribute
the maximum 20-point rule bonus. Categories are deterministic: Low `<40`, Medium
`>=40`, High `>=60`, Critical `>=80`.

The resulting 0–100 value is an **application risk score**, not a calibrated
probability. Its scale mixes model outputs and a rule bonus; no probability
calibration was performed.

### Measured validation results

| Metric | Ensemble validation |
|---|---:|
| Accuracy | 0.9928669854908 |
| Precision | 0.9900621118012423 |
| Recall | 0.99625 |
| F1 | 0.9931464174454828 |
| ROC-AUC | 0.9984230777328617 |

Confusion matrix `[[TN, FP], [FN, TP]]`: **`[[5873, 64], [24, 6376]]`**.

| Risk category | Rows |
|---|---:|
| Low | 5,897 |
| Medium | 1,020 |
| High | 4,123 |
| Critical | 1,297 |

| Risk score statistic | Value |
|---|---:|
| Min | 0.21780749035699695 |
| Mean | 43.38746897382866 |
| Max | 97.67155129224194 |

### Interpretation and limits

An ensemble is not required to outperform DistilBERT on every metric. Its purpose
is per-email probability-level fusion with explicit deterministic evidence, not
averaging global model scores. The strong validation values do not prove
real-world phishing generalization: random splits can retain source-specific
formatting or near-duplicate/template shortcuts, labels are historical mixed
phishing/spam/fraud data, and no source-disjoint or temporal validation was run.
Also, 512-token right truncation can discard trailing email context, including
URLs or signatures. The held-out test split remains reserved.
