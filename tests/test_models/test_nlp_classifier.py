import ast
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from src.models import nlp_classifier as nlp


def test_predeclared_config_and_length_choice():
    config = nlp.NLPTrainingConfig(max_length=256)
    assert config.seed == 42 and config.num_train_epochs == 3
    assert config.learning_rate == 2e-5 and config.weight_decay == 0.01
    assert config.train_batch_size * config.gradient_accumulation_steps == 16
    assert nlp.choose_max_length(np.array([10, 20, 128]))["max_length"] == 128
    decision = nlp.choose_max_length(np.array([20, 200, 600]))
    assert decision["max_length"] == 256 and not decision["target_met"]
    assert decision["truncated_documents"] == 1
    assert decision["removed_tokens"] == 344
    assert decision["truncation_side"] == "right"
    for length in (0, 513):
        with pytest.raises(ValueError):
            nlp.NLPTrainingConfig(max_length=length)
    with pytest.raises(ValueError):
        nlp.NLPTrainingConfig(max_length=256, seed=0)
    with pytest.raises(ValueError):
        nlp.choose_max_length(np.array([]))


def test_length_audit_has_no_truncation_or_padding():
    calls = []

    def tokenizer(texts, **kwargs):
        calls.append(kwargs)
        assert kwargs["truncation"] is False and kwargs["padding"] is False
        assert kwargs["add_special_tokens"] is True
        return {"input_ids": [[0] * (len(text) + 2) for text in texts]}

    lengths = nlp.training_token_lengths(tokenizer, ["a", "bbb", ""], batch_size=2)
    np.testing.assert_array_equal(lengths, [3, 5, 2])
    assert len(calls) == 2


def test_tokenize_development_uses_fixed_tokenizer_and_no_metadata(monkeypatch):
    class Dataset:
        rows: dict

        @classmethod
        def from_dict(cls, rows):
            value = cls()
            value.rows = rows
            assert set(rows) == {"text", "labels"}
            return value

        def map(self, function, **kwargs):
            assert kwargs["remove_columns"] == ["text"]
            return {**function(self.rows), "labels": self.rows["labels"]}

    original = nlp.importlib.import_module
    monkeypatch.setattr(nlp.importlib, "import_module", lambda name: SimpleNamespace(Dataset=Dataset) if name == "datasets" else original(name))
    calls = []

    def tokenizer(texts, **kwargs):
        calls.append((texts, kwargs))
        assert kwargs == {"truncation": True, "max_length": 128, "padding": False, "return_token_type_ids": False}
        return {"input_ids": [[1, 2]] * len(texts), "attention_mask": [[1, 1]] * len(texts)}

    result = nlp.tokenize_development(tokenizer, ["train-a", "train-b"], [0, 1], ["val-a", "val-b"], [0, 1], max_length=128)
    assert set(result) == {"train", "validation"} and len(calls) == 2
    assert calls[0][0] == ["train-a", "train-b"] and calls[1][0] == ["val-a", "val-b"]


def test_metrics_use_positive_softmax_probability_and_confusion_matrix():
    prediction = SimpleNamespace(predictions=np.array([[1000, 998], [998, 1000], [1000, 1001], [1001, 1000]]), label_ids=np.array([0, 1, 0, 1]))
    metrics = nlp.transformer_metrics(prediction)
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["accuracy"] == metrics["precision"] == metrics["recall"] == metrics["f1"] == 0.5
    assert set(nlp._trainer_metrics(prediction)) == {"accuracy", "precision", "recall", "f1", "roc_auc"}
    with pytest.raises(ValueError):
        nlp.transformer_metrics(SimpleNamespace(predictions=np.array([[float("nan"), 0]]), label_ids=[0]))


def test_probability_reload_requires_identical_predictions_and_close_probabilities():
    reference = np.array([[0.9, 0.1], [0.2, 0.8]])
    assert nlp.verify_probability_reload(reference, reference.copy())["max_absolute_difference"] == 0
    close = reference + np.array([[1e-8, -1e-8], [0, 0]])
    assert nlp.verify_probability_reload(reference, close)["identical_predictions"]
    with pytest.raises(AssertionError):
        nlp.verify_probability_reload(reference, reference[:, ::-1])
    with pytest.raises(AssertionError):
        nlp.verify_probability_reload(reference, reference + 0.01)


def test_trainer_contract_and_forbidden_test_dataset(monkeypatch, tmp_path):
    captured = {}

    def arguments(**kwargs):
        captured["arguments"] = kwargs
        return SimpleNamespace(**kwargs)

    def trainer(**kwargs):
        captured["trainer"] = kwargs
        return SimpleNamespace(**kwargs)

    fake_transformers = SimpleNamespace(TrainingArguments=arguments, Trainer=trainer, DataCollatorWithPadding=lambda **kwargs: kwargs)
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True))
    original = nlp.importlib.import_module
    monkeypatch.setattr(nlp.importlib, "import_module", lambda name: {"torch": fake_torch, "transformers": fake_transformers}.get(name) or original(name))
    dataset = SimpleNamespace(column_names=["input_ids", "attention_mask", "labels"])
    development = {"train": dataset, "validation": dataset}
    nlp.build_trainer(object(), object(), development, nlp.NLPTrainingConfig(max_length=256), tmp_path / "run")
    args = captured["arguments"]
    assert args["eval_strategy"] == args["save_strategy"] == "epoch"
    assert args["load_best_model_at_end"] and args["metric_for_best_model"] == "f1"
    assert args["seed"] == args["data_seed"] == 42
    assert args["report_to"] == "none" and not args["push_to_hub"]
    assert captured["trainer"]["train_dataset"] is dataset
    with pytest.raises(ValueError, match="sirf"):
        nlp.build_trainer(object(), object(), {**development, "test": dataset}, nlp.NLPTrainingConfig(max_length=256), tmp_path / "run")
    fake_torch.cuda.is_available = lambda: False
    with pytest.raises(RuntimeError, match="CUDA"):
        nlp.build_trainer(object(), object(), development, nlp.NLPTrainingConfig(max_length=256), tmp_path / "run")


def test_notebook_is_unexecuted_valid_python_and_has_explicit_review_gates():
    path = Path(__file__).resolve().parents[2] / "notebooks/02_nlp_training.ipynb"
    notebook = json.loads(path.read_text())
    assert notebook["nbformat"] == 4
    ids = [cell["id"] for cell in notebook["cells"]]
    assert len(ids) == len(set(ids))
    code = []
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell["outputs"] == [] and cell["execution_count"] is None
            # Jupyter spec allows source as str OR list[str]; normalise before parsing.
            cell_src = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
            ast.parse(cell_src)
            code.append(cell_src)
    source = "\n".join(code)
    assert "development['test']" not in source and "data.test_text" not in source
    assert "APPROVE_TRUNCATION_AND_TRAINING = False" in source
    assert "APPROVE_VALIDATION_FOR_UPLOAD = False" in source
    assert "PUBLIC_HUB_REPOSITORY = False" in source
    assert "get_secret('HF_TOKEN')" in source
    assert "revision=hub_revision" in source
    assert "verify_probability_reload(reference_probabilities, hub_probabilities)" in source
