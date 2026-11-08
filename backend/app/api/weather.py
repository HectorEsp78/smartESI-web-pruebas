"""HTTP routes for the Environment (weather station) tab."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.weather_map import DEFAULT_WEATHER_DAYS
from app.schemas.weather import WeatherOverviewResponse
from app.services import weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/overview", response_model=WeatherOverviewResponse)
async def get_overview(
    days: int = Query(
        DEFAULT_WEATHER_DAYS,
        description="Ventana de análisis: 7, 30 o 90 días.",
    ),
) -> WeatherOverviewResponse:
    """Weather station, indoor reference, AEMET comparison and energy crosses."""
    try:
        return await weather_service.build_overview(days)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
