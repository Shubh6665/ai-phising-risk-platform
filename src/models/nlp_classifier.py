"""DistilBERT preparation/training helpers; optional GPU libraries lazy-load hoti hain."""

import importlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from src.evaluation.metrics import compute_classification_metrics

BASE_CHECKPOINT = "distilbert/distilbert-base-uncased"
ID2LABEL = {0: "legitimate", 1: "phishing_spam"}


@dataclass(frozen=True)
class NLPTrainingConfig:
    max_length: int
    num_train_epochs: int = 3
    train_batch_size: int = 8
    eval_batch_size: int = 8
    gradient_accumulation_steps: int = 2
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    seed: int = 42

    def __post_init__(self):
        if not 4 <= self.max_length <= 512:
            raise ValueError("DistilBERT length special tokens sahit 4..512 honi chahiye")
        if min(self.num_train_epochs, self.train_batch_size, self.eval_batch_size, self.gradient_accumulation_steps) < 1:
            raise ValueError("Epochs/batch/accumulation positive hone chahiye")
        if self.learning_rate <= 0 or self.weight_decay < 0 or not 0 <= self.warmup_ratio < 1:
            raise ValueError("Invalid optimizer configuration")
        if self.seed != 42:
            raise ValueError("Project experiment ka reproducible seed 42 hai")

    def to_dict(self) -> dict:
        return asdict(self)


def training_token_lengths(tokenizer: Any, train_text: list[str], *, batch_size: int = 128) -> np.ndarray:
    """Train-only full token lengths; encoder ko oversized sequence feed nahi hoti."""
    if not train_text or batch_size < 1:
        raise ValueError("Nonempty training text aur positive batch size required")
    lengths = []
    for start in range(0, len(train_text), batch_size):
        encoded = tokenizer(
            train_text[start:start + batch_size], truncation=False, padding=False,
            add_special_tokens=True, return_attention_mask=False,
            return_token_type_ids=False, verbose=False,
        )
        lengths.extend(len(ids) for ids in encoded["input_ids"])
    return np.asarray(lengths, dtype=np.int64)


def choose_max_length(lengths: np.ndarray, *, memory_cap: int = 256, target_coverage: float = 0.9) -> dict:
    """Predeclared memory cap; measured coverage se 128/256 choice, no metric tuning."""
    if memory_cap not in (128, 256, 512) or not 0 < target_coverage <= 1:
        raise ValueError("Invalid cap/coverage")
    if lengths.ndim != 1 or not len(lengths) or np.any(lengths < 2):
        raise ValueError("Special-token-inclusive lengths required")
    candidates = [length for length in (128, 256, 512) if length <= memory_cap]
    coverage = {str(length): float(np.mean(lengths <= length)) for length in candidates}
    selected = next((length for length in candidates if coverage[str(length)] >= target_coverage), memory_cap)
    return {
        "training_documents": len(lengths),
        "percentiles": {str(p): float(np.percentile(lengths, p)) for p in (50, 75, 90, 95, 99)},
        "maximum_tokens": int(lengths.max()),
        "coverage_by_length": coverage,
        "memory_cap": memory_cap, "target_coverage": target_coverage,
        "max_length": selected,
        "target_met": coverage[str(selected)] >= target_coverage,
        "truncated_documents": int(np.sum(lengths > selected)),
        "truncated_fraction": float(np.mean(lengths > selected)),
        "removed_tokens": int(np.maximum(lengths - selected, 0).sum()),
        "truncation_side": "right", "padding": "dynamic_batch",
    }


def create_distilbert_components(revision: str):
    """Same resolved HF commit se pretrained tokenizer aur two-class model load karo."""
    transformers = importlib.import_module("transformers")
    transformers.set_seed(42)
    tokenizer = transformers.AutoTokenizer.from_pretrained(BASE_CHECKPOINT, revision=revision, use_fast=True)
    tokenizer.truncation_side = "right"
    tokenizer.padding_side = "right"
    model = transformers.AutoModelForSequenceClassification.from_pretrained(
        BASE_CHECKPOINT, revision=revision, num_labels=2,
        id2label=ID2LABEL, label2id={name: index for index, name in ID2LABEL.items()},
        use_safetensors=True,
    )
    return tokenizer, model


def tokenize_development(tokenizer: Any, train_text: list[str], train_labels: list[int],
                         validation_text: list[str], validation_labels: list[int], *, max_length: int) -> dict:
    """Only train/validation arguments; fixed tokenizer, no fit and no test dataset."""
    NLPTrainingConfig(max_length=max_length)
    datasets = importlib.import_module("datasets")
    result = {}
    for name, texts, labels in (("train", train_text, train_labels), ("validation", validation_text, validation_labels)):
        if len(texts) != len(labels) or not texts or set(labels) != {0, 1}:
            raise ValueError("Both binary classes aur matching nonempty text/labels required")
        dataset = datasets.Dataset.from_dict({"text": texts, "labels": labels})
        result[name] = dataset.map(
            lambda batch: tokenizer(batch["text"], truncation=True, max_length=max_length,
                                    padding=False, return_token_type_ids=False),
            batched=True, batch_size=128, remove_columns=["text"],
        )
    return result


def transformer_metrics(prediction: Any) -> dict:
    """Stable softmax se positive class-1 probability; existing metrics reuse karo."""
    raw = prediction.predictions
    logits = np.asarray(raw[0] if isinstance(raw, tuple) else raw, dtype=np.float64)
    labels = np.asarray(prediction.label_ids)
    if logits.shape != (len(labels), 2) or not np.isfinite(logits).all():
        raise ValueError("Expected finite [rows, 2] logits")
    scores = np.exp(logits - logits.max(axis=1, keepdims=True))
    probabilities = scores / scores.sum(axis=1, keepdims=True)
    return compute_classification_metrics(labels.tolist(), logits.argmax(axis=1).tolist(), probabilities[:, 1].tolist())


def _trainer_metrics(prediction: Any) -> dict:
    # Trainer logs scalar metrics; full confusion matrix final validation report mein rehti hai.
    return {name: value for name, value in transformer_metrics(prediction).items() if name != "confusion_matrix"}


def build_trainer(model: Any, tokenizer: Any, development: dict, config: NLPTrainingConfig, output_dir: Path):
    """CUDA required; no test key, no automatic OOM config changes, no Hub push during training."""
    torch = importlib.import_module("torch")
    transformers = importlib.import_module("transformers")
    if not torch.cuda.is_available():
        raise RuntimeError("Kaggle CUDA GPU enable karo; CPU training automatically nahi hogi")
    if set(development) != {"train", "validation"}:
        raise ValueError("Trainer ko sirf train/validation datasets do")
    for dataset in development.values():
        if set(dataset.column_names) != {"input_ids", "attention_mask", "labels"}:
            raise ValueError("Unexpected model columns; source/text metadata allowed nahi")
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError("Existing run directory overwrite mat karo")
    arguments = transformers.TrainingArguments(
        output_dir=str(output_dir), num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.train_batch_size,
        per_device_eval_batch_size=config.eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate, weight_decay=config.weight_decay,
        warmup_ratio=config.warmup_ratio, lr_scheduler_type="linear", optim="adamw_torch",
        eval_strategy="epoch", save_strategy="epoch", save_total_limit=2,
        load_best_model_at_end=True, metric_for_best_model="f1", greater_is_better=True,
        seed=config.seed, data_seed=config.seed, fp16=True,
        logging_strategy="steps", logging_steps=100, report_to="none",
        push_to_hub=False, save_safetensors=True, dataloader_num_workers=0,
    )
    return transformers.Trainer(
        model=model, args=arguments, train_dataset=development["train"],
        eval_dataset=development["validation"], processing_class=tokenizer,
        data_collator=transformers.DataCollatorWithPadding(tokenizer=tokenizer, padding=True),
        compute_metrics=_trainer_metrics,
    )


def sample_probabilities(model: Any, tokenizer: Any, texts: list[str], *, max_length: int, batch_size: int = 8) -> np.ndarray:
    """Deterministic eval-mode FP32 forward; dropout off, same-device reload comparison."""
    torch = importlib.import_module("torch")
    if not texts or batch_size < 1:
        raise ValueError("Nonempty deterministic sample required")
    model.eval()
    device = next(model.parameters()).device
    batches = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            inputs = tokenizer(texts[start:start + batch_size], truncation=True, max_length=max_length,
                               padding=True, return_token_type_ids=False, return_tensors="pt")
            inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
            batches.append(torch.softmax(model(**inputs).logits.float(), dim=-1).cpu().numpy())
    return np.concatenate(batches)


def verify_probability_reload(reference: np.ndarray, reloaded: np.ndarray) -> dict:
    """Probabilities tolerance 1e-6; hard predictions exactly identical hone chahiye."""
    if reference.shape != reloaded.shape or reference.ndim != 2 or reference.shape[1] != 2:
        raise ValueError("Expected matching [sample_rows, 2] probabilities")
    if not np.isfinite(reference).all() or not np.isfinite(reloaded).all():
        raise ValueError("Probabilities must be finite")
    np.testing.assert_array_equal(reference.argmax(axis=1), reloaded.argmax(axis=1))
    np.testing.assert_allclose(reference, reloaded, rtol=0, atol=1e-6)
    return {"sample_rows": len(reference), "identical_predictions": True,
            "probabilities_atol": 1e-6, "max_absolute_difference": float(np.max(np.abs(reference - reloaded)))}
