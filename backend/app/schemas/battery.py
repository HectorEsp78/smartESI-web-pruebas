"""Response models of the battery pages in the Maintenance tab."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.core.battery_map import BatteryUnit

BatteryLevel = Literal["ok", "medium", "low", "critical", "unknown"]
HistoryGranularity = Literal["hour", "day"]
DataSource = Literal["mock", "database"]


class BatterySensorStatus(BaseModel):
    id: str
    label: str
    entity_id: str
    unit: BatteryUnit
    value: float | None
    """Last valid reading, in ``unit``."""
    estimated_pct: float | None
    """Approximate percentage of millivolt sensors; ``None`` for percent sensors."""
    level: BatteryLevel
    """``unknown`` whenever there is no current reading, even with an old value."""
    reading_at: datetime | None
    age_hours: float | None
    is_current: bool
    """False when the last row is not a valid reading or the last one is too old."""


class BatteryGroupSummary(BaseModel):
    total: int
    low: int
    critical: int
    without_current_reading: int


class BatteryGroupResponse(BaseModel):
    group: str
    label: str
    unit: BatteryUnit
    generated_at: datetime
    summary: BatteryGroupSummary
    sensors: list[BatterySensorStatus]
    data_source: DataSource


class BatteryHistoryPoint(BaseModel):
    timestamp: datetime
    value: float | None
    """``None`` marks a gap: the chart must not join the readings around it."""
    estimated_pct: float | None


class BatteryHistoryResponse(BaseModel):
    group: str
    sensor_id: str
    label: str
    unit: BatteryUnit
    start: datetime
    end: datetime
    granularity: HistoryGranularity
    low_threshold: float
    critical_threshold: float
    min_value: float | None
    max_value: float | None
    points: list[BatteryHistoryPoint]
    data_source: DataSource
