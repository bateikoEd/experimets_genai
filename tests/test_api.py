import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import get_engine, reset_connections, session_scope
from app.models import Base, House
from app.services.embeddings import SimpleEmbeddingGenerator
from app.services.vector_store import VectorStoreService


@pytest.fixture(scope="module")
def client(tmp_path_factory) -> TestClient:
    tmp_dir = tmp_path_factory.mktemp("data")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_dir}/test.db"
    os.environ["VECTOR_DB_PATH"] = str(tmp_dir / "vectors")
    os.environ["DATA_CSV_PATH"] = str(Path(tmp_dir) / "sample.csv")
    get_settings.cache_clear()
    reset_connections()

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with session_scope() as session:
        homes = [
            House(
                external_id=1,
                title="Cozy Home",
                description="Cozy 2BHK home in Austin with garden",
                price_rupees=7500000,
                location="Austin",
            ),
            House(
                external_id=2,
                title="Luxury Condo",
                description="Luxury condo downtown with skyline views",
                price_rupees=15000000,
                location="Austin",
            ),
        ]
        session.add_all(homes)
        session.flush()
        generator = SimpleEmbeddingGenerator()
        vector_service = VectorStoreService()
        vector_service.sync_embeddings(session, generator)

    from app.main import app  # import after DB ready

    return TestClient(app)


def test_ask_endpoint_returns_answer(client: TestClient):
    response = client.post("/api/v1/ask", json={"question": "What is a luxury option in Austin?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert isinstance(body["sources"], list)
    assert 0 <= body["confidence"] <= 1


def test_data_crud_cycle(client: TestClient):
    payload = {
        "external_id": 99,
        "title": "Test Listing",
        "description": "Brand new test property",
    }
    create_resp = client.post("/api/v1/data", json=payload)
    assert create_resp.status_code == 201
    house_id = create_resp.json()["id"]

    update_payload = payload | {"title": "Updated Listing"}
    update_resp = client.put(f"/api/v1/data/{house_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Listing"

    delete_resp = client.delete(f"/api/v1/data/{house_id}")
    assert delete_resp.status_code == 204


def test_health_endpoint(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"ok", "degraded"}
    assert any(comp["name"] == "database" for comp in data["components"])
