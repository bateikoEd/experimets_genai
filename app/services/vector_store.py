from __future__ import annotations

import json
from typing import List, Sequence, Tuple

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Embedding, House


class LocalVectorStore:
    """Simple cosine-similarity vector store persisted to disk for reproducibility."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.snapshot_path = self.settings.vector_store_path / "vectors.json"
        self._records: List[Tuple[int, np.ndarray]] = []

    def load_from_db(self, session: Session) -> None:
        embeddings = session.scalars(select(Embedding)).all()
        self._records = [
            (embedding.house_id, np.asarray(embedding.vector, dtype=float))
            for embedding in embeddings
            if embedding.vector
        ]
        self._persist_snapshot()

    def _persist_snapshot(self) -> None:
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {"house_id": house_id, "vector": record.tolist()}
            for house_id, record in self._records
        ]
        self.snapshot_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    def top_k(self, query_vector: Sequence[float], k: int) -> List[Tuple[int, float]]:
        if not self._records:
            return []
        q = np.asarray(query_vector, dtype=float)
        norm = np.linalg.norm(q)
        if norm:
            q = q / norm
        scores = []
        for house_id, vector in self._records:
            denom = np.linalg.norm(vector)
            if denom == 0:
                continue
            sim = float(np.dot(q, vector / denom))
            scores.append((house_id, sim))
        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:k]


class VectorStoreService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.store = LocalVectorStore(self.settings)

    def sync_embeddings(self, session: Session, generator) -> int:
        houses = session.scalars(select(House)).all()
        upserted = 0
        for house in houses:
            if not house.description:
                continue
            embedding = session.scalars(
                select(Embedding).where(Embedding.house_id == house.id)
            ).first()
            vector = generator.embed(house.description)
            if embedding:
                embedding.vector = vector
            else:
                embedding = Embedding(house_id=house.id, vector=vector)
                session.add(embedding)
            upserted += 1
        session.flush()
        self.store.load_from_db(session)
        return upserted

    def query(self, query_vector: Sequence[float], k: int) -> List[Tuple[int, float]]:
        return self.store.top_k(query_vector, k)
