"""Business logic for the Environment tab: school station against AEMET.

The tab compares the school weather station (``weather.meteo``) with the AEMET
observatory of Ciudad Real, stored in the same recorder. Everything is read-only.

How the two sources are aligned: an AEMET observation stamped 17:00 describes
the hour that has just finished, so it is paired with the station's mean from
16:00 to 17:00. Measured on the recorder, that pairing gives the best correlation
of all the possible offsets. Hourly station values are therefore keyed by the
*end* of their hour, in naive UTC.

AEMET has gaps in the recorder, so the response says how much of the period can
really be compared and only pairs hours where both sources have a value. The raw
PM readings have no declared unit: they are shown as a relative index and are
never compared with health thresholds.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from itertools import pairwise
from typing import Literal

from app.core.cache import TTLCache
from app.core.clock import (
    elapsed_hours,
    ensure_utc,
    local_now,
    local_tz,
    to_local,
    to_utc_naive,
    utc_now,
    validate_query_dates,
)
from app.core.config import settings
from app.core.weather_map import (
    AEMET_COMPLETE_COVERAGE_PCT,
    AEMET_ELEVATION_M,
    AEMET_ENTITIES,
    AEMET_GAP_MIN_HOURS,
    AEMET_HUMIDITY_ENTITY,
    AEMET_MIN_HOURS_PER_DAY,
    AEMET_PRECIPITATION_ENTITY,
    AEMET_PRESSURE_ENTITY,
    AEMET_STALE_HOURS,
    AEMET_TEMPERATURE_ENTITY,
    DAYTIME_END_HOUR,
    DAYTIME_START_HOUR,
    DEFAULT_INTERVAL_MINUTES,
    DEFAULT_WEATHER_DAYS,
    HOURLY_SERIES_MAX_DAYS,
    HUMIDITY_MAX_PCT,
    HUMIDITY_MIN_PCT,
    HUMIDITY_SATURATED_PCT,
    MAX_WEATHER_DAYS,
    PM_MAX_RAW,
    PRECIPITATION_MAX_MM,
    PRESSURE_MAX_HPA,
    PRESSURE_MIN_HPA,
    TEMPERATURE_MAX_C,
    TEMPERATURE_MIN_C,
    WEATHER_ENTITY,
    WeatherGranularity,
    pressure_to_station_level,
)
from app.schemas.weather import (
    AemetAvailability,
    AemetCoverage,
    AemetGap,
    AemetLatest,
    HourlyBias,
    HumidityComparison,
    MetricComparison,
    TemperatureComparison,
    WeatherComparison,
    WeatherCurrent,
    WeatherOverviewResponse,
    WeatherSeriesPoint,
    WeatherSummary,
)
from app.services import mock_data

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS, max_entries=16)
_ONE_HOUR = timedelta(hours=1)
_AEMET_RANGES: dict[str, tuple[float, float]] = {
    AEMET_TEMPERATURE_ENTITY: (TEMPERATURE_MIN_C, TEMPERATURE_MAX_C),
    AEMET_HUMIDITY_ENTITY: (HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT),
    AEMET_PRESSURE_ENTITY: (PRESSURE_MIN_HPA, PRESSURE_MAX_HPA),
    AEMET_PRECIPITATION_ENTITY: (0.0, PRECIPITATION_MAX_MM),
}


@dataclass(frozen=True)
class _Period:
    start: datetime  # aware, school timezone
    end: datetime  # aware, school timezone
    granularity: WeatherGranularity

    @property
    def start_utc(self) -> datetime:
        return to_utc_naive(self.start)

    @property
    def end_utc(self) -> datetime:
        return to_utc_naive(self.end)


@dataclass
class _StationSample:
    timestamp: datetime  # naive UTC
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None  # reduced to sea level, as published
    pm1: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    battery_pct: float | None = None


@dataclass
class _Dataset:
    data_source: Literal["mock", "database"]
    station: list[_StationSample] = field(default_factory=list)
    # Per AEMET entity: value by observation hour (naive UTC).
    aemet: dict[str, dict[datetime, float]] = field(default_factory=dict)
    latest_station: _StationSample | None = None
    latest_aemet: dict[str, tuple[datetime, float]] = field(default_factory=dict)


# --- Small helpers -------------------------------------------------------------


def _round(value: float | None, digits: int = 1) -> float | None:
    return round(value, digits) if value is not None else None


def _mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return statistics.fmean(items) if items else None


def _hours_since(moment: datetime) -> float:
    return max(0.0, (utc_now() - moment).total_seconds() / 3600.0)


def _floor_hour(moment: datetime) -> datetime:
    return moment.replace(minute=0, second=0, microsecond=0)


def _median_interval_hours(timestamps: list[datetime]) -> float:
    deltas = [
        (current - previous).total_seconds() / 3600.0
        for previous, current in pairwise(sorted(timestamps))
        if current > previous
    ]
    if not deltas:
        return DEFAULT_INTERVAL_MINUTES / 60.0
    # Ignore absurd values: a multi-day outage must not make the expected sample
    # count collapse to a handful of rows.
    return min(max(statistics.median(deltas), 1.0 / 60.0), 6.0)


def _correlation(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 3:
        return None
    mean_x = statistics.fmean(x for x, _ in pairs)
    mean_y = statistics.fmean(y for _, y in pairs)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denominator = math.sqrt(
        sum((x - mean_x) ** 2 for x, _ in pairs) * sum((y - mean_y) ** 2 for _, y in pairs)
    )
    return numerator / denominator if denominator else None


# --- Parsing -------------------------------------------------------------------


def _parse_float(value: object, minimum: float, maximum: float) -> float | None:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    # Written this way round so ``nan`` is rejected too.
    return parsed if minimum <= parsed <= maximum else None


def _attributes(raw: str | None) -> dict[str, object]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _parse_station(
    timestamp: datetime,
    state: str | None,
    raw_attributes: str | None,
) -> _StationSample | None:
    attributes = _attributes(raw_attributes)
    # Reset rows (the ``0`` written when the recorder restarts) only carry
    # ``friendly_name``/``state_class``: they are not real observations.
    known_keys = {"Humidity", "Pressure", "PM1", "PM2.5", "PM10", "Battery"}
    if not known_keys & attributes.keys():
        return None
    sample = _StationSample(
        timestamp=timestamp,
        temperature_c=_parse_float(state, TEMPERATURE_MIN_C, TEMPERATURE_MAX_C),
        humidity_pct=_parse_float(attributes.get("Humidity"), HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT),
        pressure_hpa=_parse_float(attributes.get("Pressure"), PRESSURE_MIN_HPA, PRESSURE_MAX_HPA),
        pm1=_parse_float(attributes.get("PM1"), 0.0, PM_MAX_RAW),
        pm25=_parse_float(attributes.get("PM2.5"), 0.0, PM_MAX_RAW),
        pm10=_parse_float(attributes.get("PM10"), 0.0, PM_MAX_RAW),
        battery_pct=_parse_float(attributes.get("Battery"), 0.0, 100.0),
    )
    measurements = (
        sample.temperature_c,
        sample.humidity_pct,
        sample.pressure_hpa,
        sample.pm1,
        sample.pm25,
        sample.pm10,
    )
    return None if all(value is None for value in measurements) else sample


def _observation_hour(row_time: datetime, raw_attributes: str | None) -> datetime:
    """Hour AEMET observed the value (naive UTC), not when the row was written."""
    raw = _attributes(raw_attributes).get("last_update")
    if isinstance(raw, str):
        try:
            # ``%z`` also accepts the ``+0000`` that ``fromisoformat`` rejects on
            # Python 3.10.
            observed = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            pass
        else:
            return _floor_hour(observed.astimezone(timezone.utc).replace(tzinfo=None))
    return _floor_hour(row_time)


# --- Dataset loading -----------------------------------------------------------


async def _database_dataset(period: _Period) -> _Dataset:
    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import weather_data

    database = await weather_data.load_weather_data(period.start, period.end)

    station = [
        sample
        for timestamp, state, attributes in database.weather
        if (sample := _parse_station(timestamp, state, attributes)) is not None
    ]

    aemet: dict[str, dict[datetime, float]] = {}
    latest_aemet: dict[str, tuple[datetime, float]] = {}
    for entity_id in AEMET_ENTITIES:
        minimum, maximum = _AEMET_RANGES[entity_id]
        values: dict[datetime, float] = {}
        # A repeated observation (a recorder restart) keeps its latest row.
        for timestamp, state, attributes in database.aemet.get(entity_id, []):
            value = _parse_float(state, minimum, maximum)
            if value is not None:
                values[_observation_hour(timestamp, attributes)] = value
        aemet[entity_id] = values

        latest = database.latest.get(entity_id)
        if latest is not None:
            state, attributes, updated = latest
            value = _parse_float(state, minimum, maximum)
            if value is not None:
                latest_aemet[entity_id] = (_observation_hour(updated, attributes), value)

    latest_station_row = database.latest.get(WEATHER_ENTITY)
    latest_station = (
        _parse_station(latest_station_row[2], latest_station_row[0], latest_station_row[1])
        if latest_station_row
        else None
    )

    return _Dataset(
        data_source="database",
        station=station,
        aemet=aemet,
        latest_station=latest_station,
        latest_aemet=latest_aemet,
    )


def _mock_dataset(period: _Period) -> _Dataset:
    """Deterministic series with the same shape as the real sources."""
    station: list[_StationSample] = []
    aemet: dict[str, dict[datetime, float]] = {entity_id: {} for entity_id in AEMET_ENTITIES}

    cursor = _floor_hour(period.start_utc)
    while cursor < period.end_utc:
        key = cursor.isoformat()
        local = to_local(cursor)
        hour = local.hour + local.minute / 60.0
        season = 16.5 + 8.0 * math.cos((local.month - 7) * math.pi * 2.0 / 12.0)
        daily = 6.0 * math.sin((hour - 9.0) * math.pi * 2.0 / 24.0)
        reference = season + daily
        # The station is exposed to the sun: warmer than AEMET during the day.
        solar = max(0.0, 4.0 * math.sin((hour - 8.0) * math.pi / 10.0)) if 8 <= hour <= 18 else 0.0

        humidity = min(100.0, max(20.0, 62.0 - 2.0 * (reference - 16.0)))
        sea_level_pressure = 1016.0 + 2.0 * math.sin((hour - 6.0) * math.pi * 2.0 / 24.0)
        pm25 = max(0.0, 6000.0 + mock_data.stable_noise("weather-pm", key, amplitude=2500.0))

        station.append(
            _StationSample(
                timestamp=cursor,
                temperature_c=round(
                    reference + solar + mock_data.stable_noise("station-t", key, amplitude=0.6), 1
                ),
                humidity_pct=round(
                    min(100.0, humidity + mock_data.stable_noise("station-h", key, amplitude=4.0)),
                    1,
                ),
                pressure_hpa=round(
                    sea_level_pressure + mock_data.stable_noise("station-p", key, amplitude=0.4), 1
                ),
                pm1=round(pm25 * 0.95),
                pm25=round(pm25),
                pm10=round(pm25 * 1.03),
                battery_pct=100.0,
            )
        )

        observed = cursor + _ONE_HOUR
        if observed <= period.end_utc:
            aemet[AEMET_TEMPERATURE_ENTITY][observed] = round(
                reference + mock_data.stable_noise("aemet-t", key, amplitude=0.5), 1
            )
            aemet[AEMET_HUMIDITY_ENTITY][observed] = round(humidity, 0)
            aemet[AEMET_PRESSURE_ENTITY][observed] = round(
                pressure_to_station_level(sea_level_pressure, AEMET_ELEVATION_M) + 2.0, 1
            )
            is_raining = mock_data.stable_noise("aemet-r", key, amplitude=1.0) > 0.92
            aemet[AEMET_PRECIPITATION_ENTITY][observed] = 1.2 if is_raining else 0.0

        cursor += _ONE_HOUR

    return _Dataset(
        data_source="mock",
        station=station,
        aemet=aemet,
        latest_station=station[-1] if station else None,
        latest_aemet={
            entity_id: max(values.items())
            for entity_id, values in aemet.items()
            if values
        },
    )


async def _load_dataset(period: _Period) -> _Dataset:
    # Periods ending today use the current instant as the upper bound. Round
    # that bound down to the hour so the cache key is stable between requests.
    key = ("weather-dataset", period.start.isoformat(), _floor_hour(period.end).isoformat())
    hit = _cache.get(key)
    if hit is not None:
        return hit
    if settings.DATA_SOURCE == "database":
        value = await _database_dataset(period)
    else:
        value = _mock_dataset(period)
    _cache.set(key, value)
    return value


# --- Period --------------------------------------------------------------------


def resolve_period(start: date | None = None, end: date | None = None) -> _Period:
    """Validate the custom date inputs and return local, inclusive bounds."""
    validate_query_dates(*(value for value in (start, end) if value is not None))
    now = local_now()
    today = now.date()
    end_date = end or today
    start_date = start or (end_date - timedelta(days=DEFAULT_WEATHER_DAYS - 1))

    if start_date > end_date:
        raise ValueError("La fecha inicial no puede ser posterior a la final.")
    if end_date > today:
        raise ValueError("La fecha final no puede ser futura.")
    days = (end_date - start_date).days + 1
    if days > MAX_WEATHER_DAYS:
        raise ValueError(f"El periodo máximo es de un año ({MAX_WEATHER_DAYS} días).")

    start_local = datetime.combine(start_date, time.min, tzinfo=local_tz())
    end_local = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=local_tz())
    return _Period(
        start=start_local,
        end=min(end_local, now),
        granularity="hour" if days <= HOURLY_SERIES_MAX_DAYS else "day",
    )


# --- Alignment -----------------------------------------------------------------


def _station_hourly(
    samples: list[_StationSample],
    read: Callable[[_StationSample], float | None],
) -> dict[datetime, float]:
    """Mean of a station measurement per hour, keyed by the *end* of the hour."""
    buckets: dict[datetime, list[float]] = defaultdict(list)
    for sample in samples:
        value = read(sample)
        if value is not None:
            buckets[_floor_hour(sample.timestamp) + _ONE_HOUR].append(value)
    return {key: statistics.fmean(values) for key, values in buckets.items()}


def _station_pressure_at_observatory(sample: _StationSample) -> float | None:
    if sample.pressure_hpa is None:
        return None
    return pressure_to_station_level(sample.pressure_hpa, AEMET_ELEVATION_M)


def _in_period(key: datetime, period: _Period) -> bool:
    """True when the hour that ends at ``key`` belongs to the period."""
    return period.start_utc < key <= period.end_utc


def _paired(
    station: dict[datetime, float],
    aemet: dict[datetime, float],
    period: _Period,
) -> dict[datetime, tuple[float, float]]:
    return {
        key: (station[key], value)
        for key, value in aemet.items()
        if key in station and _in_period(key, period)
    }


# --- Comparison ----------------------------------------------------------------


def _compare(pairs: list[tuple[float, float]], digits: int = 1) -> MetricComparison:
    differences = [station - aemet for station, aemet in pairs]
    return MetricComparison(
        samples=len(pairs),
        station_avg=_round(_mean(station for station, _ in pairs), digits),
        aemet_avg=_round(_mean(aemet for _, aemet in pairs), digits),
        bias=_round(_mean(differences), digits),
        mean_absolute_error=_round(_mean(abs(value) for value in differences), digits),
        correlation=_round(_correlation(pairs), 3),
    )


def _build_comparison(dataset: _Dataset, period: _Period) -> WeatherComparison:
    temperature = _paired(
        _station_hourly(dataset.station, lambda sample: sample.temperature_c),
        dataset.aemet.get(AEMET_TEMPERATURE_ENTITY, {}),
        period,
    )
    humidity = _paired(
        _station_hourly(dataset.station, lambda sample: sample.humidity_pct),
        dataset.aemet.get(AEMET_HUMIDITY_ENTITY, {}),
        period,
    )
    pressure = _paired(
        _station_hourly(dataset.station, _station_pressure_at_observatory),
        dataset.aemet.get(AEMET_PRESSURE_ENTITY, {}),
        period,
    )

    daytime: list[float] = []
    nighttime: list[float] = []
    by_local_hour: dict[int, list[float]] = defaultdict(list)
    for key, (station, aemet) in temperature.items():
        hour = to_local(key).hour
        by_local_hour[hour].append(station - aemet)
        (daytime if DAYTIME_START_HOUR <= hour < DAYTIME_END_HOUR else nighttime).append(
            station - aemet
        )

    saturated = [pair for pair in humidity.values() if pair[0] >= HUMIDITY_SATURATED_PCT]
    unsaturated = [pair for pair in humidity.values() if pair[0] < HUMIDITY_SATURATED_PCT]

    return WeatherComparison(
        temperature=TemperatureComparison(
            **_compare(list(temperature.values())).model_dump(),
            daytime_bias=_round(_mean(daytime)),
            nighttime_bias=_round(_mean(nighttime)),
        ),
        humidity=HumidityComparison(
            **_compare(list(humidity.values())).model_dump(),
            saturated_pct=(
                _round(len(saturated) / len(humidity) * 100.0, 0) if humidity else None
            ),
            unsaturated_bias=_round(_mean(station - aemet for station, aemet in unsaturated)),
        ),
        pressure=_compare(list(pressure.values())),
        hourly_bias=[
            HourlyBias(hour=hour, temperature_bias_c=_round(_mean(by_local_hour.get(hour, []))))
            for hour in range(24)
        ],
    )


def _build_gaps(observed: list[datetime], period: _Period) -> list[AemetGap]:
    """Silences of the AEMET record inside the period, newest first."""
    # The sentinels make the silences at both ends of the period count as well.
    before_first = _floor_hour(period.start_utc)
    after_last = _floor_hour(period.end_utc) + _ONE_HOUR
    gaps: list[AemetGap] = []
    for previous, current in pairwise([before_first, *observed, after_last]):
        missing = round((current - previous) / _ONE_HOUR) - 1
        if missing >= AEMET_GAP_MIN_HOURS:
            gaps.append(
                AemetGap(
                    start=ensure_utc(previous + _ONE_HOUR),
                    end=ensure_utc(current - _ONE_HOUR),
                    hours=missing,
                )
            )
    return sorted(gaps, key=lambda gap: gap.start, reverse=True)


def _build_availability(
    dataset: _Dataset,
    period: _Period,
    compared_hours: int,
) -> AemetAvailability:
    observed = sorted(
        key
        for key in dataset.aemet.get(AEMET_TEMPERATURE_ENTITY, {})
        if _in_period(key, period)
    )
    period_hours = max(1, round(elapsed_hours(period.start, period.end)))
    coverage_pct = min(100.0, compared_hours / period_hours * 100.0)
    coverage: AemetCoverage
    if compared_hours == 0:
        coverage = "none"
    elif coverage_pct >= AEMET_COMPLETE_COVERAGE_PCT:
        coverage = "complete"
    else:
        coverage = "partial"

    return AemetAvailability(
        coverage=coverage,
        period_hours=period_hours,
        observed_hours=len(observed),
        compared_hours=compared_hours,
        coverage_pct=round(coverage_pct, 1),
        first_observation=ensure_utc(observed[0]) if observed else None,
        last_observation=ensure_utc(observed[-1]) if observed else None,
        gaps=_build_gaps(observed, period),
    )


# --- Series --------------------------------------------------------------------


def _hour_grid(period: _Period) -> list[datetime]:
    """The end of every hour of the period, so a gap is drawn as a gap."""
    grid: list[datetime] = []
    cursor = _floor_hour(period.start_utc) + _ONE_HOUR
    while cursor - _ONE_HOUR < period.end_utc:
        grid.append(cursor)
        cursor += _ONE_HOUR
    return grid


def _hourly_series(dataset: _Dataset, period: _Period) -> list[WeatherSeriesPoint]:
    station = dataset.station
    temperature = _station_hourly(station, lambda sample: sample.temperature_c)
    humidity = _station_hourly(station, lambda sample: sample.humidity_pct)
    pressure = _station_hourly(station, _station_pressure_at_observatory)
    pm1 = _station_hourly(station, lambda sample: sample.pm1)
    pm25 = _station_hourly(station, lambda sample: sample.pm25)
    pm10 = _station_hourly(station, lambda sample: sample.pm10)
    battery = _station_hourly(station, lambda sample: sample.battery_pct)
    aemet_temperature = dataset.aemet.get(AEMET_TEMPERATURE_ENTITY, {})
    aemet_humidity = dataset.aemet.get(AEMET_HUMIDITY_ENTITY, {})
    aemet_pressure = dataset.aemet.get(AEMET_PRESSURE_ENTITY, {})
    aemet_precipitation = dataset.aemet.get(AEMET_PRECIPITATION_ENTITY, {})

    return [
        WeatherSeriesPoint(
            timestamp=ensure_utc(key),
            station_temperature_c=_round(temperature.get(key)),
            aemet_temperature_c=_round(aemet_temperature.get(key)),
            station_humidity_pct=_round(humidity.get(key)),
            aemet_humidity_pct=_round(aemet_humidity.get(key)),
            station_pressure_hpa=_round(pressure.get(key)),
            aemet_pressure_hpa=_round(aemet_pressure.get(key)),
            aemet_precipitation_mm=_round(aemet_precipitation.get(key)),
            pm1=_round(pm1.get(key), 0),
            pm25=_round(pm25.get(key), 0),
            pm10=_round(pm10.get(key), 0),
            battery_pct=_round(battery.get(key), 0),
        )
        for key in _hour_grid(period)
    ]


def _daily_series(dataset: _Dataset, period: _Period) -> list[WeatherSeriesPoint]:
    samples_by_day: dict[date, list[_StationSample]] = defaultdict(list)
    for sample in dataset.station:
        if period.start_utc <= sample.timestamp <= period.end_utc:
            samples_by_day[to_local(sample.timestamp).date()].append(sample)

    aemet_by_day: dict[str, dict[date, list[float]]] = {}
    for entity_id, values in dataset.aemet.items():
        by_day: dict[date, list[float]] = defaultdict(list)
        for key, value in values.items():
            if _in_period(key, period):
                # The 00:00 observation describes the last hour of the day before.
                by_day[to_local(key - _ONE_HOUR).date()].append(value)
        aemet_by_day[entity_id] = by_day

    def aemet_mean(entity_id: str, day: date) -> float | None:
        values = aemet_by_day.get(entity_id, {}).get(day, [])
        return _mean(values) if len(values) >= AEMET_MIN_HOURS_PER_DAY else None

    def station_mean(
        samples: list[_StationSample], read: Callable[[_StationSample], float | None]
    ) -> float | None:
        return _mean(value for sample in samples if (value := read(sample)) is not None)

    points: list[WeatherSeriesPoint] = []
    day = period.start.date()
    # A past period ends at the midnight that opens the following day.
    last_day = (period.end - timedelta(microseconds=1)).date()
    while day <= last_day:
        samples = samples_by_day.get(day, [])
        rain = aemet_by_day.get(AEMET_PRECIPITATION_ENTITY, {}).get(day)
        points.append(
            WeatherSeriesPoint(
                timestamp=ensure_utc(datetime.combine(day, time.min, tzinfo=local_tz())),
                station_temperature_c=_round(
                    station_mean(samples, lambda sample: sample.temperature_c)
                ),
                aemet_temperature_c=_round(aemet_mean(AEMET_TEMPERATURE_ENTITY, day)),
                station_humidity_pct=_round(
                    station_mean(samples, lambda sample: sample.humidity_pct)
                ),
                aemet_humidity_pct=_round(aemet_mean(AEMET_HUMIDITY_ENTITY, day)),
                station_pressure_hpa=_round(
                    station_mean(samples, _station_pressure_at_observatory)
                ),
                aemet_pressure_hpa=_round(aemet_mean(AEMET_PRESSURE_ENTITY, day)),
                aemet_precipitation_mm=_round(sum(rain)) if rain else None,
                pm1=_round(station_mean(samples, lambda sample: sample.pm1), 0),
                pm25=_round(station_mean(samples, lambda sample: sample.pm25), 0),
                pm10=_round(station_mean(samples, lambda sample: sample.pm10), 0),
                battery_pct=_round(station_mean(samples, lambda sample: sample.battery_pct), 0),
            )
        )
        day += timedelta(days=1)
    return points


# --- Current values and summary ------------------------------------------------


def _build_current(dataset: _Dataset) -> WeatherCurrent:
    latest = dataset.latest_station or (dataset.station[-1] if dataset.station else None)
    if latest is None:
        return WeatherCurrent()

    age_hours = _hours_since(latest.timestamp)
    interval = _median_interval_hours([sample.timestamp for sample in dataset.station])
    return WeatherCurrent(
        temperature_c=_round(latest.temperature_c),
        humidity_pct=_round(latest.humidity_pct),
        pressure_hpa=_round(latest.pressure_hpa),
        pm1=_round(latest.pm1, 0),
        pm25=_round(latest.pm25, 0),
        pm10=_round(latest.pm10, 0),
        battery_pct=_round(latest.battery_pct, 0),
        last_updated=ensure_utc(latest.timestamp),
        age_hours=_round(age_hours),
        status="ok" if age_hours <= max(2.0, interval * 2.0) else "stale",
    )


def _build_aemet_latest(dataset: _Dataset) -> AemetLatest:
    if not dataset.latest_aemet:
        return AemetLatest()

    def value(entity_id: str) -> float | None:
        latest = dataset.latest_aemet.get(entity_id)
        return latest[1] if latest else None

    observed_at = max(moment for moment, _ in dataset.latest_aemet.values())
    age_hours = _hours_since(observed_at)
    return AemetLatest(
        temperature_c=_round(value(AEMET_TEMPERATURE_ENTITY)),
        humidity_pct=_round(value(AEMET_HUMIDITY_ENTITY)),
        pressure_hpa=_round(value(AEMET_PRESSURE_ENTITY)),
        observed_at=ensure_utc(observed_at),
        age_hours=_round(age_hours),
        stale=age_hours > AEMET_STALE_HOURS,
    )


def _build_summary(dataset: _Dataset, period: _Period) -> WeatherSummary:
    samples = [
        sample
        for sample in dataset.station
        if period.start_utc <= sample.timestamp <= period.end_utc
    ]

    def collect(read: Callable[[_StationSample], float | None]) -> list[float]:
        return [value for sample in samples if (value := read(sample)) is not None]

    temperatures = collect(lambda sample: sample.temperature_c)
    humidities = collect(lambda sample: sample.humidity_pct)
    batteries = collect(lambda sample: sample.battery_pct)

    interval = _median_interval_hours([sample.timestamp for sample in samples])
    expected = elapsed_hours(period.start, period.end) / interval
    coverage = min(100.0, len(samples) / expected * 100.0) if expected > 0 else None

    rain = [
        value
        for key, value in dataset.aemet.get(AEMET_PRECIPITATION_ENTITY, {}).items()
        if _in_period(key, period)
    ]

    return WeatherSummary(
        samples=len(samples),
        coverage_pct=_round(coverage),
        temperature_avg_c=_round(_mean(temperatures)),
        temperature_min_c=_round(min(temperatures, default=None)),
        temperature_max_c=_round(max(temperatures, default=None)),
        humidity_avg_pct=_round(_mean(humidities)),
        humidity_min_pct=_round(min(humidities, default=None)),
        humidity_max_pct=_round(max(humidities, default=None)),
        pressure_avg_hpa=_round(_mean(collect(lambda sample: sample.pressure_hpa))),
        pm25_avg=_round(_mean(collect(lambda sample: sample.pm25)), 0),
        pm10_avg=_round(_mean(collect(lambda sample: sample.pm10)), 0),
        battery_min_pct=_round(min(batteries, default=None), 0),
        aemet_precipitation_mm=_round(sum(rain)) if rain else None,
        aemet_rainy_hours=sum(1 for value in rain if value > 0),
    )


def _notes(data_source: Literal["mock", "database"]) -> list[str]:
    source = (
        "Datos simulados: el backend está en modo mock."
        if data_source == "mock"
        else "Datos reales del recorder de Home Assistant (solo lectura)."
    )
    return [
        source,
        "AEMET es el observatorio oficial de Ciudad Real, no la estación del centro.",
        "Cada observación horaria de AEMET se compara con la media de la estación en la hora "
        "anterior, y solo se comparan las horas con datos de ambas fuentes.",
        "La presión de la estación se publica a nivel del mar; para compararla se reduce a la "
        f"altitud del observatorio de AEMET ({AEMET_ELEVATION_M} m).",
        f"Una media diaria de AEMET necesita al menos {AEMET_MIN_HOURS_PER_DAY} observaciones.",
        "La humedad de la estación se considera saturada desde "
        f"el {HUMIDITY_SATURATED_PCT:.0f} %: ahí el sensor deja de distinguir valores.",
        "Las partículas no declaran unidad: se muestran como índice relativo y no se comparan "
        "con umbrales sanitarios.",
    ]


async def build_overview(
    start: date | None = None,
    end: date | None = None,
) -> WeatherOverviewResponse:
    period = resolve_period(start, end)
    dataset = await _load_dataset(period)
    comparison = _build_comparison(dataset, period)
    series = (
        _hourly_series(dataset, period)
        if period.granularity == "hour"
        else _daily_series(dataset, period)
    )

    return WeatherOverviewResponse(
        start=ensure_utc(period.start),
        end=ensure_utc(period.end),
        granularity=period.granularity,
        generated_at=ensure_utc(utc_now()),
        current=_build_current(dataset),
        aemet_latest=_build_aemet_latest(dataset),
        aemet_availability=_build_availability(
            dataset, period, comparison.temperature.samples
        ),
        comparison=comparison,
        summary=_build_summary(dataset, period),
        series=series,
        data_source=dataset.data_source,
        notes=_notes(dataset.data_source),
    )


def clear_cache() -> None:
    _cache.clear()
