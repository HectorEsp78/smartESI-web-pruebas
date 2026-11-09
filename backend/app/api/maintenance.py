"""HTTP routes for the Maintenance tab."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.core.maintenance_map import DEFAULT_MAINTENANCE_DAYS
from app.schemas.battery import BatteryGroupResponse, BatteryHistoryResponse
from app.schemas.maintenance import (
    MaintenanceDeviceDetailResponse,
    MaintenanceOverviewResponse,
)
from app.services import battery_service, maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/batteries/{group_id}", response_model=BatteryGroupResponse)
async def get_battery_group(group_id: str) -> BatteryGroupResponse:
    """Current battery level of every sensor of a group."""
    try:
        return await battery_service.build_group(group_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Grupo de baterías no encontrado.") from exc


@router.get(
    "/batteries/{group_id}/{sensor_id}/history",
    response_model=BatteryHistoryResponse,
)
async def get_battery_history(
    group_id: str,
    sensor_id: str,
    start: date | None = Query(None, description="Primer día del periodo (incluido)."),
    end: date | None = Query(None, description="Último día del periodo (incluido)."),
) -> BatteryHistoryResponse:
    """Battery history of one sensor."""
    try:
        return await battery_service.build_history(group_id, sensor_id, start, end)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sensor de batería no encontrado.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview", response_model=MaintenanceOverviewResponse)
async def get_overview(
    days: int = Query(
        DEFAULT_MAINTENANCE_DAYS,
        description="Ventana de análisis en días. Valores admitidos: 7, 30 o 90.",
    ),
) -> MaintenanceOverviewResponse:
    """Compact maintenance index: devices, decisions, outages and heatmap."""
    try:
        return await maintenance_service.build_overview(days)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/devices/{device_id}", response_model=MaintenanceDeviceDetailResponse)
async def get_device_detail(
    device_id: str,
    days: int = Query(
        DEFAULT_MAINTENANCE_DAYS,
        description="Ventana de análisis en días. Valores admitidos: 7, 30 o 90.",
    ),
) -> MaintenanceDeviceDetailResponse:
    """Battery history, daily transmission and outages for one device."""
    try:
        return await maintenance_service.build_device_detail(device_id, days)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
