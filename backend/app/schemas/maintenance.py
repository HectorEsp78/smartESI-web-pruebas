"""Response models for the Maintenance tab.

The tab is intentionally read-only: it combines the recorder's heartbeat and
battery history to decide which devices need a battery change, a repair or a
replacement. There is no maintenance log in this version, so every derived
field is an approximation and is documented in the tab notes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MaintenanceMode = Literal["periodic", "event"]
BatteryUnit = Literal["percent", "millivolt"]
BatteryStatus = Literal["critical", "low", "medium", "ok", "unknown"]
BatteryBucket = Literal["ok", "low", "unknown"]
HeartbeatStatus = Literal["ok", "late", "silent", "event", "unknown"]
DataStatus = Literal["ok", "device_silent", "global_outage", "group_outage", "unknown"]
MatrixCategory = Literal[
    "correcto",
    "revisar_dispositivo",
    "cambiar_bateria",
    "bateria_y_dispositivo",
    "sin_lectura_bateria",
    "revisar_sin_datos",
]
PriorityLabel = Literal["urgent", "high", "medium", "low"]
OutageScope = Literal["global", "group", "individual"]


class MaintenanceBatteryInfo(BaseModel):
    """Current battery reading and the forecasts derived from its history."""

    value: float | None = None
    unit: BatteryUnit | None = None
    # Percentage used for comparisons. For mV sensors it is an approximation
    # from the documented cell curve; the raw mV remain authoritative.
    estimated_pct: float | None = None
    status: BatteryStatus = "unknown"
    reading_at: datetime | None = None
    age_hours: float | None = None
    stale: bool = False
    # Percentage points per 30 days. Negative means the battery is draining.
    trend_30d_pct: float | None = None
    replacement_detected: bool = False
    replacement_at: datetime | None = None
    replacement_in_period: bool = False
    # Days until the estimated percentage reaches the critical threshold. Null
    # when the battery is stable or there is not enough history.
    days_to_critical: float | None = None
    forecast_30d_pct: float | None = None
    forecast_60d_pct: float | None = None
    forecast_90d_pct: float | None = None
    forecast_replacement_at: datetime | None = None


class MaintenanceHeartbeatInfo(BaseModel):
    """Transmission health: last message, cadence and silence threshold."""

    last_at: datetime | None = None
    silence_hours: float | None = None
    updates_per_day: float | None = None
    expected_per_day: float | None = None
    ratio: float | None = None
    median_interval_hours: float | None = None
    p95_interval_hours: float | None = None
    threshold_hours: float | None = None
    status: HeartbeatStatus = "unknown"


class MaintenanceAvailabilityInfo(BaseModel):
    """Availability and outage metrics.

    Global/group outages are reported separately and excluded from the
    individual downtime, so a recorder outage is not counted as dozens of
    device failures.
    """

    availability_pct: float | None = None
    outages_total: int = 0
    outages_individual: int = 0
    outages_global: int = 0
    outages_group: int = 0
    downtime_hours: float | None = None
    mtbf_hours: float | None = None
    mttr_hours: float | None = None


class MaintenanceDeviceSummary(BaseModel):
    """Compact row used by the overview table and by the detail header."""

    id: str
    label: str
    type: str
    location: str | None = None
    mode: MaintenanceMode
    has_battery: bool
    notes: str | None = None

    battery: MaintenanceBatteryInfo | None = None
    heartbeat: MaintenanceHeartbeatInfo
    availability: MaintenanceAvailabilityInfo

    battery_bucket: BatteryBucket = "unknown"
    data_status: DataStatus = "unknown"
    data_ok: bool = False
    matrix_category: MatrixCategory = "revisar_sin_datos"
    priority: int = Field(default=0, ge=0, le=100)
    priority_label: PriorityLabel = "low"
    decision: str
    reasons: list[str] = Field(default_factory=list)


class MaintenanceOutage(BaseModel):
    """A correlated or individual gap in the recorder data."""

    scope: OutageScope
    start: datetime
    end: datetime
    duration_hours: float
    device_count: int
    device_ids: list[str] = Field(default_factory=list)
    ongoing: bool = False


class MaintenanceHeatmapCell(BaseModel):
    """Transmission coverage for one device and one local day."""

    device_id: str
    date: str
    updates: int = 0
    expected: float | None = None
    availability_pct: float | None = None


class MaintenanceSummary(BaseModel):
    devices_total: int
    devices_periodic: int
    devices_event: int
    with_battery: int
    low_battery: int
    critical_battery: int
    unknown_battery: int
    no_data: int
    global_outages: int
    group_outages: int
    individual_outages: int
    avg_availability_pct: float | None = None
    replacements_detected: int = 0
    forecast_replace_30d: int = 0
    forecast_replace_60d: int = 0
    forecast_replace_90d: int = 0


class MaintenanceOverviewResponse(BaseModel):
    start: datetime
    end: datetime
    days: int
    generated_at: datetime
    summary: MaintenanceSummary
    devices: list[MaintenanceDeviceSummary]
    outages: list[MaintenanceOutage]
    heatmap: list[MaintenanceHeatmapCell]
    data_source: Literal["mock", "database"]
    notes: list[str] = Field(default_factory=list)


class MaintenanceBatteryPoint(BaseModel):
    timestamp: datetime
    value: float | None = None
    unit: BatteryUnit | None = None
    estimated_pct: float | None = None


class MaintenanceDailyPoint(BaseModel):
    date: str
    updates: int = 0
    expected: float | None = None
    availability_pct: float | None = None


class MaintenanceDeviceDetailResponse(BaseModel):
    start: datetime
    end: datetime
    days: int
    generated_at: datetime
    device: MaintenanceDeviceSummary
    battery_history: list[MaintenanceBatteryPoint]
    daily: list[MaintenanceDailyPoint]
    outages: list[MaintenanceOutage]
    data_source: Literal["mock", "database"]
    notes: list[str] = Field(default_factory=list)
