from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session, session_scope
from app.models import House
from app.schemas import (
    AskRequest,
    AskResponse,
    HealthComponentStatus,
    HealthResponse,
    HousePayload,
    HouseResponse,
)
from app.services.lmstudio import LMStudioClient
from app.services.rag import RAGService
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/api/v1", tags=["qa"])
settings = get_settings()
rag_service = RAGService(settings=settings)
vector_service = rag_service.vector_service
lm_client = rag_service.lm_client

try:
    with session_scope() as _session:
        vector_service.store.load_from_db(_session)
except Exception:
    pass


def _serialize_house(house: House) -> HouseResponse:
    return HouseResponse(
        id=house.id,
        external_id=house.external_id,
        title=house.title,
        description=house.description,
        amount_rupees=house.amount_rupees,
        price_rupees=house.price_rupees,
        location=house.location,
        carpet_area_sqft=house.carpet_area_sqft,
        status=house.status,
        floor=house.floor,
        transaction=house.transaction,
        furnishing=house.furnishing,
        facing=house.facing,
        overlooking=house.overlooking,
        society=house.society,
        bathroom_count=house.bathroom_count,
        balcony_count=house.balcony_count,
        car_parking=house.car_parking,
        ownership=house.ownership,
        super_area=house.super_area,
        dimensions=house.dimensions,
        plot_area=house.plot_area,
        created_at=house.created_at,
        updated_at=house.updated_at,
    )


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest, session: Session = Depends(get_session)) -> AskResponse:
    result = rag_service.answer_question(
        session=session,
        question_text=payload.question,
        session_id=payload.session_id,
        context=payload.context,
    )
    return AskResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"],
    )


@router.get("/data", response_model=List[HouseResponse])
def list_houses(
    session: Session = Depends(get_session),
    limit: int = Query(default=25, ge=1, le=200),
) -> List[HouseResponse]:
    rows = session.scalars(select(House).limit(limit)).all()
    return [_serialize_house(row) for row in rows]


@router.post("/data", response_model=HouseResponse, status_code=201)
def create_house(payload: HousePayload, session: Session = Depends(get_session)) -> HouseResponse:
    existing = session.scalars(select(House).where(House.external_id == payload.external_id)).first()
    if existing:
        raise HTTPException(status_code=409, detail="external_id already exists")
    house = House(**payload.model_dump())
    session.add(house)
    session.flush()
    return _serialize_house(house)


@router.put("/data/{house_id}", response_model=HouseResponse)
def update_house(house_id: int, payload: HousePayload, session: Session = Depends(get_session)) -> HouseResponse:
    house = session.get(House, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    for key, value in payload.model_dump().items():
        setattr(house, key, value)
    session.flush()
    return _serialize_house(house)


@router.delete("/data/{house_id}", status_code=204, response_class=Response)
def delete_house(house_id: int, session: Session = Depends(get_session)) -> Response:
    house = session.get(House, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    session.delete(house)
    return Response(status_code=204)


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_session)) -> HealthResponse:
    components: List[HealthComponentStatus] = []
    try:
        count = session.scalar(select(func.count()).select_from(House))
    except Exception:  # pragma: no cover
        count = None
    components.append(
        HealthComponentStatus(
            name="database",
            status="ok" if count is not None else "error",
            details={"houses": count},
        )
    )

    components.append(
        HealthComponentStatus(
            name="vector_store",
            status="ok" if vector_service.store.snapshot_path.exists() else "cold",
            details={"snapshot": str(vector_service.store.snapshot_path)},
        )
    )

    lm_status = lm_client.health_check()
    components.append(
        HealthComponentStatus(
            name="lm_studio",
            status=lm_status.get("status", "unknown"),
            latency_ms=lm_status.get("latency_ms"),
            details={"model": lm_client.model},
        )
    )

    overall = "ok" if all(c.status in {"ok", "offline"} for c in components) else "degraded"
    return HealthResponse(status=overall, components=components, timestamp=datetime.utcnow())
