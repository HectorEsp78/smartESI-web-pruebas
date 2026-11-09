"""HTTP routes for the Environment (weather station vs AEMET) tab."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas.weather import WeatherOverviewResponse
from app.services import weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/overview", response_model=WeatherOverviewResponse)
async def get_overview(
    start: date | None = Query(None, description="Primer día del periodo (incluido)."),
    end: date | None = Query(None, description="Último día del periodo (incluido)."),
) -> WeatherOverviewResponse:
    """School weather station compared with the AEMET observatory of Ciudad Real."""
    try:
        return await weather_service.build_overview(start, end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
