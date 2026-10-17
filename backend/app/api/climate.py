from fastapi import APIRouter, HTTPException, Query, status

from app.core.energy_map import BUILDINGS_BY_ID
from app.schemas.climate import (
    ClimateRange,
    EmptySpacesResponse,
    GasResponse,
    ValvesResponse,
)
from app.services import climate_service
from app.services.energy_service import ALL_BUILDINGS

router = APIRouter(prefix="/climate", tags=["climate"])


def _validate_building(building_id: str) -> None:
    if building_id in (None, "", ALL_BUILDINGS):
        return
    if building_id not in BUILDINGS_BY_ID:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown building '{building_id}'",
        )


@router.get("/gas", response_model=GasResponse)
def get_gas(
    range_: ClimateRange = Query("day", alias="range"),
    building: str = ALL_BUILDINGS,
) -> GasResponse:
    _validate_building(building)
    return climate_service.build_gas(range_, building)


@router.get("/valves", response_model=ValvesResponse)
def get_valves(
    range_: ClimateRange = Query("day", alias="range"),
    building: str = ALL_BUILDINGS,
) -> ValvesResponse:
    _validate_building(building)
    return climate_service.build_valves(range_, building)


@router.get("/empty-spaces", response_model=EmptySpacesResponse)
def get_empty_spaces(
    range_: ClimateRange = Query("day", alias="range"),
    building: str = ALL_BUILDINGS,
) -> EmptySpacesResponse:
    _validate_building(building)
    return climate_service.build_empty_spaces(range_, building)
