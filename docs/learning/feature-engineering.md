# Feature engineering — Phase 2 Step 5

## What it is and where it fits

**Level 1:** A feature is a measurable description of one email, such as its number of links or
exclamation marks. It is not a phishing prediction. Different emails become rows of numbers with
the same columns; a future model can learn from those rows.

**Level 2:** The extractors are deterministic, stateless functions of a single email's combined
text. They do not learn a vocabulary or scale numeric columns. `src/features/feature_pipeline.py`
uses `build_email_text(subject, body)` from `src/data/loader.py` to create a single reproducible
representation. Call `extract_features()` on each *already cleaned* split independently:

`load_raw_emails` -> `preprocess_emails` -> `split_emails` -> `extract_features` per split

Never fit TF-IDF, scalers or other data-dependent transformations on the entire dataset; those
belong to later phases and must be fitted on training data only.

## The implemented features

From `src/features/text_features.py`:

| Feature | Meaning |
|---|---|
| `word_count` | Count of `\b\w+\b` tokens (including numbers/underscores) |
| `average_word_length` | Sum of token lengths / token count; 0 for no tokens |
| `uppercase_ratio` | Uppercase alphabetic chars / all alphabetic chars; 0 for no letters |
| `exclamation_count` | Literal `!` count |
| `phishing_keyword_count` | Whole-word, case-insensitive occurrence count of predefined `verify`, `account`, `urgent`, `click`, `suspended` |

The fixed keyword list is a design choice, not a learned list or a claim that these words prove
phishing. It can produce false positives (e.g. a legitimate account notice).

From `src/features/url_features.py` (parsed offline; **no HTTP requests or DNS lookups**):

| Feature | Meaning |
|---|---|
| `url_count` | Number of parseable HTTP(S) URLs found in the combined email |
| `https_url_count` | How many use HTTPS (not a guarantee of safety) |
| `max_url_length` | Longest extracted URL length |
| `max_hostname_dot_count` | Largest dot count among parsed hostnames |
| `has_ip_address_url` | 1 if at least one link's hostname parses as an IP address, else 0 |

For no URL, every URL feature is 0. When there are multiple URLs, counts cover all links and
length/dot-count take the maximum. `urlsplit` and `ipaddress` analyze the strings without
contacting any host. URLs found only inside HTML `href` remain available because Step 3 cleaning
preserves their targets. Regex extraction trims common sentence punctuation; it can truncate
legitimate URLs ending with those characters. Bare `www.example.com` or relative links do not
match. Some source datasets had URLs stripped/pre-tokenized before loading; they cannot be
recovered by this extractor.

## Feature-matrix boundary

`extract_features(emails)` reads **only** `subject` and `body`. It returns ten numerical columns
in a fixed order (`TEXT_FEATURE_NAMES + URL_FEATURE_NAMES`), with one row per input email and
no `label`, `source`, raw text or pre-computed dataset `urls` flag. The `source` column stays on
the input splits for later per-source evaluation; it cannot enter this matrix accidentally.
The extractor does not clean again (Step 3's entity decode is intentionally one-pass) or learn
statistics from other rows. An empty input returns an empty DataFrame with the same numeric
schema; this behavior was added after a small test caught pandas inferring float columns for
an empty input and failing to concatenate subject and body.

## Checks performed and limitations

Unit tests use in-memory examples, not the raw dataset. They cover empty emails and matrices,
repeated whole-word keywords, uppercase ratios, punctuation, link targets from HTML, multiple
links, missing/malformed links, IPv6, IPs only in the URL path/query, output dtypes, one-to-one
batch alignment and the absence of metadata in the feature matrix. A test initially failed
because its handwritten expected letter count was off by one; checking the tokens fixed the
*test*, not the extractor. An empty-table test caught pandas inferring float columns on empty
input; the pipeline now returns a stable numeric schema for that case.

A test blocks DNS resolution and socket connections while extracting features from actual URL
strings, confirming extraction does not make a network call. Code inspection confirms it uses
only `re`, `urllib.parse.urlsplit` and `ipaddress`, not any HTTP/DNS client. URLs are **never
fetched**; a parsed address does not imply the destination is safe or reachable.

### Measured full-data verification (Python 3.12; default split seed 42)

The actual six raw CSVs were loaded, cleaned, globally deduplicated (82,249 remaining), and split
with `split_emails()`. Feature extraction was run **separately** on train, validation and test in
sequential batches of 512 to bound memory usage. For every batch, the row count, schema, numeric
dtypes and 0-based output index were checked; the first and last rows were cross-checked against
independent per-email extraction. A separate test checks that a batch matches individually
extracted rows even if the input DataFrame index is irregular.

| Split | Input rows | Feature rows | NaNs | Infinite values |
|---|---:|---:|---:|---:|
| Train | 57,574 | 57,574 | 0 | 0 |
| Validation | 12,337 | 12,337 | 0 | 0 |
| Test | 12,338 | 12,338 | 0 | 0 |

Every batch in every split had **exactly** these ordered columns:
`word_count`, `average_word_length`, `uppercase_ratio`, `exclamation_count`,
`phishing_keyword_count`, `url_count`, `https_url_count`, `max_url_length`,
`max_hostname_dot_count`, `has_ip_address_url`.

All columns were numeric. `average_word_length` and `uppercase_ratio` were `float64`; the other
eight were `int64`. The output contained **only** these ten columns; `source` and `label` were
explicitly absent. Feature rows were 1:1 with input rows and in input order (the output index is
reset to 0..N-1 within each batch). The extracted values themselves were not used for training.

Nonzero **row counts**, measured over all rows in each split (a count of emails for which the
feature is nonzero, **not** the sum of feature values):

| Feature | Train | Validation | Test |
|---|---:|---:|---:|
| `word_count` | 57,573 | 12,337 | 12,338 |
| `average_word_length` | 57,573 | 12,337 | 12,338 |
| `uppercase_ratio` | 34,449 | 7,445 | 7,351 |
| `exclamation_count` | 20,444 | 4,405 | 4,396 |
| `phishing_keyword_count` | 10,909 | 2,326 | 2,326 |
| `url_count` | 22,400 | 4,830 | 4,802 |
| `https_url_count` | 1,501 | 302 | 335 |
| `max_url_length` | 22,400 | 4,830 | 4,802 |
| `max_hostname_dot_count` | 22,365 | 4,823 | 4,797 |
| `has_ip_address_url` | 110 | 24 | 23 |

A separate check found that an empty email yields zeros/defaults for all features, and an email
with no detected HTTP(S) URL yields zero for all five URL features. Pandas may coerce a mixed
integer/float **row** accessed with `.iloc[0]` to float when printing a dictionary (e.g. `0.0`);
that does not change the per-column `int64`/`float64` schema reported above.

**Limitations:** These are descriptive counts, *not* metrics or evidence of predictive usefulness.
Phase 3 should evaluate per-source behavior: URL presence and email formatting differ sharply
among the six source datasets, so even without a `source` feature, a model could learn
source-specific shortcuts. Regex link parsing will miss bare/relative URLs and URLs mangled by
upstream dataset processing.

**Interview takeaway:** Why can these rules run without fitting? Every output depends only on one
email and fixed code. A TF-IDF vocabulary, by contrast, depends on the frequency of words across
emails, so fitting it on validation/test data would cause leakage.

## Phase 2 completion checkpoint

**Status: complete.** The existing ten features are sufficient for the planned Phase 2 scope:
text statistics and fixed keyword signals, URL structure from the same email, and a combined
numeric matrix with deterministic tests. No additional features were added for feature-count
padding, and no model was trained or evaluated.

Verified pipeline:

```text
Raw per-source CSVs
→ deterministic cleaning
→ exact deduplication
→ stratified 70/15/15 split (seed 42)
→ deterministic text + URL feature extraction
→ numeric feature matrix
```

`load_raw_emails()` loads the six source files; `preprocess_emails()` cleans and globally
exact-deduplicates; `split_emails()` partitions the result; `extract_features()` runs separately
on each split. Subject and body are combined in `build_email_text()`. Source remains analysis
metadata and neither source nor label enters the feature matrix. No train/holdout-dependent
fitting occurs in Phase 2.

Measured raw count: **82,486** (42,891 class 1 / 39,595 class 0). After cleaning and exact
deduplication: **82,249** (42,667 class 1 / 39,582 class 0), removing **237** rows. Final splits:
train **57,574**, validation **12,337**, test **12,338**, with zero exact combined-text overlap.
The prior full-data feature verification covered all these rows and found no NaNs or infinities.
The final full suite contains **51 passing tests**, including 14 feature tests. Raw CSVs remain
ignored. `implementation_plan.md` is retained unchanged as the original planning document;
these learning notes record the actual implementation decisions and measured results.

Remaining limitations are documented, not blockers for this phase: source-formatting shortcuts,
near-duplicates not caught by exact deduplication, regex URL coverage, mixed phishing/spam label
semantics, and one-pass entity decoding (one real body changes if cleaned again). Predictive
performance remains unmeasured. Phase 3 requires a separate explicit instruction.
