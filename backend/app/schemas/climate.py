"""Response models for the climate endpoints (gas, degree-days and valves)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ClimateRange = Literal["day", "week", "month", "year"]


class GasPoint(BaseModel):
    timestamp: datetime
    gas: float
    degree_days: float
    outdoor_temperature: float
    indoor_temperature: float
    valve_open_pct: float


class GasStats(BaseModel):
    total_gas: float
    cost_eur: float
    co2_kg: float
    total_degree_days: float
    gas_per_degree_day: float
    correlation_degree_days: float
    avg_outdoor_temperature: float
    avg_indoor_temperature: float
    avg_valve_open_pct: float


class GasResponse(BaseModel):
    range: ClimateRange
    building_id: str
    unit: str
    stats: GasStats
    series: list[GasPoint]


class ValvePoint(BaseModel):
    timestamp: datetime
    valve_open_pct: float
    avg_temperature: float
    setpoint_c: float
    outdoor_temperature: float


class ValveSpace(BaseModel):
    space_id: str
    label: str
    building_id: str
    kind: str
    setpoint_c: float
    avg_temperature: float
    avg_outdoor_temperature: float
    valve_open_pct: float
    sample_hours: int
    hours_valve_open: int
    hours_below_setpoint: int
    deviation_c: float
    status: str  # "ok" | "fria" | "valvula_abierta" | "valvula_cerrada"


class ValvesResponse(BaseModel):
    """Cruza el estado de las electroválvulas con la temperatura de cada aula."""

    range: ClimateRange
    building_id: str
    setpoint_c: float
    series: list[ValvePoint]
    spaces: list[ValveSpace]


class EmptySpace(BaseModel):
    space_id: str
    label: str
    building_id: str
    building_label: str
    kind: str
    avg_temperature_unoccupied: float
    outdoor_temperature: float
    heated_unoccupied_hours: float
    gas_estimate: float
    cost_eur: float
    annualized_cost_eur: float


class EmptySpacesResponse(BaseModel):
    """Temperatura y gas gastados en espacios sin ocupación."""

    range: ClimateRange
    building_id: str
    heat_base_temperature_c: float
    total_gas_estimate: float
    total_cost_eur: float
    total_annualized_cost_eur: float
    total_heated_unoccupied_hours: float
    spaces: list[EmptySpace]
