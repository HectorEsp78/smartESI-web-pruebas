"""Weather-station and AEMET catalogue for the Environment tab.

The recorder exposes the school station as ``weather.meteo``. Its *state* is the
outdoor temperature; the other measurements live in the state attributes:

- ``Humidity`` (%)
- ``Pressure`` (hPa, reduced to sea level)
- ``PM1``, ``PM2.5`` and ``PM10`` (raw particle readings, no unit published)
- ``Battery`` (%)

The station does not publish wind, rain or solar radiation. The ``sensor.aemet_*``
entities are the official AEMET observatory of Ciudad Real, an external reference
stored hourly; each row carries its observation time in the ``last_update``
attribute and is written about 30 minutes later.

All values are read-only. The raw particle readings are intentionally not
compared with health thresholds because their unit is unknown.
"""

from __future__ import annotations

from typing import Literal

WeatherGranularity = Literal["hour", "day"]

WEATHER_ENTITY = "weather.meteo"

AEMET_TEMPERATURE_ENTITY = "sensor.aemet_temperature"
AEMET_HUMIDITY_ENTITY = "sensor.aemet_humidity"
AEMET_PRESSURE_ENTITY = "sensor.aemet_pressure"
AEMET_PRECIPITATION_ENTITY = "sensor.aemet_precipitation"

AEMET_ENTITIES: tuple[str, ...] = (
    AEMET_TEMPERATURE_ENTITY,
    AEMET_HUMIDITY_ENTITY,
    AEMET_PRESSURE_ENTITY,
    AEMET_PRECIPITATION_ENTITY,
)

DEFAULT_WEATHER_DAYS = 30
MAX_WEATHER_DAYS = 366
# Up to this many days the charts keep hourly detail; longer periods use days.
HOURLY_SERIES_MAX_DAYS = 7

# The station normally reports every 15 minutes. Used only as a fallback when
# the actual cadence cannot be inferred from the data.
DEFAULT_INTERVAL_MINUTES = 15.0

# AEMET reports station pressure at the Ciudad Real observatory (626.17 m).
AEMET_ELEVATION_M = 626.17
AEMET_STALE_HOURS = 24.0
# Silences at least this long are listed as gaps in the AEMET record.
AEMET_GAP_MIN_HOURS = 6
# A daily AEMET mean needs this many observations: a few hours of a single
# afternoon would not represent the day.
AEMET_MIN_HOURS_PER_DAY = 12
# From this coverage of the period the comparison is considered complete.
AEMET_COMPLETE_COVERAGE_PCT = 95.0

TEMPERATURE_MIN_C = -30.0
TEMPERATURE_MAX_C = 60.0
HUMIDITY_MIN_PCT = 1.0
HUMIDITY_MAX_PCT = 100.0
PRESSURE_MIN_HPA = 800.0
PRESSURE_MAX_HPA = 1100.0
PRECIPITATION_MAX_MM = 500.0
PM_MAX_RAW = 100_000.0

# The station's humidity sensor saturates: at this value it no longer measures.
HUMIDITY_SATURATED_PCT = 99.0

# Local hours used to separate the effect of the sun on the station.
DAYTIME_START_HOUR = 9
DAYTIME_END_HOUR = 18


def pressure_to_station_level(pressure_hpa: float, elevation_m: float) -> float:
    """Reduce a sea-level pressure to the given altitude (barometric formula)."""
    factor = (1.0 - 2.25577e-5 * elevation_m) ** 5.25588
    return pressure_hpa * factor
