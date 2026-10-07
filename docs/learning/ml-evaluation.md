# Classical ML and evaluation — Phase 3 Step 1

## Scope and supervised classification

Implemented so far: **one untuned Logistic Regression baseline**, evaluated on validation only.
No Random Forest, ensemble, cross-validation, class-weight comparison, threshold tuning or final
model selection has been implemented. No model artifact has been saved.

Supervised learning uses labeled examples to learn a mapping from features to a target. Our
binary target is `0 = legitimate`, `1 = phishing/spam`. The positive class mixes phishing, spam
and Nigerian-fraud examples; these results must not be described as pure phishing detection.
Each email is represented by the ten deterministic features from Phase 2, not by raw text or
TF-IDF. The `source` column is metadata only and is never a model feature.

## Logistic Regression: intuition and technical view

**Level 1:** The model learns a weight for each feature, adds them together with an intercept,
and converts the score to a number between 0 and 1. Despite its name it is a classifier here.

**Level 2:** Given feature vector x, the model calculates `z = w·x + b`, then
`P(class 1 | x) = sigmoid(z) = 1 / (1 + exp(-z))`. Fitting minimizes logistic loss with L2
regularization. Regularization discourages very large weights; `C` is the inverse of its
strength. A smaller C means stronger regularization. No C search was done in this step.
The decision boundary is linear in the scaled feature space; it cannot automatically model
arbitrary feature interactions like a tree-based model can.

Why it is our baseline: it is simple, fast enough for local CPU training and easy to explain.
It gives an honest measured reference before evaluating a more complex model. Simpler does not
mean good enough for deployment; predictive usefulness must be measured.

## The scikit-learn methods and reusable implementation

`src/models/baseline.py` exposes `create_baseline()`, an **unfitted** `Pipeline` containing
`StandardScaler` followed by `LogisticRegression`.

- `fit(X_train, y_train)`: fits the scaler on training features and trains classifier weights
  on the scaled training features and labels. Only training data may enter this call.
- `predict(X_validation)`: transforms validation features using the *training-fitted* scaler,
  then returns hard labels. We used the classifier's default decision threshold (0.5 probability
  boundary; exact ties resolve to class 0), with no threshold tuning.
- `predict_proba(X_validation)`: transforms without refitting and returns one column per class.
  We locate class 1 in `model.classes_` rather than blindly assuming a column index.

The model's class-1 probability preserves more information than a binary label and can later
be an ensemble input. It is **not** a calibrated confidence guarantee and **not** our eventual
0–100 application risk score. Calibration and ensemble logic were not implemented here.

`src/evaluation/metrics.py` computes metrics without fitting anything. `scripts/train_ml.py` is
only orchestration: load, preprocess, split, feature extraction for train/validation, fit on
train, evaluate validation and print JSON. Reproduce from the repository root:

```bash
.venv/bin/python -m scripts.train_ml
```

No new dependency was needed; pandas, NumPy and scikit-learn were installed in Phase 2.

## Training-only range inspection and scaling decision

Ranges were measured **only on the training features**, before fitting the classifier:

| Feature | Training minimum | Training maximum |
|---|---:|---:|
| `word_count` | 0 | 288,888 |
| `average_word_length` | 0 | 56.509091 |
| `uppercase_ratio` | 0 | 1 |
| `exclamation_count` | 0 | 414 |
| `phishing_keyword_count` | 0 | 1,157 |
| `url_count` | 0 | 467 |
| `https_url_count` | 0 | 137 |
| `max_url_length` | 0 | 1,217 |
| `max_hostname_dot_count` | 0 | 10 |
| `has_ip_address_url` | 0 | 1 |

Word count has median 127 but maximum 288,888, demonstrating a large outlier. Because units and
ranges differ drastically, scaling helps numerical optimization and makes regularization less
dependent on feature units. `StandardScaler` calculates training means and standard deviations
(population variance, ddof=0), then uses `(x - training_mean) / training_std` on every input.
It does **not** clip outliers, make data normally distributed, or remove source shortcuts.
Outliers may still dominate its variance estimates; this is a baseline limitation, not a reason
to redesign Phase 2 or silently fit another transformation on the complete dataset.

## Class balance, configuration and holdout discipline

Training: **27,707 legitimate / 29,867 phishing-spam**, positive share **0.5187584674**.
Validation: **5,937 legitimate / 6,400 phishing-spam**, 12,337 total.
This is near-balanced, so `class_weight=None` is the initial reference. The security objective
may justify weighting positive errors more heavily, but that should be a separate later
validation comparison rather than an unmeasured claim of improvement.

Exact configuration of the measured run:
- Python 3.12.15, scikit-learn 1.9.1.
- Unchanged Phase 2 split: 70/15/15, random seed 42.
- StandardScaler defaults: `with_mean=True`, `with_std=True`.
- Logistic Regression: `C=1.0`, `solver="lbfgs"`, `max_iter=1000`, `tol=0.0001`,
  `fit_intercept=True`, `class_weight=None`, `random_state=42`; other defaults unchanged.
- Effective L2 regularization. On this sklearn version, the default `penalty="deprecated"`
  is an API sentinel, not an absence of regularization; default `l1_ratio=0.0` selects L2.
  We do not explicitly pass the deprecated penalty argument.
- `lbfgs` is a numerical optimizer; `max_iter` is an iteration cap, not a number of epochs.
  This measured fit converged in **19 iterations** with no ConvergenceWarning. The script raises
  on that warning instead of silently accepting a non-converged fit. Random state is specified,
  but lbfgs does not use stochastic shuffling here.

The scaler's measured `n_samples_seen_` was **57,574**, matching training rows. Unit tests check
its learned means against training data and verify that prediction on very different
validation-like data does not change its means, scales or sample count.

Only training data fits anything. Validation is used for this baseline measurement and can
later support comparisons/tuning; it is not used to fit the scaler or classifier. The existing
split function still creates the held-out test partition, but the training script never
extracts its features, predicts on it or evaluates it. The 12,338 test emails remain reserved
for final evaluation. Repeatedly checking test results while choosing models/settings would
turn the test set into tuning data and make the final estimate optimistic.

## Metric definitions (positive = phishing/spam)

Confusion matrix rows are actual class `[0,1]`, columns predicted class `[0,1]`:
`[[TN, FP], [FN, TP]]`.

- **TN:** legitimate and predicted legitimate.
- **FP:** legitimate but flagged as phishing; unnecessary alerts/quarantine can damage trust.
- **FN:** phishing/spam but predicted legitimate; missed threats are a serious security cost.
- **TP:** phishing/spam and correctly flagged.

| Metric | Formula / meaning | Security interpretation |
|---|---|---|
| Accuracy | `(TP+TN)/(TP+TN+FP+FN)` | Overall correctness; can conceal class imbalance or costly misses |
| Precision | `TP/(TP+FP)` | Among flagged emails, how many actually are phishing/spam? |
| Recall | `TP/(TP+FN)` | Among phishing/spam emails, how many did we catch? |
| F1 | `2*precision*recall/(precision+recall)` | Harmonic mean; penalizes a low precision or recall, but gives neither error cost priority |
| ROC-AUC | Area under TPR-vs-FPR curve across thresholds | Ranking discrimination; equivalently probability a random positive receives a higher score than a random negative, with ties half-weighted |

ROC-AUC uses **probabilities**, not hard predictions. It is not accuracy and does not establish
acceptable recall at the default threshold or probability calibration. Metrics explicitly use
class 1 as positive; undefined precision/F1 are assigned 0 if no positives are predicted.

## Actual validation results (one baseline run)

| Metric | Measured value |
|---|---:|
| Accuracy | 0.7186512118 |
| Precision | 0.7277250816 |
| Recall | 0.7312500000 |
| F1 | 0.7294832827 |
| ROC-AUC | 0.7846716566 |

| Actual / predicted | Legitimate (0) | Phishing/spam (1) |
|---|---:|---:|
| Legitimate (0) | **4,186 TN** | **1,751 FP** |
| Phishing/spam (1) | **1,720 FN** | **4,680 TP** |

Interpretation: 4,680 of 6,400 positives were detected, but 1,720 were missed. Of 6,431 flagged
emails, 4,680 were actually positive and 1,751 were legitimate. Both kinds of error are substantial.
This is a real baseline, **not a deployment-ready phishing detector**. ROC-AUC shows useful
ranking signal in this dataset, but it does not prove generalization or justify deployment.
No tuning, Random Forest comparison, cross-validation, final test evaluation or model-selection
claim accompanies these numbers.

## Limitations and interview takeaways

- Features are only ten handcrafted structural/statistical signals; no vocabulary or semantic
  email representation has been trained in this step.
- Source-specific formatting and URL presence may act as shortcuts despite excluding `source`.
  The random stratified split cannot remove that bias. Per-source performance should be checked
  in a later evaluation step; it has not been measured here.
- Exact deduplication does not eliminate near-duplicate templates spanning train/validation.
- Labels mix phishing and spam; the old dataset may not represent modern email traffic.
- Scaling does not correct outliers; L2 regularization does not by itself guarantee generalization.
- This is a single seeded validation measurement, without confidence intervals or repeated folds.
- Class weights and thresholds were not tuned; recall may improve at the cost of more false alarms.
- `zero_division=0` is supported by the runtime API but its inferred type signature in this
  environment incorrectly expects a string. Narrow type-checker annotations preserve the tested
  behavior rather than changing metric semantics to silence the editor.

Questions to be able to answer:
1. Why a linear classifier first? It establishes an interpretable reference for later complexity.
2. How did you prevent scaling leakage? Pipeline fit gets only training rows; prediction only transforms.
3. Why not class-weight immediately? The measured training class balance is near 52/48; weighting
   for security costs is a separate experiment, not a default fix for severe imbalance.
4. Why does AUC need probabilities? It compares rankings across thresholds rather than a single label cut.
5. Why are these not final metrics? They are validation results used during development; test is held out.
