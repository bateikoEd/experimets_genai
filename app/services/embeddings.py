from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable, List

import numpy as np

from app.config import Settings, get_settings

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


class SimpleEmbeddingGenerator:
    """Lightweight embedding generator that hashes tokens into a dense vector."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.dimension = self.settings.embedding_dimension

    def embed(self, text: str) -> List[float]:
        tokens = TOKEN_PATTERN.findall(text.lower())
        if not tokens:
            return [0.0] * self.dimension

        vector = np.zeros(self.dimension, dtype=float)
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            idx = int(digest, 16) % self.dimension
            vector[idx] += 1.0

        norm = math.sqrt(float(np.dot(vector, vector)))
        if norm:
            vector /= norm
        return vector.round(6).tolist()


def batch_embed(generator: SimpleEmbeddingGenerator, texts: Iterable[str]) -> List[List[float]]:
    return [generator.embed(text) for text in texts]
