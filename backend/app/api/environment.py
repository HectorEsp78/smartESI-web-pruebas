"""HTTP routes for the Infrastructure (room environment) tab."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas.environment import (
    EnvironmentOverviewResponse,
    EnvironmentRoomDetailResponse,
)
from app.services import environment_service

router = APIRouter(prefix="/environment", tags=["environment"])


@router.get("/overview", response_model=EnvironmentOverviewResponse)
async def get_overview(
    start: date | None = Query(None, description="Primer día del periodo (incluido)."),
    end: date | None = Query(None, description="Último día del periodo (incluido)."),
) -> EnvironmentOverviewResponse:
    """Compact index of confirmed rooms and their current/period values."""
    try:
        return await environment_service.build_overview(start, end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/rooms/{room_id}", response_model=EnvironmentRoomDetailResponse)
async def get_room_detail(
    room_id: str,
    start: date | None = Query(None, description="Primer día del periodo (incluido)."),
    end: date | None = Query(None, description="Último día del periodo (incluido)."),
) -> EnvironmentRoomDetailResponse:
    """Detail page for one confirmed room, including charts and cross-analysis."""
    try:
        return await environment_service.build_room_detail(room_id, start, end)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Estancia no encontrada.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
