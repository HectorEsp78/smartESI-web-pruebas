"""Load battery readings from the recorder, read-only.

The latest row tells whether a sensor still reports. When that row is not a valid
reading (``unknown``, ``unavailable``, a glitch), a second query looks for the
last valid one, so only those few sensors need it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.battery_map import LATEST_READING_LOOKBACK_DAYS, BatteryGroup, BatterySensor
from app.db import repository
from app.db.session import AsyncSessionLocal


@dataclass(frozen=True)
class LatestBatteryRows:
    """Last row of a sensor (``None`` if it has none) and its last valid reading."""

    last_state: str | None
    last_row_at: datetime | None
    valid_value: float | None
    valid_at: datetime | None


def parse_reading(state: str | None, valid_range: tuple[float, float]) -> float | None:
    """Numeric value of a raw state, or ``None`` if it is not a valid reading."""
    if state is None:
        return None
    try:
        value = float(state)
    except ValueError:
        return None
    low, high = valid_range
    return value if low <= value <= high else None


async def load_latest_readings(
    group: BatteryGroup, now_utc: datetime
) -> dict[str, LatestBatteryRows]:
    """Latest row and latest valid reading of every sensor of a group, by entity."""
    entity_ids = [sensor.entity_id for sensor in group.sensors]
    lookback = timedelta(days=LATEST_READING_LOOKBACK_DAYS)
    low, high = group.valid_range

    async with AsyncSessionLocal() as session:
        latest = await repository.fetch_latest_state_snapshots(
            session, entity_ids, now_utc, lookback
        )
        invalid = [
            entity_id
            for entity_id in entity_ids
            if entity_id in latest
            and parse_reading(latest[entity_id][0], group.valid_range) is None
        ]
        fallback = await repository.fetch_latest_numeric_states(
            session, invalid, now_utc, low, high
        )

    rows: dict[str, LatestBatteryRows] = {}
    for entity_id in entity_ids:
        if entity_id not in latest:
            rows[entity_id] = LatestBatteryRows(None, None, None, None)
            continue
        state, _attributes, last_updated = latest[entity_id]
        value = parse_reading(state, group.valid_range)
        if value is not None:
            rows[entity_id] = LatestBatteryRows(state, last_updated, value, last_updated)
        else:
            valid_value, valid_at = fallback.get(entity_id, (None, None))
            rows[entity_id] = LatestBatteryRows(state, last_updated, valid_value, valid_at)
    return rows


async def load_hourly_means(
    group: BatteryGroup,
    sensor: BatterySensor,
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple[int, float]]:
    """Hourly mean of the valid readings as ``(epoch_seconds, mean)``."""
    low, high = group.valid_range
    async with AsyncSessionLocal() as session:
        rows = await repository.fetch_hourly_numeric_state_means(
            session, [sensor.entity_id], start_utc, end_utc, low, high
        )
    return [(bucket, mean) for _entity_id, bucket, mean in rows]
