"""Business logic for the "occupancy vs. air quality" data-crossing chart.

Returns paired, aggregated points (occupancy, CO₂, temperature, humidity) plus a
few summary statistics (Pearson correlation, linear regression, and the share of
time the air quality is good/moderate/poor) that are useful for decision-making.

With ``DATA_SOURCE=database`` the occupancy comes from the entrance/exit
counters and the CO₂/temperature/humidity from the real sensors. Only four
classrooms have a CO₂ probe; buildings without one fall back to the synthetic
model so the chart is never empty.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.core.cache import TTLCache
from app.core.clock import local_now, local_tz
from app.core.config import settings
from app.core.energy_map import (
    BUILDINGS,
    BUILDINGS_BY_ID,
    SPACES_BY_BUILDING,
    BuildingConfig,
)
from app.schemas.correlation import (
    CorrelationPoint,
    CorrelationRange,
    CorrelationStats,
    OccupancyAirQualityResponse,
)
from app.services import mock_data, stats

# Thresholds aligned with the main Smart ESI project (ppm).
CO2_GOOD_MAX = 800.0
CO2_MODERATE_MAX = 1200.0

ALL_BUILDINGS = "all"

_STEP_HOURS: dict[CorrelationRange, int] = {
    "day": 1,
    "week": 3,
    "month": 12,
    "year": 24,
}

_SPAN_HOURS: dict[CorrelationRange, int] = {
    "day": 24,
    "week": 7 * 24,
    "month": 30 * 24,
    "year": 365 * 24,
}

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS)


def _floor_hour(value: datetime) -> datetime:
    return value.replace(minute=0, second=0, microsecond=0)


def _floor_hour_local(value: datetime) -> datetime:
    return value.astimezone(local_tz()).replace(minute=0, second=0, microsecond=0)


def _scope(building_id: str | None) -> list[BuildingConfig]:
    if building_id in (None, "", ALL_BUILDINGS):
        return list(BUILDINGS)
    building = BUILDINGS_BY_ID.get(building_id)
    return [building] if building else []


def _regression(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Return (r, slope, intercept) of the least-squares fit of ys on xs."""
    fit = stats.least_squares(xs, ys)
    return fit.r, fit.slope, fit.intercept


def _per_building(
    scope: list[BuildingConfig],
    by_space: dict[str, dict[datetime, float]],
) -> dict[str, dict[datetime, float]]:
    """Average the per-space series of each building into one series."""
    result: dict[str, dict[datetime, float]] = {}
    for building in scope:
        series = [
            by_space[space.id]
            for space in SPACES_BY_BUILDING.get(building.id, [])
            if space.id in by_space
        ]
        if not series:
            continue
        totals: dict[datetime, float] = {}
        counts: dict[datetime, int] = {}
        for item in series:
            for hour, value in item.items():
                totals[hour] = totals.get(hour, 0.0) + value
                counts[hour] = counts.get(hour, 0) + 1
        result[building.id] = {
            hour: totals[hour] / counts[hour] for hour in totals
        }
    return result


@dataclass
class _DatabaseSeries:
    """Real hourly series (local hour) used when ``DATA_SOURCE=database``."""

    occupancy: dict[str, dict[datetime, int]] = field(default_factory=dict)
    co2: dict[str, dict[datetime, float]] = field(default_factory=dict)
    temperature: dict[str, dict[datetime, float]] = field(default_factory=dict)
    humidity: dict[str, dict[datetime, float]] = field(default_factory=dict)


class _CorrelationProvider:
    """Real/synthetic source for occupancy and air quality.

    A value is considered real only for the building/hour where the database
    returned a reading; otherwise the synthetic model is used, so a missing
    sensor does not leave holes in the chart.
    """

    def __init__(self, database: _DatabaseSeries | None) -> None:
        self._database = database

    def occupancy(self, building: BuildingConfig, when: datetime) -> int:
        if self._database is not None:
            value = self._database.occupancy.get(building.id, {}).get(
                _floor_hour_local(when)
            )
            if value is not None:
                return value
        return mock_data.hour_occupancy(building, when)

    def co2(self, building: BuildingConfig, occupancy: int, when: datetime) -> float:
        if self._database is not None:
            value = self._database.co2.get(building.id, {}).get(
                _floor_hour_local(when)
            )
            if value is not None:
                return value
        return mock_data.hour_co2(building, occupancy, when)

    def temperature(
        self, building: BuildingConfig, occupancy: int, when: datetime
    ) -> float:
        if self._database is not None:
            value = self._database.temperature.get(building.id, {}).get(
                _floor_hour_local(when)
            )
            if value is not None:
                return value
        return mock_data.hour_temperature(building, occupancy, when)

    def humidity(self, building: BuildingConfig, occupancy: int, when: datetime) -> float:
        if self._database is not None:
            value = self._database.humidity.get(building.id, {}).get(
                _floor_hour_local(when)
            )
            if value is not None:
                return value
        return mock_data.hour_humidity(building, occupancy, when)


async def _load_provider(
    scope: list[BuildingConfig], start: datetime, end: datetime
) -> _CorrelationProvider:
    if settings.DATA_SOURCE != "database":
        return _CorrelationProvider(None)

    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import database_data
    from app.db.session import AsyncSessionLocal

    space_ids = [
        space.id for building in scope for space in SPACES_BY_BUILDING.get(building.id, [])
    ]
    building_ids = [building.id for building in scope]

    async with AsyncSessionLocal() as session:
        occupancy = await database_data.load_hourly_occupancy(
            session, building_ids, start, end
        )
        co2 = await database_data.load_hourly_space_co2(
            session, space_ids, start, end
        )
        temperature = await database_data.load_hourly_space_temperatures(
            session, space_ids, start, end
        )
        humidity = await database_data.load_hourly_space_humidity(
            session, space_ids, start, end
        )

    return _CorrelationProvider(
        _DatabaseSeries(
            occupancy=occupancy,
            co2=_per_building(scope, co2),
            temperature=_per_building(scope, temperature),
            humidity=_per_building(scope, humidity),
        )
    )


async def build_occupancy_air_quality(
    range_: CorrelationRange, building_id: str
) -> OccupancyAirQualityResponse:
    cache_key: Hashable = ("occupancy-air-quality", range_, building_id)
    hit = _cache.get(cache_key)
    if hit is not None:
        return hit

    async def _compute() -> OccupancyAirQualityResponse:
        now = local_now()
        step = _STEP_HOURS[range_]
        end = _floor_hour(now) + timedelta(hours=1)
        start = end - timedelta(hours=_SPAN_HOURS[range_])
        scope = _scope(building_id)
        capacity_total = sum(building.max_capacity for building in scope)
        provider = await _load_provider(scope, start, end)

        points: list[CorrelationPoint] = []
        cursor = start
        while cursor < end:
            bucket_end = min(cursor + timedelta(hours=step), end)

            occ_acc = 0.0
            co2_acc = 0.0
            temp_acc = 0.0
            hum_acc = 0.0
            hours = 0

            hour_cursor = cursor
            while hour_cursor < bucket_end:
                occ_hour = 0
                co2_num = 0.0
                temp_num = 0.0
                hum_num = 0.0
                weight_sum = 0.0
                for building in scope:
                    occupancy = provider.occupancy(building, hour_cursor)
                    occ_hour += occupancy
                    weight = occupancy + 1.0
                    co2_num += provider.co2(building, occupancy, hour_cursor) * weight
                    temp_num += (
                        provider.temperature(building, occupancy, hour_cursor) * weight
                    )
                    hum_num += (
                        provider.humidity(building, occupancy, hour_cursor) * weight
                    )
                    weight_sum += weight

                occ_acc += occ_hour
                co2_acc += co2_num / weight_sum
                temp_acc += temp_num / weight_sum
                hum_acc += hum_num / weight_sum
                hours += 1
                hour_cursor += timedelta(hours=1)

            hours = max(hours, 1)
            occupancy_avg = occ_acc / hours
            occupancy_pct = (occupancy_avg / capacity_total * 100) if capacity_total else 0.0

            points.append(
                CorrelationPoint(
                    timestamp=cursor,
                    occupancy=round(occupancy_avg),
                    capacity=capacity_total,
                    occupancy_pct=round(occupancy_pct, 1),
                    co2=round(co2_acc / hours, 1),
                    temperature=round(temp_acc / hours, 1),
                    humidity=round(hum_acc / hours, 1),
                )
            )

            cursor = bucket_end

        xs = [point.occupancy for point in points]
        ys = [point.co2 for point in points]
        r, slope, intercept = _regression([float(x) for x in xs], ys)

        sample_size = len(points)
        avg_occupancy = sum(xs) / sample_size if sample_size else 0.0
        avg_pct = (
            sum(point.occupancy_pct for point in points) / sample_size if sample_size else 0.0
        )
        avg_co2 = sum(ys) / sample_size if sample_size else 0.0
        max_co2 = max(ys) if ys else 0.0

        good = sum(1 for value in ys if value < CO2_GOOD_MAX)
        moderate = sum(1 for value in ys if CO2_GOOD_MAX <= value <= CO2_MODERATE_MAX)
        poor = sum(1 for value in ys if value > CO2_MODERATE_MAX)

        def _pct(count: int) -> float:
            return round(count / sample_size * 100, 1) if sample_size else 0.0

        stats_response = CorrelationStats(
            sample_size=sample_size,
            pearson_r=round(r, 3),
            slope=round(slope, 4),
            intercept=round(intercept, 1),
            avg_occupancy=round(avg_occupancy, 1),
            avg_occupancy_pct=round(avg_pct, 1),
            avg_co2=round(avg_co2, 1),
            max_co2=round(max_co2, 1),
            good_pct=_pct(good),
            moderate_pct=_pct(moderate),
            poor_pct=_pct(poor),
        )

        return OccupancyAirQualityResponse(
            range=range_,
            building_id=building_id or ALL_BUILDINGS,
            points=points,
            stats=stats_response,
        )

    value = await _compute()
    _cache.set(cache_key, value)
    return value


def clear_cache() -> None:
    _cache.clear()
