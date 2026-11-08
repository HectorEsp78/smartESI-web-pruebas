"""HTTP routes for the Maintenance tab."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.maintenance_map import DEFAULT_MAINTENANCE_DAYS
from app.schemas.maintenance import (
    MaintenanceDeviceDetailResponse,
    MaintenanceOverviewResponse,
)
from app.services import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


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
