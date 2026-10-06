# Python for ML (pandas) — Phase 2

> Only things actually implemented and measured in this project are recorded here.
> Updated so far: Phase 2, Step 2 (dataset loading + global exact deduplication) and
> Step 3 (deterministic text preprocessing) and Step 4 (stratified splitting).
> Phase 2 Step 5 feature notes and measured full-data verification are in `feature-engineering.md`.

## 1. The dataset on disk (measured)

Source: Kaggle "Phishing Email Dataset" (naserabdullahalam). Files live in
`data/raw/archive/` (gitignored — the data is never committed).

| File | Columns | Rows | Phishing share |
|---|---|---|---|
| `CEAS_08.csv` | sender, receiver, date, subject, body, label, urls | 39,154 | 0.558 |
| `Enron.csv` | subject, body, label | 29,767 | 0.470 |
| `Ling.csv` | subject, body, label | 2,859 | 0.160 |
| `Nazario.csv` | sender, receiver, date, subject, body, urls, label | 1,565 | 1.000 |
| `Nigerian_Fraud.csv` | sender, receiver, date, subject, body, urls, label | 3,332 | 1.000 |
| `SpamAssasin.csv` | sender, receiver, date, subject, body, label, urls | 5,809 | 0.296 |
| `phishing_email.csv` | text_combined, label (pre-combined copy) | 82,486 | — |

Result of `load_raw_emails()` on the real data:

- Shape: **82,486 rows x 4 columns** (`subject`, `body`, `label`, `source`)
- Class balance: **42,891 phishing (1)** / **39,595 legitimate (0)**, phishing share 0.52
- Missing values after filling: 0. Before filling, subject was missing in a few hundred rows
  (empty subject: 347 rows; empty body: 1 row; both empty: 0)
- Exact duplicate emails (subject + body): **0**; duplicates with conflicting labels: **0**
- After `deduplicate_emails()`: 82,486 rows (nothing removed)

## 2. Why we use the six per-source files, not `phishing_email.csv`

**Problem found by measuring, not assuming.** `phishing_email.csv` has the same 82,486
emails, but its text was already lowercased and stripped of punctuation: 0 uppercase
letters, 0 `!`, 0 `@`. URLs lose their structure (`http://a.b.com/x` becomes
`http a b com x`).

That would break the planned features:
- URL features cannot be extracted with a regex from text with no `://`, dots or slashes.
- Uppercase ratio and exclamation count would be constant zeros.

The per-source files keep the raw text (49,262 bodies contain uppercase, 27,751 contain `!`,
30,425 contain `@`, 38,839 contain `http`). The same total (82,486) and the same class
counts prove it is the same dataset. This was a correction to an implementation detail,
not a change to the dataset strategy.

**Lesson:** always inspect what preprocessing a "ready-made" dataset has already applied.
Information destroyed upstream cannot be recovered.

## 3. Design of `src/data/loader.py`

```
6 CSVs -> read only subject/body/label -> fill missing text with "" -> add `source`
       -> concat -> (later) build_email_text -> deduplicate_emails -> split (Step 4)
```

- `load_raw_emails()` — reads the six files, validates them, returns four columns.
- `build_email_text(subject, body)` — the single place where subject and body are combined
  (`subject + "\n\n" + body`). Training and later API serving must use the same function so
  the model sees the same representation.
- `deduplicate_emails()` — drops exact duplicates of the combined text, keeping the first.

Decisions:
- **`sender`, `receiver`, `date` and the pre-computed `urls` flag are never read.** They exist
  in only some files, so they identify the source rather than describe phishing (Nazario has
  no legitimate emails at all). They also would not exist in a real pasted email.
- **`source` is metadata only.** It is kept for per-source analysis and must never enter the
  model feature matrix.
- **The loader does not clean text.** No lowercasing, stripping or HTML removal. That is Step 3,
  so useful raw information (e.g. uppercase) is not lost silently.
- **Deduplication is exact and case-sensitive.** Normalizing before comparing would be cleaning.
- **Deduplication before the split is safe** because it only removes identical rows and learns
  nothing from the data (no leakage). Duplicates left across train/test would inflate metrics,
  because the test set would contain emails already seen in training.

## 4. pandas / Python concepts used

- **DataFrame**: a table in memory. `df.shape` is (rows, columns); `df.columns`; `df.dtypes`.
- **`pd.read_csv(path, usecols=...)`**: reads only the needed columns, which saves memory and
  also guarantees unwanted metadata never enters our data. `usecols` can be a function
  (`lambda c: c in REQUIRED_COLUMNS`) so files with different column sets all work.
- **`fillna("")`**: replaces missing values (NaN) with an empty string.
- **`pd.concat(frames, ignore_index=True)`**: stacks tables vertically and renumbers the index.
- **`Series.duplicated(keep="first")`**: boolean mask, True for every repeat after the first.
  `df.loc[~mask]` keeps the rows where the mask is False.
- **`value_counts()`**, **`groupby(...).agg(["count","mean"])`**: class balance and the phishing
  share per source (mean of a 0/1 label = share of 1s).
- **pandas 3.x** shows text columns as dtype `str` (older versions used `object`).
- **pytest `tmp_path`**: a temporary folder per test, so loader tests write tiny CSVs instead
  of needing the 500 MB dataset. Tests assert on behaviour (columns, filled blanks, errors,
  no mutation of the input).

## 5. Known limitations (to carry into evaluation documentation)

1. **Source shortcut risk.** Source composition differs a lot: Nazario and Nigerian_Fraud are
   100% phishing, Ling is 16%, SpamAssasin 30%, Enron 47%, CEAS_08 56%. Sources also have
   different formatting (e.g. Enron/Ling text is pre-tokenized like `hplno 531 . xls`; CEAS has
   raw text). A random stratified split keeps the overall phishing ratio, but a model may learn
   *source style* instead of phishing, which would inflate metrics. `source` stays metadata only;
   **per-source evaluation should be considered in Phase 3** and honestly reported.
2. **Exact deduplication only.** Exact dedup removed 0 rows, but near-duplicates (e.g. template
   spam differing by a few characters) are not detected. As a hint only: the already-normalized
   `phishing_email.csv` contained 408 duplicate rows after its lowercasing/punctuation removal,
   which suggests near-duplicates exist in the data. This was measured on a different
   representation than the one we use, so it is not proof. Step 3 removes exact duplicates
   after deterministic cleaning; near-duplicates differing in meaningful text remain.
3. **Dataset labels** are "phishing/spam" vs legitimate (the 1 class mixes phishing, spam and
   Nigerian-fraud emails), so this is not a pure phishing-only task.

## 6. Step 3 — Text preprocessing (`src/data/preprocessor.py`)

**Intuition.** Raw emails contain noise that has nothing to do with phishing (Windows line endings,
invisible characters, HTML leftovers, garbled accents). Cleaning removes that noise so features
and models see consistent text, while keeping the signal (case, `!`, URLs, `@`).

**Why it is safe before the split.** Every function is a pure function of ONE string. It learns
nothing from the dataset (no vocabulary, no averages), so it cannot leak information between
train and test. Fitted steps (TF-IDF, scalers) are different and wait until after the split.

### What we measured before writing any rule (82,486 emails)
| Noise | Emails affected |
|---|---|
| `\r` line endings | 31,657 (mostly Enron 28,796 and Ling 2,616) |
| 3+ blank lines | 34,139 (after counting subject+body together) |
| runs of 2+ spaces | 30,636 |
| non-breaking space `\xa0` | 2,630 |
| control / zero-width chars | 537 |
| HTML tags (known tag names) | a few hundred (~0.7%); no `<style>`/`<script>`/`<img>` at all |
| mojibake-looking text (`Ã`, `â€`, `Â`) | 83 |
| entities like `&amp;` | ~140 |

HTML turned out to be rare. The real noise was whitespace and line endings, so the design is
mostly whitespace normalization rather than a heavy HTML pipeline.

### What it does, in order (`clean_text`)
1. Remove invisible characters (control, zero-width).
2. `repair_mojibake` — fix `â€¢` -> `•`, `Â£` -> `£`, one suspicious sequence at a time.
3. `strip_html` — remove comments and a whitelist of real tag names; keep the target of
   `<a href="...">` as text so link URLs are still visible to URL features.
4. Decode entities that end with `;` (`&amp;`, `&#169;`).
5. `normalize_whitespace` — `\r\n`->`\n`, unicode spaces -> space, collapse runs of spaces,
   max one blank line, `strip()`. `clean_subject` additionally forces one line.

`preprocess_emails` = clean every email, then `deduplicate_emails` again, because cleaning can
make two different raw emails identical.

### Decisions and why
- **Whitelist of tag names, not `<[^>]*>`.** A generic pattern also removes `<http://...>`,
  `<user@host>` and `<what>`; 774 emails contain `<email@host>`. The tag name must be followed by
  whitespace, `/` or `>` so `<a@b.com>` is not mistaken for the `<a>` tag.
- **Keep `href` targets.** Only 10 emails have a URL exclusively inside an `href`, but stripping
  them would silently delete exactly what URL features need.
- **Only decode entities ending in `;`.** `html.unescape` alone would turn the `&copy` inside
  `page?a=1&copy=2` into a copyright sign and corrupt the URL.
- **No quoted-printable decoding.** `=3D` appears in only 227 emails, and the soft-line-break
  pattern `=\n` also matches decorative `=====` lines and Enron's `total supply = 5`, so decoding
  would corrupt real text.
- **Do not delete U+FFFD (�).** It marks information already lost; deleting it glues words together.
- **No lowercasing, no punctuation stripping.** That is exactly the damage that made
  `phishing_email.csv` unusable (section 2). Case and `!` are features.
- **No `ftfy` dependency.** The mojibake problem touches 83 emails; a small, tested function is
  enough and one fewer dependency to explain.

### Debugging lesson: test on real data, not just unit tests
All unit tests passed, yet running the cleaner on the real dataset and checking **idempotency**
(`clean(clean(x)) == clean(x)`) exposed a bug in my first mojibake repair:

- First version: encode the *whole* email as cp1252 and decode as UTF-8, all-or-nothing.
- Real emails mix mojibake (`Â©`) with a *genuine* non-breaking space (`\xa0`). One legitimate
  `\xa0` made the whole-text round trip fail, so nothing was repaired on pass 1. The `\xa0` was
  then turned into a space, and pass 2 succeeded -> not idempotent.
- My first guess (move invisible-character removal earlier) was wrong, which I confirmed by
  inspecting the actual failing bytes instead of assuming. Root cause: the repair unit was too big.
- Fix: repair each suspicious sequence on its own (a lead char `Ã..ô` followed by 1-3
  continuation chars), and keep a sequence only if that small piece decodes as valid UTF-8.
  Regression tests were added for the real failing pattern.

Also, one of my own tests briefly contained `... or True` and a comparison of a call with itself;
both would pass whatever the code did. Reviewing tests for assertions that cannot fail is part of
testing.

### Measured results of preprocessing (real data)
- Rows: 82,486 -> **82,249** after cleaning + dedup (**237 removed**; before cleaning exact dedup
  removed 0). Removed by source: CEAS_08 171, Nigerian_Fraud 24, Enron 22, Nazario 13,
  SpamAssasin 7, Ling 0.
- Duplicate groups after cleaning: 128, with **0 conflicting labels** (so dropping copies never
  discards a disagreement).
- Class balance after: **42,667 phishing / 39,582 legitimate** (phishing share 0.5188).
- Signal preserved exactly: emails with uppercase 49,448 -> 49,448; with `!` 29,393 -> 29,393;
  with `@` 30,734 -> 30,734; with `https?://` 32,087 -> 32,087.
- Noise removed: `\r` 31,657 -> 0; `\xa0` 2,630 -> 0; control/zero-width 537 -> 0;
  3+ newlines -> 0; 2+ spaces -> 0.
- Mojibake-looking emails 83 -> 28. The remaining matches include legitimate text (Portuguese
  `NÃO`) and malformed/unsupported sequences; these were left unchanged.
- Empty bodies after cleaning: 5 (was 1); empty subjects: 347; no email has both empty.
- Idempotency on the full dataset: all subjects and 82,485 of 82,486 bodies. The one exception is
  a Nazario email containing `pdf&amp;amp;jpeg`: first pass yields `pdf&amp;jpeg`, second pass
  yields `pdf&jpeg`. We intentionally decode **one layer per pass**, not recursively. Recursing
  could change legitimate literal entity text or expose encoded markup (e.g. `&amp;lt;script&amp;gt;`
  becomes a tag after multiple passes); suppressing all nested entities would preserve opaque
  markup instead of cleaning it. The same `clean_text` function is used once per input in training
  and will be used once for serving. Do not re-clean already-cleaned inputs; the one remaining
  non-idempotent email is a documented limitation with a regression test.
- Cleaning all emails takes about 7.7 seconds in this local run (not a performance guarantee).

### Limitations discovered
1. **URL presence is strongly source-correlated.** Emails containing `http(s)://`: CEAS_08 26,228,
   SpamAssasin 4,572, Nigerian_Fraud 1,100, Nazario 194, **Enron 0, Ling 0**. A URL feature may
   therefore partly measure *which source* an email came from. This adds to the source-shortcut
   risk in section 5 and should be checked with per-source evaluation in Phase 3.
2. **Near-duplicates remain.** Only exact duplicates of the cleaned text are removed.
3. **Cleaning changes most emails** (79,417 of 82,486 differ from raw, mainly via whitespace and
   line endings). That is expected, but it means the text a model sees is not the original
   byte-for-byte text.
4. **Mojibake repair is partial** by design; a wrong repair is considered worse than none.

### Interview takeaways (preprocessing)
- *"How do you avoid leakage in preprocessing?"* — Only stateless per-string rules run before the
  split. Anything that learns from data (vocabulary, scaling) is fit on the training split only.
- *"Why not just strip all `<...>`?"* — Emails contain `<user@host>` and `<http://...>`; I
  measured 774 emails with `<email@host>`, so I only strip known HTML tag names.
- *"How did you validate the cleaner?"* — Unit tests, then a before/after measurement on the real
  data (signals preserved, noise removed) and an idempotency check, which found a real bug.

## 7. Step 4 — Reproducible train/validation/test split (`src/data/splitter.py`)

**Level 1 — intuition:** Training emails teach the model, validation emails help choose settings,
and test emails are held back for a final unbiased check. If class 1 is ~52% overall, we want
roughly the same share in each group; otherwise a change in class mix can obscure comparisons.

**Level 2 — technical:** `train_test_split(..., stratify=emails["label"], random_state=42)`
randomly partitions rows while keeping the binary-label ratio approximately constant. Two splits
produce 70% training and 30% temporary, then divide temporary data 50/50 for validation and test
(70/15/15 overall). Rounding gives validation one fewer row than test. The same seed and the same
ordered input yield the same assignment. `source` is carried along as **metadata**, not used for
stratification and not part of any model feature matrix.

**Flow:** `load_raw_emails()` -> `preprocess_emails()` (clean and global exact dedup) ->
`split_emails()` -> train / validation / test. The split function refuses duplicate combined texts
or missing/invalid labels so this boundary is hard to bypass by accident. No vocabulary, scaler,
or other transformer is fitted here; such fitting happens **only on training data in later phases**.

Real-data results with default seed 42 (82,249 cleaned, deduplicated emails):

| Split | Rows | Legitimate (0) | Phishing/spam (1) | Share of 1 |
|---|---:|---:|---:|---:|
| Train | 57,574 | 27,707 | 29,867 | 0.51876 |
| Validation | 12,337 | 5,937 | 6,400 | 0.51876 |
| Test | 12,338 | 5,938 | 6,400 | 0.51872 |

The three sets have **zero exact combined-text overlap** and their union is all 82,249 rows.
All four columns (`subject`, `body`, `label`, `source`) are carried into each split. Source counts
on train / validation / test respectively: CEAS_08 27,252 / 5,885 / 5,846; Enron 20,833 /
4,397 / 4,515; Ling 2,023 / 436 / 400; Nazario 1,100 / 220 / 232; Nigerian_Fraud 2,318 /
529 / 461; SpamAssasin 4,048 / 870 / 884. We stratify by **label alone**. Source style may still
act as a shortcut even when the `source` column is excluded as a model feature; per-source
performance should be assessed in Phase 3. Near-duplicate templates are not prevented from
spanning splits by this exact-overlap check.

**Interview takeaway:** Why not fit preprocessing on all rows before splitting? Global exact
cleaning/dedup only applies fixed, row-local rules; learning a TF-IDF vocabulary or feature mean
from the validation/test emails would transfer information from holdout data into training and
make model evaluation less trustworthy.

## 8. Interview takeaways

- *"Why did you not use the pre-combined CSV?"* — I measured it: it was lowercased with
  punctuation removed, which would have made URL and uppercase/exclamation features impossible.
  The per-source files contained the same emails with the raw text.
- *"Why deduplicate before splitting?"* — Identical emails in both train and test inflate the
  metrics. Exact dedup learns nothing from the data, so doing it first causes no leakage.
- *"Why is `source` not a feature?"* — It would let the model learn dataset identity (Nazario is
  100% phishing) rather than phishing signals, and it does not exist at serving time.
