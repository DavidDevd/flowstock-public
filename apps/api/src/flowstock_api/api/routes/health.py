from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from flowstock_api.infrastructure.database import DatabaseProbe

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok", "not_ready"]
    checks: dict[str, str]


@router.get("/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    return HealthResponse(status="ok", checks={"api": "ok"})


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse}},
)
def readiness(request: Request) -> HealthResponse | JSONResponse:
    probe: DatabaseProbe = request.app.state.database_probe
    if probe.is_ready():
        return HealthResponse(status="ok", checks={"database": "ok"})
    return JSONResponse(
        status_code=503,
        content=HealthResponse(
            status="not_ready",
            checks={"database": "failed"},
        ).model_dump(),
    )
