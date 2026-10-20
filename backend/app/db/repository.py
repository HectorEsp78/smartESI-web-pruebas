"""Read-only SQLAlchemy queries against the Home Assistant recorder database.

Every statement here is a ``SELECT``. The tables belong to Home Assistant and
are never modified.

Query shapes:

- ``fetch_statistics_sums`` — cumulative ``sum`` series from ``statistics``
  (energy and gas meters). The hourly consumption is the difference between
  consecutive rows.
- ``fetch_statistics_means`` — hourly ``mean`` series from ``statistics``
  (temperature and humidity sensors with long-term statistics). Much cheaper
  than scanning a year of raw ``states`` rows.
- ``fetch_hourly_state_values`` — hourly average of a numeric ``states`` value,
  bucketed with ``FLOOR(UNIX_TIMESTAMP(last_updated) / 3600)``. Home Assistant
  only writes a row when the value changes, so gaps are filled forward in Python
  (see ``database_data``); the value right before the window is loaded with
  ``fetch_last_state_values_before`` so the first hour is not lost.
- ``fetch_hourly_state_snapshots`` — last raw ``state``/``attributes`` per entity
  and hour. Used for the people counters, whose attributes cannot be averaged
  in SQL (they are a JSON object).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Float, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ha import State, Statistics, StatisticsMeta

# Matches plain decimal numbers; discards "unavailable", "unknown", "None"…
_NUMERIC_STATE_PATTERN = r"^-?[0-9]+(\.[0-9]+)?$"

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


async def fetch_statistics_means(
    session: AsyncSession,
    statistic_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, datetime, float]]:
    """Hourly ``mean`` rows of the given statistics in ``[start, end)``.

    Returns ``(statistic_id, start, mean)`` ordered by statistic then time. This
    is the fast path for temperature/humidity sensors: HA already stores the
    hourly mean, so no raw ``states`` scan is needed.
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
    return [(statistic_id, start, float(value)) for statistic_id, start, value in result.all()]


async def fetch_last_statistics_means_before(
    session: AsyncSession,
    statistic_ids: list[str],
    before_utc: datetime,
    lookback: timedelta,
) -> dict[str, float]:
    """Last hourly ``mean`` of each statistic just before ``before_utc``.

    Seeds the fill-forward of the series when the first hour of the window has
    no row. Mirrors ``fetch_last_state_values_before`` for the statistics table.
    """
    if not statistic_ids:
        return {}

    subq = (
        select(
            Statistics.metadata_id.label("metadata_id"),
            func.max(Statistics.start).label("max_start"),
        )
        .where(
            Statistics.start < before_utc,
            Statistics.start >= before_utc - lookback,
            Statistics.mean.isnot(None),
        )
        .group_by(Statistics.metadata_id)
        .subquery()
    )
    stmt = (
        select(StatisticsMeta.statistic_id, Statistics.mean)
        .join(Statistics, Statistics.metadata_id == StatisticsMeta.id)
        .join(
            subq,
            and_(
                Statistics.metadata_id == subq.c.metadata_id,
                Statistics.start == subq.c.max_start,
            ),
        )
        .where(StatisticsMeta.statistic_id.in_(statistic_ids))
    )
    result = await session.execute(stmt)
    return {statistic_id: float(value) for statistic_id, value in result.all()}


async def fetch_hourly_state_values(
    session: AsyncSession,
    entity_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[str, int, float]]:
    """Average numeric value per entity and UTC hour in ``[start, end)``.

    Returns ``(entity_id, bucket_epoch_seconds, avg_value)``. Non-numeric states
    are filtered out *before* the cast so MariaDB's implicit 0-coercion cannot
    pollute the average.
    """
    if not entity_ids:
        return []

    bucket_ts = (func.floor(func.unix_timestamp(State.last_updated) / _HOUR_SECONDS) * _HOUR_SECONDS).label(
        "bucket_ts"
    )
    stmt = (
        select(
            State.entity_id,
            bucket_ts,
            func.avg(cast(State.state, Float)).label("value"),
        )
        .where(
            State.entity_id.in_(entity_ids),
            State.last_updated >= start_utc,
            State.last_updated < end_utc,
            State.state.regexp_match(_NUMERIC_STATE_PATTERN),
        )
        .group_by(State.entity_id, bucket_ts)
        .order_by(State.entity_id, bucket_ts)
    )
    result = await session.execute(stmt)
    return [
        (entity_id, int(bucket), float(value))
        for entity_id, bucket, value in result.all()
        if value is not None
    ]


async def fetch_last_state_values_before(
    session: AsyncSession,
    entity_ids: list[str],
    before_utc: datetime,
    lookback: timedelta,
) -> dict[str, float]:
    """Last numeric state of each entity just before ``before_utc``.

    Used to seed the fill-forward of the hourly series. Non-numeric states
    (``unavailable``, ``unknown``…) are skipped.
    """
    snapshots = await fetch_last_state_snapshots_before(
        session, entity_ids, before_utc, lookback
    )
    values: dict[str, float] = {}
    for entity_id, (raw, _attributes) in snapshots.items():
        try:
            values[entity_id] = float(raw)
        except (TypeError, ValueError):
            continue
    return values


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
