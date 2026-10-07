# Classical ML and evaluation — Phase 3 complete

## Scope and supervised classification

Completed: **untuned Logistic Regression and Random Forest baselines** (Steps 1–2),
**training-only five-fold CV** (Step 3), a controlled **None-vs-balanced class-weight comparison**
(Step 4), and **explicit model selection, development refit, serialization and one final held-out
test evaluation** (Step 5). The earlier sections record the experiment boundaries at that time.
Both core model implementations and Phase 2 code are unchanged. No ensemble, threshold tuning,
new hyperparameter search or Phase 4 work has been implemented. The selected unweighted RF is
saved locally and ignored by git. The final test has now been evaluated once; it must not be used
for further selection or tuning.

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

Step 2 stopped at the baseline comparison. The separately approved training-only CV experiment
is recorded below; class-weight experiments, threshold tuning, serialization and ensemble work
remain unimplemented.

## Step 3 — Cross-validation: intuition and methodology

**Level 1:** Instead of trusting a single split, divide the existing training set into five groups.
Train a fresh model on four groups and evaluate on the fifth. Repeat so each group is evaluated
once. We get five measurements of each model's sensitivity to the data partition.

**Level 2:** StratifiedKFold preserves the class ratio approximately in each fold. Every training
row participates in fold-validation exactly once and in four fold-training sets. Each iteration
clones the estimator and fits it from scratch. Passing the whole LR Pipeline (not an already
scaled matrix) ensures its StandardScaler learns means/variances only from that fold's training
rows. Predictions transform fold-validation with that same fold-fitted scaler. RF needs no scaler.

This is **not** another name for the project's held-out validation/test sets. CV operates only
inside the original 57,574-row training split. The held-out validation set used in Steps 1–2
and the final test set are not extracted, fitted or scored in this CV experiment. The existing
Phase 2 split function still creates those partitions; the CV entry point accesses only `.train`.
The sklearn result keys named `test_accuracy`, etc. denote *fold-validation scores*, not our
held-out test set.

Five folds balance computation (five fresh fits per model) with repeated measurements. We did
not change models or hyperparameters based on scores. CV is intended to measure stability, not
produce a higher score. CV models train on fewer rows than the full-training baselines, so CV
means and prior held-out validation metrics are not measurements on identical conditions.

### Exact configuration and implementation

- Existing cleaned/deduplicated split with seed 42; CV input is **only** 57,574 training rows:
  27,707 legitimate and 29,867 phishing/spam. The same ten deterministic numerical features are
  used, excluding `source` and `label` from the matrix.
- `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`, identical fold membership for LR/RF.
- Folds 1–4: **46,059 fold-training / 11,515 fold-validation rows**; fold 5:
  **46,060 / 11,514**. Every score below is fold-validation, not training performance.
- Models are the unchanged `create_baseline()` and `create_classifier()` configurations from
  Steps 1–2. Class weights remain None; thresholds remain default. No search or tuning occurred.
- `cross_validate(..., n_jobs=1, error_score="raise", return_train_score=False)`; no fitted
  estimators or artifacts are returned/saved. ConvergenceWarning also raises instead of being hidden.
- Accuracy, precision, recall and F1 use hard labels; positive class is 1; undefined
  precision/recall/F1 use zero. ROC-AUC scorer explicitly uses `predict_proba`.
- Mean is the unweighted mean of the five fold scores. Standard deviation uses **ddof=0**
  (population SD of these observed scores). Neither is a pooled out-of-fold metric or confidence interval.

Reusable logic: `src/evaluation/cross_validation.py` contains `evaluate_cross_validation()`;
`tests/test_evaluation/test_cross_validation.py` tests it on small in-memory examples.
`scripts/cross_validate_ml.py` only orchestrates loading/cleaning/splitting and train-only extraction:

```bash
.venv/bin/python -m scripts.cross_validate_ml
```

### Actual LR per-fold results (scikit-learn 1.9.1)

| Fold | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| 1 | 0.7203647416 | 0.7301136364 | 0.7313357884 | 0.7307242014 | 0.7841482615 |
| 2 | 0.7197568389 | 0.7244647818 | 0.7420488785 | 0.7331514099 | 0.7838127222 |
| 3 | 0.7139383413 | 0.7220288414 | 0.7292817680 | 0.7256371814 | 0.7823740001 |
| 4 | 0.7165436387 | 0.7247386760 | 0.7312908086 | 0.7280000000 | 0.7839225299 |
| 5 | 0.7229459788 | 0.7315693127 | 0.7359785702 | 0.7337673176 | 0.7866258719 |

### Actual RF per-fold results

| Fold | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| 1 | 0.8723404255 | 0.9109489051 | 0.8356210244 | 0.8716605553 | 0.9449196684 |
| 2 | 0.8683456361 | 0.9098933431 | 0.8282557750 | 0.8671573782 | 0.9420885348 |
| 3 | 0.8670429874 | 0.9045537341 | 0.8314080027 | 0.8664398500 | 0.9430940677 |
| 4 | 0.8679114199 | 0.9051692756 | 0.8325799431 | 0.8673585070 | 0.9407049484 |
| 5 | 0.8681605003 | 0.9058116232 | 0.8324125230 | 0.8675623800 | 0.9421878088 |

### Actual mean ± standard deviation

| Metric | LR mean ± SD | RF mean ± SD |
|---|---:|---:|
| Accuracy | 0.7187099079 ± 0.0031381334 | 0.8687601938 ± 0.0018449263 |
| Precision | 0.7265830496 ± 0.0036320090 | 0.9072753762 ± 0.0026204631 |
| Recall | 0.7339871627 ± 0.0045912485 | 0.8320554536 ± 0.0023652752 |
| F1 | 0.7302560221 ± 0.0030774985 | 0.8680357341 ± 0.0018515066 |
| ROC-AUC | 0.7841766771 ± 0.0013744862 | 0.9425990056 ± 0.0013890773 |

### Stability, security interpretation and limitations

RF scores higher on all five metrics in every fold here. Its recall SD is about 0.00237 vs
LR's 0.00459, and precision SD about 0.00262 vs 0.00363. Both models vary relatively little across
these shuffled stratified partitions. RF's ROC-AUC SD is slightly **larger** than LR's, so this is
not evidence that RF has lower variance on every metric. A single shuffled five-fold run does
not measure variance across many seeds or model configurations and cannot establish statistical
significance. Fold-training sets overlap substantially; five scores are not independent draws.

Recall matters because false negatives are missed phishing/spam; mean RF recall ~0.832 still
leaves substantial misses. Precision matters because false positives cause unnecessary alarms;
RF mean precision ~0.907 is stronger than LR's ~0.727 here. Neither alone is sufficient: high
precision can coexist with poor attack coverage, while chasing recall can swamp users with false
alarms. F1 offers a balance, not an explicit security cost model. AUC measures ranking, not
calibration or recall at an operational threshold.

CV replicates the broad LR/RF comparison inside training data, but does not prove deployment
safety or eliminate the earlier source-shortcut and near-duplicate risks. Random folds may share
source style and near-duplicate templates, making biased performance look stable. Mixed phishing/
spam labels and old source data also remain limitations. No grouping/time-based evaluation,
per-source CV, learning curve, calibration or final test measurement has been performed. The
held-out test set remains reserved; using it to choose CV settings or models would weaken its
role as final independent evidence.

### Verification and interview takeaways

Focused tests check five folds for both models, exact repeatability, output keys/ranges, mean/SD
calculations, mismatched-row/insufficient-class rejection, and five independent LR scaler fits.
A script-level test makes held-out validation/test access raise, proving the entry point uses
only the supplied training partition. The caller's original LR pipeline remains unfitted after
CV because sklearn fits clones. Phase 2 and both model factories remain unchanged.
Focused CV tests: **5 passed**. Full suite after this step: **67 passed**, with no saved artifacts.

An inferred sklearn signature incorrectly typed `error_score` as a float only. The valid runtime
option `"raise"` was retained with a narrow annotation instead of replacing it with silent NaNs.

Interview questions:
1. Why not scale the full training set before CV? Fold-validation values would influence the scaler,
   leaking information into each fold's model. Fit the pipeline independently inside every fold.
2. What does small SD prove? Stability under these particular partitions, not causal signal or
   real-world generalization; fold scores overlap in their training data.
3. Why stratify? Preserve approximate class balance so changing priors do not dominate comparisons.
4. Why not use held-out validation/test inside CV? It would no longer be an independent evaluation
   boundary. CV here measures only the original training split.
5. Did CV improve the models? No configuration changed; it measured performance/stability.

Historical Step 3 boundary: CV measured the unchanged baselines; class weighting was deferred
until the separately approved Step 4 below.

## Step 4 — Class imbalance and controlled class-weight experiment

### Concept and hypothesis

Class imbalance means one target class has more examples than the other. Our training split is
close to balanced: **27,707 legitimate** and **29,867 phishing/spam** out of **57,574** rows.
Phishing/spam is slightly the majority, not the minority. Therefore we measured weighting rather
than assuming it would improve phishing recall.

- `class_weight=None`: each training example has equal class-based weight.
- `class_weight="balanced"`: sklearn calculates `N / (K × n_class)` from training labels,
  where `N` is the training row count, `K` the number of classes, and `n_class` that class's count.
  Each class consequently has equal total weight before RF bootstrap sampling.
- Weighting changes the training objective, not the rows, labels or split. In LR it weights the
  classification loss; in RF it weights impurity calculations and leaf class statistics.
- When positives are the minority, upweighting them can increase recall at the cost of precision,
  but this is not guaranteed. Here positives are downweighted: measured recall **decreased**.

Actual training-derived weights:

| Class | Count | Balanced weight |
|---|---:|---:|
| 0 — legitimate | 27,707 | 1.0389793193055907 |
| 1 — phishing/spam | 29,867 | 0.9638396892891821 |

### Exact controlled configurations and data boundaries

Run: `.venv/bin/python -m scripts.compare_class_weights`, Python **3.12.15**, sklearn **1.9.1**.
All four variants use the same Phase 2 seed-42 training and held-out validation partitions,
unchanged ten features and default `predict()` decision rule. Validation has **12,337** rows:
**5,937 legitimate / 6,400 phishing-spam**. Neither `source` nor `label` is a feature.

| Variant | Configuration |
|---|---|
| `lr_unweighted` | Independent StandardScaler → LR; `class_weight=None` |
| `lr_balanced` | Independent StandardScaler → LR; `class_weight="balanced"` |
| `rf_unweighted` | Existing RF configuration; `class_weight=None` |
| `rf_balanced` | Same RF configuration; `class_weight="balanced"` |

Both LR variants retain `C=1.0`, effective L2 regularization (`l1_ratio=0.0` in sklearn 1.9.1),
`solver="lbfgs"`, `max_iter=1000`, `tol=1e-4`, `fit_intercept=True`, `random_state=42` and all
other defaults. Each variant fits its own scaler **on training only**; class weights are not
passed to the scaler. RF retains `n_estimators=200`, `criterion="gini"`, `max_depth=12`,
`min_samples_leaf=5`, `min_samples_split=2`, `max_features="sqrt"`, `bootstrap=True`,
`random_state=42`, `n_jobs=1` and all other defaults. Only class weight changes within each pair.

`create_class_weight_variants()` clones the existing estimators for explicit balanced variants;
it does not change either factory. `run_class_weight_experiment()` accepts only supplied
training/validation matrices, fits on training, and returns configurations, metrics and deltas,
not fitted models. It rejects unexpected feature columns/order and mismatched row counts.
Convergence warnings raise instead of silently accepting an unconverged LR run.

The script runs the existing load/clean/deduplicate/split flow once, then extracts **train and
validation features only**. Creating the reserved test partition is not using it for fitting
or evaluation. No test feature extraction, test predictions, CV rerun, threshold tuning,
hyperparameter tuning or artifact serialization occurred. The final test boundary remains
untouched so it can provide an independent final evaluation after later approved decisions.

### Actual validation results

Both unweighted variants reproduced the previously recorded baseline metrics exactly.
The table rounds measured values to nine decimal places; all confusion counts are exact.
Positive class is phishing/spam, not exclusively phishing.

| Variant | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| LR None | 0.718651212 | 0.727725082 | 0.731250000 | 0.729483283 | 0.784671657 |
| LR balanced | 0.708356975 | 0.743991641 | 0.667500000 | 0.703673200 | 0.783113946 |
| RF None | 0.864796952 | 0.903341289 | 0.827968750 | 0.864014349 | 0.941323559 |
| RF balanced | 0.864715895 | 0.906233900 | 0.824531250 | 0.863454144 | 0.940899786 |

Confusion matrix order is `[[TN, FP], [FN, TP]]`:

| Variant | Confusion matrix | False alarms (FP) | Missed positives (FN) |
|---|---|---:|---:|
| LR None | `[[4186, 1751], [1720, 4680]]` | 1,751 | 1,720 |
| LR balanced | `[[4467, 1470], [2128, 4272]]` | 1,470 | 2,128 |
| RF None | `[[5370, 567], [1101, 5299]]` | 567 | 1,101 |
| RF balanced | `[[5391, 546], [1123, 5277]]` | 546 | 1,123 |

Measured deltas, **balanced minus unweighted**, on the 0–1 metric scale:

| Metric | LR delta | RF delta |
|---|---:|---:|
| Accuracy | -0.010294237 | -0.000081057 |
| Precision | +0.016266559 | +0.002892611 |
| Recall | -0.063750000 | -0.003437500 |
| F1 | -0.025810082 | -0.000560205 |
| ROC-AUC | -0.001557710 | -0.000423773 |

### Security interpretation and decision

Recall measures how many actual positives we catch; false negatives are missed phishing/spam.
Precision measures how many positive alarms are correct; false positives cause unnecessary
quarantines/reviews. Neither alone is sufficient, and accuracy does not resolve their costs.

- **LR balanced** removes **281 false alarms** but adds **408 missed positives**. Recall drops
  **6.375 percentage points**, while precision rises about **1.627 percentage points**. F1 and
  ROC-AUC also decline. This is not an attractive tradeoff for the stated recall-sensitive goal.
- **RF balanced** removes **21 false alarms** but adds **22 missed positives**. Recall drops
  **0.34375 percentage points**, precision rises about **0.28926 percentage points**, and F1/
  ROC-AUC decline slightly. The change is small; there is no demonstrated benefit for our goal.

**Recommendation: retain `class_weight=None` for both model families.** Unweighted RF remains
our stronger validation candidate, not a final selected/saved/deployed model. No core setting
was changed by this experiment. A different operational cost policy might value fewer alarms,
but no explicit cost model was measured here, so we do not claim universal optimality.

### Verification, limitations and interview takeaways

Focused experiment tests: **4 passed**. Full suite: **71 passed**. Tests verify that only class
weight differs, factories remain unchanged, LR scalers and RF estimators fit training rows only,
returned metrics/deltas and weights are correct, input matrices are not mutated, metadata is
rejected, and the script cannot access the test partition. Editor diagnostics for the three
new Python files show no errors or warnings. Narrow casts for sklearn `clone()` resolve broad
inferred return types without changing runtime behavior or estimator settings.

Limitations:
- One controlled comparison on the existing validation split, not an independent final test.
- Small RF differences are not evidence of statistical significance; no significance test ran.
- Excluding `source` does not eliminate source-format/style shortcuts in random splits.
- Exact deduplication does not remove near-duplicates; mixed phishing/spam labels and older
  email data limit generalization to current, purely phishing attacks.
- Model probabilities are not demonstrated calibrated risk probabilities.
- These results support keeping current weights for this dataset/configuration, not claiming
  that balancing never helps. No weighting variants were cross-validated in this step.

Interview takeaways:
1. Why test weighting on nearly balanced data? To measure the precision/recall tradeoff rather
   than assuming a conventional technique improves performance.
2. Why did recall fall? Positives were the majority and were downweighted; this is consistent
   with the result, not proof that weights always move recall in a fixed direction.
3. What made the experiment controlled? Identical splits, features, model settings and default
   prediction rules; only class weight differed. Training labels determined the weights.
4. Does weighting resample data? No. It changes example influence during fitting.
5. Why not use the test set to choose weights? That would contaminate the independent final
   evaluation with a model-selection decision.

Historical Step 4 boundary: class-weight experiments finished before the separately approved
selection/serialization step below. No configuration was changed in response to weighting results.

## Step 5 — Explicit model selection and final serialization

### Model selection: development evidence, not test evidence

Model selection means choosing one of the four already measured configurations. We use
**highest held-out validation F1**, with exact ties resolved by **recall → ROC-AUC → precision**,
then ascending candidate name for a fully reproducible tie. Accuracy is reported, not ranked.
This rule is declared before final test access; it is a transparent project policy, not a
universal optimal security cost function. F1 balances false alarms and missed positives;
recall and confusion counts explicitly inform our security interpretation.

`src/evaluation/model_selection.py` selects from supplied measurements without fitting anything
or knowing test results. `docs/classical_ml_development.json` transcribes existing Step 1–4
measurements with provenance at commit `8d8db01`; no CV, baseline or weighting experiment was
rerun. The JSON's CV summary uses the ten-decimal precision already recorded in Step 3.
The four validation results and exact confusion matrices remain in Step 4 above.

**Selected: `rf_unweighted` (Random Forest, `class_weight=None`).** Its validation F1
**0.8640143486059025** is highest among the four candidates. Versus unweighted LR, RF has both
higher recall and precision as well as higher F1/AUC. Versus weighted RF, its precision is
slightly lower, but recall, F1 and AUC are higher: weighting saved 21 alarms while adding 22
misses. Weighted LR sacrificed 408 detections for 281 fewer alarms. For the recall-sensitive
objective, retain `class_weight=None`; do not choose solely on accuracy or assume weights help.

Previously measured training-only CV supports this choice's stability; it does not choose a
new configuration or guarantee generalization. Population SD is `ddof=0`, not a confidence
interval. Weighted variants were not cross-validated.

| Metric | Unweighted LR CV mean ± SD | Unweighted RF CV mean ± SD |
|---|---:|---:|
| Accuracy | 0.7187099079 ± 0.0031381334 | 0.8687601938 ± 0.0018449263 |
| Precision | 0.7265830496 ± 0.0036320090 | 0.9072753762 ± 0.0026204631 |
| Recall | 0.7339871627 ± 0.0045912485 | 0.8320554536 ± 0.0023652752 |
| F1 | 0.7302560221 ± 0.0030774985 | 0.8680357341 ± 0.0018515066 |
| ROC-AUC | 0.7841766771 ± 0.0013744862 | 0.9425990056 ± 0.0013890773 |

### Frozen configuration and development refit

The final estimator is a fresh instance from the unchanged RF factory:

```text
n_estimators=200, criterion="gini", max_depth=12,
min_samples_leaf=5, min_samples_split=2, max_features="sqrt",
bootstrap=True, class_weight=None, random_state=42, n_jobs=1
```

All remaining sklearn defaults are unchanged (`max_samples=None`, `max_leaf_nodes=None`,
`min_weight_fraction_leaf=0.0`, `min_impurity_decrease=0.0`, `ccp_alpha=0.0`, `oob_score=False`,
`warm_start=False`, `verbose=0`, `monotonic_cst=None`). No scaling is needed for RF and none was
added. The original LR scaler/model pipeline remains unchanged.

After selection, concatenate the original **57,574 training + 12,337 validation rows**, then
extract the same deterministic features and fit once on **69,911 development rows**:
**33,644 legitimate / 36,267 phishing-spam**. The split seed remains 42; global deterministic
cleaning and exact deduplication still occur before splitting. No test rows enter fitting.

This is intentional final refitting, not leakage: validation has finished its development role.
However, **the saved model has now trained on validation rows**. Future work must not call its
validation performance independent or use those predictions as leakage-free ensemble tuning
inputs. This step does not redesign future evaluation; it records the boundary explicitly.

### Serialization, feature contract and security

Serialization stores learned estimator state rather than retraining on startup. `joblib` handles
sklearn estimators and NumPy arrays; it was already installed via sklearn and is now declared
as a direct dependency in the existing `data` extra because this project imports it directly.

`src/models/registry.py` saves a `ClassicalModelArtifact` containing:
- The complete fitted estimator; an LR artifact would include its entire fitted scaler pipeline.
- The ten feature names in fixed order and class mapping `[0, 1]`.
- Selected configuration, selection rule, development row count, split seed and evidence hash.
- Artifact schema, feature contract, Python/sklearn/NumPy/pandas/joblib versions, and SHA-256
  fingerprints of the unchanged cleaning/feature code.

Predictable paths, both gitignored:
- Model: **`model_artifacts/ml/classical_model.joblib`**.
- Local measured run report: `model_artifacts/ml/classical_model_final_evaluation.json`.

The artifact takes **numeric feature matrices**, not raw emails. Email inference must use the
same Phase 2 cleaning and extraction code; deterministic preprocessing is maintained in `src/`,
not copied into the pickle. The loader checks code fingerprints, sklearn version, fitted state,
feature order and class mapping. The prediction wrapper rejects reordered/missing/extra columns,
nonnumeric values and NaN/infinite values instead of silently guessing. Fingerprints are
conservative: even a source-only formatting change requires explicit artifact compatibility
review. Matching hashes/versions are not a substitute for reproducing the full environment.

**Only load trusted local artifacts.** `joblib.load()` can execute arbitrary code during
unpickling, before metadata validation. Checks do not make untrusted downloads safe. Sklearn
serialization is not a portable cross-version serving format; keep the recorded environment.
Measured environment: Python **3.12.15**, sklearn **1.9.1**, NumPy **2.5.3**, pandas **3.0.6**,
joblib **1.6.0**.

The real run verified exactly equal predictions **and probabilities** before/after loading on
**128 development rows**, preserving all ten columns. Synthetic tests verify both RF and the
full LR pipeline (including fitted scaler statistics), rejected schemas and no overwrite.
Final artifact SHA-256:
`0fe95d47acb45a4caab6d600d6266b27efb44746e61e61e6a8e738337e9ffcc0`.

### ONE final held-out test evaluation

Command executed once: `.venv/bin/python -m scripts.finalize_classical_ml`.
The script reserves a local report before fitting and refuses to run if a final artifact/report
already exists. A failed run's reserved report must be investigated, not deleted to casually
repeat evaluation. The guard reduces accidental repeats; it is not a tamper-proof audit system.

After frozen selection, development refit, save and development-only load-equivalence checks,
the script first extracts test features. It calls `predict` and `predict_proba` once each on
the same **12,338 held-out test rows** and calculates all final metrics in one evaluation:
**5,938 legitimate / 6,400 phishing-spam**. No other model is tested. Synthetic tests of this
workflow are not evaluations of the real held-out dataset.

| Metric | Development validation (train-only RF) | Final test (development-refitted RF) |
|---|---:|---:|
| Accuracy | 0.864796952257437 | 0.8674015237477711 |
| Precision | 0.9033412887828163 | 0.9067622950819673 |
| Recall | 0.82796875 | 0.8296875 |
| F1 | 0.8640143486059025 | 0.866514360313316 |
| ROC-AUC | 0.9413235588260063 | 0.9416939494568879 |

Final test confusion matrix, `[[TN, FP], [FN, TP]]`:

```text
[[5392,  546],
 [1090, 5310]]
```

There are **546 false alarms** and **1,090 missed phishing/spam examples**. Recall still misses
**17.03125%** of positives. Final test scores are close to development validation scores, but
these are different partitions and differently fitted estimators; the small increases are not
proof of a retraining improvement or statistical significance. CV is stability evidence from
the original training subset, validation was selection evidence, test is the final held-out
estimate. No test result changed model settings, weights, features or prediction thresholds.

### Verification, limitations and interview takeaways

Focused new tests cover evidence-driven selection (any of the four can win), tie rules, malformed
measurements, the recorded winner, RF/LR round-trip behavior, fitted/schema/version checks, and
synthetic workflow ordering: development-only fit, save/load before test access, exactly one
metric evaluation and blocked rerun. **12 focused tests passed; the full suite passed all 83
tests**. The artifact also loaded successfully in a fresh Python process; file size is
**5,953,919 bytes**. All five new Python files have no editor errors or warnings. Raw CSVs and
both artifact/report files are confirmed ignored; Phase 2 and both baseline factories are
unchanged. No real test evaluation was repeated during these verification checks.

Limitations remain: different source composition and source-format/style shortcuts despite
excluding `source`; exact deduplication does not remove near-duplicate/template effects; mixed
phishing/spam labels and old emails; random splits are not source-disjoint or temporal tests.
A stable CV and similar held-out score under the same dataset distribution **do not demonstrate
production-level generalization**. Probabilities are not calibrated; no operating-cost study,
threshold optimization or live-security validation was performed. Never reuse this final test
result to repeatedly select future variants; no additional evaluation design was implemented here.

Interview takeaways:
1. Selection vs fitting? Choose configuration on development evidence, then fit a fresh estimator
   on development data; final test remains separate until those decisions are frozen.
2. Why not choose highest accuracy? Precision/recall and misses/alarms matter; our explicit F1
   policy and security tradeoff explain the choice rather than a generic accuracy claim.
3. Why save more than a model name? Learned state, feature order, fitted transformations, class
   mapping and version/code contracts must agree at inference time.
4. What does exact save/load equivalence prove? Serialization preserved outputs on checked inputs;
   it does not prove detection quality or universal compatibility.
5. What does one test evaluation prove? One held-out estimate under this split/distribution, not
   resilience to future attacks or freedom from source shortcuts.

Stop point: Phase 3 classical ML complete. No Phase 4, NLP or ensemble/risk-score work.
