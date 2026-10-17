"""Response models for the energy endpoints (the public API contract)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

EnergyRange = Literal["day", "week", "month", "year"]
EnergyMetric = Literal["kwh", "cost", "co2"]


class EnergyPoint(BaseModel):
    timestamp: datetime
    value: float


class EnergyConsumptionResponse(BaseModel):
    range: EnergyRange
    metric: EnergyMetric
    unit: str
    granularity: str
    building_id: str
    total: float
    average: float
    peak: EnergyPoint | None
    series: list[EnergyPoint]


class BuildingShare(BaseModel):
    building_id: str
    label: str
    total: float
    share: float


class SpaceShare(BaseModel):
    space_id: str
    label: str
    building_id: str
    building_label: str
    kind: str
    total: float
    share: float


class EnergyByBuildingResponse(BaseModel):
    range: EnergyRange
    metric: EnergyMetric
    unit: str
    total: float
    buildings: list[BuildingShare]
    spaces: list[SpaceShare]


class EnergyBreakdownPoint(BaseModel):
    timestamp: datetime
    base: float
    activity: float
    lighting: float
    other: float


class EnergyBreakdownResponse(BaseModel):
    """Carga base (fuera de horario) frente a actividad, y luz frente al resto."""

    range: EnergyRange
    unit: str
    building_id: str
    total: float
    base_total: float
    activity_total: float
    lighting_total: float
    other_total: float
    base_share: float
    lighting_share: float
    series: list[EnergyBreakdownPoint]


class EnergyComparePoint(BaseModel):
    timestamp: datetime
    current: float
    previous: float


class EnergyCompareResponse(BaseModel):
    """Comparativa del periodo actual con el periodo anterior del mismo tamaño."""

    range: EnergyRange
    metric: EnergyMetric
    unit: str
    building_id: str
    current_total: float
    previous_total: float
    delta_pct: float
    series: list[EnergyComparePoint]


class BuildingEfficiency(BaseModel):
    building_id: str
    label: str
    area_m2: float
    total: float
    cost_eur: float
    occupancy_hours: float
    kwh_per_m2: float
    kwh_per_person_hour: float
    share: float


class SpaceEfficiency(BaseModel):
    space_id: str
    label: str
    building_id: str
    building_label: str
    kind: str
    area_m2: float
    total: float
    cost_eur: float
    occupancy_hours: float
    kwh_per_m2: float
    kwh_per_person_hour: float
    share: float


class EnergyEfficiencyResponse(BaseModel):
    """Consumo de electricidad normalizado por superficie y por ocupación."""

    range: EnergyRange
    unit: str
    total: float
    avg_kwh_per_m2: float
    buildings: list[BuildingEfficiency]
    spaces: list[SpaceEfficiency]
