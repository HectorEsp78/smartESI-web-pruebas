"""Load weather-station data from the Home Assistant recorder, read-only.

``weather.meteo`` stores the outdoor temperature in ``states.state`` and the
remaining measurements (humidity, pressure, particles, battery) in the JSON
``attributes`` column. ``sensor.ambiente`` is the indoor reference and the
AEMET entities are an external comparison. Long-term statistics are used only
for the cumulative gas/electricity meters; the weather series is read from the
raw states because the attributes cannot be averaged in SQL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.core.weather_map import (
    AEMET_ENTITIES,
    AMBIENT_ENTITY,
    ELECTRICITY_ENTITY,
    GAS_COST_ENTITY,
    GAS_M3_ENTITY,
    WEATHER_ENTITY,
)
from app.db import repository
from app.db.session import AsyncSessionLocal

_BASELINE_LOOKBACK = timedelta(days=2)
_LATEST_LOOKBACK = timedelta(days=365)


@dataclass
class WeatherDatabaseData:
    """Raw rows needed by the weather service."""

    weather: list[tuple[datetime, str, str | None]] = field(default_factory=list)
    ambient: list[tuple[datetime, str, str | None]] = field(default_factory=list)
    aemet: dict[str, list[tuple[datetime, str, str | None]]] = field(default_factory=dict)
    latest: dict[str, tuple[str, str | None, datetime]] = field(default_factory=dict)
    sums: dict[str, list[tuple[datetime, float]]] = field(default_factory=dict)


def _to_utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _split_snapshots(
    rows: list[tuple[str, datetime, str, str | None]],
    entity_ids: list[str],
) -> dict[str, list[tuple[datetime, str, str | None]]]:
    grouped: dict[str, list[tuple[datetime, str, str | None]]] = {
        entity_id: [] for entity_id in entity_ids
    }
    for entity_id, last_updated, state, attributes in rows:
        grouped.setdefault(entity_id, []).append((last_updated, state, attributes))
    return grouped


async def load_weather_data(
    start_local: datetime,
    end_local: datetime,
) -> WeatherDatabaseData:
    """Read the weather station, indoor reference, AEMET and energy meters."""
    start_utc = _to_utc_naive(start_local)
    end_utc = _to_utc_naive(end_local)

    entity_ids = [WEATHER_ENTITY, AMBIENT_ENTITY, *AEMET_ENTITIES]
    statistic_ids = [GAS_M3_ENTITY, GAS_COST_ENTITY, ELECTRICITY_ENTITY]

    async with AsyncSessionLocal() as session:
        snapshots = await repository.fetch_state_snapshots(
            session,
            entity_ids,
            start_utc,
            end_utc,
        )
        grouped = _split_snapshots(snapshots, entity_ids)

        latest = await repository.fetch_latest_state_snapshots(
            session,
            entity_ids,
            end_utc + timedelta(minutes=1),
            _LATEST_LOOKBACK,
        )

        sum_rows = await repository.fetch_statistics_sums(
            session,
            statistic_ids,
            start_utc - _BASELINE_LOOKBACK,
            end_utc,
        )

    sums: dict[str, list[tuple[datetime, float]]] = {
        statistic_id: [] for statistic_id in statistic_ids
    }
    for statistic_id, timestamp, total in sum_rows:
        sums.setdefault(statistic_id, []).append((timestamp, total))

    return WeatherDatabaseData(
        weather=grouped.get(WEATHER_ENTITY, []),
        ambient=grouped.get(AMBIENT_ENTITY, []),
        aemet={entity_id: grouped.get(entity_id, []) for entity_id in AEMET_ENTITIES},
        latest=latest,
        sums=sums,
    )
