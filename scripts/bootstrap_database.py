"""Bootstrap PostgreSQL schema, ingest CSV data, sync embeddings, and verify LM Studio."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import session_scope
from app.pipeline.ingest import DataProcessingPipeline
from app.services.embeddings import SimpleEmbeddingGenerator
from app.services.lmstudio import LMStudioClient
from app.services.vector_store import VectorStoreService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> None:
    pipeline = DataProcessingPipeline()
    embeddings = SimpleEmbeddingGenerator()
    vector_service = VectorStoreService()

    with session_scope() as session:
        rows = pipeline.run(session)
        synced = vector_service.sync_embeddings(session, embeddings)
        logging.info("Pipeline complete: %s rows ingested, %s embeddings synced", rows, synced)

    lm_client = LMStudioClient()
    health = lm_client.health_check()
    logging.info("LM Studio health: %s", health)


if __name__ == "__main__":
    main()
