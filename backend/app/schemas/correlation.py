"""Response models for the occupancy vs. air-quality (data-crossing) endpoint."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

CorrelationRange = Literal["day", "week", "month", "year"]


class CorrelationPoint(BaseModel):
    timestamp: datetime
    occupancy: int
    capacity: int
    occupancy_pct: float
    co2: float
    temperature: float
    humidity: float


class CorrelationStats(BaseModel):
    sample_size: int
    pearson_r: float
    slope: float
    intercept: float
    avg_occupancy: float
    avg_occupancy_pct: float
    avg_co2: float
    max_co2: float
    good_pct: float
    moderate_pct: float
    poor_pct: float


class OccupancyAirQualityResponse(BaseModel):
    range: CorrelationRange
    building_id: str
    points: list[CorrelationPoint]
    stats: CorrelationStats
