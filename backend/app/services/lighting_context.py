"""Time buckets and occupancy context shared by the Lighting charts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.buildings import BUILDINGS, BUILDINGS_BY_ID, BuildingConfig
from app.core.clock import local_now, local_tz
from app.core.config import settings
from app.schemas.lighting import LightingRange
from app.services import mock_data

ALL_BUILDINGS = "all"


@dataclass(frozen=True)
class Bucket:
    start: datetime
    end: datetime


def _floor_hour(value: datetime) -> datetime:
    return value.replace(minute=0, second=0, microsecond=0)


def _floor_hour_local(value: datetime) -> datetime:
    """Floor to the hour in the school's timezone (DB series are local-keyed)."""
    return value.astimezone(local_tz()).replace(minute=0, second=0, microsecond=0)


def _floor_day(value: datetime) -> datetime:
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def _floor_month(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(value: datetime, months: int) -> datetime:
    index = value.month - 1 + months
    year = value.year + index // 12
    month = index % 12 + 1
    return value.replace(year=year, month=month, day=1)


def build_buckets(range_: LightingRange) -> list[Bucket]:
    """Return the last day/week/month/year as ready-to-plot buckets."""
    now = local_now()

    if range_ == "day":
        last = _floor_hour(now)
        return [
            Bucket(last - timedelta(hours=i), last - timedelta(hours=i) + timedelta(hours=1))
            for i in range(23, -1, -1)
        ]

    if range_ == "week":
        last = _floor_day(now)
        days = 7
    elif range_ == "month":
        last = _floor_day(now)
        days = 30
    else:  # year
        last_month = _floor_month(now)
        return [
            Bucket(_add_months(last_month, -i), _add_months(last_month, -i + 1))
            for i in range(11, -1, -1)
        ]

    return [
        Bucket(last - timedelta(days=i), last - timedelta(days=i) + timedelta(days=1))
        for i in range(days - 1, -1, -1)
    ]


def scope_buildings(building_id: str | None) -> list[BuildingConfig]:
    """Buildings selected by the filter (all, one, or an unknown id)."""
    if building_id in (None, "", ALL_BUILDINGS):
        return list(BUILDINGS)
    building = BUILDINGS_BY_ID.get(building_id)
    return [building] if building else []


class OccupancyProvider:
    """Hourly people count: the real counters or the synthetic model."""

    def __init__(self, database: dict[str, dict[datetime, int]] | None) -> None:
        self._database = database

    def hour_occupancy(self, building: BuildingConfig, when: datetime) -> int:
        if self._database is not None:
            value = self._database.get(building.id, {}).get(_floor_hour_local(when))
            if value is not None:
                return value
        return mock_data.hour_occupancy(building, when)


async def load_occupancy_provider(
    scope: list[BuildingConfig], start: datetime, end: datetime
) -> OccupancyProvider:
    """Real occupancy counters when available, synthetic model otherwise."""
    if settings.DATA_SOURCE != "database":
        return OccupancyProvider(None)

    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import database_data
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        data = await database_data.load_hourly_occupancy(
            session, [building.id for building in scope], start, end
        )
    return OccupancyProvider(data)
