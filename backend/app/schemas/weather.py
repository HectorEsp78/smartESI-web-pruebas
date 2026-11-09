"""Response models of the Environment (weather station vs AEMET) tab."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

WeatherStatus = Literal["ok", "stale", "missing"]
AemetCoverage = Literal["complete", "partial", "none"]


class WeatherCurrent(BaseModel):
    """Latest station reading, always as of now."""

    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    pm1: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    battery_pct: float | None = None
    last_updated: datetime | None = None
    age_hours: float | None = None
    status: WeatherStatus = "missing"


class AemetLatest(BaseModel):
    """Latest AEMET observation in the recorder, always as of now."""

    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    observed_at: datetime | None = None
    age_hours: float | None = None
    stale: bool = True


class AemetGap(BaseModel):
    start: datetime
    end: datetime
    hours: int


class AemetAvailability(BaseModel):
    """How much of the selected period can really be compared with AEMET."""

    coverage: AemetCoverage = "none"
    period_hours: int = 0
    observed_hours: int = 0
    compared_hours: int = 0
    coverage_pct: float = 0.0
    first_observation: datetime | None = None
    last_observation: datetime | None = None
    gaps: list[AemetGap] = []


class MetricComparison(BaseModel):
    """Station against AEMET over the hours where both have a value."""

    samples: int = 0
    station_avg: float | None = None
    aemet_avg: float | None = None
    # Station minus AEMET.
    bias: float | None = None
    mean_absolute_error: float | None = None
    correlation: float | None = None


class TemperatureComparison(MetricComparison):
    daytime_bias: float | None = None
    nighttime_bias: float | None = None


class HumidityComparison(MetricComparison):
    # Share of the compared hours with the station's sensor saturated.
    saturated_pct: float | None = None
    # Bias over the hours where the station's sensor was still measuring.
    unsaturated_bias: float | None = None


class HourlyBias(BaseModel):
    hour: int
    temperature_bias_c: float | None = None


class WeatherComparison(BaseModel):
    temperature: TemperatureComparison
    humidity: HumidityComparison
    pressure: MetricComparison
    hourly_bias: list[HourlyBias]


class WeatherSummary(BaseModel):
    samples: int = 0
    coverage_pct: float | None = None
    temperature_avg_c: float | None = None
    temperature_min_c: float | None = None
    temperature_max_c: float | None = None
    humidity_avg_pct: float | None = None
    humidity_min_pct: float | None = None
    humidity_max_pct: float | None = None
    pressure_avg_hpa: float | None = None
    pm25_avg: float | None = None
    pm10_avg: float | None = None
    battery_min_pct: float | None = None
    aemet_precipitation_mm: float | None = None
    aemet_rainy_hours: int = 0


class WeatherSeriesPoint(BaseModel):
    timestamp: datetime
    station_temperature_c: float | None = None
    aemet_temperature_c: float | None = None
    station_humidity_pct: float | None = None
    aemet_humidity_pct: float | None = None
    # Both pressures at the altitude of the AEMET observatory.
    station_pressure_hpa: float | None = None
    aemet_pressure_hpa: float | None = None
    aemet_precipitation_mm: float | None = None
    pm1: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    battery_pct: float | None = None


class WeatherOverviewResponse(BaseModel):
    start: datetime
    end: datetime
    granularity: Literal["hour", "day"]
    generated_at: datetime
    current: WeatherCurrent
    aemet_latest: AemetLatest
    aemet_availability: AemetAvailability
    comparison: WeatherComparison
    summary: WeatherSummary
    series: list[WeatherSeriesPoint]
    data_source: Literal["mock", "database"]
    notes: list[str]
