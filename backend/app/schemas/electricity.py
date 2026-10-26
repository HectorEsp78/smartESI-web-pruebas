"""Response models for the Electricity tab.

The tab has its own contract because it works with explicit date ranges and a
building/sector catalogue.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

ElectricityMetric = Literal["kwh", "cost"]
ElectricityGranularity = Literal["day", "week", "month", "year"]


class ElectricityStats(BaseModel):
    """Summary statistics of the selected scope over the selected range."""

    total: float
    average: float
    minimum: float
    maximum: float
    # Average consumption during closed hours (nights and weekends), in the
    # selected metric per hour.
    baseline_hourly: float
    # Same baseline projected to the whole range (as if the school had been
    # closed for the entire range).
    baseline_total: float
    buckets: int
    unit: str


class ElectricityPoint(BaseModel):
    timestamp: datetime
    value: float
    # Expected consumption if the school had been closed during the bucket.
    baseline: float


class ElectricityBuildingStats(BaseModel):
    building_id: str
    label: str
    kind: str
    total: float
    average: float
    minimum: float
    maximum: float
    baseline_total: float
    share: float
    note: str = ""
    series: list[ElectricityPoint]


class ElectricitySectorStats(BaseModel):
    sector_id: str
    label: str
    building_id: str
    building_label: str
    floor: str
    total: float
    average: float
    minimum: float
    maximum: float
    share_of_building: float
    has_data: bool
    note: str = ""
    series: list[ElectricityPoint]


class ElectricityResponse(BaseModel):
    start: date
    end: date
    granularity: ElectricityGranularity
    metric: ElectricityMetric
    unit: str
    scope: str
    scope_label: str
    building_id: str | None
    sector_id: str | None
    series: list[ElectricityPoint]
    stats: ElectricityStats
    buildings: list[ElectricityBuildingStats]
    sectors: list[ElectricitySectorStats]
    site_total: float
    fermin_total: float
    sectors_total: float
    unmetered_total: float
    sector_coverage: float
    data_start: date


class ElectricityComparePoint(BaseModel):
    index: int
    timestamp_a: datetime
    timestamp_b: datetime
    period_a: float
    period_b: float
    # Common closed-hour baseline projected to the bucket (average of the two
    # periods' bucket lengths).
    baseline: float


class ElectricityCompareResponse(BaseModel):
    granularity: ElectricityGranularity
    metric: ElectricityMetric
    unit: str
    scope: str
    scope_label: str
    building_id: str | None
    sector_id: str | None
    start_a: date
    end_a: date
    start_b: date
    end_b: date
    period_a_days: int
    period_b_days: int
    period_a: ElectricityStats
    period_b: ElectricityStats
    baseline_hourly: float
    delta_pct: float
    series: list[ElectricityComparePoint]


class ElectricityBuildingRef(BaseModel):
    id: str
    label: str
    kind: str
    note: str = ""


class ElectricitySectorRef(BaseModel):
    id: str
    label: str
    building_id: str
    building_label: str
    floor: str
    available: bool
    note: str = ""


class ElectricityMetaResponse(BaseModel):
    buildings: list[ElectricityBuildingRef]
    sectors: list[ElectricitySectorRef]
    data_start: date
    price_eur_per_kwh: float
    # "database" means real recorder data; "mock" means synthetic development data.
    data_source: Literal["mock", "database"]
