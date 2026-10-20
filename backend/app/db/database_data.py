"""Loads real Home Assistant data as hourly series keyed by *local* hour.

The services aggregate by local buckets (hour/day/month, Europe/Madrid). To keep
that code unchanged, this module fetches the raw rows once per window and turns
them into ``{local_hour: value}`` dictionaries the services can look up directly.

Nothing here writes to the database: it only reads through ``app.db.repository``.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import local_tz
from app.core.config import settings
from app.core.energy_map import BUILDINGS_BY_ID
from app.db import repository
from app.db.entity_map import (
    BUILDING_ENERGY_STATISTIC,
    BUILDING_OCCUPANCY_COUNTERS,
    OUTDOOR_TEMPERATURE_ENTITY,
    SITE_ENERGY_KEY,
    SITE_ENERGY_STATISTIC,
    SITE_GAS_STATISTIC,
    SPACE_CO2_ENTITY,
    SPACE_HUMIDITY_ENTITY,
    SPACE_TEMPERATURE_ENTITY,
    OccupancyCounter,
)

_HOUR_SECONDS = 3600
# How far back to look for the last known value before a window (fill-forward seed).
_BASELINE_LOOKBACK = timedelta(days=3)


def _to_utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _floor_epoch(value_utc_naive: datetime) -> int:
    seconds = int(value_utc_naive.replace(tzinfo=timezone.utc).timestamp())
    return seconds // _HOUR_SECONDS * _HOUR_SECONDS


def _local_hour_from_epoch(epoch_seconds: int) -> datetime:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).astimezone(local_tz()).replace(
        minute=0, second=0, microsecond=0
    )


def parse_counter_value(
    state: str | None,
    attributes: str | None,
    attribute: str | None = None,
) -> float | None:
    """Numeric value of a counter stored in ``state`` or in a JSON attribute.

    Returns ``None`` for ``unavailable``/``unknown`` states, missing attributes
    and non-numeric values, so a broken counter cannot be mistaken for 0.
    """
    raw: object
    if attribute is None:
        raw = state
    else:
        try:
            parsed = json.loads(attributes) if isinstance(attributes, str) else attributes
        except (TypeError, ValueError):
            return None
        if not isinstance(parsed, dict):
            return None
        raw = parsed.get(attribute)

    try:
        return float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def net_occupancy(entrance: float | None, exit_: float | None, capacity: int) -> int | None:
    """People inside between two cumulative daily counters.

    The counters reset at midnight, so their difference is the current
    occupancy. A negative difference (a reset in progress or a lost reading) is
    clamped to 0, and a difference above the building capacity is capped so a
    corrupted counter cannot inflate the chart.
    """
    if entrance is None or exit_ is None:
        return None
    return max(0, min(int(round(entrance - exit_)), max(capacity, 0)))


def average_series(series: list[dict[datetime, float]]) -> dict[datetime, float]:
    """Hour-by-hour mean of several ``{local_hour: value}`` series.

    Used to turn per-space temperatures/humidity into one series per building.
    Only hours present in at least one series are returned.
    """
    totals: dict[datetime, float] = {}
    counts: dict[datetime, int] = {}
    for item in series:
        for hour, value in item.items():
            totals[hour] = totals.get(hour, 0.0) + value
            counts[hour] = counts.get(hour, 0) + 1
    return {hour: totals[hour] / counts[hour] for hour in totals}


def cumulative_to_hourly(
    rows: list[tuple[datetime, float]],
    max_delta: float | None = None,
    spread: bool = True,
) -> dict[datetime, float]:
    """Turn a cumulative ``sum`` series into hourly consumption (local hour).

    Home Assistant writes one statistics row per hour even when the meter value
    has not changed, so a *change* from one value to the next may have happened
    several hours later (a meter outage, a recorder restart, a re-import).

    HA stores the cumulative ``sum`` at the **end** of the period identified by
    ``start``. Therefore the difference between the rows at 10:00 and 11:00 is
    the consumption of the 11:00-12:00 period and belongs to the 11:00 bucket
    (the *current* row), not to the previous one. This is the same convention
    used by the Home Assistant energy dashboard.

    - With ``spread=True`` (electricity) the difference is spread evenly over the
      elapsed hours, because it is a real catch-up of consumption.
    - With ``spread=False`` (gas) the whole difference is kept in the current
      hour and then dropped by the ``max_delta`` guard if it is implausible; the
      gas meter has long periods with corrupted ``sum``/``state`` jumps that must
      not be counted at all.

    Always: negative differences (a meter reset) produce 0, and a value above
    ``max_delta`` is ignored so a bad row cannot inflate a whole chart.
    """
    hourly: dict[datetime, float] = {}
    last_change_time: datetime | None = None
    last_change_sum: float | None = None
    previous_sum: float | None = None

    for start, total in rows:
        if previous_sum is not None and total == previous_sum:
            continue  # value unchanged: just an hourly duplicate row

        if last_change_sum is None:
            last_change_time, last_change_sum = start, total
        else:
            delta = total - last_change_sum
            per_hour = delta if delta > 0 else 0.0
            hours = 1
            if spread:
                elapsed_hours = max(1.0, (start - last_change_time).total_seconds() / 3600.0)
                per_hour = per_hour / elapsed_hours
                hours = int(round(elapsed_hours))
            if max_delta is not None and per_hour > max_delta:
                per_hour = 0.0
            # The delta closes the interval at ``start``: attribute it to that
            # hour (and to the preceding ones when several hours were missing).
            first_hour = start - timedelta(hours=hours - 1)
            for offset in range(hours):
                step = first_hour + timedelta(hours=offset)
                key = _local_hour_from_epoch(_floor_epoch(step))
                hourly[key] = hourly.get(key, 0.0) + per_hour
            last_change_time, last_change_sum = start, total

        previous_sum = total

    return hourly


async def _load_state_series(
    session: AsyncSession,
    entity_ids: list[str],
    start_local: datetime,
    end_local: datetime,
) -> dict[str, dict[datetime, float]]:
    """Hourly averaged states per entity, fill-forward, keyed by local hour.

    Temperature/humidity sensors are read from HA's ``statistics`` table first:
    it already stores the hourly mean and avoids scanning a year of raw
    ``states`` rows. Any entity without long-term statistics (CO2, air quality,
    devices that only record state changes) falls back to ``states``.
    """
    if not entity_ids:
        return {}

    start_utc = _to_utc_naive(start_local)
    end_utc = _to_utc_naive(end_local)
    start_epoch = _floor_epoch(start_utc)
    end_epoch = _floor_epoch(end_utc)

    averages: dict[str, dict[int, float]] = {}
    baselines: dict[str, float] = {}

    if settings.USE_STATISTICS_FOR_STATES:
        stat_rows = await repository.fetch_statistics_means(
            session, entity_ids, start_utc, end_utc
        )
        for entity_id, start, value in stat_rows:
            averages.setdefault(entity_id, {})[_floor_epoch(start)] = value
        baselines.update(
            await repository.fetch_last_statistics_means_before(
                session, entity_ids, start_utc, _BASELINE_LOOKBACK
            )
        )

    # Entities with neither statistics rows nor a statistics baseline are read
    # from the raw states table (the old, slower path).
    missing = [
        entity_id
        for entity_id in entity_ids
        if entity_id not in averages and entity_id not in baselines
    ]
    if missing:
        rows = await repository.fetch_hourly_state_values(
            session, missing, start_utc, end_utc
        )
        for entity_id, epoch, value in rows:
            averages.setdefault(entity_id, {})[epoch] = value
        baselines.update(
            await repository.fetch_last_state_values_before(
                session, missing, start_utc, _BASELINE_LOOKBACK
            )
        )

    series: dict[str, dict[datetime, float]] = {}
    for entity_id in {*averages.keys(), *baselines.keys()}:
        measured = averages.get(entity_id, {})
        last_value = baselines.get(entity_id)
        filled: dict[datetime, float] = {}
        for epoch in range(start_epoch, end_epoch, _HOUR_SECONDS):
            if epoch in measured:
                last_value = measured[epoch]
            if last_value is not None:
                filled[_local_hour_from_epoch(epoch)] = last_value
        if filled:
            series[entity_id] = filled

    return series


async def _load_counter_series(
    session: AsyncSession,
    counters: list[OccupancyCounter],
    start_local: datetime,
    end_local: datetime,
) -> dict[tuple[str, str | None], dict[datetime, float]]:
    """Hourly last value of each people counter, fill-forward, local hour.

    Keyed by ``(entity_id, attribute)`` because two counters can share the same
    entity (Módulo B stores ``LTR_SUM`` and ``RTL_SUM`` in one JSON attribute).
    """
    if not counters:
        return {}

    start_utc = _to_utc_naive(start_local)
    end_utc = _to_utc_naive(end_local)
    start_epoch = _floor_epoch(start_utc)
    end_epoch = _floor_epoch(end_utc)
    counter_by_key = {(c.entity_id, c.attribute): c for c in counters}
    entity_ids = sorted({counter.entity_id for counter in counters})

    rows = await repository.fetch_hourly_state_snapshots(
        session, entity_ids, start_utc, end_utc
    )
    snapshots = await repository.fetch_last_state_snapshots_before(
        session, entity_ids, start_utc, _BASELINE_LOOKBACK
    )

    measured: dict[tuple[str, str | None], dict[int, float]] = {}
    for entity_id, epoch, state, attributes in rows:
        for key, counter in counter_by_key.items():
            if counter.entity_id != entity_id:
                continue
            value = parse_counter_value(state, attributes, counter.attribute)
            if value is not None:
                measured.setdefault(key, {})[epoch] = value

    baselines: dict[tuple[str, str | None], float] = {}
    for entity_id, (state, attributes) in snapshots.items():
        for key, counter in counter_by_key.items():
            if counter.entity_id != entity_id:
                continue
            value = parse_counter_value(state, attributes, counter.attribute)
            if value is not None:
                baselines[key] = value

    series: dict[tuple[str, str | None], dict[datetime, float]] = {}
    for key in {*measured.keys(), *baselines.keys()}:
        values = measured.get(key, {})
        last_value = baselines.get(key)
        filled: dict[datetime, float] = {}
        for epoch in range(start_epoch, end_epoch, _HOUR_SECONDS):
            if epoch in values:
                last_value = values[epoch]
            if last_value is not None:
                filled[_local_hour_from_epoch(epoch)] = last_value
        if filled:
            series[key] = filled

    return series


async def load_hourly_energy(
    session: AsyncSession,
    building_ids: list[str],
    start_local: datetime,
    end_local: datetime,
    *,
    include_site: bool = False,
) -> dict[str, dict[datetime, float]]:
    """Hourly electrical kWh, keyed by building id (or ``SITE_ENERGY_KEY``).

    ``include_site=True`` adds the whole-site meter used by Home Assistant's
    "cuadro general" card. The site series is stored under ``SITE_ENERGY_KEY``
    so it cannot be confused with a building.
    """
    entity_to_key: dict[str, str] = {}
    if include_site:
        entity_to_key[SITE_ENERGY_STATISTIC] = SITE_ENERGY_KEY
    entity_to_key.update(
        {
            BUILDING_ENERGY_STATISTIC[building_id]: building_id
            for building_id in building_ids
            if building_id in BUILDING_ENERGY_STATISTIC
        }
    )
    if not entity_to_key:
        return {}

    # One extra hour so the first in-window hour has a preceding sum to subtract.
    rows = await repository.fetch_statistics_sums(
        session,
        list(entity_to_key.keys()),
        _to_utc_naive(start_local - timedelta(hours=1)),
        _to_utc_naive(end_local),
    )

    by_entity: dict[str, list[tuple[datetime, float]]] = {}
    for statistic_id, start, total in rows:
        by_entity.setdefault(statistic_id, []).append((start, total))

    return {
        entity_to_key[statistic_id]: cumulative_to_hourly(
            series, max_delta=settings.ENERGY_MAX_KWH_PER_HOUR
        )
        for statistic_id, series in by_entity.items()
    }


async def load_hourly_gas(
    session: AsyncSession,
    start_local: datetime,
    end_local: datetime,
) -> dict[datetime, float]:
    """Hourly site-wide gas consumption in kWh, keyed by local hour.

    The meter reports m3; the value is converted with ``GAS_KWH_PER_M3`` so the
    API keeps serving kWh like the synthetic model.
    """
    rows = await repository.fetch_statistics_sums(
        session,
        [SITE_GAS_STATISTIC],
        _to_utc_naive(start_local - timedelta(hours=1)),
        _to_utc_naive(end_local),
    )
    cubic_metres = cumulative_to_hourly(
        [(start, total) for _, start, total in rows],
        max_delta=settings.GAS_MAX_M3_PER_HOUR,
        spread=False,
    )
    factor = settings.GAS_KWH_PER_M3
    return {hour: value * factor for hour, value in cubic_metres.items()}


async def load_hourly_outdoor_temperature(
    session: AsyncSession,
    start_local: datetime,
    end_local: datetime,
) -> dict[datetime, float]:
    """Hourly outdoor temperature (°C), keyed by local hour."""
    series = await _load_state_series(
        session, [OUTDOOR_TEMPERATURE_ENTITY], start_local, end_local
    )
    return series.get(OUTDOOR_TEMPERATURE_ENTITY, {})


async def _load_space_series(
    session: AsyncSession,
    entity_map: dict[str, str],
    space_ids: list[str],
    start_local: datetime,
    end_local: datetime,
) -> dict[str, dict[datetime, float]]:
    """Generic per-space series loader for a ``{space_id: entity_id}`` map."""
    entity_to_space = {
        entity_map[space_id]: space_id
        for space_id in space_ids
        if space_id in entity_map
    }
    if not entity_to_space:
        return {}

    by_entity = await _load_state_series(
        session, list(entity_to_space.keys()), start_local, end_local
    )
    return {
        entity_to_space[entity_id]: series
        for entity_id, series in by_entity.items()
    }


async def load_hourly_space_temperatures(
    session: AsyncSession,
    space_ids: list[str],
    start_local: datetime,
    end_local: datetime,
) -> dict[str, dict[datetime, float]]:
    """Hourly indoor temperature per space, keyed by space id then local hour."""
    return await _load_space_series(
        session, SPACE_TEMPERATURE_ENTITY, space_ids, start_local, end_local
    )


async def load_hourly_space_humidity(
    session: AsyncSession,
    space_ids: list[str],
    start_local: datetime,
    end_local: datetime,
) -> dict[str, dict[datetime, float]]:
    """Hourly relative humidity per space, keyed by space id then local hour."""
    return await _load_space_series(
        session, SPACE_HUMIDITY_ENTITY, space_ids, start_local, end_local
    )


async def load_hourly_space_co2(
    session: AsyncSession,
    space_ids: list[str],
    start_local: datetime,
    end_local: datetime,
) -> dict[str, dict[datetime, float]]:
    """Hourly CO2 (ppm) per instrumented space, keyed by space id then local hour.

    Only A11/A12/A21/A22 have an air-quality sensor; the other spaces are
    absent from the result and the caller falls back to the synthetic model.
    """
    return await _load_space_series(
        session, SPACE_CO2_ENTITY, space_ids, start_local, end_local
    )


async def load_hourly_occupancy(
    session: AsyncSession,
    building_ids: list[str],
    start_local: datetime,
    end_local: datetime,
) -> dict[str, dict[datetime, int]]:
    """Hourly people per building, keyed by building id then local hour.

    Derived from the entrance/exit counters (``max(0, entrada - salida)``).
    Buildings without both counters, or counters with no usable readings, are
    omitted so the caller can fall back to the synthetic occupancy.
    """
    buildings = [
        building_id
        for building_id in building_ids
        if building_id in BUILDING_OCCUPANCY_COUNTERS
    ]
    if not buildings:
        return {}

    counters = [
        counter
        for building_id in buildings
        for counter in BUILDING_OCCUPANCY_COUNTERS[building_id]
    ]
    by_entity = await _load_counter_series(
        session, counters, start_local, end_local
    )

    occupancy: dict[str, dict[datetime, int]] = {}
    for building_id in buildings:
        entrance_counter, exit_counter = BUILDING_OCCUPANCY_COUNTERS[building_id]
        entrance = by_entity.get(
            (entrance_counter.entity_id, entrance_counter.attribute), {}
        )
        exit_ = by_entity.get(
            (exit_counter.entity_id, exit_counter.attribute), {}
        )
        building = BUILDINGS_BY_ID.get(building_id)
        capacity = building.max_capacity if building else 0

        series: dict[datetime, int] = {}
        for hour, entrance_value in entrance.items():
            exit_value = exit_.get(hour)
            people = net_occupancy(entrance_value, exit_value, capacity)
            if people is not None:
                series[hour] = people
        if series:
            occupancy[building_id] = series

    return occupancy
