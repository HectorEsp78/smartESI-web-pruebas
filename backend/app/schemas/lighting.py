"""Response models for the lighting (luminarias) endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

LightingRange = Literal["day", "week", "month", "year"]


class LightingPoint(BaseModel):
    timestamp: datetime
    lighting: float
    other: float
    total: float
    occupancy_pct: float
    daylight_hours: float


class LightingConsumptionResponse(BaseModel):
    range: LightingRange
    building_id: str
    unit: str
    total: float
    lighting_total: float
    other_total: float
    lighting_share: float
    cost_eur: float
    co2_kg: float
    series: list[LightingPoint]


class LightingSpace(BaseModel):
    space_id: str
    label: str
    building_id: str
    building_label: str
    kind: str
    area_m2: float
    lighting: float
    share_of_lighting: float
    share_of_building: float
    cost_eur: float


class LightingBySpaceResponse(BaseModel):
    range: LightingRange
    building_id: str
    unit: str
    lighting_total: float
    spaces: list[LightingSpace]


class LightingWasteSpace(BaseModel):
    space_id: str
    label: str
    building_id: str
    building_label: str
    kind: str
    total_lighting: float
    empty_lighting: float
    waste_pct: float
    cost_eur: float
    annualized_cost_eur: float
    empty_hours: float
    avg_daily_empty_cost: float


class LightingWasteResponse(BaseModel):
    """Consumo de luminarias sin ocupación (despilfarro detectable)."""

    range: LightingRange
    building_id: str
    total_lighting: float
    waste_lighting: float
    waste_share: float
    waste_cost_eur: float
    annualized_cost_eur: float
    avg_daily_empty_cost: float
    spaces: list[LightingWasteSpace]
