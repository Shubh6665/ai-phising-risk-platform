# Notebooks: orchestration, reusable logic nahi

`src/` source of truth hai. Notebook sirf environment setup, experiment orchestration aur
measured outputs inspect karta hai. Kaggle cells ko local GPU run samajhkar report nahi karna.

## `02_nlp_training.ipynb` — actual remote run abhi pending

### Kaggle setup

1. Kaggle notebook mein **GPU accelerator** aur **Internet** enable karo. GPU access ke liye
   Kaggle account verification/quota requirements ho sakte hain; availability assume nahi ki.
2. Current project snapshot private Kaggle source input ke roop mein attach karo. Snapshot mein
   `pyproject.toml`, `src/`, `docs/`, `tests/`, `scripts/` rakho. `.env`, credentials, `.venv`,
   `.git`, raw emails aur model weights include **mat** karo. Notebook exact source install
   karta hai; attached input read-only hai, so working copy `/kaggle/working/` mein banti hai.
3. Existing Kaggle phishing-email dataset separately attach karo. Six per-source CSVs same
   folder mein available hone chahiye; aggregated `phishing_email.csv` use nahi hoti.
4. Source/raw directory auto-discovery ambiguous hui toh cell clearly fail karegi. Arbitrary
   first match choose nahi hoga. Input attachments correct karo; filenames silently rename nahi.
5. Notebook cells top-to-bottom clean session mein run karo. Local manifest CSV hashes, exact
   train/validation text+label order aur all split counts verify karega.

### Training review gates

- Length audit **training data only** par hai; chosen length plus truncation fraction inspect karo.
- `APPROVE_TRUNCATION_AND_TRAINING = False` default intentional hai. Length report review ke
  baad True set karke continue karo. Default Run All approval cell par stop hota hai.
- Initial config: 3 epochs, LR 2e-5, weight decay 0.01, batch 8, accumulation 2, seed 42;
  epoch-wise validation/best F1 checkpoint. No test evaluation or hyperparameter sweep.
- GPU unavailable ho toh CPU fallback nahi. OOM ho toh failure report preserve karo; batch 4
  + accumulation 4 effective batch 16 maintain kar sakta hai. Length reduction tail-information
  loss increase karti hai. Changes explicit new run/configuration ke roop mein record karo;
  existing run overwrite/resume silently mat karo. Quota/runtime limits actual report mein likho.

### Artifact / HF Hub

Kaggle-only files `model_artifacts/nlp/` ke under rahenge; large weights git mein nahi.
Local reload validation prefix ke 32 fixed examples use karta hai. Same FP32 eval-mode forward
mein labels exactly equal, probabilities absolute tolerance 1e-6; yeh mixed-precision Trainer
logits ke bitwise-match claim se different hai. Saved tokenizer chosen max length preserve karta hai.

Validation/loss/history + local reload review ke baad `APPROVE_VALIDATION_FOR_UPLOAD` True karo.
Kaggle Secrets mein **`HF_TOKEN`** write-scoped token add/enable karo—cell mein value paste mat karo.
Default private repo: runtime HF owner + `/phishing-risk-distilbert`; actual complete identifier
successful run report mein milega. Existing repo overwrite nahi hoti. Public repo only if dataset
licensing, privacy/memorization risks aur publication rights independently reviewed hain.
Model card/config/tokenizer/weights only upload hote hain; raw emails/optimizer checkpoints nahi.
Hub reload exact uploaded commit SHA use karta hai; success ke bina Hub verification claim nahi.

### Return these measured outputs

Download:
- `/kaggle/working/model_artifacts/nlp/distilbert-step2-report.json`
- `environment-requirements.txt`
- failure report, if any
- executed notebook for review (committing se pehle outputs/possible secrets clear karo)

Report se actual GPU, base revision, sequence-length distribution/truncation, epochs/losses,
validation metrics/confusion, baseline comparison, local/Hub reload aur HF identifier verify
karke `docs/learning/nlp-transformers.md` / `docs/evaluation_results.md` update karenge.
Raw emails/weights/secret token conversation ya git mein share mat karo.

**Current verification:** notebook Python syntax aur local dependency-light contract tests;
real Kaggle/HF execution **pending**. No FastAPI/RAG/LangGraph/later-phase work.
