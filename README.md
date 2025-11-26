# experimets_genai

AI-powered question-answering stack for house price analytics. The system ingests the provided CSV dataset into PostgreSQL (or SQLite for local development), synchronizes embeddings into a lightweight vector store, exposes MCP-backed data access, and serves a FastAPI-based RAG endpoint.

## Getting Started

1. **Install dependencies**
	```bash
	python3 -m pip install -r requirements.txt
	```
2. **Prepare environment variables (optional)** – copy `.env.example` if you maintain one, or export the following before running services:
	```bash
	export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/house_prices
	export DATA_CSV_PATH=data/house_prices.csv
	export VECTOR_DB_PATH=artifacts/vector_store
	export LM_STUDIO_URL=http://localhost:1234  # optional, falls back to offline responses
	```
3. **Bootstrap the data foundation** – creates tables, ingests the CSV, syncs embeddings, and performs an LM Studio health check.
	```bash
	python scripts/bootstrap_database.py
	```

## Running Services

- **Question-Answering API**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
  Key endpoints:
  - `POST /api/v1/ask` – Ask natural-language questions about the dataset.
  - `GET|POST|PUT|DELETE /api/v1/data` – CRUD proxy to the database for house records.
  - `GET /api/v1/health` – Component status for DB, vector store, and LM Studio.

- **MCP Server** – exposes structured SQL access with reader/writer roles.
  ```bash
  uvicorn scripts.mcp_server:app --host 0.0.0.0 --port 8001
  ```
  Pass `X-Role: reader` for SELECT-only access or `X-Role: writer` for mutations.

## Development Notes

- Data ingestion is handled by `app/pipeline/ingest.py`, which normalizes key fields (currency, area, counts) before persisting into PostgreSQL-compatible schemas defined in `app/models.py`.
- Embeddings are generated via `SimpleEmbeddingGenerator` (hash-based) and synchronized through `VectorStoreService`, which keeps a JSON snapshot under `artifacts/vector_store`.
- `RAGService` coordinates vector retrieval, structured lookups, LM Studio prompting, and question logging.

## Testing

Run the FastAPI integration tests (uses temporary SQLite database and offline LM fallback):

```bash
pytest
```

Logs for pipeline steps and LM Studio checks are written under `logs/` by default.