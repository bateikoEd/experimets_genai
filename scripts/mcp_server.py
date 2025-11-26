"""Run a lightweight MCP-compatible FastAPI server for database operations."""

import sys
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.mcp import MCPService, Role

app = FastAPI(title="House MCP Server")
service = MCPService()


class SQLPayload(BaseModel):
    sql: str
    params: dict | None = None


def get_role(x_role: str = Header(...)) -> Role:
    try:
        return Role(x_role.lower())
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid role") from exc


@app.post("/query")
def run_query(payload: SQLPayload, role: Role = Depends(get_role)):
    try:
        return {"rows": service.execute(role, payload.sql, payload.params)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/mutate")
def run_mutation(payload: SQLPayload, role: Role = Depends(get_role)):
    if role != Role.writer:
        raise HTTPException(status_code=403, detail="Only writers may mutate data")
    service.execute(role, payload.sql, payload.params)
    return {"status": "ok"}


@app.get("/health")
def health():
    try:
        payload = service.smoke_test()
        return {"status": "ok", **payload}
    except Exception:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="Database unreachable")
