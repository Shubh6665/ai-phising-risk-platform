# Python for ML (pandas) — Phase 2

> Only things actually implemented and measured in this project are recorded here.
> Updated so far: Phase 2, Step 2 (dataset loading + global exact deduplication).

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
   representation than the one we use, so it is not proof; whether to address near-duplicates
   (e.g. after cleaning in Step 3) is an open decision.
3. **Dataset labels** are "phishing/spam" vs legitimate (the 1 class mixes phishing, spam and
   Nigerian-fraud emails), so this is not a pure phishing-only task.

## 6. Interview takeaways

- *"Why did you not use the pre-combined CSV?"* — I measured it: it was lowercased with
  punctuation removed, which would have made URL and uppercase/exclamation features impossible.
  The per-source files contained the same emails with the raw text.
- *"Why deduplicate before splitting?"* — Identical emails in both train and test inflate the
  metrics. Exact dedup learns nothing from the data, so doing it first causes no leakage.
- *"Why is `source` not a feature?"* — It would let the model learn dataset identity (Nazario is
  100% phishing) rather than phishing signals, and it does not exist at serving time.
