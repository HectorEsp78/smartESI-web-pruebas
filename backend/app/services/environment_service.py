"""Business logic for the Infrastructure (room environment) tab.

The tab exposes one page per confirmed room. Each page combines:

- temperature and humidity (long-term statistics);
- CO₂ (raw states, because this recorder has no CO₂ statistics);
- presence (statistics for the generic sensors, raw transitions for motion);
- building-level ambient temperature and gas as decision-making context.

The service loads the whole room catalogue once per period, caches that
read-only dataset and then builds either the compact index or one room detail.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from itertools import pairwise
from typing import TYPE_CHECKING, Literal

from app.core.cache import TTLCache
from app.core.clock import ensure_utc, local_now, local_tz, validate_query_dates
from app.core.config import settings
from app.core.environment_map import (
    AMBIENT_TEMPERATURE_ENTITY,
    CO2_MAX_PPM,
    CO2_MIN_PPM,
    DEFAULT_ENVIRONMENT_DAYS,
    ENVIRONMENT_ROOMS,
    ENVIRONMENT_ROOMS_BY_ID,
    GAS_COST_ENTITY,
    GAS_M3_ENTITY,
    HUMIDITY_MAX_PCT,
    HUMIDITY_MIN_PCT,
    MAX_ENVIRONMENT_DAYS,
    TEMPERATURE_MAX_C,
    TEMPERATURE_MIN_C,
    EnvironmentQuality,
    EnvironmentRoomConfig,
    building_label,
    co2_status,
    humidity_status,
    parse_presence,
    temperature_status,
    worst_status,
)
from app.schemas.environment import (
    EnvironmentBenchmark,
    EnvironmentCo2Occupancy,
    EnvironmentContext,
    EnvironmentGranularity,
    EnvironmentHeatmapCell,
    EnvironmentOverviewResponse,
    EnvironmentRoomDetailResponse,
    EnvironmentRoomSummary,
    EnvironmentSeriesPoint,
    EnvironmentSummary,
    EnvironmentThermalRecovery,
)
from app.services import mock_data
from app.services.lighting_context import Bucket

if TYPE_CHECKING:
    from app.db.environment_data import EnvironmentDatabaseData

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS, max_entries=32)
_ONE_DAY = timedelta(days=1)


@dataclass
class _RoomData:
    temperature: dict[datetime, float] = field(default_factory=dict)
    humidity: dict[datetime, float] = field(default_factory=dict)
    co2: dict[datetime, float] = field(default_factory=dict)
    presence: dict[datetime, float] = field(default_factory=dict)
    current_temperature: float | None = None
    current_temperature_at: datetime | None = None
    current_humidity: float | None = None
    current_humidity_at: datetime | None = None
    current_co2: float | None = None
    current_co2_at: datetime | None = None
    current_presence: bool | None = None
    current_presence_at: datetime | None = None


@dataclass
class _Dataset:
    data_source: Literal["mock", "database"]
    rooms: dict[str, _RoomData]
    ambient: dict[datetime, float]
    gas_m3: dict[datetime, float]
    gas_cost: dict[datetime, float]


@dataclass(frozen=True)
class _Period:
    start: datetime
    end: datetime
    start_date: date
    end_date: date
    days: int
    granularity: EnvironmentGranularity


def _floor_hour(value: datetime) -> datetime:
    return value.astimezone(local_tz()).replace(minute=0, second=0, microsecond=0)


def _series_timestamp(key: datetime, now: datetime) -> datetime:
    """End of the statistics hour, capped at ``now`` for the current hour."""
    return min(key + timedelta(hours=1), now)


def _last_value(
    series: dict[datetime, float],
    *,
    max_age: timedelta | None = None,
) -> tuple[float | None, datetime | None]:
    if not series:
        return None, None
    now = local_now()
    key = max(series)
    if max_age is not None and now - key > max_age:
        return None, None
    return series[key], _series_timestamp(key, now)


def _last_valid_value(
    series: dict[datetime, float],
    minimum: float,
    maximum: float,
    *,
    max_age: timedelta | None = None,
) -> tuple[float | None, datetime | None]:
    """Newest credible value, skipping restart zeros and stale readings."""
    now = local_now()
    for key in sorted(series, reverse=True):
        if max_age is not None and now - key > max_age:
            break
        value = series[key]
        if minimum <= value <= maximum:
            return value, _series_timestamp(key, now)
    return None, None


def _current_from_raw(
    latest: dict[str, tuple[str, str | None, datetime]],
    entity: str | None,
    minimum: float,
    maximum: float,
    *,
    max_age: timedelta | None = None,
) -> tuple[float | None, datetime | None]:
    if not entity:
        return None, None
    row = latest.get(entity)
    if row is None:
        return None, None
    state, _attributes, updated_at = row
    updated = ensure_utc(updated_at)
    if max_age is not None and ensure_utc(local_now()) - updated > max_age:
        return None, None
    try:
        value = float(state)
    except (TypeError, ValueError):
        return None, None
    # Written this way round so ``nan`` is rejected too.
    if not minimum <= value <= maximum:
        return None, None
    return value, updated


def _current_presence_from_raw(
    latest: dict[str, tuple[str, str | None, datetime]],
    entity: str | None,
    *,
    max_age: timedelta | None = None,
) -> tuple[bool | None, datetime | None]:
    if not entity:
        return None, None
    row = latest.get(entity)
    if row is None:
        return None, None
    state, _attributes, updated_at = row
    updated = ensure_utc(updated_at)
    if max_age is not None and ensure_utc(local_now()) - updated > max_age:
        return None, None
    value = parse_presence(state)
    return (value, updated) if value is not None else (None, None)


def _filter_series(
    series: dict[datetime, float],
    minimum: float,
    maximum: float,
) -> dict[datetime, float]:
    return {key: value for key, value in series.items() if minimum <= value <= maximum}


def _database_room_data(
    room: EnvironmentRoomConfig, database: EnvironmentDatabaseData
) -> _RoomData:
    temperature = (
        _filter_series(
            database.statistics.get(room.temperature_entity, {}),
            TEMPERATURE_MIN_C,
            TEMPERATURE_MAX_C,
        )
        if room.temperature_entity
        else {}
    )
    humidity = (
        _filter_series(
            database.statistics.get(room.humidity_entity, {}),
            HUMIDITY_MIN_PCT,
            HUMIDITY_MAX_PCT,
        )
        if room.humidity_entity
        else {}
    )
    co2 = (
        _filter_series(
            database.co2.get(room.co2_entity, {}),
            CO2_MIN_PPM,
            CO2_MAX_PPM,
        )
        if room.co2_entity
        else {}
    )
    if room.presence_statistic_id:
        presence = _filter_series(
            database.statistics.get(room.presence_statistic_id, {}), 0.0, 1.0
        )
    else:
        presence = (
            _filter_series(database.presence.get(room.presence_entity, {}), 0.0, 1.0)
            if room.presence_entity
            else {}
        )

    # Temperature/humidity: the hourly statistic is more stable than the last raw
    # row, which can be a 0 written while Home Assistant restarts.
    current_temperature, temperature_at = _last_valid_value(
        temperature,
        TEMPERATURE_MIN_C,
        TEMPERATURE_MAX_C,
        max_age=_ONE_DAY,
    )
    current_humidity, humidity_at = _last_valid_value(
        humidity,
        HUMIDITY_MIN_PCT,
        HUMIDITY_MAX_PCT,
        max_age=_ONE_DAY,
    )
    if current_temperature is None and room.temperature_entity:
        current_temperature, temperature_at = _current_from_raw(
            database.latest,
            room.temperature_entity,
            TEMPERATURE_MIN_C,
            TEMPERATURE_MAX_C,
            max_age=_ONE_DAY,
        )
    if current_humidity is None and room.humidity_entity:
        current_humidity, humidity_at = _current_from_raw(
            database.latest,
            room.humidity_entity,
            HUMIDITY_MIN_PCT,
            HUMIDITY_MAX_PCT,
            max_age=_ONE_DAY,
        )

    # CO₂ has no statistics. Keep the last valid raw value for a day so an
    # overnight sensor reset does not blank the cards.
    current_co2, co2_at = _current_from_raw(
        database.latest,
        room.co2_entity,
        CO2_MIN_PPM,
        CO2_MAX_PPM,
        max_age=_ONE_DAY,
    )
    if current_co2 is None:
        current_co2, co2_at = _last_valid_value(
            co2, CO2_MIN_PPM, CO2_MAX_PPM, max_age=_ONE_DAY
        )

    current_presence, presence_at = _current_presence_from_raw(
        database.latest, room.presence_entity, max_age=_ONE_DAY
    )
    if current_presence is None and presence:
        last_presence, presence_at = _last_value(presence, max_age=_ONE_DAY)
        if last_presence is not None:
            current_presence = last_presence >= 0.5

    return _RoomData(
        temperature=temperature,
        humidity=humidity,
        co2=co2,
        presence=presence,
        current_temperature=current_temperature,
        current_temperature_at=temperature_at,
        current_humidity=current_humidity,
        current_humidity_at=humidity_at,
        current_co2=current_co2,
        current_co2_at=co2_at,
        current_presence=current_presence,
        current_presence_at=presence_at,
    )


def _mock_room_data(
    room: EnvironmentRoomConfig, start: datetime, end: datetime
) -> _RoomData:
    temperature: dict[datetime, float] = {}
    humidity: dict[datetime, float] = {}
    co2: dict[datetime, float] = {}
    presence: dict[datetime, float] = {}

    cursor = _floor_hour(start)
    limit = min(end, _floor_hour(local_now()) + timedelta(hours=1))
    while cursor < limit:
        ratio = mock_data.environment_presence_ratio(room.id, cursor)
        if room.temperature_entity:
            temperature[cursor] = mock_data.environment_temperature(room.id, cursor)
        if room.humidity_entity:
            humidity[cursor] = mock_data.environment_humidity(room.id, cursor)
        if room.co2_entity:
            co2[cursor] = mock_data.environment_co2(room.id, cursor)
        if room.presence_entity:
            presence[cursor] = ratio
        cursor += timedelta(hours=1)

    now = local_now()
    current_temperature = (
        mock_data.environment_temperature(room.id, now) if room.temperature_entity else None
    )
    current_humidity = (
        mock_data.environment_humidity(room.id, now) if room.humidity_entity else None
    )
    current_co2 = mock_data.environment_co2(room.id, now) if room.co2_entity else None
    current_presence = (
        mock_data.environment_presence(room.id, now) if room.presence_entity else None
    )
    current_at = now if room.presence_entity else None

    return _RoomData(
        temperature=temperature,
        humidity=humidity,
        co2=co2,
        presence=presence,
        current_temperature=current_temperature,
        current_temperature_at=now if current_temperature is not None else None,
        current_humidity=current_humidity,
        current_humidity_at=now if current_humidity is not None else None,
        current_co2=current_co2,
        current_co2_at=now if current_co2 is not None else None,
        current_presence=current_presence,
        current_presence_at=current_at,
    )


def _hourly_increments(rows: list[tuple[datetime, float]]) -> dict[datetime, float]:
    """Turn cumulative meter sums into non-negative local-hour increments.

    A drop in the long-term ``sum`` is a recorder correction, not consumption:
    it is ignored, because taking the new total as the increment would add the
    whole history of the meter to a single hour.
    """
    increments: dict[datetime, float] = defaultdict(float)
    for (_previous_at, previous), (current_at, current) in pairwise(sorted(rows)):
        delta = current - previous
        if delta <= 0:
            continue
        key = current_at.astimezone(local_tz()).replace(
            minute=0, second=0, microsecond=0
        )
        increments[key] += delta
    return dict(increments)


def _mock_dataset(period: _Period) -> _Dataset:
    rooms = {
        room.id: _mock_room_data(room, period.start, period.end)
        for room in ENVIRONMENT_ROOMS
    }
    ambient: dict[datetime, float] = {}
    gas_m3: dict[datetime, float] = {}
    gas_cost: dict[datetime, float] = {}
    cursor = _floor_hour(period.start)
    while cursor < period.end:
        ambient[cursor] = mock_data.environment_ambient_temperature(cursor)
        gas_m3[cursor] = mock_data.environment_gas_m3(cursor)
        gas_cost[cursor] = mock_data.environment_gas_cost(cursor)
        cursor += timedelta(hours=1)
    return _Dataset(
        data_source="mock",
        rooms=rooms,
        ambient=ambient,
        gas_m3=gas_m3,
        gas_cost=gas_cost,
    )


async def _database_dataset(period: _Period) -> _Dataset:
    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import environment_data

    database = await environment_data.load_environment_data(period.start, period.end)
    rooms = {
        room.id: _database_room_data(room, database) for room in ENVIRONMENT_ROOMS
    }
    ambient = _filter_series(
        database.statistics.get(AMBIENT_TEMPERATURE_ENTITY, {}),
        TEMPERATURE_MIN_C,
        TEMPERATURE_MAX_C,
    )
    return _Dataset(
        data_source="database",
        rooms=rooms,
        ambient=ambient,
        gas_m3=_hourly_increments(database.gas_sums.get(GAS_M3_ENTITY, [])),
        gas_cost=_hourly_increments(database.gas_sums.get(GAS_COST_ENTITY, [])),
    )


async def _load_dataset(period: _Period) -> _Dataset:
    # Periods ending today use the current instant as the upper bound. Round
    # that bound down to the hour so the cache key is stable between requests;
    # otherwise the moving microseconds would make every request a cache miss.
    cache_end = period.end.replace(minute=0, second=0, microsecond=0)
    key = ("environment-dataset", period.start.isoformat(), cache_end.isoformat())
    hit = _cache.get(key)
    if hit is not None:
        return hit
    if settings.DATA_SOURCE == "database":
        value = await _database_dataset(period)
    else:
        value = _mock_dataset(period)
    _cache.set(key, value)
    return value


def resolve_period(
    start: date | None = None,
    end: date | None = None,
) -> _Period:
    """Validate the custom date inputs and return local, inclusive bounds."""
    validate_query_dates(*(value for value in (start, end) if value is not None))
    today = local_now().date()
    end_date = end or today
    start_date = start or (end_date - timedelta(days=DEFAULT_ENVIRONMENT_DAYS - 1))

    if start_date > end_date:
        raise ValueError("La fecha inicial no puede ser posterior a la final.")
    if end_date > today:
        raise ValueError("La fecha final no puede ser futura.")

    days = (end_date - start_date).days + 1
    if days > MAX_ENVIRONMENT_DAYS:
        raise ValueError("El periodo máximo es de un año (366 días).")

    start_local = datetime.combine(start_date, time.min, tzinfo=local_tz())
    end_local = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=local_tz())
    if end_date == today:
        end_local = min(end_local, local_now())
    if end_local <= start_local:
        end_local = start_local + timedelta(hours=1)

    if days <= 7:
        granularity: EnvironmentGranularity = "hour"
    elif days <= 120:
        granularity = "day"
    else:
        granularity = "week"

    return _Period(
        start=start_local,
        end=end_local,
        start_date=start_date,
        end_date=end_date,
        days=days,
        granularity=granularity,
    )


def _build_buckets(period: _Period) -> list[Bucket]:
    buckets: list[Bucket] = []
    if period.granularity == "hour":
        step = timedelta(hours=1)
    elif period.granularity == "day":
        step = timedelta(days=1)
    else:
        step = timedelta(days=7)

    cursor = period.start
    while cursor < period.end:
        bucket_end = min(cursor + step, period.end)
        buckets.append(Bucket(cursor, bucket_end))
        cursor = bucket_end
    return buckets


def _bucket_mean(
    series: dict[datetime, float], bucket: Bucket
) -> float | None:
    values = [
        value for key, value in series.items() if bucket.start <= key < bucket.end
    ]
    return sum(values) / len(values) if values else None


def _bucket_sum(series: dict[datetime, float], bucket: Bucket) -> float | None:
    values = [
        value for key, value in series.items() if bucket.start <= key < bucket.end
    ]
    return sum(values) if values else None


def _values_in(
    series: dict[datetime, float], start: datetime, end: datetime
) -> list[float]:
    return [value for key, value in series.items() if start <= key < end]


def _round(value: float | None, digits: int = 1) -> float | None:
    return round(value, digits) if value is not None else None


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _percent(count: int, total: int) -> float | None:
    return count / total * 100.0 if total else None


def _build_summary(
    room: EnvironmentRoomConfig, data: _RoomData, period: _Period
) -> EnvironmentRoomSummary:
    temperatures = _values_in(data.temperature, period.start, period.end)
    humidities = _values_in(data.humidity, period.start, period.end)
    co2_values = _values_in(data.co2, period.start, period.end)
    presence_values = _values_in(data.presence, period.start, period.end)

    occupied_hours = sum(presence_values) if presence_values else None
    empty_hours = (
        sum(1.0 - value for value in presence_values) if presence_values else None
    )
    occupied_total = (occupied_hours or 0.0) + (empty_hours or 0.0)
    occupancy_pct = (
        occupied_hours / occupied_total * 100.0
        if occupied_hours is not None and occupied_total > 0
        else None
    )

    # Comfort is temperature + humidity; CO₂ is reported separately as air
    # quality. Only hours with the needed values count.
    comfort_total = 0
    comfort_good = 0
    for key in set(data.temperature) & set(data.humidity):
        if not (period.start <= key < period.end):
            continue
        comfort_total += 1
        if (
            TEMPERATURE_MIN_C <= data.temperature[key] <= TEMPERATURE_MAX_C
            and HUMIDITY_MIN_PCT <= data.humidity[key] <= HUMIDITY_MAX_PCT
            and temperature_status(data.temperature[key]) == "good"
            and humidity_status(data.humidity[key]) == "good"
        ):
            comfort_good += 1

    statuses: list[EnvironmentQuality] = [
        temperature_status(data.current_temperature),
        humidity_status(data.current_humidity),
        co2_status(data.current_co2),
    ]
    environmental_updates = [
        value
        for value in (
            data.current_temperature_at,
            data.current_humidity_at,
            data.current_co2_at,
        )
        if value is not None
    ]
    updated_values = environmental_updates or (
        [data.current_presence_at] if data.current_presence_at is not None else []
    )

    peak_co2 = max(co2_values) if co2_values else None
    peak_co2_at = None
    if peak_co2 is not None:
        for key in sorted(data.co2):
            if period.start <= key < period.end and data.co2[key] == peak_co2:
                peak_co2_at = ensure_utc(key)
                break

    return EnvironmentRoomSummary(
        room_id=room.id,
        label=room.label,
        building_id=room.building_id,
        building_label=building_label(room.building_id),
        kind=room.kind,
        has_temperature=room.temperature_entity is not None,
        has_humidity=room.humidity_entity is not None,
        has_co2=room.co2_entity is not None,
        has_presence=room.presence_entity is not None,
        current_temperature_c=_round(data.current_temperature),
        temperature_updated_at=data.current_temperature_at,
        current_humidity_pct=_round(data.current_humidity),
        humidity_updated_at=data.current_humidity_at,
        current_co2_ppm=_round(data.current_co2, 0),
        co2_updated_at=data.current_co2_at,
        current_presence=data.current_presence,
        presence_updated_at=data.current_presence_at,
        last_updated=max(updated_values) if updated_values else None,
        temperature_status=temperature_status(data.current_temperature),
        humidity_status=humidity_status(data.current_humidity),
        co2_status=co2_status(data.current_co2),
        comfort_status=worst_status(*statuses),
        avg_temperature_c=_round(_mean(temperatures)),
        min_temperature_c=_round(min(temperatures) if temperatures else None),
        max_temperature_c=_round(max(temperatures) if temperatures else None),
        avg_humidity_pct=_round(_mean(humidities)),
        min_humidity_pct=_round(min(humidities) if humidities else None),
        max_humidity_pct=_round(max(humidities) if humidities else None),
        avg_co2_ppm=_round(_mean(co2_values), 0),
        peak_co2_ppm=_round(peak_co2, 0),
        peak_co2_at=peak_co2_at,
        co2_above_800_pct=_round(
            _percent(sum(1 for value in co2_values if value > 800), len(co2_values)),
            0,
        ),
        co2_above_1000_pct=_round(
            _percent(sum(1 for value in co2_values if value > 1000), len(co2_values)),
            0,
        ),
        occupancy_pct=_round(occupancy_pct, 0),
        occupied_hours=_round(occupied_hours),
        empty_hours=_round(empty_hours),
        comfort_good_pct=_round(_percent(comfort_good, comfort_total), 0),
    )


def _summary(rooms: list[EnvironmentRoomSummary]) -> EnvironmentSummary:
    temperatures = [room.avg_temperature_c for room in rooms if room.avg_temperature_c is not None]
    humidities = [room.avg_humidity_pct for room in rooms if room.avg_humidity_pct is not None]
    co2_values = [room.avg_co2_ppm for room in rooms if room.avg_co2_ppm is not None]
    co2_alerts = [room.current_co2_ppm for room in rooms if room.current_co2_ppm is not None]
    occupancy = [room.occupancy_pct for room in rooms if room.occupancy_pct is not None]

    return EnvironmentSummary(
        rooms_total=len(rooms),
        occupied_now=sum(1 for room in rooms if room.current_presence is True),
        rooms_with_presence=sum(1 for room in rooms if room.has_presence),
        rooms_with_climate=sum(
            1 for room in rooms if room.has_temperature or room.has_humidity or room.has_co2
        ),
        rooms_with_co2=sum(1 for room in rooms if room.has_co2),
        avg_temperature_c=_round(_mean(temperatures)),
        avg_humidity_pct=_round(_mean(humidities)),
        avg_co2_ppm=_round(_mean(co2_values), 0),
        co2_alert_rooms=sum(1 for value in co2_alerts if value is not None and value > 800),
        comfort_good_rooms=sum(1 for room in rooms if room.comfort_status == "good"),
        occupancy_pct=_round(_mean(occupancy), 0),
    )


def _build_benchmark(
    rooms: list[EnvironmentRoomSummary], excluded_room_id: str
) -> EnvironmentBenchmark:
    # Compare the selected room with the *other* rooms, not with itself.
    comparison = [room for room in rooms if room.room_id != excluded_room_id]
    temperatures = [
        room.avg_temperature_c
        for room in comparison
        if room.avg_temperature_c is not None
    ]
    humidities = [
        room.avg_humidity_pct
        for room in comparison
        if room.avg_humidity_pct is not None
    ]
    co2_values = [
        room.avg_co2_ppm for room in comparison if room.avg_co2_ppm is not None
    ]
    occupancy = [
        room.occupancy_pct for room in comparison if room.occupancy_pct is not None
    ]
    return EnvironmentBenchmark(
        avg_temperature_c=_round(_mean(temperatures)),
        avg_humidity_pct=_round(_mean(humidities)),
        avg_co2_ppm=_round(_mean(co2_values), 0),
        occupancy_pct=_round(_mean(occupancy), 0),
        rooms_temperature=sum(
            1 for room in comparison if room.avg_temperature_c is not None
        ),
        rooms_humidity=sum(
            1 for room in comparison if room.avg_humidity_pct is not None
        ),
        rooms_co2=sum(1 for room in comparison if room.avg_co2_ppm is not None),
        rooms_presence=sum(1 for room in comparison if room.occupancy_pct is not None),
    )


def _build_series(
    data: _RoomData, dataset: _Dataset, period: _Period
) -> list[EnvironmentSeriesPoint]:
    points: list[EnvironmentSeriesPoint] = []
    for bucket in _build_buckets(period):
        presence = _bucket_mean(data.presence, bucket)
        points.append(
            EnvironmentSeriesPoint(
                timestamp=ensure_utc(bucket.start),
                temperature_c=_round(_bucket_mean(data.temperature, bucket)),
                humidity_pct=_round(_bucket_mean(data.humidity, bucket)),
                co2_ppm=_round(_bucket_mean(data.co2, bucket), 0),
                presence_pct=_round(
                    presence * 100.0 if presence is not None else None,
                    0,
                ),
                ambient_temperature_c=_round(_bucket_mean(dataset.ambient, bucket)),
                gas_m3=_round(_bucket_sum(dataset.gas_m3, bucket), 1),
                gas_cost_eur=_round(_bucket_sum(dataset.gas_cost, bucket), 2),
            )
        )
    return points


def _build_heatmap(data: _RoomData, period: _Period) -> list[EnvironmentHeatmapCell]:
    presence: dict[tuple[int, int], list[float]] = defaultdict(list)
    co2: dict[tuple[int, int], list[float]] = defaultdict(list)
    for key, value in data.presence.items():
        if period.start <= key < period.end:
            presence[(key.weekday(), key.hour)].append(value * 100.0)
    for key, value in data.co2.items():
        if period.start <= key < period.end:
            co2[(key.weekday(), key.hour)].append(value)
    return [
        EnvironmentHeatmapCell(
            weekday=weekday,
            hour=hour,
            presence_pct=_round(_mean(presence.get((weekday, hour), [])), 0),
            co2_ppm=_round(_mean(co2.get((weekday, hour), [])), 0),
        )
        for weekday in range(7)
        for hour in range(24)
    ]


def _correlation(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 3:
        return None
    xs = [pair[0] for pair in pairs]
    ys = [pair[1] for pair in pairs]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denominator = (
        sum((x - mean_x) ** 2 for x in xs) ** 0.5
        * sum((y - mean_y) ** 2 for y in ys) ** 0.5
    )
    return numerator / denominator if denominator else None


def _build_co2_occupancy(data: _RoomData, period: _Period) -> EnvironmentCo2Occupancy:
    pairs: list[tuple[float, float]] = []
    occupied: list[float] = []
    empty: list[float] = []
    for key in set(data.presence) & set(data.co2):
        if not (period.start <= key < period.end):
            continue
        presence = data.presence[key]
        co2 = data.co2[key]
        pairs.append((presence, co2))
        if presence >= 0.5:
            occupied.append(co2)
        elif presence <= 0.05:
            empty.append(co2)
    occupied_mean = _mean(occupied)
    empty_mean = _mean(empty)
    lift = (
        (occupied_mean - empty_mean) / empty_mean * 100.0
        if occupied_mean is not None and empty_mean is not None and empty_mean > 0
        else None
    )
    return EnvironmentCo2Occupancy(
        occupied_co2_ppm=_round(occupied_mean, 0),
        empty_co2_ppm=_round(empty_mean, 0),
        lift_pct=_round(lift, 0),
        correlation=_round(_correlation(pairs), 2),
        occupied_hours=_round(sum(value for value in data.presence.values() if value >= 0.5)),
        empty_hours=_round(sum(1.0 - value for value in data.presence.values() if value <= 0.05)),
    )


def _build_thermal_recovery(data: _RoomData, period: _Period) -> EnvironmentThermalRecovery:
    if not data.temperature or not data.presence:
        return EnvironmentThermalRecovery()

    keys = sorted(
        key
        for key in set(data.temperature) & set(data.presence)
        if period.start <= key < period.end
    )
    empty_by_date: dict[date, list[float]] = defaultdict(list)
    for key in keys:
        if data.presence[key] <= 0.05:
            empty_by_date[key.date()].append(data.temperature[key])
    all_empty = [value for values in empty_by_date.values() for value in values]
    overall_baseline = _median(all_empty)
    if overall_baseline is None:
        return EnvironmentThermalRecovery()

    recoveries: list[float] = []
    changes: list[float] = []
    no_recovery = 0
    for index in range(len(keys) - 1):
        key = keys[index]
        next_key = keys[index + 1]
        if next_key - key != timedelta(hours=1):
            continue
        if data.presence[key] < 0.5 or data.presence[next_key] > 0.05:
            continue
        day_baseline = _median(empty_by_date.get(next_key.date(), []))
        baseline = day_baseline if day_baseline is not None else overall_baseline
        start_temperature = data.temperature[next_key]
        if abs(start_temperature - baseline) < 0.5:
            continue
        recovery: float | None = None
        for hours in range(1, 7):
            probe = next_key + timedelta(hours=hours)
            if probe in data.temperature and abs(data.temperature[probe] - baseline) <= 0.5:
                recovery = float(hours)
                break
        if recovery is None:
            no_recovery += 1
            recovery = 6.0
        recoveries.append(recovery)
        next_temperature = data.temperature.get(next_key + timedelta(hours=1))
        if next_temperature is not None:
            changes.append(next_temperature - start_temperature)

    return EnvironmentThermalRecovery(
        baseline_temperature_c=_round(overall_baseline),
        transitions=len(recoveries),
        median_recovery_hours=_round(_median(recoveries), 1),
        median_change_per_hour_c=_round(_median(changes), 1),
        no_recovery_count=no_recovery,
    )


def _build_context(
    room_data: _RoomData, dataset: _Dataset, period: _Period
) -> EnvironmentContext:
    ambient_values = _values_in(dataset.ambient, period.start, period.end)
    current_ambient, ambient_at = _last_valid_value(
        dataset.ambient,
        TEMPERATURE_MIN_C,
        TEMPERATURE_MAX_C,
        max_age=_ONE_DAY,
    )
    differences = [
        room_data.temperature[key] - dataset.ambient[key]
        for key in set(room_data.temperature) & set(dataset.ambient)
        if period.start <= key < period.end
    ]
    gas_m3 = _bucket_sum(dataset.gas_m3, Bucket(period.start, period.end))
    gas_cost = _bucket_sum(dataset.gas_cost, Bucket(period.start, period.end))
    gas_days = max((period.end - period.start).total_seconds() / 86400.0, 1e-9)
    return EnvironmentContext(
        current_ambient_temperature_c=_round(current_ambient),
        ambient_updated_at=ambient_at,
        avg_ambient_temperature_c=_round(_mean(ambient_values)),
        avg_indoor_minus_ambient_c=_round(_mean(differences)),
        gas_m3=_round(gas_m3, 1),
        gas_cost_eur=_round(gas_cost, 2),
        gas_cost_per_day_eur=_round(gas_cost / gas_days if gas_cost is not None else None, 2),
        gas_days=_round(gas_days, 1),
        has_gas=gas_m3 is not None or gas_cost is not None,
    )


def _notes(data_source: Literal["mock", "database"]) -> list[str]:
    notes = [
        "Solo se muestran estancias con sensores identificados. Los laboratorios y los sensores Shelly genéricos se excluyen mientras no exista un mapa fiable de sala.",
        "CO₂ en ppm. Umbrales orientativos: 600 ppm bueno, 800 ppm moderado y 1.000 ppm alto.",
        "La temperatura ambiente de referencia procede de sensor.ambiente, sin una sala confirmada. El gas es del edificio y puede incluir usos distintos de la calefacción.",
    ]
    if data_source == "mock":
        notes.insert(0, "Datos simulados: el backend está en modo mock.")
    else:
        notes.insert(0, "Datos reales del recorder de Home Assistant (solo lectura).")
    return notes


async def build_overview(
    start: date | None = None,
    end: date | None = None,
) -> EnvironmentOverviewResponse:
    period = resolve_period(start, end)
    dataset = await _load_dataset(period)
    rooms = [
        _build_summary(room, dataset.rooms[room.id], period)
        for room in ENVIRONMENT_ROOMS
    ]
    return EnvironmentOverviewResponse(
        start=ensure_utc(period.start),
        end=ensure_utc(period.end),
        granularity=period.granularity,
        generated_at=ensure_utc(local_now()),
        rooms=rooms,
        summary=_summary(rooms),
        data_source=dataset.data_source,
        notes=_notes(dataset.data_source),
    )


async def build_room_detail(
    room_id: str,
    start: date | None = None,
    end: date | None = None,
) -> EnvironmentRoomDetailResponse:
    room = ENVIRONMENT_ROOMS_BY_ID.get(room_id)
    if room is None:
        raise KeyError(room_id)
    period = resolve_period(start, end)
    dataset = await _load_dataset(period)
    summaries = [
        _build_summary(candidate, dataset.rooms[candidate.id], period)
        for candidate in ENVIRONMENT_ROOMS
    ]
    summary = next(item for item in summaries if item.room_id == room_id)
    data = dataset.rooms[room_id]
    series = _build_series(data, dataset, period)

    return EnvironmentRoomDetailResponse(
        start=ensure_utc(period.start),
        end=ensure_utc(period.end),
        granularity=period.granularity,
        generated_at=ensure_utc(local_now()),
        room=summary,
        benchmark=_build_benchmark(summaries, room_id),
        context=_build_context(data, dataset, period),
        series=series,
        heatmap=_build_heatmap(data, period),
        co2_occupancy=_build_co2_occupancy(data, period),
        thermal_recovery=_build_thermal_recovery(data, period),
        data_source=dataset.data_source,
        notes=_notes(dataset.data_source),
    )


def clear_cache() -> None:
    _cache.clear()
