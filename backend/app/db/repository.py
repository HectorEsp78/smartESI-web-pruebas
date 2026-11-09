"""Read-only SQLAlchemy queries against the Home Assistant recorder database.

Every statement here is a ``SELECT``. The tables belong to Home Assistant and
are never modified.

- ``fetch_statistics_sums`` — cumulative ``sum`` series from ``statistics``
  (electricity meters). Hourly consumption is the difference between
  consecutive rows.
- ``fetch_hourly_state_snapshots`` — last raw ``state``/``attributes`` per
  entity and hour for the people counters, whose JSON attributes cannot be
  averaged in SQL.
- ``fetch_last_state_snapshots_before`` — the value right before a window, so
  the first hour can be filled forward.
- ``fetch_statistics_means`` — hourly ``mean`` rows for temperature, humidity
  and presence statistics.
- ``fetch_hourly_numeric_state_means`` — hourly averages of numeric raw states
  (CO₂), which has no long-term statistics in this recorder.
- ``fetch_state_rows`` — raw transitions for motion sensors.
- ``fetch_latest_state_snapshots`` — last raw value/timestamp for the live cards.
- ``fetch_latest_numeric_states`` — last valid reading of the battery sensors whose
  latest row is ``unknown`` or a glitch.
- ``fetch_state_timestamps`` /``fetch_last_state_timestamps_before`` — heartbeat
  timestamps for the Maintenance tab.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ha import State, Statistics, StatisticsMeta

_HOUR_SECONDS = 3600


def _latest_state_ids(entity_ids: list[str], before_utc: datetime, lookback: timedelta):
    """Subquery with the newest ``state_id`` of each entity before ``before_utc``.

    ``MAX(state_id)`` per entity keeps this a set of index lookups instead of a
    scan of the recorder's ``states`` table.
    """
    return (
        select(func.max(State.state_id).label("max_id"))
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated < before_utc,
            State.last_updated >= before_utc - lookback,
        )
        .group_by(State.entity_id)
        .subquery()
    )


async def fetch_statistics_means(
    session: AsyncSession,
    statistic_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, datetime, float]]:
    """Hourly ``mean`` rows of the given statistics in ``[start, end)``.

    Used by the environment tab for sensors whose long-term statistics already
    exist (temperature, humidity and the generic presence sensors). Returns
    ``(statistic_id, start, mean)`` ordered by statistic then time.
    """
    if not statistic_ids:
        return []

    stmt = (
        select(StatisticsMeta.statistic_id, Statistics.start, Statistics.mean)
        .join(Statistics, Statistics.metadata_id == StatisticsMeta.id)
        .where(
            StatisticsMeta.statistic_id.in_(statistic_ids),
            Statistics.start >= start_utc,
            Statistics.start < end_utc,
            Statistics.mean.isnot(None),
        )
        .order_by(StatisticsMeta.statistic_id, Statistics.start)
    )
    result = await session.execute(stmt)
    return [
        (statistic_id, start, float(mean))
        for statistic_id, start, mean in result.all()
        if mean is not None
    ]


async def fetch_hourly_numeric_state_means(
    session: AsyncSession,
    entity_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
    min_value: float,
    max_value: float,
) -> list[tuple[str, int, float]]:
    """Hourly average of numeric raw ``state`` values in ``[start, end)``.

    Used for CO₂ because those entities do not have long-term statistics in this
    recorder. Non-numeric states (``unknown``, ``unavailable``) and impossible
    values are filtered before averaging. Returns
    ``(entity_id, bucket_epoch_seconds, mean)``.
    """
    if not entity_ids:
        return []

    bucket_ts = (
        func.floor(func.unix_timestamp(State.last_updated) / _HOUR_SECONDS)
        * _HOUR_SECONDS
    ).label("bucket_ts")
    numeric_state = cast(State.state, Numeric(12, 3))
    mean_value = func.avg(numeric_state).label("mean_value")
    stmt = (
        select(State.entity_id, bucket_ts, mean_value)
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated >= start_utc,
            State.last_updated < end_utc,
            State.state.op("REGEXP")(r"^-?[0-9]+(\.[0-9]+)?$"),
            numeric_state.between(min_value, max_value),
        )
        .group_by(State.entity_id, bucket_ts)
        .order_by(State.entity_id, bucket_ts)
    )
    result = await session.execute(stmt)
    return [
        (entity_id, int(bucket), float(mean))
        for entity_id, bucket, mean in result.all()
    ]


async def fetch_state_rows(
    session: AsyncSession,
    entity_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, datetime, str]]:
    """Raw ``state`` transitions of the given entities in ``[start, end)``.

    Presence/motion sensors only write a row when their state changes, so the
    service turns these transitions into time-weighted occupancy fractions.
    """
    if not entity_ids:
        return []

    stmt = (
        select(State.entity_id, State.last_updated, State.state)
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated >= start_utc,
            State.last_updated < end_utc,
        )
        .order_by(State.entity_id, State.last_updated)
    )
    result = await session.execute(stmt)
    return list(result.tuples().all())


async def fetch_state_snapshots(
    session: AsyncSession,
    entity_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, datetime, str, str | None]]:
    """Raw ``state`` and ``attributes`` rows in ``[start, end)``.

    Weather entities keep most measurements in the JSON ``attributes`` column,
    so the service needs the raw rows instead of an SQL average. The range is
    bounded by the requested period (at most 90 days), which keeps the result
    small enough to parse in Python.
    """
    if not entity_ids:
        return []

    stmt = (
        select(
            State.entity_id,
            State.last_updated,
            State.state,
            State.attributes,
        )
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated >= start_utc,
            State.last_updated < end_utc,
        )
        .order_by(State.entity_id, State.last_updated)
    )
    result = await session.execute(stmt)
    return list(result.tuples().all())


async def fetch_latest_state_snapshots(
    session: AsyncSession,
    entity_ids: list[str],
    before_utc: datetime,
    lookback: timedelta,
) -> dict[str, tuple[str, str | None, datetime]]:
    """Latest raw ``(state, attributes, last_updated)`` of each entity."""
    if not entity_ids:
        return {}

    subq = _latest_state_ids(entity_ids, before_utc, lookback)
    stmt = select(
        State.entity_id, State.state, State.attributes, State.last_updated
    ).join(subq, State.state_id == subq.c.max_id)
    result = await session.execute(stmt)
    return {
        entity_id: (state, attributes, last_updated)
        for entity_id, state, attributes, last_updated in result.all()
    }


async def fetch_latest_numeric_states(
    session: AsyncSession,
    entity_ids: list[str],
    before_utc: datetime,
    min_value: float,
    max_value: float,
) -> dict[str, tuple[float, datetime]]:
    """Latest numeric ``state`` within the range of each entity, with its time."""
    if not entity_ids:
        return {}

    numeric_state = cast(State.state, Numeric(12, 3))
    latest = (
        select(func.max(State.state_id).label("max_id"))
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated < before_utc,
            State.state.op("REGEXP")(r"^-?[0-9]+(\.[0-9]+)?$"),
            numeric_state.between(min_value, max_value),
        )
        .group_by(State.entity_id)
        .subquery()
    )
    stmt = select(State.entity_id, State.state, State.last_updated).join(
        latest, State.state_id == latest.c.max_id
    )
    result = await session.execute(stmt)
    return {
        entity_id: (float(state), last_updated)
        for entity_id, state, last_updated in result.all()
    }


async def fetch_state_timestamps(
    session: AsyncSession,
    entity_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, datetime]]:
    """Raw ``last_updated`` timestamps of each entity in ``[start, end)``.

    Used by the Maintenance tab to measure how often a device transmits and to
    detect silence gaps. Only the timestamp is read, so the query stays light
    even for high-frequency CO₂/meter heartbeats.
    """
    if not entity_ids:
        return []

    stmt = (
        select(State.entity_id, State.last_updated)
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated >= start_utc,
            State.last_updated < end_utc,
        )
        .order_by(State.entity_id, State.last_updated)
    )
    result = await session.execute(stmt)
    return list(result.tuples().all())


async def fetch_last_state_timestamps_before(
    session: AsyncSession,
    entity_ids: list[str],
    before_utc: datetime,
    lookback: timedelta,
) -> dict[str, datetime]:
    """Last ``last_updated`` of each entity before ``before_utc``.

    Maintenance uses this only for devices that produced no heartbeat inside the
    selected period, so a long lookback (legacy valves) stays cheap.
    """
    if not entity_ids:
        return {}

    subq = _latest_state_ids(entity_ids, before_utc, lookback)
    stmt = select(State.entity_id, State.last_updated).join(
        subq, State.state_id == subq.c.max_id
    )
    result = await session.execute(stmt)
    return dict(result.tuples().all())


async def fetch_statistics_sums(
    session: AsyncSession,
    statistic_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, datetime, float]]:
    """Cumulative ``sum`` rows of the given statistics in ``[start, end)``.

    Returns ``(statistic_id, start, sum)`` ordered by statistic then time. Rows
    without a ``sum`` (mean-only sensors) are skipped.
    """
    if not statistic_ids:
        return []

    stmt = (
        select(StatisticsMeta.statistic_id, Statistics.start, Statistics.sum)
        .join(Statistics, Statistics.metadata_id == StatisticsMeta.id)
        .where(
            StatisticsMeta.statistic_id.in_(statistic_ids),
            Statistics.start >= start_utc,
            Statistics.start < end_utc,
            Statistics.sum.isnot(None),
        )
        .order_by(StatisticsMeta.statistic_id, Statistics.start)
    )
    result = await session.execute(stmt)
    return [
        (statistic_id, start, float(total))
        for statistic_id, start, total in result.all()
        if total is not None
    ]


async def fetch_last_state_snapshots_before(
    session: AsyncSession,
    entity_ids: list[str],
    before_utc: datetime,
    lookback: timedelta,
) -> dict[str, tuple[str, str | None]]:
    """Last raw ``(state, attributes)`` of each entity before ``before_utc``.

    Returns the raw strings because some counters live in the JSON ``attributes``
    column.
    """
    if not entity_ids:
        return {}

    subq = _latest_state_ids(entity_ids, before_utc, lookback)
    stmt = select(State.entity_id, State.state, State.attributes).join(
        subq, State.state_id == subq.c.max_id
    )
    result = await session.execute(stmt)
    return {
        entity_id: (state, attributes)
        for entity_id, state, attributes in result.all()
    }


async def fetch_hourly_state_snapshots(
    session: AsyncSession,
    entity_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, int, str, str | None]]:
    """Last raw ``state``/``attributes`` per entity and UTC hour in ``[start, end)``.

    Returns ``(entity_id, bucket_epoch_seconds, state, attributes)``. The
    occupancy counters change on every person crossing the door, so averaging
    them makes no sense; taking the last row of each hour gives the occupancy at
    the end of that hour. The JSON attributes are parsed in Python.
    """
    if not entity_ids:
        return []

    bucket_ts = (
        func.floor(func.unix_timestamp(State.last_updated) / _HOUR_SECONDS)
        * _HOUR_SECONDS
    ).label("bucket_ts")
    max_id = func.max(State.state_id).label("max_id")
    hourly = (
        select(State.entity_id, bucket_ts, max_id)
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated >= start_utc,
            State.last_updated < end_utc,
        )
        .group_by(State.entity_id, bucket_ts)
        .subquery()
    )
    stmt = (
        select(
            State.entity_id,
            hourly.c.bucket_ts,
            State.state,
            State.attributes,
        )
        .join(hourly, State.state_id == hourly.c.max_id)
        .order_by(State.entity_id, hourly.c.bucket_ts)
    )
    result = await session.execute(stmt)
    return [
        (entity_id, int(bucket), state, attributes)
        for entity_id, bucket, state, attributes in result.all()
    ]
