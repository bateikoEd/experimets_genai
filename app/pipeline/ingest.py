from __future__ import annotations

import logging
import math
import re
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Base, House

logger = logging.getLogger(__name__)
MONEY_PATTERN = re.compile(r"(?P<value>[0-9.]+)\s*(?P<unit>Cr|crore|Lac|Lakh|k|K)?", re.IGNORECASE)
AREA_PATTERN = re.compile(r"(?P<value>[0-9.]+)")


class DataProcessingPipeline:
    """End-to-end CSV ingestion with validation, cleaning, and persistence."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def run(self, session: Session, csv_path: Optional[Path] = None) -> int:
        path = csv_path or self.settings.data_csv_path
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {path}")

        df = pd.read_csv(path)
        logger.info("Loaded %s rows from %s", len(df.index), path)
        cleaned = self._clean_dataframe(df)
        if cleaned.empty:
            raise ValueError("Cleaned dataframe is empty; aborting persistence")

        self._persist(cleaned, session)
        logger.info("Persisted %s house rows", len(cleaned.index))
        return len(cleaned.index)

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"Index", "Title", "Description", "location"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        df = df.copy()
        df["Index"] = pd.to_numeric(df["Index"], errors="coerce")
        df = df.dropna(subset=["Index", "Title"])

        df["Amount(in rupees)"] = df["Amount(in rupees)"].apply(self._parse_money)
        df["Price (in rupees)"] = df["Price (in rupees)"].apply(self._parse_money)
        df["Carpet Area"] = df["Carpet Area"].apply(self._parse_area)
        df["Super Area"] = df.get("Super Area", pd.Series(dtype=float)).apply(self._parse_area)
        df["Plot Area"] = df.get("Plot Area", pd.Series(dtype=float)).apply(self._parse_area)
        df["Bathroom"] = df.get("Bathroom", pd.Series(dtype=float)).apply(self._parse_int)
        df["Balcony"] = df.get("Balcony", pd.Series(dtype=float)).apply(self._parse_int)

        return df

    def _persist(self, df: pd.DataFrame, session: Session) -> None:
        Base.metadata.create_all(session.bind)
        external_ids = [int(idx) for idx in df["Index"].tolist()]
        existing: dict[int, House] = {}
        chunk_size = 900  # stay under SQLite's 999 parameter limit
        for i in range(0, len(external_ids), chunk_size):
            chunk = external_ids[i : i + chunk_size]
            rows = session.scalars(select(House).where(House.external_id.in_(chunk))).all()
            existing.update({row.external_id: row for row in rows})

        for _, row in df.iterrows():
            ext_id = int(row["Index"])
            house = existing.get(ext_id)
            if not house:
                house = House(external_id=ext_id, title=str(row["Title"]))
                session.add(house)

            house.description = _safe_str(row.get("Description"))
            house.amount_rupees = _safe_float(row.get("Amount(in rupees)"))
            house.price_rupees = _safe_float(row.get("Price (in rupees)"))
            house.location = _safe_str(row.get("location"))
            house.carpet_area_sqft = _safe_float(row.get("Carpet Area"))
            house.status = _safe_str(row.get("Status"))
            house.floor = _safe_str(row.get("Floor"))
            house.transaction = _safe_str(row.get("Transaction"))
            house.furnishing = _safe_str(row.get("Furnishing"))
            house.facing = _safe_str(row.get("facing"))
            house.overlooking = _safe_str(row.get("overlooking"))
            house.society = _safe_str(row.get("Society"))
            house.bathroom_count = _safe_int(row.get("Bathroom"))
            house.balcony_count = _safe_int(row.get("Balcony"))
            house.car_parking = _safe_str(row.get("Car Parking"))
            house.ownership = _safe_str(row.get("Ownership"))
            house.super_area = _safe_float(row.get("Super Area"))
            house.dimensions = _safe_str(row.get("Dimensions"))
            house.plot_area = _safe_float(row.get("Plot Area"))

    def _parse_money(self, value: object) -> Optional[float]:
        if not isinstance(value, str) or not value.strip():
            return None
        match = MONEY_PATTERN.search(value.replace(",", ""))
        if not match:
            return None
        number = float(match.group("value"))
        unit = match.group("unit")
        if not unit:
            return number
        unit = unit.lower()
        if unit in {"cr", "crore"}:
            return number * 1e7
        if unit in {"lac", "lakh"}:
            return number * 1e5
        if unit in {"k"}:
            return number * 1e3
        return number

    def _parse_area(self, value: object) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            return None
        match = AREA_PATTERN.search(value.replace(",", ""))
        return float(match.group("value")) if match else None

    def _parse_int(self, value: object) -> Optional[int]:
        if isinstance(value, (int, float)) and not math.isnan(value):
            return int(value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None


def _safe_float(value: object) -> Optional[float]:
    if isinstance(value, (int, float)) and not math.isnan(value):
        return float(value)
    return None


def _safe_int(value: object) -> Optional[int]:
    if isinstance(value, (int, float)) and not math.isnan(value):
        return int(value)
    return None


def _safe_str(value: object) -> Optional[str]:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
