"""Response models for the Environment (weather station) tab."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.weather_map import WeatherGranularity

WeatherStatus = Literal["ok", "stale", "missing"]


class WeatherCurrent(BaseModel):
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    pressure_station_hpa: float | None = None
    pm1: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    battery_pct: float | None = None
    last_updated: datetime | None = None
    age_hours: float | None = None
    status: WeatherStatus = "missing"
    dew_point_c: float | None = None
    absolute_humidity_g_m3: float | None = None
    heat_index_c: float | None = None
    pressure_trend_3h_hpa: float | None = None
    pressure_trend_24h_hpa: float | None = None
    pm25_pm10_ratio: float | None = None


class WeatherSummary(BaseModel):
    samples: int = 0
    coverage_pct: float | None = None
    median_interval_hours: float | None = None
    outage_hours: float | None = None
    battery_min_pct: float | None = None
    battery_avg_pct: float | None = None

    temperature_avg_c: float | None = None
    temperature_min_c: float | None = None
    temperature_max_c: float | None = None
    temperature_amplitude_avg_c: float | None = None

    humidity_avg_pct: float | None = None
    humidity_min_pct: float | None = None
    humidity_max_pct: float | None = None

    pressure_avg_hpa: float | None = None
    pressure_min_hpa: float | None = None
    pressure_max_hpa: float | None = None
    pressure_range_hpa: float | None = None

    dew_point_avg_c: float | None = None
    absolute_humidity_avg_g_m3: float | None = None

    pm1_avg: float | None = None
    pm25_avg: float | None = None
    pm10_avg: float | None = None
    pm25_max: float | None = None

    hot_hours: float | None = None
    cold_hours: float | None = None
    dry_hours: float | None = None
    humid_hours: float | None = None
    tropical_nights: int = 0
    heat_index_max_c: float | None = None

    heating_degree_days: float | None = None
    cooling_degree_days: float | None = None


class WeatherSeriesPoint(BaseModel):
    timestamp: datetime
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    dew_point_c: float | None = None
    pm1: float | None = None
    pm25: float | None = None
    pm10: float | None = None

    indoor_temperature_c: float | None = None
    indoor_humidity_pct: float | None = None
    indoor_co2_ppm: float | None = None
    indoor_tvoc: float | None = None

    aemet_temperature_c: float | None = None
    aemet_humidity_pct: float | None = None
    aemet_pressure_hpa: float | None = None

    gas_m3: float | None = None
    electricity_kwh: float | None = None


class WeatherDailyPoint(BaseModel):
    date: str
    samples: int = 0
    coverage_pct: float | None = None
    temperature_min_c: float | None = None
    temperature_avg_c: float | None = None
    temperature_max_c: float | None = None
    humidity_avg_pct: float | None = None
    pressure_avg_hpa: float | None = None
    pm25_avg: float | None = None
    pm25_max: float | None = None
    indoor_temperature_avg_c: float | None = None
    gas_m3: float | None = None
    electricity_kwh: float | None = None
    heating_degree_days: float | None = None
    cooling_degree_days: float | None = None


class WeatherIndoorCross(BaseModel):
    available: bool = False
    samples: int = 0
    current_temperature_c: float | None = None
    current_humidity_pct: float | None = None
    current_co2_ppm: float | None = None
    current_tvoc: float | None = None
    current_pressure_hpa: float | None = None
    current_updated_at: datetime | None = None

    avg_temperature_c: float | None = None
    avg_humidity_pct: float | None = None
    avg_co2_ppm: float | None = None
    avg_tvoc: float | None = None
    avg_pressure_hpa: float | None = None

    outdoor_minus_indoor_c: float | None = None
    outdoor_minus_indoor_humidity_pct: float | None = None
    temperature_correlation: float | None = None
    humidity_correlation: float | None = None
    pressure_bias_hpa: float | None = None


class WeatherAemetHourlyBias(BaseModel):
    hour: int = Field(ge=0, le=23)
    temperature_bias_c: float | None = None


class WeatherAemetCross(BaseModel):
    available: bool = False
    stale: bool = False
    samples: int = 0
    last_updated: datetime | None = None

    temperature_bias_c: float | None = None
    temperature_mae_c: float | None = None
    temperature_correlation: float | None = None
    humidity_bias_pct: float | None = None
    humidity_mae_pct: float | None = None
    humidity_correlation: float | None = None
    pressure_bias_hpa: float | None = None
    pressure_correlation: float | None = None

    daytime_temperature_bias_c: float | None = None
    nighttime_temperature_bias_c: float | None = None
    precipitation_mm: float | None = None
    visibility_min_km: float | None = None
    hourly_bias: list[WeatherAemetHourlyBias] = Field(default_factory=list)


class WeatherEnergyCross(BaseModel):
    available: bool = False
    days: int = 0
    excluded_days: int = 0
    gas_m3: float | None = None
    gas_cost_eur: float | None = None
    electricity_kwh: float | None = None
    heating_degree_days: float | None = None
    cooling_degree_days: float | None = None
    gas_per_degree_day: float | None = None
    electricity_per_degree_day: float | None = None
    temperature_gas_correlation: float | None = None
    temperature_electricity_correlation: float | None = None
    heating_degree_gas_correlation: float | None = None
    cooling_degree_electricity_correlation: float | None = None


class WeatherPmCross(BaseModel):
    available: bool = False
    pm25_avg: float | None = None
    pm10_avg: float | None = None
    pm25_pm10_ratio: float | None = None
    pm1_pm25_ratio: float | None = None
    humidity_correlation: float | None = None
    temperature_correlation: float | None = None
    co2_correlation: float | None = None
    tvoc_correlation: float | None = None
    caveat: str = (
        "La estación no publica la unidad de PM1/PM2.5/PM10. Se muestran como "
        "índice relativo y no se comparan con umbrales sanitarios."
    )


class WeatherOverviewResponse(BaseModel):
    start: datetime
    end: datetime
    days: int
    granularity: WeatherGranularity
    generated_at: datetime
    current: WeatherCurrent
    summary: WeatherSummary
    series: list[WeatherSeriesPoint]
    daily: list[WeatherDailyPoint]
    indoor_cross: WeatherIndoorCross
    aemet_cross: WeatherAemetCross
    energy_cross: WeatherEnergyCross
    pm_cross: WeatherPmCross
    data_source: Literal["mock", "database"]
    notes: list[str] = Field(default_factory=list)
