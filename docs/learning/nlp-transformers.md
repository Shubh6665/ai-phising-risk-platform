# Phase 4 Step 1 — TF-IDF + Logistic Regression NLP baseline

## Scope: abhi kya actually implemented hai?

Is step mein local **TF-IDF + Logistic Regression** text baseline implement/train kiya aur
original validation split par evaluate kiya. Transformer training, notebooks, external model
hosting aur ensemble abhi implement nahi hue. File ka naam project plan follow karta hai;
is note mein current implemented baseline hi explain kiya gaya hai.

## Handcrafted model vs text model

Phase 3 models ko ten predefined numeric features dikhte the: word count, urgency keyword
count, uppercase ratio, URL length, etc. Actual email vocabulary unka direct input nahi tha.
Ab model cleaned **subject + body** ke words/phrases se representation learn karta hai.
Classifier still Logistic Regression hai; representation change hui hai, deep learning nahi.

Flow:

```text
Six per-source CSVs
→ unchanged deterministic Phase 2 cleaning + exact deduplication
→ same seed-42 stratified split
→ existing build_email_text(subject, body), separator "\n\n"
→ train-fitted TF-IDF vocabulary/IDF
→ sparse text matrix
→ Logistic Regression
→ validation metrics
```

Cleaning once hoti hai; cleaned text ko dobara clean nahi karte. Phase 2 ka one-pass entity
handling unchanged hai. `source` metadata hai, aur `label` target; dono text mein concatenate
nahi hote. Sender/receiver/date/precomputed URL fields bhi NLP inputs nahi hain.

## TF-IDF: simple intuition aur technical meaning

**TF = Term Frequency:** ek document/email mein term kitni baar aaya. Is configuration mein
raw occurrence count use hota hai (`binary=False`, `sublinear_tf=False`).

**DF = Document Frequency:** training ke kitne emails mein term at least once present hai.
Ek email mein ten repetitions DF ko ten nahi banate; us email ka contribution one hai.

**IDF = Inverse Document Frequency:** widespread terms ko lower weight, fewer training emails
mein present terms ko higher weight. sklearn ka `smooth_idf=True` formula:

```text
idf(t) = log((1 + N) / (1 + df(t))) + 1
unnormalized tfidf(t, email) = raw_count(t, email) × idf(t)
```

`N` sirf training document count hai. Plus-one smoothing numerical edge cases avoid karti hai.
Term sab documents mein ho toh IDF **1** hota hai, zero nahi. Final email vector L2-normalize
hota hai: weights ke squares ka sum nonempty/nonzero rows ke liye one hota hai.

Important distinction: **rare term automatically informative nahi hota**. Random identifiers,
source boilerplate ya typos bhi rare ho sakte hain. IDF labels use nahi karta; supervised LR
training labels ke against positive/negative coefficients learn karta hai.

## Matrix aur sparse representation

Rows emails hain; columns training vocabulary ke word/ngram terms hain. Har cell us email
mein term ka normalized TF-IDF weight hai. Har email vocabulary ka small subset contain karta
hai, so majority cells zero hote hain. Sparse matrix zero cells ko individually store nahi
karti; nonzero values aur positions store karti hai.

Script matrices ko sparse rakhta hai; `.toarray()` nahi karta. Training matrix summary measure
karne ke baad us matrix ko release karta hai, then validation transform hoti hai. Yeh second
training transform only measurement hai, refit nahi. Model fit ke during initial training
matrix bhi isi fitted representation se banti hai.

## N-grams aur vocabulary controls

- **Unigram:** one token, e.g. `verify`.
- **Bigram:** two adjacent tokens, e.g. `verify account`.
- `ngram_range=(1, 2)` dono include karta hai. Adjacency token sequence ki hoti hai;
  newline/punctuation boundary meaningful sentence boundary ki tarah enforce nahi hoti.
- `min_df=2`: term at least two training emails mein ho. Singleton noise reduce hoti hai;
  genuinely useful singleton term bhi drop ho sakta hai. Ye untuned conservative choice hai.
- `max_df=1.0`: extra frequent-term pruning nahi. Corpus evidence ke bina arbitrary cutoff nahi.
- `max_features=None`: vocabulary cap nahi. Metrics improve karne ke liye aggressive pruning nahi.
- Default token pattern `(?u)\b\w\w+\b`: Unicode word tokens, at least two characters.
  Punctuation largely token boundaries banati hai; single-character tokens ignore hote hain.
  URLs bhi word-like pieces mein tokenize hote hain, semantic URL parsing nahi hoti.

`lowercase=True` se `URGENT` aur `urgent` same token banenge. Phase 2 text unchanged/case-preserved
rehti hai; vectorizer apni representation mein case merge karta hai. Is NLP baseline mein
capitalization aur punctuation ke explicit handcrafted signals nahi hain. `strip_accents=None`,
`stop_words=None`; accent stripping aur predefined stop-word removal nahi ki.

## Exact initial configuration — results dekhkar tune nahi ki

```text
TfidfVectorizer:
  input="content", encoding="utf-8", decode_error="strict"
  analyzer="word", lowercase=True, strip_accents=None
  ngram_range=(1, 2), min_df=2, max_df=1.0, max_features=None
  stop_words=None, token_pattern="(?u)\\b\\w\\w+\\b"
  tokenizer=None, preprocessor=None, vocabulary=None
  binary=False, use_idf=True, smooth_idf=True, sublinear_tf=False
  norm="l2", dtype=float64

LogisticRegression:
  C=1.0, solver="lbfgs", max_iter=1000, tol=1e-4
  fit_intercept=True, class_weight=None, random_state=42
  effective L2 regularization (sklearn 1.9.1: l1_ratio=0.0)
  remaining defaults unchanged
```

`StandardScaler` add nahi kiya: TF-IDF already row-normalized sparse features deta hai.
Dense-style centering sparse structure destroy karegi; extra scaling is baseline ke liye
justified nahi thi. `C=1.0` regularization strength inverse control karta hai; optimize nahi kiya.
Default prediction rule unchanged hai. Class weighting experiment repeat nahi hua; Phase 3 ka
finding text models par universally apply nahi hota, but this initial baseline unweighted hai.

## Vocabulary fitting aur leakage boundary

Vocabulary selection, DF/IDF aur `min_df` filtering **training text par hi fit** hote hain.
Validation sirf fitted training vectorizer se transform hoti hai; unknown terms ignore hote hain.
Vocabulary/IDF validation include karke fit kiya, toh evaluation distribution representation ko
influence karegi—even without labels. Yeh data leakage hoti hai.

Pipeline: `EmailTextInput → TfidfVectorizer → LogisticRegression`.
`EmailTextInput` stateless schema guard hai: flat list/tuple of strings accept karta hai;
DataFrames, mappings, nested lists, missing values aur raw scalar string reject karta hai.
Pandas Series caller `.tolist()` se pass karta hai. Yeh text normalize/change nahi karta.
Fitted vectorizer aur classifier same pipeline mein rehte hain; no separate manually maintained
vocabulary/classifier pairing. Pipeline caller ko train-only discipline follow karni hoti hai;
API train vs validation ka intent automatically identify nahi kar sakti.

Existing split unchanged:
- **Training: 57,574**, legitimate **27,707**, phishing/spam **29,867**.
- **Validation: 12,337**, legitimate **5,937**, phishing/spam **6,400**.
- NLP Step 1 mein test partition access, feature extraction, prediction ya evaluation **nahi** hui.
  Phase 3 ka historical final test result is NLP comparison/selection mein reuse nahi kiya.

## Actual real-data run aur representation findings

Command:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m scripts.train_nlp_baseline
```

Numerical-library threads single rakhe to avoid CPU oversubscription; model configuration
change nahi ki. Python **3.12.15**, sklearn **1.9.1**. LR **18 iterations** mein converge hua;
convergence warnings ko script error treat karta hai, hide nahi karta.

| Measurement | Training | Validation |
|---|---:|---:|
| Matrix shape | `(57574, 1064372)` | `(12337, 1064372)` |
| Vocabulary columns | 1,064,372 | same train-fitted 1,064,372 |
| Nonzero entries | 16,962,766 | 3,478,829 |
| dtype | float64 | float64 |
| Sparse | yes | yes |

Large vocabulary untuned bigrams/no cap ka actual consequence hai. Sparse storage essential
hai; serving memory/latency abhi benchmark nahi hui. Is step mein model artifact save nahi hua.

## Actual validation metrics

Positive label `1` dataset ka **phishing/spam** mix hai—not pure phishing only.

| Metric | TF-IDF + LR |
|---|---:|
| Accuracy | 0.9850855151171274 |
| Precision | 0.9844139650872819 |
| Recall | 0.986875 |
| F1 | 0.9856429463171036 |
| ROC-AUC | 0.9987274717870978 |

Confusion matrix order `[[TN, FP], [FN, TP]]`:

```text
[[5837,  100],
 [  84, 6316]]
```

**100 legitimate emails falsely flagged**; **84 phishing/spam emails missed**.
Recall detection coverage batata hai; precision alarm correctness. F1 dono balance karta hai,
but explicit security cost model nahi hai. ROC-AUC ranking measure karta hai, calibration nahi.

## Same validation split par Phase 3 comparison

Historical **train-only, unweighted** LR/RF validation results use kiye. Saved final RF use
nahi kiya, kyunki woh train+validation par refitted hai; validation uske liye independent nahi.
No handcrafted-model rerun hua.

| Model / representation | Accuracy | Precision | Recall | F1 | ROC-AUC | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| LR / ten handcrafted features | 0.718651212 | 0.727725082 | 0.731250000 | 0.729483283 | 0.784671657 | 1,751 | 1,720 |
| RF / ten handcrafted features | 0.864796952 | 0.903341289 | 0.827968750 | 0.864014349 | 0.941323559 | 567 | 1,101 |
| LR / TF-IDF text | 0.985085515 | 0.984413965 | 0.986875000 | 0.985642946 | 0.998727472 | 100 | 84 |

Measured deltas, **TF-IDF minus handcrafted**, 0–1 metric scale:

| Metric | vs handcrafted LR | vs handcrafted RF |
|---|---:|---:|
| Accuracy | +0.266434303 | +0.120288563 |
| Precision | +0.256688883 | +0.081072676 |
| Recall | +0.255625000 | +0.158906250 |
| F1 | +0.256159664 | +0.121628598 |
| ROC-AUC | +0.214055815 | +0.057403913 |

Vs LR: **1,651 fewer false alarms, 1,636 fewer misses**.
Vs RF: **467 fewer false alarms, 1,017 fewer misses**.
Yahan text representation measured validation metrics par help karti hai; precision/recall
tradeoff worsen nahi hua. Conclusion one metric se nahi—both errors aur all five metrics se hai.

Lekin comparison **apples-to-apples feature-space comparison nahi**: ten designer-chosen
statistics vs over one million learned lexical columns. LR-vs-LR classifier family same hone
se representation ki importance suggest hoti hai, but causal proof/general robustness claim nahi.
TF-IDF-vs-RF mein representation aur classifier family dono differ karte hain. Same rows/split
fair development comparison provide karte hain, identical information access nahi.

## Limitations aur interview takeaways

- Random split source-specific vocabulary/style ko share kar sakta hai; excluding `source`
  column alone source shortcuts remove nahi karta. High text scores shortcuts bhi reflect kar
  sakte hain, sirf genuine phishing semantics nahi.
- Exact deduplication near-duplicate/template leakage eliminate nahi karti. Lowercasing different
  case-preserved emails ko same representation bhi bana sakti hai; Phase 2 dedup policy unchanged.
- Mixed spam/phishing/fraud labels, historical emails, no source-disjoint/temporal validation.
- Bag-of-ngrams broad word order/context understand nahi karta. Bigrams limited adjacency dete
  hain; contextual embeddings/attention wala model abhi implemented nahi hai.
- Unknown terms dropped; empty/all-OOV text zero vector deta hai, LR intercept se probabilities
  milti hain. Valid numerical output informative evidence ki guarantee nahi.
- Probabilities calibrated prove nahi hui; no NLP test evaluation, text-model CV, tuning,
  inference latency/memory benchmark or production-level generalization evidence.
- Large vocabulary future operational consideration hai; this step ne uske basis par config
  change ya post-result pruning nahi ki.

Interview questions:
1. Why fit vocabulary only on train? Validation DF/vocabulary use karna representation leakage hai.
2. Sparse kyun? Har email few vocabulary columns use karta hai; dense zeros waste memory.
3. IDF rare word ko phishing bolta hai? Nahi, IDF label-free weighting hai; LR learns target relation.
4. Why no scaler? TF-IDF L2-normalized sparse representation; centering unsuitable/unnecessary here.
5. Higher score ka meaning? This same validation distribution par fewer misses/alarms—not production proof.
6. Why not compare saved RF predictions? Final RF validation par trained hai, unfair/leaky comparison hoga.

## Verification aur stop point

Reusable model factory: `src/models/nlp_baseline.py`.
Experiment orchestration: `scripts/train_nlp_baseline.py`.
Focused tests: `tests/test_models/test_nlp_baseline.py`.
Tests train-only vectorizer fit, vocabulary/IDF immutability during validation, sparse output,
ngram/lowercase behavior, schema rejection, probabilities, repeatability, OOV/empty handling,
and script-level forbidden test access verify karte hain.

Actual verification: **12 focused tests passed; full suite mein 95 tests passed**.
Teen new Python files ke editor diagnostics clean hain. Phase 2 aur Phase 3 LR/RF/registry
code unchanged hai. Classical artifact ka SHA-256 unchanged confirm hua:
`0fe95d47acb45a4caab6d600d6266b27efb44746e61e61e6a8e738337e9ffcc0`.
Raw CSVs aur existing artifacts ignored hain; koi new NLP artifact create nahi hua.

Debugging lesson: pandas column access static checker ko Series/DataFrame union lag sakta hai;
known single-column Series par narrow `cast` use kiya. Metrics return type floats ke saath
confusion matrix list bhi include karta hai; scalar metric keys par float cast kiya. Casts runtime
text/metrics change nahi karte, typing clarify karte hain. Real training run aur unit tests mein
failure nahi hua; convergence warning hoti toh script error raise karti, silently report nahi banati.

## Phase 4 Step 2 — DistilBERT fine-tuning preparation (remote run pending)

Is repository step mein **Kaggle-ready notebook aur reusable source helpers** implement hue hain;
actual Kaggle GPU training, validation run, model save, Hub push/reload abhi execute nahi hue.
Isliye GPU name, token-length distribution, chosen max length, losses, DistilBERT metrics aur
HF model identifier abhi report nahi kiye ja sakte. In values ko invent karna learning-first
project ke against hoga.

### Transformer intuition

Transformer sequence ke har token ka contextual representation surrounding tokens ke through
self-attention se banata hai. TF-IDF fixed lexical columns deta hai; transformer learned
contextual hidden states deta hai. Self-attention useful context combine karta hai, but quadratic
attention cost ki wajah se sequence length practical constraint hai.

**DistilBERT** BERT ka smaller distilled encoder hai: project ke Kaggle GPU constraint ke liye
chosen manageable checkpoint `distilbert/distilbert-base-uncased`. Pretrained model ko scratch
se train nahi karte, kyunki language representation already learned hoti hai; labeled project
emails se task adaptation cheaper hai. Fine-tuning mein encoder weights aur new two-class
classification head update honge. Tokenizer vocabulary fixed pretrained artifact hai—project
text par fit nahi hoti.

`AutoTokenizer` text ko WordPiece/subword tokens mein convert karta hai. Rare words, URLs ya
unknown strings multiple subwords ban sakte hain. `input_ids` vocabulary ke integer indices
hain; `attention_mask` real token=1 aur padding=0 mark karta hai. Sequence-classification
model first special token (`[CLS]` conceptual BERT classification position; DistilBERT uses
its first-token representation) se contextual vector lekar classification head ko deta hai.
Head two logits banata hai; softmax se classes `0=legitimate`, `1=phishing_spam` probabilities.

### Reusable run design

`src/data/nlp_dataset.py` same Phase 2 raw six-CSV → deterministic cleaning/dedup → seed-42
split flow use karta hai. It exposes only train/validation text+labels, while test ka counts
and label counts manifest audit ke liye record karta hai; test text/tokenization/prediction
expose nahi hota. CSV hashes aur ordered train/validation text-label hashes se Kaggle input
identity verify hoti hai. Current manifest counts: **57,574 train / 12,337 validation /
12,338 test**, with Phase 2 raw **82,486** and cleaned **82,249** rows.

`src/models/nlp_classifier.py` lazy-imports optional HF/Torch libraries, so local dependency-light
suite importable rehti hai. It provides:

- train-only full token-length audit and predeclared max-length selection;
- `NLPTrainingConfig` with seed 42, 3 epochs, batch 8 × accumulation 2, LR `2e-5`, weight decay
  `0.01`, warmup ratio `0.1`, linear scheduler and FP16;
- fixed tokenizer/model loading, train/validation-only tokenization, dynamic padding;
- Hugging Face `Trainer`, epoch-wise validation/save, best checkpoint by validation F1;
- local probability/prediction reload equivalence check and aggregate report helpers.

`notebooks/02_nlp_training.ipynb` orchestration cells install the project on Kaggle, verify
exactly one CUDA GPU and print actual GPU name, show token sample, measure **training-only**
length percentiles, then choose the smallest candidate among 128/256 reaching predeclared 90%
coverage under 256 memory cap. If coverage is not met, 256 is still selected and truncation
fraction/removed tokens are reported. Right truncation preserves the cleaned subject/body prefix
but can lose later URLs, quoted material or closing instructions. Dynamic padding pads only to
the longest example in each batch. OOM retry is not automatic; lower batch + higher accumulation
and its information/runtime tradeoff must be recorded as a new explicit run.

Two notebook approvals intentionally default False: inspect truncation report before training,
and inspect validation/loss/reload before HF upload. CPU fallback is forbidden. Test is never
passed to Trainer/evaluation. Hub upload is private by default, uses Kaggle Secret `HF_TOKEN`,
never prints the token, and uploads only model/tokenizer plus aggregate model card—not raw emails
or optimizer checkpoints. Public upload needs separate dataset license/privacy review.

### Current verification and limitations

Local focused tests: **9 passed**; full suite: **104 passed**. Notebook JSON/code syntax validated;
all code-cell outputs remain empty and unexecuted. New helper diagnostics are clean. Actual
Kaggle runtime, CUDA use, memory/quota behavior, training/validation loss curve, DistilBERT
validation metrics and Hub reload remain **pending**. Existing source-style shortcuts,
near-duplicates, mixed labels, historical data and random source composition remain limitations;
a future high score would not prove robust phishing understanding.

Interview takeaways:
1. Why pretrained fine-tuning? Scratch training needs much more data/compute; fine-tuning adapts
   general language representations to this labeled task.
2. Why max length? Transformer memory/attention cost grows with sequence length; finite positions
   force a documented truncation tradeoff.
3. Does tokenizer fit on our emails? No. Pretrained vocabulary/merge rules are fixed; only model
   parameters train on train labels.
4. Why dynamic padding? Avoid padding every email to global maximum, reducing wasted GPU memory.
5. Why test only after development decisions? Test remains independent held-out evidence.
6. Why not claim DistilBERT understands phishing from a score? Dataset shortcuts and validation
   distribution can produce high scores without robust semantic generalization.

**Stop: Phase 4 Step 2 implementation/preparation only.** No verified remote run yet; no FastAPI,
RAG, LangGraph, ensemble or later phase.
