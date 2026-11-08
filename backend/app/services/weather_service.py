"""Business logic for the Environment (weather station) tab.

The tab combines the school weather station (``weather.meteo``) with the indoor
reference sensor (``sensor.ambiente``), the external AEMET reference and the
building energy meters. The station publishes temperature, humidity, pressure,
raw particle readings and battery; it does not publish wind or rain.

Everything is read-only. The raw PM readings have no declared unit, so they are
shown as a relative index and are never compared with health thresholds.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal

from app.core.buildings import BUILDINGS
from app.core.cache import TTLCache
from app.core.clock import ensure_utc, local_now, local_tz, to_local, utc_now
from app.core.config import settings
from app.core.weather_map import (
    AEMET_ELEVATION_M,
    AEMET_ENTITIES,
    AEMET_HUMIDITY_ENTITY,
    AEMET_PRECIPITATION_ENTITY,
    AEMET_PRESSURE_ENTITY,
    AEMET_STALE_HOURS,
    AEMET_TEMPERATURE_ENTITY,
    AEMET_VISIBILITY_ENTITY,
    ALLOWED_WEATHER_DAYS,
    AMBIENT_ENTITY,
    COLD_TEMPERATURE_C,
    COOLING_BASE_C,
    DEFAULT_INTERVAL_MINUTES,
    DRY_HUMIDITY_PCT,
    ELECTRICITY_ENTITY,
    ELECTRICITY_DAILY_MAX_KWH,
    GAS_COST_ENTITY,
    GAS_DAILY_MAX_M3,
    GAS_M3_ENTITY,
    HEATING_BASE_C,
    HOT_TEMPERATURE_C,
    HUMID_HUMIDITY_PCT,
    HUMIDITY_MAX_PCT,
    HUMIDITY_MIN_PCT,
    PM_MAX_RAW,
    PRESSURE_MAX_HPA,
    PRESSURE_MIN_HPA,
    PRESSURE_TREND_24H,
    PRESSURE_TREND_3H,
    TEMPERATURE_MAX_C,
    TEMPERATURE_MIN_C,
    TROPICAL_NIGHT_C,
    WEATHER_ENTITY,
    WeatherGranularity,
    pressure_to_station_level,
)
from app.schemas.weather import (
    WeatherAemetCross,
    WeatherAemetHourlyBias,
    WeatherCurrent,
    WeatherDailyPoint,
    WeatherEnergyCross,
    WeatherIndoorCross,
    WeatherOverviewResponse,
    WeatherPmCross,
    WeatherSeriesPoint,
    WeatherSummary,
)
from app.services import mock_data

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS, max_entries=16)
_ONE_HOUR = timedelta(hours=1)


@dataclass(frozen=True)
class _Period:
    start: datetime  # aware, school timezone
    end: datetime  # aware, school timezone
    days: int
    granularity: WeatherGranularity


@dataclass
class _WeatherPoint:
    timestamp: datetime  # naive UTC
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    pm1: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    battery_pct: float | None = None


@dataclass
class _AmbientPoint:
    timestamp: datetime
    temperature_c: float | None = None
    humidity_pct: float | None = None
    co2_ppm: float | None = None
    tvoc: float | None = None
    pressure_hpa: float | None = None
    lux: float | None = None


@dataclass
class _AemetPoint:
    timestamp: datetime
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    precipitation_mm: float | None = None
    visibility_km: float | None = None


@dataclass
class _Dataset:
    data_source: Literal["mock", "database"]
    weather: list[_WeatherPoint] = field(default_factory=list)
    ambient: list[_AmbientPoint] = field(default_factory=list)
    aemet: dict[str, list[_AemetPoint]] = field(default_factory=dict)
    latest_weather: _WeatherPoint | None = None
    latest_ambient: _AmbientPoint | None = None
    latest_aemet: dict[str, _AemetPoint | None] = field(default_factory=dict)
    gas_m3: dict[datetime, float] = field(default_factory=dict)
    gas_cost: dict[datetime, float] = field(default_factory=dict)
    electricity_kwh: dict[datetime, float] = field(default_factory=dict)


# --- Small helpers -------------------------------------------------------------


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _round(value: float | None, digits: int = 1) -> float | None:
    return round(value, digits) if value is not None else None


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _median_interval_hours(timestamps: list[datetime]) -> float:
    if len(timestamps) < 2:
        return DEFAULT_INTERVAL_MINUTES / 60.0
    ordered = sorted(timestamps)
    deltas = [
        (current - previous).total_seconds() / 3600.0
        for previous, current in zip(ordered, ordered[1:])
        if current > previous
    ]
    if not deltas:
        return DEFAULT_INTERVAL_MINUTES / 60.0
    interval = statistics.median(deltas)
    # Ignore absurd gaps: a multi-day outage must not make the expected sample
    # count collapse to a handful of rows.
    return min(max(interval, 1.0 / 60.0), 6.0)


def _parse_float(
    value: object,
    minimum: float,
    maximum: float,
) -> float | None:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed < minimum or parsed > maximum:
        return None
    return parsed


def _attrs(raw: str | None) -> dict[str, object]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _local_date(timestamp: datetime) -> str:
    return to_local(timestamp).date().isoformat()


def _local_hour(timestamp: datetime) -> int:
    return to_local(timestamp).hour


def _corr(pairs: list[tuple[float | None, float | None]]) -> float | None:
    clean = [(x, y) for x, y in pairs if x is not None and y is not None]
    if len(clean) < 3:
        return None
    count = len(clean)
    mean_x = sum(x for x, _ in clean) / count
    mean_y = sum(y for _, y in clean) / count
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in clean)
    denominator = math.sqrt(
        sum((x - mean_x) ** 2 for x, _ in clean)
        * sum((y - mean_y) ** 2 for _, y in clean)
    )
    if denominator == 0:
        return None
    return round(numerator / denominator, 3)


def _dew_point(temperature_c: float | None, humidity_pct: float | None) -> float | None:
    if temperature_c is None or humidity_pct is None or humidity_pct <= 0:
        return None
    a, b = 17.62, 243.12
    gamma = math.log(humidity_pct / 100.0) + (a * temperature_c) / (b + temperature_c)
    return round((b * gamma) / (a - gamma), 1)


def _absolute_humidity(
    temperature_c: float | None,
    humidity_pct: float | None,
) -> float | None:
    if temperature_c is None or humidity_pct is None:
        return None
    saturation = 6.112 * math.exp(
        (17.67 * temperature_c) / (temperature_c + 243.5)
    )
    return round(
        (humidity_pct / 100.0) * saturation * 216.7 / (temperature_c + 273.15),
        2,
    )


def _heat_index(
    temperature_c: float | None,
    humidity_pct: float | None,
) -> float | None:
    if temperature_c is None:
        return None
    if humidity_pct is None or temperature_c < 27.0 or humidity_pct < 40.0:
        return round(temperature_c, 1)
    t = temperature_c * 9.0 / 5.0 + 32.0
    rh = humidity_pct
    value = (
        -42.379
        + 2.04901523 * t
        + 10.14333127 * rh
        - 0.22475541 * t * rh
        - 0.00683783 * t * t
        - 0.05481717 * rh * rh
        + 0.00122874 * t * t * rh
        + 0.00085282 * t * rh * rh
        - 0.00000199 * t * t * rh * rh
    )
    return round((value - 32.0) * 5.0 / 9.0, 1)


def _hourly_means(points: list[object], attribute: str) -> dict[datetime, float]:
    buckets: dict[datetime, list[float]] = defaultdict(list)
    for point in points:
        value = getattr(point, attribute)
        if value is None:
            continue
        timestamp = getattr(point, "timestamp")
        key = timestamp.replace(minute=0, second=0, microsecond=0)
        buckets[key].append(float(value))
    return {key: statistics.fmean(values) for key, values in buckets.items()}


# --- Parsing -------------------------------------------------------------------


def _parse_weather(
    timestamp: datetime,
    state: str | None,
    raw_attributes: str | None,
) -> _WeatherPoint | None:
    attributes = _attrs(raw_attributes)
    # Reset rows (for example the two ``0`` values written when the recorder was
    # restored) only carry ``friendly_name``/``state_class``. Without any known
    # measurement attribute they are not a real observation.
    known_keys = {"Humidity", "Pressure", "PM1", "PM2.5", "PM10", "Battery"}
    if not known_keys & attributes.keys():
        return None
    point = _WeatherPoint(
        timestamp=timestamp,
        temperature_c=_parse_float(state, TEMPERATURE_MIN_C, TEMPERATURE_MAX_C),
        humidity_pct=_parse_float(
            attributes.get("Humidity"), HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT
        ),
        pressure_hpa=_parse_float(
            attributes.get("Pressure"), PRESSURE_MIN_HPA, PRESSURE_MAX_HPA
        ),
        pm1=_parse_float(attributes.get("PM1"), 0.0, PM_MAX_RAW),
        pm25=_parse_float(attributes.get("PM2.5"), 0.0, PM_MAX_RAW),
        pm10=_parse_float(attributes.get("PM10"), 0.0, PM_MAX_RAW),
        battery_pct=_parse_float(attributes.get("Battery"), 0.0, 100.0),
    )
    if all(
        value is None
        for value in (
            point.temperature_c,
            point.humidity_pct,
            point.pressure_hpa,
            point.pm1,
            point.pm25,
            point.pm10,
        )
    ):
        return None
    return point


def _parse_ambient(
    timestamp: datetime,
    state: str | None,
    raw_attributes: str | None,
) -> _AmbientPoint | None:
    attributes = _attrs(raw_attributes)
    known_keys = {"Humedad", "CO2", "TVOC", "Presion", "Iluminacion visible"}
    if not known_keys & attributes.keys():
        return None
    point = _AmbientPoint(
        timestamp=timestamp,
        temperature_c=_parse_float(state, TEMPERATURE_MIN_C, TEMPERATURE_MAX_C),
        humidity_pct=_parse_float(
            attributes.get("Humedad"), HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT
        ),
        co2_ppm=_parse_float(attributes.get("CO2"), 300.0, 5000.0),
        tvoc=_parse_float(attributes.get("TVOC"), 0.0, 10000.0),
        pressure_hpa=_parse_float(attributes.get("Presion"), 800.0, 1100.0),
        lux=_parse_float(attributes.get("Iluminacion visible"), 0.0, 200_000.0),
    )
    if all(
        value is None
        for value in (
            point.temperature_c,
            point.humidity_pct,
            point.co2_ppm,
            point.tvoc,
            point.pressure_hpa,
        )
    ):
        return None
    return point


def _parse_aemet(
    timestamp: datetime,
    state: str | None,
    entity_id: str,
) -> _AemetPoint | None:
    point = _AemetPoint(timestamp=timestamp)
    if entity_id == AEMET_TEMPERATURE_ENTITY:
        point.temperature_c = _parse_float(state, -30.0, 60.0)
    elif entity_id == AEMET_HUMIDITY_ENTITY:
        point.humidity_pct = _parse_float(state, 0.0, 100.0)
    elif entity_id == AEMET_PRESSURE_ENTITY:
        point.pressure_hpa = _parse_float(state, 800.0, 1100.0)
    elif entity_id == AEMET_PRECIPITATION_ENTITY:
        point.precipitation_mm = _parse_float(state, 0.0, 500.0)
    elif entity_id == AEMET_VISIBILITY_ENTITY:
        point.visibility_km = _parse_float(state, 0.0, 1000.0)
    else:
        return None
    if all(
        value is None
        for value in (
            point.temperature_c,
            point.humidity_pct,
            point.pressure_hpa,
            point.precipitation_mm,
            point.visibility_km,
        )
    ):
        return None
    return point


def _hourly_increments(rows: list[tuple[datetime, float]]) -> dict[datetime, float]:
    """Split cumulative statistics into hourly increments.

    Negative jumps are counter resets and are ignored instead of producing a
    negative consumption spike. The first row is only a baseline.
    """
    increments: dict[datetime, float] = defaultdict(float)
    previous_total: float | None = None
    for timestamp, total in sorted(rows):
        if previous_total is not None:
            delta = total - previous_total
            if delta >= 0:
                key = timestamp.replace(minute=0, second=0, microsecond=0)
                increments[key] += delta
        previous_total = total
    return dict(increments)


# --- Dataset loading -----------------------------------------------------------


def _latest_weather(dataset: _Dataset) -> _WeatherPoint | None:
    if dataset.latest_weather is not None:
        return dataset.latest_weather
    return dataset.weather[-1] if dataset.weather else None


def _latest_ambient(dataset: _Dataset) -> _AmbientPoint | None:
    if dataset.latest_ambient is not None:
        return dataset.latest_ambient
    return dataset.ambient[-1] if dataset.ambient else None


async def _database_dataset(period: _Period) -> _Dataset:
    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import weather_data

    database = await weather_data.load_weather_data(period.start, period.end)

    weather = [
        point
        for timestamp, state, attributes in database.weather
        if (point := _parse_weather(timestamp, state, attributes)) is not None
    ]
    ambient = [
        point
        for timestamp, state, attributes in database.ambient
        if (point := _parse_ambient(timestamp, state, attributes)) is not None
    ]

    aemet: dict[str, list[_AemetPoint]] = {}
    latest_aemet: dict[str, _AemetPoint | None] = {}
    for entity_id in AEMET_ENTITIES:
        aemet[entity_id] = [
            point
            for timestamp, state, _attributes in database.aemet.get(entity_id, [])
            if (point := _parse_aemet(timestamp, state, entity_id)) is not None
        ]
        latest = database.latest.get(entity_id)
        latest_aemet[entity_id] = (
            _parse_aemet(latest[2], latest[0], entity_id) if latest else None
        )

    latest_weather_row = database.latest.get(WEATHER_ENTITY)
    latest_ambient_row = database.latest.get(AMBIENT_ENTITY)

    return _Dataset(
        data_source="database",
        weather=weather,
        ambient=ambient,
        aemet=aemet,
        latest_weather=(
            _parse_weather(
                latest_weather_row[2], latest_weather_row[0], latest_weather_row[1]
            )
            if latest_weather_row
            else None
        ),
        latest_ambient=(
            _parse_ambient(
                latest_ambient_row[2], latest_ambient_row[0], latest_ambient_row[1]
            )
            if latest_ambient_row
            else None
        ),
        latest_aemet=latest_aemet,
        gas_m3=_hourly_increments(database.sums.get(GAS_M3_ENTITY, [])),
        gas_cost=_hourly_increments(database.sums.get(GAS_COST_ENTITY, [])),
        electricity_kwh=_hourly_increments(database.sums.get(ELECTRICITY_ENTITY, [])),
    )


def _mock_dataset(period: _Period) -> _Dataset:
    weather: list[_WeatherPoint] = []
    ambient: list[_AmbientPoint] = []
    aemet: dict[str, list[_AemetPoint]] = {entity_id: [] for entity_id in AEMET_ENTITIES}
    gas_m3: dict[datetime, float] = {}
    gas_cost: dict[datetime, float] = {}
    electricity_kwh: dict[datetime, float] = {}

    cursor = ensure_utc(period.start).replace(tzinfo=None)
    cursor = cursor.replace(minute=0, second=0, microsecond=0)
    while cursor < ensure_utc(period.end).replace(tzinfo=None):
        local = to_local(cursor)
        month = local.month
        hour = local.hour + local.minute / 60.0

        season = 16.5 + 8.0 * math.cos((month - 7) * math.pi * 2.0 / 12.0)
        daily = 6.0 * math.sin((hour - 9.0) * math.pi * 2.0 / 24.0)
        temperature = season + daily + mock_data.stable_noise(
            "weather-temp", cursor.isoformat(), amplitude=1.0
        )
        humidity = _clamp(
            62.0
            - 1.6 * (temperature - 18.0)
            + mock_data.stable_noise("weather-hum", cursor.isoformat(), amplitude=4.0),
            20.0,
            98.0,
        )
        pressure = (
            1016.0
            + 4.0 * math.cos((month - 1) * math.pi * 2.0 / 12.0)
            + 2.0 * math.sin((hour - 6.0) * math.pi * 2.0 / 24.0)
            + mock_data.stable_noise("weather-pres", cursor.isoformat(), amplitude=1.2)
        )
        pm25 = _clamp(
            6000.0
            + 3000.0 * math.sin((hour - 7.0) * math.pi * 2.0 / 24.0)
            + mock_data.stable_noise("weather-pm", cursor.isoformat(), amplitude=2500.0),
            0.0,
            20_000.0,
        )
        pm1 = _clamp(
            pm25 * 0.95
            + mock_data.stable_noise("weather-pm1", cursor.isoformat(), amplitude=100.0),
            0.0,
            20_000.0,
        )
        pm10 = _clamp(
            pm25 * 1.03
            + mock_data.stable_noise("weather-pm10", cursor.isoformat(), amplitude=100.0),
            0.0,
            20_000.0,
        )
        battery = _clamp(
            90.0 + mock_data.stable_noise("weather-batt", cursor.isoformat(), amplitude=5.0),
            0.0,
            100.0,
        )
        weather.append(
            _WeatherPoint(
                timestamp=cursor,
                temperature_c=round(temperature, 1),
                humidity_pct=round(humidity, 1),
                pressure_hpa=round(pressure, 1),
                pm1=round(pm1, 0),
                pm25=round(pm25, 0),
                pm10=round(pm10, 0),
                battery_pct=round(battery, 0),
            )
        )

        indoor_temperature = _clamp(
            temperature
            + 4.0
            + mock_data.stable_noise("indoor-temp", cursor.isoformat(), amplitude=0.7),
            17.0,
            32.0,
        )
        indoor_humidity = _clamp(
            humidity
            - 12.0
            + mock_data.stable_noise("indoor-hum", cursor.isoformat(), amplitude=3.0),
            30.0,
            65.0,
        )
        occupancy = mock_data.environment_presence_ratio("A11", local)
        indoor_co2 = _clamp(
            420.0
            + 450.0 * occupancy
            + mock_data.stable_noise("indoor-co2", cursor.isoformat(), amplitude=60.0),
            380.0,
            1500.0,
        )
        indoor_tvoc = _clamp(
            120.0
            + 200.0 * occupancy
            + mock_data.stable_noise("indoor-tvoc", cursor.isoformat(), amplitude=40.0),
            0.0,
            1000.0,
        )
        indoor_pressure = (
            pressure_to_station_level(pressure, AEMET_ELEVATION_M)
            + mock_data.stable_noise("indoor-pres", cursor.isoformat(), amplitude=0.5)
        )
        daylight = max(0.0, math.sin((hour - 7.0) * math.pi / 11.0)) if 7 <= hour <= 18 else 0.0
        indoor_lux = _clamp(
            500.0 * daylight
            + mock_data.stable_noise("indoor-lux", cursor.isoformat(), amplitude=20.0),
            0.0,
            1000.0,
        )
        ambient.append(
            _AmbientPoint(
                timestamp=cursor,
                temperature_c=round(indoor_temperature, 1),
                humidity_pct=round(indoor_humidity, 1),
                co2_ppm=round(indoor_co2, 0),
                tvoc=round(indoor_tvoc, 0),
                pressure_hpa=round(indoor_pressure, 1),
                lux=round(indoor_lux, 0),
            )
        )

        aemet_temperature = (
            temperature
            - 2.0
            + mock_data.stable_noise("aemet-temp", cursor.isoformat(), amplitude=0.6)
        )
        aemet_humidity = _clamp(
            humidity
            + 8.0
            + mock_data.stable_noise("aemet-hum", cursor.isoformat(), amplitude=4.0),
            10.0,
            100.0,
        )
        aemet_pressure = (
            pressure_to_station_level(pressure, AEMET_ELEVATION_M)
            + mock_data.stable_noise("aemet-pres", cursor.isoformat(), amplitude=0.4)
        )
        aemet[AEMET_TEMPERATURE_ENTITY].append(
            _AemetPoint(timestamp=cursor, temperature_c=round(aemet_temperature, 1))
        )
        aemet[AEMET_HUMIDITY_ENTITY].append(
            _AemetPoint(timestamp=cursor, humidity_pct=round(aemet_humidity, 1))
        )
        aemet[AEMET_PRESSURE_ENTITY].append(
            _AemetPoint(timestamp=cursor, pressure_hpa=round(aemet_pressure, 1))
        )
        aemet[AEMET_PRECIPITATION_ENTITY].append(
            _AemetPoint(timestamp=cursor, precipitation_mm=0.0)
        )
        aemet[AEMET_VISIBILITY_ENTITY].append(
            _AemetPoint(timestamp=cursor, visibility_km=20.0)
        )

        gas_m3[cursor] = mock_data.environment_gas_m3(local)
        gas_cost[cursor] = mock_data.environment_gas_cost(local)
        electricity_kwh[cursor] = sum(
            mock_data.hour_energy_kwh(building, local) for building in BUILDINGS
        )

        cursor += _ONE_HOUR

    latest_weather = weather[-1] if weather else None
    latest_ambient = ambient[-1] if ambient else None
    latest_aemet = {
        entity_id: (points[-1] if points else None)
        for entity_id, points in aemet.items()
    }

    return _Dataset(
        data_source="mock",
        weather=weather,
        ambient=ambient,
        aemet=aemet,
        latest_weather=latest_weather,
        latest_ambient=latest_ambient,
        latest_aemet=latest_aemet,
        gas_m3=gas_m3,
        gas_cost=gas_cost,
        electricity_kwh=electricity_kwh,
    )


async def _load_dataset(period: _Period) -> _Dataset:
    cache_end = period.end.replace(minute=0, second=0, microsecond=0)
    key = ("weather-dataset", period.days, cache_end.isoformat())
    hit = _cache.get(key)
    if hit is not None:
        return hit
    if settings.DATA_SOURCE == "database":
        value = await _database_dataset(period)
    else:
        value = _mock_dataset(period)
    _cache.set(key, value)
    return value


# --- Period and aggregations ---------------------------------------------------


def resolve_period(days: int) -> _Period:
    """Validate the requested window and return local bounds."""
    if days not in ALLOWED_WEATHER_DAYS:
        allowed = ", ".join(str(item) for item in ALLOWED_WEATHER_DAYS)
        raise ValueError(f"El periodo debe ser uno de: {allowed} días.")
    end = local_now()
    start = end - timedelta(days=days)
    granularity: WeatherGranularity = "hour" if days <= 7 else "day"
    return _Period(start=start, end=end, days=days, granularity=granularity)


def _day_overlap_hours(day: date, period: _Period) -> float:
    day_start = datetime.combine(day, time.min, tzinfo=local_tz())
    day_end = day_start + timedelta(days=1)
    overlap_start = max(day_start, period.start)
    overlap_end = min(day_end, period.end)
    return max(0.0, (overlap_end - overlap_start).total_seconds() / 3600.0)


def _daily_points(dataset: _Dataset, period: _Period) -> list[WeatherDailyPoint]:
    weather_by_day: dict[str, list[_WeatherPoint]] = defaultdict(list)
    for point in dataset.weather:
        weather_by_day[_local_date(point.timestamp)].append(point)

    ambient_by_day: dict[str, list[float]] = defaultdict(list)
    for point in dataset.ambient:
        if point.temperature_c is not None:
            ambient_by_day[_local_date(point.timestamp)].append(point.temperature_c)

    gas_by_day: dict[str, float] = defaultdict(float)
    for timestamp, value in dataset.gas_m3.items():
        gas_by_day[_local_date(timestamp)] += value

    electricity_by_day: dict[str, float] = defaultdict(float)
    for timestamp, value in dataset.electricity_kwh.items():
        electricity_by_day[_local_date(timestamp)] += value

    interval = _median_interval_hours([point.timestamp for point in dataset.weather])
    day_keys: list[str] = []
    cursor_day = period.start.date()
    while cursor_day <= period.end.date():
        day_keys.append(cursor_day.isoformat())
        cursor_day += timedelta(days=1)
    result: list[WeatherDailyPoint] = []

    for day_key in day_keys:
        points = weather_by_day.get(day_key, [])
        temperatures = [
            point.temperature_c for point in points if point.temperature_c is not None
        ]
        humidities = [
            point.humidity_pct for point in points if point.humidity_pct is not None
        ]
        pressures = [
            point.pressure_hpa for point in points if point.pressure_hpa is not None
        ]
        pm25 = [point.pm25 for point in points if point.pm25 is not None]
        day = date.fromisoformat(day_key)
        overlap_hours = _day_overlap_hours(day, period)
        expected = overlap_hours / interval if interval > 0 else 0.0
        coverage = min(100.0, len(points) / expected * 100.0) if expected > 0 else None
        average_temperature = _mean(temperatures)

        heating = (
            max(0.0, HEATING_BASE_C - average_temperature)
            if average_temperature is not None
            else None
        )
        cooling = (
            max(0.0, average_temperature - COOLING_BASE_C)
            if average_temperature is not None
            else None
        )

        result.append(
            WeatherDailyPoint(
                date=day_key,
                samples=len(points),
                coverage_pct=_round(coverage, 1),
                temperature_min_c=_round(min(temperatures) if temperatures else None, 1),
                temperature_avg_c=_round(average_temperature, 1),
                temperature_max_c=_round(max(temperatures) if temperatures else None, 1),
                humidity_avg_pct=_round(_mean(humidities), 1),
                pressure_avg_hpa=_round(_mean(pressures), 1),
                pm25_avg=_round(_mean(pm25), 0),
                pm25_max=_round(max(pm25) if pm25 else None, 0),
                indoor_temperature_avg_c=_round(_mean(ambient_by_day.get(day_key, [])), 1),
                gas_m3=_round(gas_by_day.get(day_key), 2),
                electricity_kwh=_round(electricity_by_day.get(day_key), 1),
                heating_degree_days=_round(heating, 1),
                cooling_degree_days=_round(cooling, 1),
            )
        )

    return result


def _summary(dataset: _Dataset, period: _Period, daily: list[WeatherDailyPoint]) -> WeatherSummary:
    points = dataset.weather
    temperatures = [
        point.temperature_c for point in points if point.temperature_c is not None
    ]
    humidities = [
        point.humidity_pct for point in points if point.humidity_pct is not None
    ]
    pressures = [
        point.pressure_hpa for point in points if point.pressure_hpa is not None
    ]
    batteries = [
        point.battery_pct for point in points if point.battery_pct is not None
    ]
    pm1 = [point.pm1 for point in points if point.pm1 is not None]
    pm25 = [point.pm25 for point in points if point.pm25 is not None]
    pm10 = [point.pm10 for point in points if point.pm10 is not None]

    interval = _median_interval_hours([point.timestamp for point in points])
    period_hours = max(0.0, (period.end - period.start).total_seconds() / 3600.0)
    expected = period_hours / interval if interval > 0 else 0.0
    coverage = min(100.0, len(points) / expected * 100.0) if expected > 0 else None
    outage_hours = max(0.0, period_hours - len(points) * interval)

    amplitudes: list[float] = []
    for daily_point in daily:
        if (
            daily_point.temperature_min_c is not None
            and daily_point.temperature_max_c is not None
            and daily_point.samples >= 2
        ):
            amplitudes.append(
                daily_point.temperature_max_c - daily_point.temperature_min_c
            )

    heat_indices = [
        value
        for point in points
        if (value := _heat_index(point.temperature_c, point.humidity_pct)) is not None
    ]
    tropical_nights = sum(
        1
        for daily_point in daily
        if daily_point.temperature_min_c is not None
        and daily_point.temperature_min_c >= TROPICAL_NIGHT_C
        and daily_point.samples >= 2
    )
    heating_degree_days = sum(
        value
        for daily_point in daily
        if (value := daily_point.heating_degree_days) is not None
    )
    cooling_degree_days = sum(
        value
        for daily_point in daily
        if (value := daily_point.cooling_degree_days) is not None
    )

    return WeatherSummary(
        samples=len(points),
        coverage_pct=_round(coverage, 1),
        median_interval_hours=_round(interval, 2),
        outage_hours=_round(outage_hours, 1),
        battery_min_pct=_round(min(batteries) if batteries else None, 0),
        battery_avg_pct=_round(_mean(batteries), 0),
        temperature_avg_c=_round(_mean(temperatures), 1),
        temperature_min_c=_round(min(temperatures) if temperatures else None, 1),
        temperature_max_c=_round(max(temperatures) if temperatures else None, 1),
        temperature_amplitude_avg_c=_round(_mean(amplitudes), 1),
        humidity_avg_pct=_round(_mean(humidities), 1),
        humidity_min_pct=_round(min(humidities) if humidities else None, 1),
        humidity_max_pct=_round(max(humidities) if humidities else None, 1),
        pressure_avg_hpa=_round(_mean(pressures), 1),
        pressure_min_hpa=_round(min(pressures) if pressures else None, 1),
        pressure_max_hpa=_round(max(pressures) if pressures else None, 1),
        pressure_range_hpa=(
            _round(max(pressures) - min(pressures), 1) if pressures else None
        ),
        dew_point_avg_c=_round(
            _mean(
                [
                    value
                    for point in points
                    if (value := _dew_point(point.temperature_c, point.humidity_pct))
                    is not None
                ]
            ),
            1,
        ),
        absolute_humidity_avg_g_m3=_round(
            _mean(
                [
                    value
                    for point in points
                    if (
                        value := _absolute_humidity(
                            point.temperature_c, point.humidity_pct
                        )
                    )
                    is not None
                ]
            ),
            2,
        ),
        pm1_avg=_round(_mean(pm1), 0),
        pm25_avg=_round(_mean(pm25), 0),
        pm10_avg=_round(_mean(pm10), 0),
        pm25_max=_round(max(pm25) if pm25 else None, 0),
        hot_hours=_round(
            sum(interval for value in temperatures if value >= HOT_TEMPERATURE_C), 1
        ),
        cold_hours=_round(
            sum(interval for value in temperatures if value <= COLD_TEMPERATURE_C), 1
        ),
        dry_hours=_round(
            sum(interval for value in humidities if value < DRY_HUMIDITY_PCT), 1
        ),
        humid_hours=_round(
            sum(interval for value in humidities if value >= HUMID_HUMIDITY_PCT), 1
        ),
        tropical_nights=tropical_nights,
        heat_index_max_c=_round(max(heat_indices) if heat_indices else None, 1),
        heating_degree_days=_round(heating_degree_days, 1),
        cooling_degree_days=_round(cooling_degree_days, 1),
    )


def _pressure_trend(
    points: list[_WeatherPoint],
    latest: _WeatherPoint,
    hours: float,
) -> float | None:
    if latest.pressure_hpa is None:
        return None
    threshold = latest.timestamp - timedelta(hours=hours)
    candidates = [
        point
        for point in points
        if point.pressure_hpa is not None and point.timestamp <= threshold
    ]
    if not candidates:
        return None
    past = max(candidates, key=lambda point: point.timestamp)
    return round(latest.pressure_hpa - past.pressure_hpa, 1)  # type: ignore[operator]


def _current(dataset: _Dataset, period: _Period) -> WeatherCurrent:
    latest = _latest_weather(dataset)
    if latest is None:
        return WeatherCurrent(status="missing")

    points = list(dataset.weather)
    if not any(point.timestamp == latest.timestamp for point in points):
        points.append(latest)
    points.sort(key=lambda point: point.timestamp)

    age_hours = max(0.0, (utc_now() - latest.timestamp).total_seconds() / 3600.0)
    interval = _median_interval_hours([point.timestamp for point in dataset.weather])
    stale_after = max(2.0, interval * 2.0)
    status: Literal["ok", "stale", "missing"] = (
        "ok" if age_hours <= stale_after else "stale"
    )

    pressure_station = (
        pressure_to_station_level(latest.pressure_hpa, AEMET_ELEVATION_M)
        if latest.pressure_hpa is not None
        else None
    )
    pm_ratio = (
        latest.pm25 / latest.pm10
        if latest.pm25 is not None and latest.pm10 not in (None, 0)
        else None
    )

    return WeatherCurrent(
        temperature_c=_round(latest.temperature_c, 1),
        humidity_pct=_round(latest.humidity_pct, 1),
        pressure_hpa=_round(latest.pressure_hpa, 1),
        pressure_station_hpa=_round(pressure_station, 1),
        pm1=_round(latest.pm1, 0),
        pm25=_round(latest.pm25, 0),
        pm10=_round(latest.pm10, 0),
        battery_pct=_round(latest.battery_pct, 0),
        last_updated=ensure_utc(latest.timestamp),
        age_hours=_round(age_hours, 1),
        status=status,
        dew_point_c=_dew_point(latest.temperature_c, latest.humidity_pct),
        absolute_humidity_g_m3=_absolute_humidity(
            latest.temperature_c, latest.humidity_pct
        ),
        heat_index_c=_heat_index(latest.temperature_c, latest.humidity_pct),
        pressure_trend_3h_hpa=_pressure_trend(points, latest, PRESSURE_TREND_3H),
        pressure_trend_24h_hpa=_pressure_trend(points, latest, PRESSURE_TREND_24H),
        pm25_pm10_ratio=_round(pm_ratio, 3),
    )


def _series(dataset: _Dataset, period: _Period, daily: list[WeatherDailyPoint]) -> list[WeatherSeriesPoint]:
    if period.granularity == "day":
        gas_by_day: dict[str, float] = defaultdict(float)
        for timestamp, value in dataset.gas_m3.items():
            gas_by_day[_local_date(timestamp)] += value
        electricity_by_day: dict[str, float] = defaultdict(float)
        for timestamp, value in dataset.electricity_kwh.items():
            electricity_by_day[_local_date(timestamp)] += value

        def _by_day(points: list[object], attribute: str) -> dict[str, list[float]]:
            grouped: dict[str, list[float]] = defaultdict(list)
            for point in points:
                value = getattr(point, attribute)
                if value is not None:
                    grouped[_local_date(getattr(point, "timestamp"))].append(float(value))
            return grouped

        indoor_humidity_by_day = _by_day(dataset.ambient, "humidity_pct")
        indoor_co2_by_day = _by_day(dataset.ambient, "co2_ppm")
        indoor_tvoc_by_day = _by_day(dataset.ambient, "tvoc")
        aemet_temperature_by_day = _by_day(
            dataset.aemet.get(AEMET_TEMPERATURE_ENTITY, []), "temperature_c"
        )
        aemet_humidity_by_day = _by_day(
            dataset.aemet.get(AEMET_HUMIDITY_ENTITY, []), "humidity_pct"
        )
        aemet_pressure_by_day = _by_day(
            dataset.aemet.get(AEMET_PRESSURE_ENTITY, []), "pressure_hpa"
        )
        pm1_by_day = _by_day(dataset.weather, "pm1")
        pm10_by_day = _by_day(dataset.weather, "pm10")

        result: list[WeatherSeriesPoint] = []
        for daily_point in daily:
            day = date.fromisoformat(daily_point.date)
            timestamp = ensure_utc(
                datetime.combine(day, time.min, tzinfo=local_tz())
            )
            result.append(
                WeatherSeriesPoint(
                    timestamp=timestamp,
                    temperature_c=daily_point.temperature_avg_c,
                    humidity_pct=daily_point.humidity_avg_pct,
                    pressure_hpa=daily_point.pressure_avg_hpa,
                    dew_point_c=_dew_point(
                        daily_point.temperature_avg_c,
                        daily_point.humidity_avg_pct,
                    ),
                    pm1=_round(_mean(pm1_by_day.get(daily_point.date, [])), 0),
                    pm25=daily_point.pm25_avg,
                    pm10=_round(_mean(pm10_by_day.get(daily_point.date, [])), 0),
                    indoor_temperature_c=daily_point.indoor_temperature_avg_c,
                    indoor_humidity_pct=_round(
                        _mean(indoor_humidity_by_day.get(daily_point.date, [])), 1
                    ),
                    indoor_co2_ppm=_round(
                        _mean(indoor_co2_by_day.get(daily_point.date, [])), 0
                    ),
                    indoor_tvoc=_round(
                        _mean(indoor_tvoc_by_day.get(daily_point.date, [])), 0
                    ),
                    aemet_temperature_c=_round(
                        _mean(aemet_temperature_by_day.get(daily_point.date, [])), 1
                    ),
                    aemet_humidity_pct=_round(
                        _mean(aemet_humidity_by_day.get(daily_point.date, [])), 1
                    ),
                    aemet_pressure_hpa=_round(
                        _mean(aemet_pressure_by_day.get(daily_point.date, [])), 1
                    ),
                    gas_m3=daily_point.gas_m3,
                    electricity_kwh=daily_point.electricity_kwh,
                )
            )
        return result

    weather_series = {
        "temperature_c": _hourly_means(dataset.weather, "temperature_c"),
        "humidity_pct": _hourly_means(dataset.weather, "humidity_pct"),
        "pressure_hpa": _hourly_means(dataset.weather, "pressure_hpa"),
        "pm1": _hourly_means(dataset.weather, "pm1"),
        "pm25": _hourly_means(dataset.weather, "pm25"),
        "pm10": _hourly_means(dataset.weather, "pm10"),
    }
    indoor_series = {
        "indoor_temperature_c": _hourly_means(dataset.ambient, "temperature_c"),
        "indoor_humidity_pct": _hourly_means(dataset.ambient, "humidity_pct"),
        "indoor_co2_ppm": _hourly_means(dataset.ambient, "co2_ppm"),
        "indoor_tvoc": _hourly_means(dataset.ambient, "tvoc"),
    }
    aemet_series = {
        "aemet_temperature_c": _hourly_means(
            dataset.aemet.get(AEMET_TEMPERATURE_ENTITY, []), "temperature_c"
        ),
        "aemet_humidity_pct": _hourly_means(
            dataset.aemet.get(AEMET_HUMIDITY_ENTITY, []), "humidity_pct"
        ),
        "aemet_pressure_hpa": _hourly_means(
            dataset.aemet.get(AEMET_PRESSURE_ENTITY, []), "pressure_hpa"
        ),
    }

    keys: set[datetime] = set()
    for series in (*weather_series.values(), *indoor_series.values(), *aemet_series.values()):
        keys.update(series)
    keys.update(dataset.gas_m3)
    keys.update(dataset.electricity_kwh)
    for timestamp in (period.start, period.end):
        keys.add(
            ensure_utc(timestamp)
            .replace(tzinfo=None)
            .replace(minute=0, second=0, microsecond=0)
        )

    # Energy statistics are fetched with a two-day baseline so the first hour
    # can be filled forward. Do not leak those baseline hours into the chart.
    start_utc = ensure_utc(period.start).replace(tzinfo=None)
    end_utc = ensure_utc(period.end).replace(tzinfo=None)
    keys = {key for key in keys if start_utc <= key <= end_utc}

    result = []
    for key in sorted(keys):
        result.append(
            WeatherSeriesPoint(
                timestamp=ensure_utc(key),
                temperature_c=_round(weather_series["temperature_c"].get(key), 1),
                humidity_pct=_round(weather_series["humidity_pct"].get(key), 1),
                pressure_hpa=_round(weather_series["pressure_hpa"].get(key), 1),
                dew_point_c=_dew_point(
                    weather_series["temperature_c"].get(key),
                    weather_series["humidity_pct"].get(key),
                ),
                pm1=_round(weather_series["pm1"].get(key), 0),
                pm25=_round(weather_series["pm25"].get(key), 0),
                pm10=_round(weather_series["pm10"].get(key), 0),
                indoor_temperature_c=_round(
                    indoor_series["indoor_temperature_c"].get(key), 1
                ),
                indoor_humidity_pct=_round(
                    indoor_series["indoor_humidity_pct"].get(key), 1
                ),
                indoor_co2_ppm=_round(indoor_series["indoor_co2_ppm"].get(key), 0),
                indoor_tvoc=_round(indoor_series["indoor_tvoc"].get(key), 0),
                aemet_temperature_c=_round(
                    aemet_series["aemet_temperature_c"].get(key), 1
                ),
                aemet_humidity_pct=_round(
                    aemet_series["aemet_humidity_pct"].get(key), 1
                ),
                aemet_pressure_hpa=_round(
                    aemet_series["aemet_pressure_hpa"].get(key), 1
                ),
                gas_m3=_round(dataset.gas_m3.get(key), 2),
                electricity_kwh=_round(dataset.electricity_kwh.get(key), 1),
            )
        )
    return result


def _indoor_cross(dataset: _Dataset) -> WeatherIndoorCross:
    latest_ambient = _latest_ambient(dataset)
    if latest_ambient is None:
        return WeatherIndoorCross()

    weather_temperature = _hourly_means(dataset.weather, "temperature_c")
    weather_humidity = _hourly_means(dataset.weather, "humidity_pct")
    weather_pressure = _hourly_means(dataset.weather, "pressure_hpa")
    indoor_temperature = _hourly_means(dataset.ambient, "temperature_c")
    indoor_humidity = _hourly_means(dataset.ambient, "humidity_pct")
    indoor_pressure = _hourly_means(dataset.ambient, "pressure_hpa")

    common = sorted(
        set(weather_temperature) & set(indoor_temperature)
    )
    temperature_differences = [
        weather_temperature[key] - indoor_temperature[key] for key in common
    ]
    humidity_differences = [
        weather_humidity[key] - indoor_humidity[key]
        for key in common
        if key in weather_humidity and key in indoor_humidity
    ]
    pressure_differences = [
        indoor_pressure[key]
        - pressure_to_station_level(weather_pressure[key], AEMET_ELEVATION_M)
        for key in common
        if key in indoor_pressure and key in weather_pressure
    ]

    return WeatherIndoorCross(
        available=bool(common),
        samples=len(common),
        current_temperature_c=_round(latest_ambient.temperature_c, 1),
        current_humidity_pct=_round(latest_ambient.humidity_pct, 1),
        current_co2_ppm=_round(latest_ambient.co2_ppm, 0),
        current_tvoc=_round(latest_ambient.tvoc, 0),
        current_pressure_hpa=_round(latest_ambient.pressure_hpa, 1),
        current_updated_at=ensure_utc(latest_ambient.timestamp),
        avg_temperature_c=_round(
            _mean([indoor_temperature[key] for key in common]), 1
        ),
        avg_humidity_pct=_round(
            _mean(
                [
                    indoor_humidity[key]
                    for key in common
                    if key in indoor_humidity
                ]
            ),
            1,
        ),
        avg_co2_ppm=_round(
            _mean([value for value in _hourly_means(dataset.ambient, "co2_ppm").values()]),
            0,
        ),
        avg_tvoc=_round(
            _mean([value for value in _hourly_means(dataset.ambient, "tvoc").values()]),
            0,
        ),
        avg_pressure_hpa=_round(
            _mean(
                [
                    indoor_pressure[key]
                    for key in common
                    if key in indoor_pressure
                ]
            ),
            1,
        ),
        outdoor_minus_indoor_c=_round(_mean(temperature_differences), 1),
        outdoor_minus_indoor_humidity_pct=_round(_mean(humidity_differences), 1),
        temperature_correlation=_corr(
            [
                (weather_temperature[key], indoor_temperature[key])
                for key in common
            ]
        ),
        humidity_correlation=_corr(
            [
                (weather_humidity.get(key), indoor_humidity.get(key))
                for key in common
            ]
        ),
        pressure_bias_hpa=_round(_mean(pressure_differences), 1),
    )


def _aemet_cross(dataset: _Dataset, period: _Period) -> WeatherAemetCross:
    aemet_temperature_points = dataset.aemet.get(AEMET_TEMPERATURE_ENTITY, [])
    aemet_humidity_points = dataset.aemet.get(AEMET_HUMIDITY_ENTITY, [])
    aemet_pressure_points = dataset.aemet.get(AEMET_PRESSURE_ENTITY, [])
    aemet_precipitation_points = dataset.aemet.get(AEMET_PRECIPITATION_ENTITY, [])
    aemet_visibility_points = dataset.aemet.get(AEMET_VISIBILITY_ENTITY, [])

    last_updated: datetime | None = None
    for points in (
        aemet_temperature_points,
        aemet_humidity_points,
        aemet_pressure_points,
        aemet_precipitation_points,
        aemet_visibility_points,
    ):
        if points:
            candidate = max(points, key=lambda point: point.timestamp).timestamp
            last_updated = candidate if last_updated is None else max(last_updated, candidate)
    for point in dataset.latest_aemet.values():
        if point is not None:
            last_updated = (
                point.timestamp if last_updated is None else max(last_updated, point.timestamp)
            )

    stale = (
        last_updated is not None
        and (utc_now() - last_updated).total_seconds() / 3600.0 > AEMET_STALE_HOURS
    )

    weather_temperature = _hourly_means(dataset.weather, "temperature_c")
    weather_humidity = _hourly_means(dataset.weather, "humidity_pct")
    weather_pressure = _hourly_means(dataset.weather, "pressure_hpa")
    aemet_temperature = _hourly_means(aemet_temperature_points, "temperature_c")
    aemet_humidity = _hourly_means(aemet_humidity_points, "humidity_pct")
    aemet_pressure = _hourly_means(aemet_pressure_points, "pressure_hpa")

    common_temperature = sorted(set(weather_temperature) & set(aemet_temperature))
    common_humidity = sorted(set(weather_humidity) & set(aemet_humidity))
    common_pressure = sorted(set(weather_pressure) & set(aemet_pressure))

    temperature_pairs = [
        (weather_temperature[key], aemet_temperature[key])
        for key in common_temperature
    ]
    humidity_pairs = [
        (weather_humidity[key], aemet_humidity[key]) for key in common_humidity
    ]
    pressure_pairs = [
        (
            pressure_to_station_level(weather_pressure[key], AEMET_ELEVATION_M),
            aemet_pressure[key],
        )
        for key in common_pressure
    ]

    temperature_biases = [a - b for a, b in temperature_pairs]
    humidity_biases = [a - b for a, b in humidity_pairs]
    pressure_biases = [a - b for a, b in pressure_pairs]

    daytime_biases: list[float] = []
    nighttime_biases: list[float] = []
    hourly_biases: dict[int, list[float]] = defaultdict(list)
    for key, bias in zip(common_temperature, temperature_biases):
        hour = _local_hour(key)
        hourly_biases[hour].append(bias)
        if 9 <= hour < 18:
            daytime_biases.append(bias)
        else:
            nighttime_biases.append(bias)

    precipitation = sum(
        point.precipitation_mm
        for point in aemet_precipitation_points
        if point.precipitation_mm is not None
        and period.start <= to_local(point.timestamp) < period.end
    )
    visibility = [
        point.visibility_km
        for point in aemet_visibility_points
        if point.visibility_km is not None
    ]

    return WeatherAemetCross(
        available=bool(common_temperature or common_humidity or common_pressure),
        stale=stale,
        samples=len(common_temperature),
        last_updated=ensure_utc(last_updated) if last_updated else None,
        temperature_bias_c=_round(_mean(temperature_biases), 1),
        temperature_mae_c=_round(
            _mean([abs(value) for value in temperature_biases]), 1
        ),
        temperature_correlation=_corr(temperature_pairs),
        humidity_bias_pct=_round(_mean(humidity_biases), 1),
        humidity_mae_pct=_round(_mean([abs(value) for value in humidity_biases]), 1),
        humidity_correlation=_corr(humidity_pairs),
        pressure_bias_hpa=_round(_mean(pressure_biases), 1),
        pressure_correlation=_corr(pressure_pairs),
        daytime_temperature_bias_c=_round(_mean(daytime_biases), 1),
        nighttime_temperature_bias_c=_round(_mean(nighttime_biases), 1),
        precipitation_mm=_round(precipitation, 1) if aemet_precipitation_points else None,
        visibility_min_km=_round(min(visibility), 1) if visibility else None,
        hourly_bias=[
            WeatherAemetHourlyBias(
                hour=hour,
                temperature_bias_c=_round(_mean(hourly_biases.get(hour, [])), 1),
            )
            for hour in range(24)
        ],
    )


def _energy_cross(
    dataset: _Dataset,
    daily: list[WeatherDailyPoint],
) -> WeatherEnergyCross:
    gas_cost_by_day: dict[str, float] = defaultdict(float)
    for timestamp, value in dataset.gas_cost.items():
        gas_cost_by_day[_local_date(timestamp)] += value

    gas_values = [
        daily_point.gas_m3
        for daily_point in daily
        if daily_point.gas_m3 is not None
    ]
    electricity_values = [
        daily_point.electricity_kwh
        for daily_point in daily
        if daily_point.electricity_kwh is not None
    ]
    gas_limit = max(
        GAS_DAILY_MAX_M3,
        4.0 * statistics.median(gas_values) if gas_values else 0.0,
    )
    electricity_limit = max(
        ELECTRICITY_DAILY_MAX_KWH,
        4.0 * statistics.median(electricity_values) if electricity_values else 0.0,
    )

    valid_days: list[WeatherDailyPoint] = []
    excluded_days = 0
    for daily_point in daily:
        if (
            daily_point.gas_m3 is not None
            and daily_point.gas_m3 > gas_limit
        ) or (
            daily_point.electricity_kwh is not None
            and daily_point.electricity_kwh > electricity_limit
        ):
            excluded_days += 1
            continue
        if daily_point.temperature_avg_c is None:
            continue
        if daily_point.gas_m3 is None and daily_point.electricity_kwh is None:
            continue
        valid_days.append(daily_point)

    if not valid_days:
        return WeatherEnergyCross(excluded_days=excluded_days)

    gas_total = sum(
        daily_point.gas_m3
        for daily_point in valid_days
        if daily_point.gas_m3 is not None
    )
    gas_cost_total = sum(
        gas_cost_by_day.get(daily_point.date, 0.0) for daily_point in valid_days
    )
    electricity_total = sum(
        daily_point.electricity_kwh
        for daily_point in valid_days
        if daily_point.electricity_kwh is not None
    )
    available = bool(gas_total or electricity_total)
    if not available:
        return WeatherEnergyCross(excluded_days=excluded_days)

    heating_days = sum(
        value
        for daily_point in valid_days
        if (value := daily_point.heating_degree_days) is not None
    )
    cooling_days = sum(
        value
        for daily_point in valid_days
        if (value := daily_point.cooling_degree_days) is not None
    )

    temperature_gas_pairs = [
        (daily_point.temperature_avg_c, daily_point.gas_m3)
        for daily_point in valid_days
    ]
    temperature_electricity_pairs = [
        (daily_point.temperature_avg_c, daily_point.electricity_kwh)
        for daily_point in valid_days
    ]
    heating_gas_pairs = [
        (daily_point.heating_degree_days, daily_point.gas_m3)
        for daily_point in valid_days
    ]
    cooling_electricity_pairs = [
        (daily_point.cooling_degree_days, daily_point.electricity_kwh)
        for daily_point in valid_days
    ]

    return WeatherEnergyCross(
        available=True,
        days=len(valid_days),
        excluded_days=excluded_days,
        gas_m3=_round(gas_total, 2),
        gas_cost_eur=_round(gas_cost_total, 2),
        electricity_kwh=_round(electricity_total, 1),
        heating_degree_days=_round(heating_days, 1),
        cooling_degree_days=_round(cooling_days, 1),
        gas_per_degree_day=(
            _round(gas_total / heating_days, 3) if heating_days >= 5.0 else None
        ),
        electricity_per_degree_day=(
            _round(electricity_total / cooling_days, 1)
            if cooling_days >= 5.0
            else None
        ),
        temperature_gas_correlation=_corr(temperature_gas_pairs),
        temperature_electricity_correlation=_corr(temperature_electricity_pairs),
        heating_degree_gas_correlation=_corr(heating_gas_pairs),
        cooling_degree_electricity_correlation=_corr(cooling_electricity_pairs),
    )


def _pm_cross(dataset: _Dataset) -> WeatherPmCross:
    points = [
        point
        for point in dataset.weather
        if point.pm25 is not None or point.pm10 is not None or point.pm1 is not None
    ]
    if not points:
        return WeatherPmCross()

    pm1 = [point.pm1 for point in points if point.pm1 is not None]
    pm25 = [point.pm25 for point in points if point.pm25 is not None]
    pm10 = [point.pm10 for point in points if point.pm10 is not None]

    pm25_hourly = _hourly_means(dataset.weather, "pm25")
    co2_hourly = _hourly_means(dataset.ambient, "co2_ppm")
    tvoc_hourly = _hourly_means(dataset.ambient, "tvoc")
    common = sorted(set(pm25_hourly) & (set(co2_hourly) | set(tvoc_hourly)))

    pm25_average = _mean(pm25)
    pm10_average = _mean(pm10)
    pm1_average = _mean(pm1)

    return WeatherPmCross(
        available=bool(pm25 or pm10),
        pm25_avg=_round(pm25_average, 0),
        pm10_avg=_round(pm10_average, 0),
        pm25_pm10_ratio=(
            _round(pm25_average / pm10_average, 3)
            if pm25_average is not None and pm10_average not in (None, 0)
            else None
        ),
        pm1_pm25_ratio=(
            _round(pm1_average / pm25_average, 3)
            if pm1_average is not None and pm25_average not in (None, 0)
            else None
        ),
        humidity_correlation=_corr(
            [(point.pm25, point.humidity_pct) for point in points]
        ),
        temperature_correlation=_corr(
            [(point.pm25, point.temperature_c) for point in points]
        ),
        co2_correlation=_corr(
            [(pm25_hourly.get(key), co2_hourly.get(key)) for key in common]
        ),
        tvoc_correlation=_corr(
            [(pm25_hourly.get(key), tvoc_hourly.get(key)) for key in common]
        ),
    )


def _notes(
    dataset: _Dataset,
    current: WeatherCurrent,
    aemet_cross: WeatherAemetCross,
    energy_cross: WeatherEnergyCross,
) -> list[str]:
    notes = [
        "La estación weather.meteo publica temperatura, humedad, presión, PM1/PM2.5/PM10 y batería; no publica viento ni lluvia.",
        "Los valores de PM no declaran unidad. Se muestran como índice relativo y no se comparan con umbrales sanitarios.",
        "AEMET es una referencia externa de Ciudad Real, no la estación del centro. Puede estar desactualizada.",
        "La temperatura exterior puede estar afectada por exposición solar; compárala con AEMET y con la temperatura interior.",
        "El gas es del edificio y la electricidad del cuadro general; los cruces energéticos son orientativos.",
    ]
    if dataset.data_source == "mock":
        notes.insert(0, "Datos simulados: el backend está en modo mock.")
    else:
        notes.insert(0, "Datos reales del recorder de Home Assistant (solo lectura).")
    if current.status == "stale" and current.last_updated is not None:
        notes.append(
            f"La estación no envía datos desde {current.last_updated.isoformat()}; "
            "las cifras actuales pueden estar desfasadas."
        )
    if aemet_cross.stale and aemet_cross.last_updated is not None:
        notes.append(
            f"AEMET no se actualiza desde {aemet_cross.last_updated.isoformat()}; "
            "el cruce usa el periodo en que ambos sensores coincidieron."
        )
    if energy_cross.excluded_days:
        notes.append(
            f"Se excluyen {energy_cross.excluded_days} día(s) con saltos anómalos de "
            "los contadores de gas o electricidad."
        )
    return notes


async def build_overview(days: int) -> WeatherOverviewResponse:
    period = resolve_period(days)
    dataset = await _load_dataset(period)
    daily = _daily_points(dataset, period)
    summary = _summary(dataset, period, daily)
    current = _current(dataset, period)
    indoor_cross = _indoor_cross(dataset)
    aemet_cross = _aemet_cross(dataset, period)
    energy_cross = _energy_cross(dataset, daily)
    pm_cross = _pm_cross(dataset)
    series = _series(dataset, period, daily)

    return WeatherOverviewResponse(
        start=ensure_utc(period.start),
        end=ensure_utc(period.end),
        days=period.days,
        granularity=period.granularity,
        generated_at=ensure_utc(utc_now()),
        current=current,
        summary=summary,
        series=series,
        daily=daily,
        indoor_cross=indoor_cross,
        aemet_cross=aemet_cross,
        energy_cross=energy_cross,
        pm_cross=pm_cross,
        data_source=dataset.data_source,
        notes=_notes(dataset, current, aemet_cross, energy_cross),
    )


def clear_cache() -> None:
    _cache.clear()
