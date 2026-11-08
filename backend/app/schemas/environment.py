"""Response models for the Infrastructure (room environment) tab."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.environment_map import EnvironmentQuality

EnvironmentGranularity = Literal["hour", "day", "week"]


class EnvironmentRoomSummary(BaseModel):
    """Current values and period aggregates for one confirmed room."""

    room_id: str
    label: str
    building_id: str
    building_label: str
    kind: str

    has_temperature: bool
    has_humidity: bool
    has_co2: bool
    has_presence: bool

    current_temperature_c: float | None = None
    temperature_updated_at: datetime | None = None
    current_humidity_pct: float | None = None
    humidity_updated_at: datetime | None = None
    current_co2_ppm: float | None = None
    co2_updated_at: datetime | None = None
    current_presence: bool | None = None
    presence_updated_at: datetime | None = None
    last_updated: datetime | None = None

    temperature_status: EnvironmentQuality = "unknown"
    humidity_status: EnvironmentQuality = "unknown"
    co2_status: EnvironmentQuality = "unknown"
    comfort_status: EnvironmentQuality = "unknown"

    avg_temperature_c: float | None = None
    min_temperature_c: float | None = None
    max_temperature_c: float | None = None
    avg_humidity_pct: float | None = None
    min_humidity_pct: float | None = None
    max_humidity_pct: float | None = None
    avg_co2_ppm: float | None = None
    peak_co2_ppm: float | None = None
    peak_co2_at: datetime | None = None
    co2_above_800_pct: float | None = None
    co2_above_1000_pct: float | None = None
    occupancy_pct: float | None = None
    occupied_hours: float | None = None
    empty_hours: float | None = None
    comfort_good_pct: float | None = None


class EnvironmentSeriesPoint(BaseModel):
    """One chart bucket for a single room."""

    timestamp: datetime
    temperature_c: float | None = None
    humidity_pct: float | None = None
    co2_ppm: float | None = None
    # Percentage of the bucket during which the room was occupied (0–100).
    presence_pct: float | None = None
    ambient_temperature_c: float | None = None
    gas_m3: float | None = None
    gas_cost_eur: float | None = None


class EnvironmentHeatmapCell(BaseModel):
    """Mean behaviour for one local weekday/hour cell (0 = Monday)."""

    weekday: int = Field(ge=0, le=6)
    hour: int = Field(ge=0, le=23)
    presence_pct: float | None = None
    co2_ppm: float | None = None


class EnvironmentCo2Occupancy(BaseModel):
    """CO₂ behaviour with and without people, plus its linear correlation."""

    occupied_co2_ppm: float | None = None
    empty_co2_ppm: float | None = None
    lift_pct: float | None = None
    correlation: float | None = None
    occupied_hours: float | None = None
    empty_hours: float | None = None


class EnvironmentThermalRecovery(BaseModel):
    """How quickly a room returns to its empty-room baseline after use."""

    baseline_temperature_c: float | None = None
    transitions: int = 0
    median_recovery_hours: float | None = None
    median_change_per_hour_c: float | None = None
    no_recovery_count: int = 0


class EnvironmentBenchmark(BaseModel):
    """Average of the other rooms for the same period, used as a comparison."""

    avg_temperature_c: float | None = None
    avg_humidity_pct: float | None = None
    avg_co2_ppm: float | None = None
    occupancy_pct: float | None = None
    rooms_temperature: int = 0
    rooms_humidity: int = 0
    rooms_co2: int = 0
    rooms_presence: int = 0


class EnvironmentContext(BaseModel):
    """Building-level ambient and gas context.

    ``sensor.ambiente`` has no confirmed room, so it is labelled as a reference.
    Gas is also building-level and may include uses other than heating.
    """

    current_ambient_temperature_c: float | None = None
    ambient_updated_at: datetime | None = None
    avg_ambient_temperature_c: float | None = None
    avg_indoor_minus_ambient_c: float | None = None
    gas_m3: float | None = None
    gas_cost_eur: float | None = None
    gas_cost_per_day_eur: float | None = None
    gas_days: float | None = None
    has_gas: bool = False


class EnvironmentSummary(BaseModel):
    rooms_total: int
    occupied_now: int
    rooms_with_presence: int
    rooms_with_climate: int
    rooms_with_co2: int
    avg_temperature_c: float | None = None
    avg_humidity_pct: float | None = None
    avg_co2_ppm: float | None = None
    co2_alert_rooms: int = 0
    comfort_good_rooms: int = 0
    occupancy_pct: float | None = None


class EnvironmentOverviewResponse(BaseModel):
    start: datetime
    end: datetime
    granularity: EnvironmentGranularity
    generated_at: datetime
    rooms: list[EnvironmentRoomSummary]
    summary: EnvironmentSummary
    data_source: Literal["mock", "database"]
    notes: list[str] = Field(default_factory=list)


class EnvironmentRoomDetailResponse(BaseModel):
    start: datetime
    end: datetime
    granularity: EnvironmentGranularity
    generated_at: datetime
    room: EnvironmentRoomSummary
    benchmark: EnvironmentBenchmark
    context: EnvironmentContext
    series: list[EnvironmentSeriesPoint]
    heatmap: list[EnvironmentHeatmapCell]
    co2_occupancy: EnvironmentCo2Occupancy
    thermal_recovery: EnvironmentThermalRecovery
    data_source: Literal["mock", "database"]
    notes: list[str] = Field(default_factory=list)
