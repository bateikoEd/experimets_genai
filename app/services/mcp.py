from __future__ import annotations

import enum
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_session_factory


class Role(enum.Enum):
    reader = "reader"
    writer = "writer"


class MCPService:
    """Minimal MCP-compatible service for executing parameterized SQL with RBAC."""

    def __init__(self, session_factory=None) -> None:
        self.session_factory = session_factory or get_session_factory()

    def execute(self, role: Role, sql: str, params: Dict[str, Any] | None = None) -> List[dict]:
        normalized = sql.strip().lower()
        if role == Role.reader and not normalized.startswith("select"):
            raise PermissionError("Readers may only execute SELECT statements")
        if not normalized:
            raise ValueError("SQL statement is empty")

        params = params or {}
        session = self.session_factory()
        try:
            result = session.execute(text(sql), params)
            if result.returns_rows:
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
            session.commit()
            return []
        finally:
            session.close()

    def smoke_test(self) -> dict:
        query = "SELECT COUNT(*) as house_count FROM houses"
        rows = self.execute(Role.reader, query)
        return rows[0] if rows else {"house_count": 0}
