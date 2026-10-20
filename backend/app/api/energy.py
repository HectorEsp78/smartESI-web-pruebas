from fastapi import APIRouter, HTTPException, Query, status

from app.core.energy_map import BUILDINGS_BY_ID
from app.schemas.energy import (
    EnergyBreakdownResponse,
    EnergyByBuildingResponse,
    EnergyCompareResponse,
    EnergyConsumptionResponse,
    EnergyEfficiencyResponse,
    EnergyMetric,
    EnergyRange,
)
from app.services import energy_service

router = APIRouter(prefix="/energy", tags=["energy"])


def _validate_building(building_id: str) -> None:
    if building_id in (None, "", energy_service.ALL_BUILDINGS):
        return
    if building_id not in BUILDINGS_BY_ID:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown building '{building_id}'",
        )


@router.get("/consumption", response_model=EnergyConsumptionResponse)
async def get_consumption(
    range_: EnergyRange = Query("day", alias="range"),
    building: str = "all",
    metric: EnergyMetric = "kwh",
) -> EnergyConsumptionResponse:
    _validate_building(building)
    return await energy_service.build_consumption(range_, building, metric)


@router.get("/by-building", response_model=EnergyByBuildingResponse)
async def get_by_building(
    range_: EnergyRange = Query("day", alias="range"),
    metric: EnergyMetric = "kwh",
) -> EnergyByBuildingResponse:
    return await energy_service.build_by_building(range_, metric)


@router.get("/breakdown", response_model=EnergyBreakdownResponse)
async def get_breakdown(
    range_: EnergyRange = Query("day", alias="range"),
    building: str = "all",
) -> EnergyBreakdownResponse:
    _validate_building(building)
    return await energy_service.build_breakdown(range_, building)


@router.get("/compare", response_model=EnergyCompareResponse)
async def get_compare(
    range_: EnergyRange = Query("day", alias="range"),
    building: str = "all",
    metric: EnergyMetric = "kwh",
) -> EnergyCompareResponse:
    _validate_building(building)
    return await energy_service.build_compare(range_, building, metric)


@router.get("/efficiency", response_model=EnergyEfficiencyResponse)
async def get_efficiency(
    range_: EnergyRange = Query("day", alias="range"),
) -> EnergyEfficiencyResponse:
    return await energy_service.build_efficiency(range_)
