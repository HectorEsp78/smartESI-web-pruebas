"""Load environment data from the Home Assistant recorder, read-only.

The recorder does not have CO₂ long-term statistics for the Airthings sensors,
so those hourly means are computed from raw ``states``. Temperature, humidity,
the generic presence sensors and the ambient reference have statistics. Gas is
read from cumulative ``sum`` rows. The four CO₂ queries run in parallel with the
smaller statistics/presence queries to keep long ranges responsive without
scanning unrelated entities.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.core.clock import local_tz
from app.core.environment_map import (
    AMBIENT_TEMPERATURE_ENTITY,
    CO2_MAX_PPM,
    CO2_MIN_PPM,
    ENVIRONMENT_ROOMS,
    GAS_COST_ENTITY,
    GAS_M3_ENTITY,
    HUMIDITY_MAX_PCT,
    HUMIDITY_MIN_PCT,
    TEMPERATURE_MAX_C,
    TEMPERATURE_MIN_C,
)
from app.db import repository
from app.db.session import AsyncSessionLocal

_BASELINE_LOOKBACK = timedelta(days=7)
_HOUR_SECONDS = 3600


@dataclass
class EnvironmentDatabaseData:
    """Hourly series keyed by local hour, plus the latest raw values."""

    statistics: dict[str, dict[datetime, float]] = field(default_factory=dict)
    co2: dict[str, dict[datetime, float]] = field(default_factory=dict)
    presence: dict[str, dict[datetime, float]] = field(default_factory=dict)
    latest: dict[str, tuple[str, str | None, datetime]] = field(default_factory=dict)
    # Cumulative gas sums, kept as raw rows so the service can split the
    # increments into local chart buckets.
    gas_sums: dict[str, list[tuple[datetime, float]]] = field(default_factory=dict)


def _to_utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _floor_epoch(value_utc_naive: datetime) -> int:
    seconds = int(value_utc_naive.replace(tzinfo=timezone.utc).timestamp())
    return seconds // _HOUR_SECONDS * _HOUR_SECONDS


def _local_hour_from_epoch(epoch_seconds: int) -> datetime:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).astimezone(local_tz()).replace(
        minute=0, second=0, microsecond=0
    )


def _local_hour(value_utc_naive: datetime) -> datetime:
    return _local_hour_from_epoch(_floor_epoch(value_utc_naive))


def parse_float(
    state: str | None,
    minimum: float,
    maximum: float,
) -> float | None:
    """Numeric value of a raw state, rejecting resets and non-numeric values."""
    try:
        value = float(state)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if value < minimum or value > maximum:
        return None
    return value


def parse_presence(state: str | None) -> bool | None:
    """Home Assistant binary and motion states → ``True``/``False``.

    ``sensor.movimiento_*`` uses ``Sí``/``No``; the generic ``sensor.presencia*``
    entities use ``1``/``0``. Unknown values are not treated as "empty".
    """
    if state is None:
        return None
    value = state.strip().lower()
    if value in {"sí", "si", "1", "on", "yes", "true"}:
        return True
    if value in {"no", "0", "off", "false"}:
        return False
    return None


def _hourly_presence(
    rows: list[tuple[str, datetime, str]],
    baseline: str | None,
    start_utc: datetime,
    end_utc: datetime,
) -> dict[datetime, float]:
    """Time-weighted presence fraction per local hour.

    The sensor rows are transitions, not periodic samples. We walk the timeline
    from the last known state before the window and split it into one-hour
    chunks, so an hour with a single long "on" interval is 100 %, not 1 row.
    """
    baseline_on = parse_presence(baseline)
    events = [
        (last_updated, parsed)
        for _entity_id, last_updated, state in rows
        if (parsed := parse_presence(state)) is not None
    ]
    events.sort(key=lambda item: item[0])

    on_seconds: dict[int, float] = {}
    total_seconds: dict[int, float] = {}
    cursor = start_utc
    current_on = bool(baseline_on)

    def add_segment(segment_start: datetime, segment_end: datetime, is_on: bool) -> None:
        if segment_end <= segment_start:
            return
        segment_cursor = segment_start
        while segment_cursor < segment_end:
            epoch = _floor_epoch(segment_cursor)
            next_hour = datetime.fromtimestamp(
                epoch + _HOUR_SECONDS, tz=timezone.utc
            ).replace(tzinfo=None)
            chunk_end = min(segment_end, next_hour)
            seconds = max(0.0, (chunk_end - segment_cursor).total_seconds())
            total_seconds[epoch] = total_seconds.get(epoch, 0.0) + seconds
            if is_on:
                on_seconds[epoch] = on_seconds.get(epoch, 0.0) + seconds
            segment_cursor = chunk_end

    for event_time, event_on in events:
        if event_time <= cursor:
            current_on = event_on
            continue
        add_segment(cursor, min(event_time, end_utc), current_on)
        cursor = max(cursor, event_time)
        current_on = event_on
        if cursor >= end_utc:
            break
    if cursor < end_utc:
        add_segment(cursor, end_utc, current_on)

    # Merge epochs that fall in the same local hour (DST fall-back) instead of
    # letting the last one overwrite the other.
    merged: dict[datetime, tuple[float, float]] = {}
    for epoch, total in total_seconds.items():
        key = _local_hour_from_epoch(epoch)
        on, previous_total = merged.get(key, (0.0, 0.0))
        merged[key] = (on + on_seconds.get(epoch, 0.0), previous_total + total)

    return {
        key: on / total
        for key, (on, total) in merged.items()
        if total > 0
    }


async def _load_co2_entity(
    entity_id: str,
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, int, float]]:
    """Load one CO₂ entity in its own session so the four queries can overlap.

    The recorder has no CO₂ statistics, so this is the most expensive part of
    the long ranges. Running one indexed query per entity in parallel is much
    faster than grouping all four in a single scan on this installation.
    """
    async with AsyncSessionLocal() as session:
        return await repository.fetch_hourly_numeric_state_means(
            session,
            [entity_id],
            start_utc,
            end_utc,
            min_value=CO2_MIN_PPM,
            max_value=CO2_MAX_PPM,
        )


async def load_environment_data(
    start_local: datetime,
    end_local: datetime,
) -> EnvironmentDatabaseData:
    """Read all sensors needed by the environment service in a few indexed queries."""
    start_utc = _to_utc_naive(start_local)
    end_utc = _to_utc_naive(end_local)

    statistic_ids = sorted(
        {
            entity
            for room in ENVIRONMENT_ROOMS
            for entity in (
                room.temperature_entity,
                room.humidity_entity,
                room.presence_statistic_id,
            )
            if entity
        }
        | {AMBIENT_TEMPERATURE_ENTITY}
    )
    co2_ids = sorted({room.co2_entity for room in ENVIRONMENT_ROOMS if room.co2_entity})
    motion_ids = sorted(
        {
            room.presence_entity
            for room in ENVIRONMENT_ROOMS
            if room.presence_entity and room.presence_statistic_id is None
        }
    )
    latest_ids = sorted(
        {
            entity
            for room in ENVIRONMENT_ROOMS
            for entity in (
                room.temperature_entity,
                room.humidity_entity,
                room.co2_entity,
                room.presence_entity,
            )
            if entity
        }
        | {AMBIENT_TEMPERATURE_ENTITY}
    )
    gas_ids = [GAS_M3_ENTITY, GAS_COST_ENTITY]

    # Start the four CO₂ scans before the smaller queries, so they overlap.
    co2_task = asyncio.gather(
        *[_load_co2_entity(entity_id, start_utc, end_utc) for entity_id in co2_ids]
    )

    try:
        async with AsyncSessionLocal() as session:
            stats_rows = await repository.fetch_statistics_means(
                session, statistic_ids, start_utc, end_utc
            )
            motion_rows = await repository.fetch_state_rows(
                session, motion_ids, start_utc, end_utc
            )
            motion_baselines = await repository.fetch_last_state_snapshots_before(
                session, motion_ids, start_utc, _BASELINE_LOOKBACK
            )
            latest = await repository.fetch_latest_state_snapshots(
                session,
                latest_ids,
                end_utc + timedelta(minutes=1),
                _BASELINE_LOOKBACK + timedelta(days=14),
            )
            gas_rows = await repository.fetch_statistics_sums(
                session,
                gas_ids,
                start_utc - timedelta(days=2),
                end_utc,
            )
    except BaseException:
        # Do not leave the parallel CO₂ tasks running if another query fails.
        co2_task.cancel()
        await asyncio.gather(co2_task, return_exceptions=True)
        raise

    co2_rows = [row for rows in await co2_task for row in rows]

    statistics: dict[str, dict[datetime, float]] = {}
    for statistic_id, start, mean in stats_rows:
        statistics.setdefault(statistic_id, {})[_local_hour(start)] = mean

    co2: dict[str, dict[datetime, float]] = {}
    for entity_id, bucket, mean in co2_rows:
        co2.setdefault(entity_id, {})[_local_hour_from_epoch(bucket)] = mean

    by_entity: dict[str, list[tuple[str, datetime, str]]] = {}
    for entity_id, last_updated, state in motion_rows:
        by_entity.setdefault(entity_id, []).append((entity_id, last_updated, state))

    presence: dict[str, dict[datetime, float]] = {}
    for entity_id, rows in by_entity.items():
        baseline = motion_baselines.get(entity_id, (None, None))[0]
        series = _hourly_presence(rows, baseline, start_utc, end_utc)
        if series:
            presence[entity_id] = series

    gas_sums: dict[str, list[tuple[datetime, float]]] = {}
    for entity_id, start, total in gas_rows:
        gas_sums.setdefault(entity_id, []).append((start, total))

    return EnvironmentDatabaseData(
        statistics=statistics,
        co2=co2,
        presence=presence,
        latest=latest,
        gas_sums=gas_sums,
    )
