# Classical ML and evaluation — Phase 3 Steps 1–2

## Scope and supervised classification

Implemented so far: **untuned Logistic Regression and Random Forest baselines**, compared on the
same validation set. Step 1's LR implementation is unchanged. No ensemble, cross-validation,
class-weight comparison, threshold tuning or final model selection has been implemented. No
model artifact has been saved; no held-out test features have been extracted.

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
At Step 1 these were baseline-only numbers, without tuning or a model-selection claim. Step 2's
same-validation-set Random Forest comparison is recorded below; no final test evaluation was done.

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

## Step 2 — Random Forest: tree and ensemble intuition

**Level 1:** A decision tree asks questions about an email's features, routing it to a leaf with
class estimates. A forest averages the probabilities from many different trees so the final
answer is not driven by one brittle sequence of questions.

**Level 2:** Training chooses feature thresholds that reduce class impurity. Our forest uses Gini
impurity, `1 - sum(class_fraction²)`. Separate trees can capture conditional interactions and
nonlinear, piecewise decision regions; LR has a linear boundary in the scaled feature space.
scikit-learn's forest averages per-tree class probabilities and predicts the class with the
largest average. This is not necessarily a majority vote over each tree's hard label.

- **Bootstrap sampling:** each tree draws a training sample with replacement. With
  `max_samples=None`, the sample has the same number of draws as the training set, but repeats
  some rows and omits others. Validation/test rows never participate.
- **Random feature selection:** `max_features="sqrt"` considers a random feature subset at
  each split (nominally three of our ten features). It is not one fixed subset per tree.
  This promotes diversity instead of letting all trees use the same strongest splits.
- **Overfitting:** deep trees can memorize small training-specific patterns. Averaging reduces
  variance, but does not prevent learning shortcuts or eliminate near-duplicate leakage.
- **Feature importance:** mean decrease in impurity (MDI) aggregates the weighted training
  impurity reduction attributed to each feature across trees, then normalizes to sum to 1.
  It does **not** prove causality, direction of effect, or held-out usefulness. Continuous/high-
  cardinality features can be favored, and correlated features can share or mask importance.

Why compare against LR? Extra complexity should improve the same measured security-relevant
outcomes, not simply yield a higher training score or accuracy on a different split.

## Step 2 — Initial configuration (chosen before viewing results)

`src/models/classifier.py` exposes `create_classifier()`, an unfitted RandomForestClassifier:

| Parameter | Value | Reason / meaning |
|---|---|---|
| `n_estimators` | 200 | Moderate tree budget for probability averaging; not tuned |
| `criterion` | `gini` | Standard class-impurity splitting rule |
| `max_depth` | 12 | Bounds path complexity rather than growing unrestricted trees |
| `min_samples_leaf` | 5 | Avoids rules supported by only one or two training samples |
| `min_samples_split` | 2 | Standard initial split threshold; leaf/depth constraints also apply |
| `max_features` | `sqrt` | Encourages different candidate splits across trees |
| `bootstrap` | `True` | Different resampled training rows per tree |
| `class_weight` | `None` | Same near-balanced baseline decision as LR |
| `random_state` | 42 | Reproducible bootstrap/feature randomness |
| `n_jobs` | 1 | Bounded local CPU usage; no parallel-worker requirement |

Other defaults are unchanged (`max_samples=None`, `oob_score=False`, `ccp_alpha=0.0`,
`max_leaf_nodes=None`, `min_impurity_decrease=0.0`, `min_weight_fraction_leaf=0.0`,
`warm_start=False`, `verbose=0`, `monotonic_cst=None` on sklearn 1.9.1).

**No scaler for RF:** tree splits depend on ordering/thresholds, not Euclidean distance or a
regularized linear coefficient magnitude. RF uses the original ten numerical features; LR
still uses its training-fitted StandardScaler. No new features or transformations were added.
Depth 12 and leaf size 5 are an initial complexity budget, not proven optimal settings. A
smaller/larger tree budget may later trade off fit, generalization and runtime; none was tried here.

## Step 2 — Reproducible same-split experiment

Run from the repository root:

```bash
.venv/bin/python -m scripts.compare_classical_ml
```

The script loads/cleans/deduplicates with the unchanged Phase 2 functions, splits with seed 42,
and extracts **only training and validation features**. It creates X_train and X_validation
once, then fits both the existing LR pipeline and RF on the **same 57,574 training emails** and
compares predictions on the **same 12,337 validation emails**. Both models use the fixed ten
feature columns; neither `source` nor `label` enters those matrices. Training labels remain
27,707 legitimate / 29,867 phishing-spam; validation remains 5,937 / 6,400. Class weighting
remains None. Default decision thresholds are used; none is tuned. The LR metrics reproduced
Step 1 exactly. No model is serialized and the test partition is not used after split creation.

## Step 2 — Actual validation results and comparison

| Metric | LR (unchanged) | RF | RF minus LR (absolute) |
|---|---:|---:|---:|
| Accuracy | 0.7186512118 | 0.8647969523 | +0.1461457405 |
| Precision | 0.7277250816 | 0.9033412888 | +0.1756162071 |
| Recall | 0.7312500000 | 0.8279687500 | +0.0967187500 |
| F1 | 0.7294832827 | 0.8640143486 | +0.1345310659 |
| ROC-AUC | 0.7846716566 | 0.9413235588 | +0.1566519023 |

These are absolute metric differences, not relative-percent improvement claims. In percentage
points, precision increases by 17.5616 and recall by 9.6719.

RF confusion matrix (rows actual, columns predicted, class order [0, 1]):

| Actual / predicted | Legitimate (0) | Phishing/spam (1) |
|---|---:|---:|
| Legitimate (0) | **5,370 TN** | **567 FP** |
| Phishing/spam (1) | **1,101 FN** | **5,299 TP** |

Compared with LR: FP decreased 1,751 -> 567 (**1,184 fewer** false alarms), and FN decreased
1,720 -> 1,101 (**619 fewer** missed positives). Higher precision means more trustworthy flags;
higher recall means more attacks caught; F1 and probability-ranking AUC also improve. Thus
RF is stronger on *this validation run*, not merely more accurate. But it still misses 1,101
of 6,400 positives, and neither validation success nor a high AUC proves deployment safety.
We have not chosen or saved a final/best model, assessed uncertainty over repeated splits,
or measured held-out test performance.

## Step 2 — Measured RF feature importance (training-derived MDI)

| Feature | Importance |
|---|---:|
| `word_count` | 0.2260900563 |
| `uppercase_ratio` | 0.1489496403 |
| `phishing_keyword_count` | 0.1368616645 |
| `max_url_length` | 0.1359282489 |
| `exclamation_count` | 0.1292385954 |
| `average_word_length` | 0.0965969687 |
| `url_count` | 0.0674566478 |
| `max_hostname_dot_count` | 0.0545649542 |
| `https_url_count` | 0.0024207477 |
| `has_ip_address_url` | 0.0018924762 |

Word count contributes the most impurity reduction, followed by casing, fixed keyword counts,
URL length and exclamation count. That is a statement about the fitted forest, **not causal
security evidence**. Length and casing can encode source-specific formatting; link availability
also varies by source. Continuous feature cardinality can contribute to MDI bias. A low MDI
value does not establish that a feature is useless; another correlated signal may have taken
its splits. We have not measured permutation importance, feature ablations or per-source
performance and must not imply that those tests passed.

## Step 2 — Verification, limitations and interview takeaways

Five focused unit tests cover the initial configuration and unfitted state, valid probabilities,
feature-schema/importance alignment, depth limits, repeatability with seed 42, predictions without
refitting and rejection of reordered features. Full project tests also pass; Phase 2, the LR
factory and its existing training script are unchanged. No artifacts were saved. A successful
validation comparison does not establish the absence of overfitting: this step has not performed
cross-validation or a train-versus-validation learning-curve analysis.

The earlier limitations still apply: near-duplicates, mixed phishing/spam labels, old/source-
biased data, and incomplete regex URL coverage. MDI can reward source shortcuts instead of
reliable phishing patterns. No threshold/class-weight tuning or calibration occurred; forest
probabilities are model estimates, not calibrated risk scores.

Interview questions:
1. Why no scaling for trees? Splits use ordering and thresholds, unlike regularized LR coefficients.
2. What makes the trees different? Bootstrap training rows and random candidate features at each split.
3. Why constrain depth/leaves? Discourage rules supported by tiny, training-specific subgroups.
4. Why is RF stronger here? On identical validation rows, both missed positives and false alarms fell;
   nonlinear interactions are possible, but this experiment does not prove the mechanism or causality.
5. Why not declare a winner yet? A single validation result is not final held-out evidence or a
   completed model-selection procedure.
6. What does importance prove? Only contribution to this forest's training impurity reduction, not
   causality, direction or generalization.

Stop point: Phase 3 Step 2 only. Cross-validation, class-weight experiments, threshold tuning,
serialization and ensemble work require separate approval.
