"""Load the weather station and AEMET rows from the recorder, read-only.

``weather.meteo`` stores the outdoor temperature in ``states.state`` and the
remaining measurements (humidity, pressure, particles, battery) in the JSON
``attributes`` column, so the raw rows are parsed in Python instead of being
averaged in SQL. The AEMET entities are read the same way because their
observation time is also an attribute.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.core.clock import to_utc_naive, utc_now
from app.core.weather_map import AEMET_ENTITIES, WEATHER_ENTITY
from app.db import repository
from app.db.session import AsyncSessionLocal

StateRow = tuple[datetime, str, str | None]

# One extra hour on each side: the first AEMET observation of the period is
# compared with the previous hour of the station, and the last one is written
# about 30 minutes after it was observed.
_WINDOW_MARGIN = timedelta(hours=1)
# Long enough to say when AEMET stopped reporting, however long ago that was.
_LATEST_LOOKBACK = timedelta(days=365)


@dataclass
class WeatherDatabaseData:
    """Raw rows needed by the weather service."""

    weather: list[StateRow] = field(default_factory=list)
    aemet: dict[str, list[StateRow]] = field(default_factory=dict)
    latest: dict[str, tuple[str, str | None, datetime]] = field(default_factory=dict)


async def load_weather_data(
    start_local: datetime,
    end_local: datetime,
) -> WeatherDatabaseData:
    """Read the weather station and AEMET rows of the period, plus the latest values."""
    entity_ids = [WEATHER_ENTITY, *AEMET_ENTITIES]

    async with AsyncSessionLocal() as session:
        rows = await repository.fetch_state_snapshots(
            session,
            entity_ids,
            to_utc_naive(start_local) - _WINDOW_MARGIN,
            to_utc_naive(end_local) + _WINDOW_MARGIN,
        )
        latest = await repository.fetch_latest_state_snapshots(
            session,
            entity_ids,
            utc_now() + timedelta(minutes=1),
            _LATEST_LOOKBACK,
        )

    grouped: dict[str, list[StateRow]] = {entity_id: [] for entity_id in entity_ids}
    for entity_id, last_updated, state, attributes in rows:
        grouped[entity_id].append((last_updated, state, attributes))

    return WeatherDatabaseData(
        weather=grouped[WEATHER_ENTITY],
        aemet={entity_id: grouped[entity_id] for entity_id in AEMET_ENTITIES},
        latest=latest,
    )
