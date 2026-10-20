from fastapi import APIRouter, HTTPException, Query, status

from app.core.energy_map import BUILDINGS_BY_ID
from app.schemas.lighting import (
    LightingBySpaceResponse,
    LightingConsumptionResponse,
    LightingRange,
    LightingWasteResponse,
)
from app.services import lighting_service
from app.services.energy_service import ALL_BUILDINGS

router = APIRouter(prefix="/lighting", tags=["lighting"])


def _validate_building(building_id: str) -> None:
    if building_id in (None, "", ALL_BUILDINGS):
        return
    if building_id not in BUILDINGS_BY_ID:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown building '{building_id}'",
        )


@router.get("/consumption", response_model=LightingConsumptionResponse)
async def get_consumption(
    range_: LightingRange = Query("day", alias="range"),
    building: str = ALL_BUILDINGS,
) -> LightingConsumptionResponse:
    _validate_building(building)
    return await lighting_service.build_consumption(range_, building)


@router.get("/by-space", response_model=LightingBySpaceResponse)
async def get_by_space(
    range_: LightingRange = Query("day", alias="range"),
    building: str = ALL_BUILDINGS,
) -> LightingBySpaceResponse:
    _validate_building(building)
    return await lighting_service.build_by_space(range_, building)


@router.get("/waste", response_model=LightingWasteResponse)
async def get_waste(
    range_: LightingRange = Query("day", alias="range"),
    building: str = ALL_BUILDINGS,
) -> LightingWasteResponse:
    _validate_building(building)
    return await lighting_service.build_waste(range_, building)
