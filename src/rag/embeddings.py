"""Embedding providers and test doubles for vector generation."""

import hashlib
from typing import Protocol, Sequence
import numpy as np


class Embedder(Protocol):
    """Protocol for vector embedding generators."""

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class SentenceTransformerEmbedder:
    """Generates dense embeddings using sentence-transformers (default: all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self.dimension = self._model.get_sentence_embedding_dimension()
        self.max_seq_length = self._model.max_seq_length

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._model.encode(list(texts), convert_to_numpy=True)
        return embeddings.tolist()


class DummyEmbedder:
    """Deterministic, offline test double for unit tests without network or model weights."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.max_seq_length = 256

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            # Deterministic, non-zero unit vector generated from MD5 digest
            seed_bytes = hashlib.md5(text.encode("utf-8")).digest()
            raw_vals = [float((b + i) % 100) / 100.0 for i, b in enumerate(seed_bytes)]
            # Expand or cycle up to target dimension
            tiled = (raw_vals * (self.dimension // len(raw_vals) + 1))[: self.dimension]
            # Normalize vector to unit length
            norm = sum(x * x for x in tiled) ** 0.5 or 1.0
            normalized = [x / norm for x in tiled]
            results.append(normalized)
        return results

