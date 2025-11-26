from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=4, description="Natural language question about houses")
    context: Optional[dict] = Field(default_factory=dict)
    session_id: Optional[str] = Field(default=None)


class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: float


class HousePayload(BaseModel):
    external_id: int
    title: str
    description: Optional[str] = None
    amount_rupees: Optional[float] = None
    price_rupees: Optional[float] = None
    location: Optional[str] = None
    carpet_area_sqft: Optional[float] = None
    status: Optional[str] = None
    floor: Optional[str] = None
    transaction: Optional[str] = None
    furnishing: Optional[str] = None
    facing: Optional[str] = None
    overlooking: Optional[str] = None
    society: Optional[str] = None
    bathroom_count: Optional[int] = None
    balcony_count: Optional[int] = None
    car_parking: Optional[str] = None
    ownership: Optional[str] = None
    super_area: Optional[float] = None
    dimensions: Optional[str] = None
    plot_area: Optional[float] = None


class HouseResponse(HousePayload):
    id: int
    created_at: datetime
    updated_at: datetime


class HealthComponentStatus(BaseModel):
    name: str
    status: str
    latency_ms: Optional[float] = None
    details: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    components: List[HealthComponentStatus]
    timestamp: datetime
