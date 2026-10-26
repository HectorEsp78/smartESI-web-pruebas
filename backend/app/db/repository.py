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
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ha import State, Statistics, StatisticsMeta

_HOUR_SECONDS = 3600


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
    return [(statistic_id, start, float(total)) for statistic_id, start, total in result.all()]


async def fetch_last_state_snapshots_before(
    session: AsyncSession,
    entity_ids: list[str],
    before_utc: datetime,
    lookback: timedelta,
) -> dict[str, tuple[str, str | None]]:
    """Last raw ``(state, attributes)`` of each entity before ``before_utc``.

    The canonical Home Assistant pattern is a correlated ``MAX(state_id)`` per
    entity. Returns the raw strings because some counters live in the JSON
    ``attributes`` column.
    """
    if not entity_ids:
        return {}

    subq = (
        select(func.max(State.state_id).label("max_id"))
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated < before_utc,
            State.last_updated >= before_utc - lookback,
        )
        .group_by(State.entity_id)
        .subquery()
    )
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
