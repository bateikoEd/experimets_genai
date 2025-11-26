import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class House(Base):
    __tablename__ = "houses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    amount_rupees: Mapped[Optional[float]] = mapped_column(Float)
    price_rupees: Mapped[Optional[float]] = mapped_column(Float)
    location: Mapped[Optional[str]] = mapped_column(String(128))
    carpet_area_sqft: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[Optional[str]] = mapped_column(String(64))
    floor: Mapped[Optional[str]] = mapped_column(String(64))
    transaction: Mapped[Optional[str]] = mapped_column(String(64))
    furnishing: Mapped[Optional[str]] = mapped_column(String(64))
    facing: Mapped[Optional[str]] = mapped_column(String(64))
    overlooking: Mapped[Optional[str]] = mapped_column(String(128))
    society: Mapped[Optional[str]] = mapped_column(String(128))
    bathroom_count: Mapped[Optional[int]] = mapped_column(Integer)
    balcony_count: Mapped[Optional[int]] = mapped_column(Integer)
    car_parking: Mapped[Optional[str]] = mapped_column(String(64))
    ownership: Mapped[Optional[str]] = mapped_column(String(64))
    super_area: Mapped[Optional[float]] = mapped_column(Float)
    dimensions: Mapped[Optional[str]] = mapped_column(String(64))
    plot_area: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    embeddings: Mapped[List["Embedding"]] = relationship(back_populates="house")


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_agent: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    questions: Mapped[List["Question"]] = relationship(back_populates="session")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sessions.id"))
    question_text: Mapped[str] = mapped_column(String)
    answer_text: Mapped[Optional[str]] = mapped_column(String)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[Optional[SessionModel]] = relationship(back_populates="questions")


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    house_id: Mapped[int] = mapped_column(Integer, ForeignKey("houses.id"), nullable=False)
    vector: Mapped[List[float]] = mapped_column(JSON, nullable=False)
    model: Mapped[str] = mapped_column(String(64), default="simple-hash")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    house: Mapped[House] = relationship(back_populates="embeddings")
