"""HTTP routes for the Electricity tab."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.core.electricity_map import (
    ELECTRICITY_BUILDINGS,
    ELECTRICITY_BUILDINGS_BY_ID,
    ELECTRICITY_DATA_START,
    ELECTRICITY_SECTORS,
)
from app.schemas.electricity import (
    ElectricityBuildingRef,
    ElectricityCompareResponse,
    ElectricityGranularity,
    ElectricityMetaResponse,
    ElectricityMetric,
    ElectricityResponse,
    ElectricitySectorRef,
)
from app.services import electricity_service

router = APIRouter(prefix="/energy/electricity", tags=["electricity"])


def _bad_request(error: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/meta", response_model=ElectricityMetaResponse)
def get_electricity_meta() -> ElectricityMetaResponse:
    """Buildings, sectors and data availability for the Electricity tab."""
    return ElectricityMetaResponse(
        buildings=[
            ElectricityBuildingRef(
                id=building.id,
                label=building.label,
                kind=building.kind,
                note=building.note,
            )
            for building in ELECTRICITY_BUILDINGS
        ],
        sectors=[
            ElectricitySectorRef(
                id=sector.id,
                label=sector.label,
                building_id=sector.building_id,
                building_label=ELECTRICITY_BUILDINGS_BY_ID[sector.building_id].label,
                floor=sector.floor,
                available=sector.available,
                note=sector.note,
            )
            for sector in ELECTRICITY_SECTORS
        ],
        data_start=ELECTRICITY_DATA_START,
        price_eur_per_kwh=settings.ENERGY_PRICE_EUR_PER_KWH,
        data_source=settings.DATA_SOURCE,
    )


@router.get("", response_model=ElectricityResponse)
async def get_electricity(
    start: date = Query(..., description="Inclusive start date (YYYY-MM-DD)"),
    end: date = Query(..., description="Inclusive end date (YYYY-MM-DD)"),
    granularity: ElectricityGranularity = "day",
    metric: ElectricityMetric = "kwh",
    building: str = "all",
    sector: str | None = None,
) -> ElectricityResponse:
    try:
        return await electricity_service.build_electricity(
            start=start,
            end=end,
            granularity=granularity,
            metric=metric,
            building=building,
            sector=sector,
        )
    except ValueError as error:
        raise _bad_request(error) from error


@router.get("/compare", response_model=ElectricityCompareResponse)
async def get_electricity_compare(
    start_a: date = Query(..., description="Inclusive start date of period A"),
    end_a: date = Query(..., description="Inclusive end date of period A"),
    start_b: date = Query(..., description="Inclusive start date of period B"),
    end_b: date = Query(..., description="Inclusive end date of period B"),
    granularity: ElectricityGranularity = "day",
    metric: ElectricityMetric = "kwh",
    building: str = "all",
    sector: str | None = None,
) -> ElectricityCompareResponse:
    try:
        return await electricity_service.build_electricity_compare(
            start_a=start_a,
            end_a=end_a,
            start_b=start_b,
            end_b=end_b,
            granularity=granularity,
            metric=metric,
            building=building,
            sector=sector,
        )
    except ValueError as error:
        raise _bad_request(error) from error
