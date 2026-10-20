from fastapi import APIRouter, HTTPException, Query, status

from app.core.energy_map import BUILDINGS_BY_ID
from app.schemas.correlation import CorrelationRange, OccupancyAirQualityResponse
from app.services import correlation_service

router = APIRouter(prefix="/correlation", tags=["correlation"])


@router.get("/occupancy-air-quality", response_model=OccupancyAirQualityResponse)
async def get_occupancy_air_quality(
    range_: CorrelationRange = Query("day", alias="range"),
    building: str = "all",
) -> OccupancyAirQualityResponse:
    if building not in (None, "", correlation_service.ALL_BUILDINGS) and building not in BUILDINGS_BY_ID:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown building '{building}'",
        )
    return await correlation_service.build_occupancy_air_quality(range_, building)
