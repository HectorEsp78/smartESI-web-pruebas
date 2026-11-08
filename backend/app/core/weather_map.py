"""Weather-station catalogue and thresholds for the Environment tab.

The recorder exposes a single weather entity, ``weather.meteo``. Its *state* is
the outdoor temperature; the rest of the measurements live in the state
attributes:

- ``Humidity`` (%)
- ``Pressure`` (hPa, reduced to sea level)
- ``PM1``, ``PM2.5`` and ``PM10`` (raw particle readings, no unit published)
- ``Battery`` (%)

The station does not publish wind, rain or solar radiation. ``sensor.ambiente``
is an indoor multi-sensor (temperature, humidity, pressure, CO₂, TVOC, light)
and is used only for the indoor/outdoor cross. The AEMET entities are an
external reference for Ciudad Real, not the school station, and are clearly
marked as such.

All values are read-only. The raw particle readings are intentionally not
compared with health thresholds because their unit is unknown.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WeatherGranularity = Literal["hour", "day"]

WEATHER_ENTITY = "weather.meteo"
AMBIENT_ENTITY = "sensor.ambiente"

AEMET_TEMPERATURE_ENTITY = "sensor.aemet_temperature"
AEMET_HUMIDITY_ENTITY = "sensor.aemet_humidity"
AEMET_PRESSURE_ENTITY = "sensor.aemet_pressure"
AEMET_PRECIPITATION_ENTITY = "sensor.aemet_precipitation"
AEMET_VISIBILITY_ENTITY = "sensor.aemet_visibility"
AEMET_SNOW_ENTITY = "sensor.aemet_snow"

AEMET_ENTITIES: tuple[str, ...] = (
    AEMET_TEMPERATURE_ENTITY,
    AEMET_HUMIDITY_ENTITY,
    AEMET_PRESSURE_ENTITY,
    AEMET_PRECIPITATION_ENTITY,
    AEMET_VISIBILITY_ENTITY,
    AEMET_SNOW_ENTITY,
)

GAS_M3_ENTITY = "sensor.daily_gas"
GAS_COST_ENTITY = "sensor.daily_gas_cost"
ELECTRICITY_ENTITY = "sensor.cuadro_general"

DEFAULT_WEATHER_DAYS = 30
ALLOWED_WEATHER_DAYS = (7, 30, 90)
MAX_WEATHER_DAYS = 90

# The station normally reports every 15 minutes. Used only as a fallback when
# the actual cadence cannot be inferred from the data.
DEFAULT_INTERVAL_MINUTES = 15.0

# AEMET reports station pressure at the Ciudad Real observatory (626.17 m).
AEMET_ELEVATION_M = 626.17
AEMET_STALE_HOURS = 24.0

TEMPERATURE_MIN_C = -20.0
TEMPERATURE_MAX_C = 60.0
HUMIDITY_MIN_PCT = 1.0
HUMIDITY_MAX_PCT = 100.0
PRESSURE_MIN_HPA = 900.0
PRESSURE_MAX_HPA = 1100.0
PM_MAX_RAW = 100_000.0

# The recorder was restored on 2026-10-12 and the cumulative energy meters
# jumped by several days' worth of consumption in a single hour. Daily values
# above these limits are treated as counter anomalies in the energy cross.
GAS_DAILY_MAX_M3 = 200.0
ELECTRICITY_DAILY_MAX_KWH = 3_000.0

HOT_TEMPERATURE_C = 30.0
COLD_TEMPERATURE_C = 10.0
TROPICAL_NIGHT_C = 20.0
DRY_HUMIDITY_PCT = 30.0
HUMID_HUMIDITY_PCT = 80.0

HEATING_BASE_C = 18.0
COOLING_BASE_C = 22.0

PRESSURE_TREND_3H = 3.0
PRESSURE_TREND_24H = 24.0


@dataclass(frozen=True)
class WeatherMetric:
    key: str
    label: str
    unit: str


WEATHER_METRICS: tuple[WeatherMetric, ...] = (
    WeatherMetric("temperature_c", "Temperatura", "°C"),
    WeatherMetric("humidity_pct", "Humedad", "%"),
    WeatherMetric("pressure_hpa", "Presión", "hPa"),
    WeatherMetric("pm25", "PM2.5", "índice"),
)


def pressure_to_station_level(pressure_hpa: float, elevation_m: float) -> float:
    """Reduce a sea-level pressure to the given altitude (barometric formula)."""
    factor = (1.0 - 2.25577e-5 * elevation_m) ** 5.25588
    return pressure_hpa * factor
