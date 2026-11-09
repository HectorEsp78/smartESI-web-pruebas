"""Current level and history of the battery sensors in the Maintenance tab."""

from __future__ import annotations

import zlib
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from app.core.battery_map import (
    BATTERY_GROUPS,
    CURRENT_READING_MAX_HOURS,
    DEFAULT_HISTORY_DAYS,
    HISTORY_GAP_HOURS,
    HOURLY_HISTORY_MAX_DAYS,
    BatteryGroup,
    BatterySensor,
)
from app.core.cache import TTLCache
from app.core.clock import (
    elapsed_hours,
    ensure_utc,
    local_hour_from_epoch,
    local_now,
    local_tz,
    to_utc_naive,
    utc_now,
    validate_query_dates,
)
from app.core.config import settings
from app.core.maintenance_map import (
    BATTERY_CRITICAL_MV,
    BATTERY_CRITICAL_PCT,
    BATTERY_LOW_MV,
    BATTERY_LOW_PCT,
    BATTERY_MEDIUM_MV,
    BATTERY_MEDIUM_PCT,
)
from app.schemas.battery import (
    BatteryGroupResponse,
    BatteryGroupSummary,
    BatteryHistoryPoint,
    BatteryHistoryResponse,
    BatteryLevel,
    BatterySensorStatus,
    DataSource,
    HistoryGranularity,
)
from app.services.maintenance_service import estimate_pct_from_mv

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS, max_entries=64)


def _data_source() -> DataSource:
    return "database" if settings.DATA_SOURCE == "database" else "mock"


def _thresholds(group: BatteryGroup) -> tuple[float, float, float]:
    """``(critical, low, medium)`` upper limits, in the unit of the group."""
    if group.unit == "millivolt":
        return BATTERY_CRITICAL_MV, BATTERY_LOW_MV, BATTERY_MEDIUM_MV
    return BATTERY_CRITICAL_PCT, BATTERY_LOW_PCT, BATTERY_MEDIUM_PCT


def classify_level(group: BatteryGroup, value: float) -> BatteryLevel:
    critical, low, medium = _thresholds(group)
    if value <= critical:
        return "critical"
    if value <= low:
        return "low"
    if value <= medium:
        return "medium"
    return "ok"


def _estimated_pct(group: BatteryGroup, value: float) -> float | None:
    if group.unit != "millivolt":
        return None
    return round(estimate_pct_from_mv(value))


def build_sensor_status(
    group: BatteryGroup,
    sensor: BatterySensor,
    value: float | None,
    reading_at: datetime | None,
    last_row_is_valid: bool,
    now_utc: datetime,
) -> BatterySensorStatus:
    """Status of a sensor from its last valid reading (times in naive UTC)."""
    age_hours = (
        elapsed_hours(ensure_utc(reading_at), ensure_utc(now_utc))
        if reading_at is not None
        else None
    )
    is_current = (
        value is not None
        and last_row_is_valid
        and age_hours is not None
        and age_hours <= CURRENT_READING_MAX_HOURS
    )
    return BatterySensorStatus(
        id=sensor.id,
        label=sensor.label,
        entity_id=sensor.entity_id,
        unit=group.unit,
        value=round(value) if value is not None else None,
        estimated_pct=_estimated_pct(group, value) if value is not None else None,
        level=classify_level(group, value) if value is not None and is_current else "unknown",
        reading_at=ensure_utc(reading_at) if reading_at is not None else None,
        age_hours=round(age_hours, 1) if age_hours is not None else None,
        is_current=is_current,
    )


# --- Mock data -----------------------------------------------------------------


def _rand(*parts: object) -> float:
    return zlib.crc32("|".join(str(part) for part in parts).encode()) / 0x100000000


def _mock_level(group: BatteryGroup, sensor: BatterySensor) -> float:
    low, high = (3100.0, 3660.0) if group.unit == "millivolt" else (8.0, 100.0)
    return low + _rand("level", sensor.id) * (high - low)


def _mock_statuses(group: BatteryGroup, now_utc: datetime) -> list[BatterySensorStatus]:
    statuses = []
    for sensor in group.sensors:
        # Like the real valves: no current reading, only an old value.
        stale = group.id == "valvulas"
        age = timedelta(days=30 + 200 * _rand("age", sensor.id) if stale else 0.5)
        statuses.append(
            build_sensor_status(
                group, sensor, _mock_level(group, sensor), now_utc - age, not stale, now_utc
            )
        )
    return statuses


def _mock_hourly_means(
    group: BatteryGroup, sensor: BatterySensor, start_utc: datetime, end_utc: datetime
) -> list[tuple[int, float]]:
    low, high = group.valid_range
    level = _mock_level(group, sensor)
    slope = 0.02 if group.unit == "percent" else 0.1  # per hour, looking back
    means: list[tuple[int, float]] = []
    cursor = start_utc.replace(minute=0, second=0, microsecond=0)
    while cursor < end_utc:
        hours_back = (end_utc - cursor).total_seconds() / 3600.0
        if _rand(sensor.id, cursor.date()) > 0.05:  # some days without readings
            value = min(high, max(low, level + slope * hours_back))
            means.append((int(ensure_utc(cursor).timestamp()), value))
        cursor += timedelta(hours=6)
    return means


# --- Group page ----------------------------------------------------------------


def _group(group_id: str) -> BatteryGroup:
    group = BATTERY_GROUPS.get(group_id)
    if group is None:
        raise KeyError(group_id)
    return group


def _sensor(group: BatteryGroup, sensor_id: str) -> BatterySensor:
    for sensor in group.sensors:
        if sensor.id == sensor_id:
            return sensor
    raise KeyError(sensor_id)


async def _load_statuses(group: BatteryGroup, now_utc: datetime) -> list[BatterySensorStatus]:
    if settings.DATA_SOURCE != "database":
        return _mock_statuses(group, now_utc)

    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import battery_data

    rows = await battery_data.load_latest_readings(group, now_utc)
    statuses = []
    for sensor in group.sensors:
        row = rows[sensor.entity_id]
        statuses.append(
            build_sensor_status(
                group,
                sensor,
                row.valid_value,
                row.valid_at,
                row.valid_at is not None and row.valid_at == row.last_row_at,
                now_utc,
            )
        )
    return statuses


async def build_group(group_id: str) -> BatteryGroupResponse:
    group = _group(group_id)
    key = ("group", group_id)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    sensors = await _load_statuses(group, utc_now())
    response = BatteryGroupResponse(
        group=group.id,
        label=group.label,
        unit=group.unit,
        generated_at=ensure_utc(utc_now()),
        summary=BatteryGroupSummary(
            total=len(sensors),
            low=sum(sensor.level == "low" for sensor in sensors),
            critical=sum(sensor.level == "critical" for sensor in sensors),
            without_current_reading=sum(not sensor.is_current for sensor in sensors),
        ),
        sensors=sensors,
        data_source=_data_source(),
    )
    _cache.set(key, response)
    return response


# --- History -------------------------------------------------------------------


def resolve_history_period(
    start: date | None = None, end: date | None = None
) -> tuple[datetime, datetime, HistoryGranularity]:
    """Validate the dates and return local bounds and the granularity to use."""
    validate_query_dates(*(value for value in (start, end) if value is not None))
    now = local_now()
    end_date = end or now.date()
    start_date = start or (end_date - timedelta(days=DEFAULT_HISTORY_DAYS - 1))

    if start_date > end_date:
        raise ValueError("La fecha inicial no puede ser posterior a la final.")
    if end_date > now.date():
        raise ValueError("La fecha final no puede ser futura.")

    days = (end_date - start_date).days + 1
    start_local = datetime.combine(start_date, time.min, tzinfo=local_tz())
    end_local = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=local_tz())
    granularity: HistoryGranularity = "hour" if days <= HOURLY_HISTORY_MAX_DAYS else "day"
    return start_local, min(end_local, now), granularity


def build_history_points(
    group: BatteryGroup,
    hourly: list[tuple[int, float]],
    granularity: HistoryGranularity,
) -> list[BatteryHistoryPoint]:
    """Aggregate hourly means, marking long silences as gaps."""
    samples: list[tuple[datetime, float]]
    if granularity == "hour":
        samples = [(local_hour_from_epoch(epoch), value) for epoch, value in hourly]
    else:
        by_day: dict[datetime, list[float]] = defaultdict(list)
        for epoch, value in hourly:
            moment = local_hour_from_epoch(epoch)
            day = datetime.combine(moment.date(), time.min, tzinfo=local_tz())
            by_day[day].append(value)
        samples = [(day, sum(values) / len(values)) for day, values in sorted(by_day.items())]

    points: list[BatteryHistoryPoint] = []
    previous: datetime | None = None
    for moment, value in samples:
        if previous is not None and elapsed_hours(previous, moment) > HISTORY_GAP_HOURS:
            gap_at = previous + (moment - previous) / 2
            points.append(BatteryHistoryPoint(timestamp=gap_at, value=None, estimated_pct=None))
        points.append(
            BatteryHistoryPoint(
                timestamp=moment,
                value=round(value, 1),
                estimated_pct=_estimated_pct(group, value),
            )
        )
        previous = moment
    return points


async def build_history(
    group_id: str,
    sensor_id: str,
    start: date | None = None,
    end: date | None = None,
) -> BatteryHistoryResponse:
    group = _group(group_id)
    sensor = _sensor(group, sensor_id)
    start_local, end_local, granularity = resolve_history_period(start, end)

    key = ("history", group_id, sensor_id, start_local.date(), end_local.date())
    cached = _cache.get(key)
    if cached is not None:
        return cached

    start_utc, end_utc = to_utc_naive(start_local), to_utc_naive(end_local)
    if settings.DATA_SOURCE == "database":
        from app.db import battery_data

        hourly = await battery_data.load_hourly_means(group, sensor, start_utc, end_utc)
    else:
        hourly = _mock_hourly_means(group, sensor, start_utc, end_utc)

    points = build_history_points(group, hourly, granularity)
    values = [point.value for point in points if point.value is not None]
    critical, low, _medium = _thresholds(group)
    response = BatteryHistoryResponse(
        group=group.id,
        sensor_id=sensor.id,
        label=sensor.label,
        unit=group.unit,
        start=start_local,
        end=end_local,
        granularity=granularity,
        low_threshold=low,
        critical_threshold=critical,
        min_value=min(values, default=None),
        max_value=max(values, default=None),
        points=points,
        data_source=_data_source(),
    )
    _cache.set(key, response)
    return response


def clear_cache() -> None:
    _cache.clear()
