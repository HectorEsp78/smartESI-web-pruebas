"""Business logic for the energy statistics.

- ``build_consumption``  → one aggregated series for the big line/area chart.
- ``build_by_building``  → totals per building + per space for the comparison chart.

The heavy aggregation is cached with a short TTL (see ``app.core.cache``).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Hashable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.core.cache import TTLCache
from app.core.clock import local_now, local_tz
from app.core.config import settings
from app.core.energy_map import (
    BUILDINGS,
    BUILDINGS_AREA_M2,
    BUILDINGS_BY_ID,
    SPACES_BY_BUILDING,
    BuildingConfig,
)
from app.db.entity_map import SITE_ENERGY_KEY
from app.schemas.energy import (
    BuildingEfficiency,
    BuildingShare,
    EnergyBreakdownPoint,
    EnergyBreakdownResponse,
    EnergyByBuildingResponse,
    EnergyComparePoint,
    EnergyCompareResponse,
    EnergyConsumptionResponse,
    EnergyEfficiencyResponse,
    EnergyMetric,
    EnergyPoint,
    EnergyRange,
    SpaceEfficiency,
    SpaceShare,
)
from app.services import mock_data

RANGES: tuple[EnergyRange, ...] = ("day", "week", "month", "year")
METRICS: tuple[EnergyMetric, ...] = ("kwh", "cost", "co2")
ALL_BUILDINGS = "all"

UNIT_BY_METRIC: dict[EnergyMetric, str] = {
    "kwh": "kWh",
    "cost": "€",
    "co2": "kg CO₂",
}

GRANULARITY_BY_RANGE: dict[EnergyRange, str] = {
    "day": "hour",
    "week": "day",
    "month": "day",
    "year": "month",
}

_RANGE_HOURS: dict[EnergyRange, int] = {
    "day": 24,
    "week": 7 * 24,
    "month": 30 * 24,
    "year": 365 * 24,
}

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS)
_cache_database = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS)


@dataclass(frozen=True)
class _Bucket:
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


def build_buckets(range_: EnergyRange) -> list[_Bucket]:
    now = local_now()

    if range_ == "day":
        last = _floor_hour(now)
        return [
            _Bucket(last - timedelta(hours=i), last - timedelta(hours=i) + timedelta(hours=1))
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
            _Bucket(_add_months(last_month, -i), _add_months(last_month, -i + 1))
            for i in range(11, -1, -1)
        ]

    return [
        _Bucket(last - timedelta(days=i), last - timedelta(days=i) + timedelta(days=1))
        for i in range(days - 1, -1, -1)
    ]


def scope_buildings(building_id: str | None) -> list[BuildingConfig]:
    if building_id in (None, "", ALL_BUILDINGS):
        return list(BUILDINGS)
    building = BUILDINGS_BY_ID.get(building_id)
    return [building] if building else []


def _is_all_scope(scope: list[BuildingConfig]) -> bool:
    return {building.id for building in scope} == {building.id for building in BUILDINGS}


class _EnergyProvider:
    """Hourly kWh source: the real database series or the synthetic generator.

    The synthetic path keeps working exactly as before; the database path just
    looks the hour up in a preloaded ``{key: {local_hour: kwh}}`` dict. The
    site-wide meter (``SITE_ENERGY_KEY``) is kept separate from the partial
    building submeters and is only used when the scope is "all buildings".
    """

    def __init__(self, database: dict[str, dict[datetime, float]] | None) -> None:
        self._database = database

    def hour_kwh(self, building: BuildingConfig, when: datetime) -> float:
        if self._database is None:
            return mock_data.hour_energy_kwh(building, when)
        return self._database.get(building.id, {}).get(_floor_hour_local(when), 0.0)

    def uses_site_meter(self, scope: list[BuildingConfig]) -> bool:
        return (
            self._database is not None
            and SITE_ENERGY_KEY in self._database
            and _is_all_scope(scope)
        )

    def hour_total(self, scope: list[BuildingConfig], when: datetime) -> float:
        """Consumption of the scope: site meter for all, submeters otherwise."""
        if self.uses_site_meter(scope):
            return self._database[SITE_ENERGY_KEY].get(_floor_hour_local(when), 0.0)
        return sum(self.hour_kwh(building, when) for building in scope)


class _OccupancyProvider:
    """Hourly people count: the real counters or the synthetic model."""

    def __init__(self, database: dict[str, dict[datetime, int]] | None) -> None:
        self._database = database

    def hour_occupancy(self, building: BuildingConfig, when: datetime) -> int:
        if self._database is not None:
            value = self._database.get(building.id, {}).get(_floor_hour_local(when))
            if value is not None:
                return value
        return mock_data.hour_occupancy(building, when)


async def _load_provider(
    scope: list[BuildingConfig],
    start: datetime,
    end: datetime,
    *,
    include_site: bool = False,
) -> _EnergyProvider:
    """Build the provider for a window, reading the real DB when configured."""
    if settings.DATA_SOURCE != "database":
        return _EnergyProvider(None)

    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import database_data
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        data = await database_data.load_hourly_energy(
            session,
            [building.id for building in scope],
            start,
            end,
            include_site=include_site,
        )
    return _EnergyProvider(data)


async def load_occupancy_provider(
    scope: list[BuildingConfig], start: datetime, end: datetime
) -> _OccupancyProvider:
    """Real occupancy counters when available, synthetic model otherwise."""
    if settings.DATA_SOURCE != "database":
        return _OccupancyProvider(None)

    from app.db import database_data
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        data = await database_data.load_hourly_occupancy(
            session, [building.id for building in scope], start, end
        )
    return _OccupancyProvider(data)


async def _cached(cache: TTLCache, key: Hashable, factory: Callable[[], Awaitable[Any]]) -> Any:
    """Await-able ``TTLCache.get_or_set`` (the factory has to await the DB)."""
    hit = cache.get(key)
    if hit is not None:
        return hit
    value = await factory()
    cache.set(key, value)
    return value


def _sum_energy(provider: _EnergyProvider, building: BuildingConfig, start: datetime, end: datetime) -> float:
    total = 0.0
    cursor = start
    while cursor < end:
        total += provider.hour_kwh(building, cursor)
        cursor += timedelta(hours=1)
    return total


def _sum_scope(
    provider: _EnergyProvider,
    scope: list[BuildingConfig],
    start: datetime,
    end: datetime,
) -> float:
    """Consumption of a scope, using the site meter when the scope is all."""
    total = 0.0
    cursor = start
    while cursor < end:
        total += provider.hour_total(scope, cursor)
        cursor += timedelta(hours=1)
    return total


def _convert(kwh: float, metric: EnergyMetric) -> float:
    if metric == "cost":
        return kwh * settings.ENERGY_PRICE_EUR_PER_KWH
    if metric == "co2":
        return kwh * settings.CO2_KG_PER_KWH
    return kwh


def _space_weights(building_id: str, range_: EnergyRange) -> dict[str, float]:
    """Normalised per-space share of a building, with a stable per-range jitter."""
    spaces = SPACES_BY_BUILDING.get(building_id, [])
    raw: dict[str, float] = {}
    for space in spaces:
        factor = 1.0 + 0.30 * mock_data.stable_noise("space", space.id, range_, amplitude=1.0)
        raw[space.id] = max(0.01, space.weight * factor)

    total = sum(raw.values())
    if total <= 0:
        return {}
    return {space_id: value / total for space_id, value in raw.items()}


async def build_consumption(
    range_: EnergyRange, building_id: str, metric: EnergyMetric
) -> EnergyConsumptionResponse:
    cache_key = ("consumption", range_, building_id, metric)

    async def _compute() -> EnergyConsumptionResponse:
        buckets = build_buckets(range_)
        scope = scope_buildings(building_id)
        provider = await _load_provider(
            scope,
            buckets[0].start,
            buckets[-1].end,
            include_site=_is_all_scope(scope),
        )

        series: list[EnergyPoint] = []
        for bucket in buckets:
            kwh = _sum_scope(provider, scope, bucket.start, bucket.end)
            series.append(
                EnergyPoint(timestamp=bucket.start, value=round(_convert(kwh, metric), 2))
            )

        total = round(sum(point.value for point in series), 2)
        average = round(total / len(series), 2) if series else 0.0
        peak = max(series, key=lambda point: point.value) if series else None

        return EnergyConsumptionResponse(
            range=range_,
            metric=metric,
            unit=UNIT_BY_METRIC[metric],
            granularity=GRANULARITY_BY_RANGE[range_],
            building_id=building_id or ALL_BUILDINGS,
            total=total,
            average=average,
            peak=peak,
            series=series,
        )

    return await _cached(_cache, cache_key, _compute)


async def build_by_building(range_: EnergyRange, metric: EnergyMetric) -> EnergyByBuildingResponse:
    cache_key = ("by-building", range_, metric)

    async def _compute() -> EnergyByBuildingResponse:
        buckets = build_buckets(range_)
        start = buckets[0].start
        end = buckets[-1].end
        scope = list(BUILDINGS)
        provider = await _load_provider(scope, start, end, include_site=True)

        building_kwh = {
            building.id: _sum_energy(provider, building, start, end) for building in BUILDINGS
        }
        submetered_kwh = sum(building_kwh.values())
        total_kwh = _sum_scope(provider, scope, start, end)
        if total_kwh <= 0:
            total_kwh = submetered_kwh
        unmetered_kwh = max(0.0, total_kwh - submetered_kwh)
        coverage = submetered_kwh / total_kwh if total_kwh else 0.0

        buildings: list[BuildingShare] = []
        spaces: list[SpaceShare] = []

        for building in BUILDINGS:
            building_kwh_value = building_kwh[building.id]
            buildings.append(
                BuildingShare(
                    building_id=building.id,
                    label=building.label,
                    total=round(_convert(building_kwh_value, metric), 2),
                    share=round(building_kwh_value / total_kwh, 4) if total_kwh else 0.0,
                )
            )

            weights = _space_weights(building.id, range_)
            for space in SPACES_BY_BUILDING.get(building.id, []):
                space_kwh = building_kwh_value * weights.get(space.id, 0.0)
                spaces.append(
                    SpaceShare(
                        space_id=space.id,
                        label=space.label,
                        building_id=building.id,
                        building_label=building.label,
                        kind=space.kind,
                        total=round(_convert(space_kwh, metric), 2),
                        share=round(space_kwh / total_kwh, 4) if total_kwh else 0.0,
                    )
                )

        buildings.sort(key=lambda item: item.total, reverse=True)
        spaces.sort(key=lambda item: item.total, reverse=True)

        return EnergyByBuildingResponse(
            range=range_,
            metric=metric,
            unit=UNIT_BY_METRIC[metric],
            total=round(_convert(total_kwh, metric), 2),
            submetered_total=round(_convert(submetered_kwh, metric), 2),
            unmetered_total=round(_convert(unmetered_kwh, metric), 2),
            coverage=round(coverage, 4),
            buildings=buildings,
            spaces=spaces,
        )

    return await _cached(_cache_database, cache_key, _compute)


def _is_active_hour(when: datetime) -> bool:
    """Working hours: weekdays from 7:00 to 21:00 (local time)."""
    local = when.astimezone(local_tz())
    hour = local.hour + local.minute / 60.0
    return local.weekday() < 5 and 7.0 <= hour < 21.0


def _split_energy(
    provider: _EnergyProvider,
    occupancy_provider: _OccupancyProvider,
    scope: list[BuildingConfig],
    start: datetime,
    end: datetime,
) -> tuple[float, float, float]:
    """Return (base_kwh, activity_kwh, lighting_kwh) for a scope over a span.

    ``base`` is the load outside working hours (nights/weekends) and ``activity``
    the load during working hours. ``lighting`` is the part of the total that the
    model attributes to luminarias (still estimated while there is no real
    lighting submetering).

    When the site meter is available, the total comes from it. The lighting
    fraction is then a capacity-weighted average of the per-building synthetic
    fractions, evaluated at the aggregate occupancy ratio.
    """
    base = activity = lighting = 0.0
    use_site = provider.uses_site_meter(scope)
    capacity = sum(building.max_capacity for building in scope)
    cursor = start
    while cursor < end:
        if use_site:
            occupancy = sum(
                occupancy_provider.hour_occupancy(building, cursor) for building in scope
            )
            ratio = occupancy / capacity if capacity else 0.0
            total = provider.hour_total(scope, cursor)
            if capacity:
                fraction = sum(
                    building.max_capacity
                    * mock_data.lighting_fraction(building, cursor, ratio)
                    for building in scope
                ) / capacity
            else:
                fraction = 0.0
            lighting += total * fraction
            if _is_active_hour(cursor):
                activity += total
            else:
                base += total
        else:
            for building in scope:
                occupancy = occupancy_provider.hour_occupancy(building, cursor)
                ratio = occupancy / building.max_capacity if building.max_capacity else 0.0
                total = provider.hour_kwh(building, cursor)
                lighting += total * mock_data.lighting_fraction(building, cursor, ratio)
                if _is_active_hour(cursor):
                    activity += total
                else:
                    base += total
        cursor += timedelta(hours=1)
    return base, activity, lighting


async def build_breakdown(range_: EnergyRange, building_id: str) -> EnergyBreakdownResponse:
    cache_key = ("breakdown", range_, building_id)

    async def _compute() -> EnergyBreakdownResponse:
        buckets = build_buckets(range_)
        scope = scope_buildings(building_id)
        provider = await _load_provider(
            scope,
            buckets[0].start,
            buckets[-1].end,
            include_site=_is_all_scope(scope),
        )
        occupancy_provider = await load_occupancy_provider(
            scope, buckets[0].start, buckets[-1].end
        )

        series: list[EnergyBreakdownPoint] = []
        for bucket in buckets:
            base, activity, lighting = _split_energy(
                provider, occupancy_provider, scope, bucket.start, bucket.end
            )
            total = base + activity
            series.append(
                EnergyBreakdownPoint(
                    timestamp=bucket.start,
                    base=round(base, 2),
                    activity=round(activity, 2),
                    lighting=round(lighting, 2),
                    other=round(total - lighting, 2),
                )
            )

        base_total = round(sum(point.base for point in series), 2)
        activity_total = round(sum(point.activity for point in series), 2)
        lighting_total = round(sum(point.lighting for point in series), 2)
        other_total = round(base_total + activity_total - lighting_total, 2)
        total = round(base_total + activity_total, 2)

        return EnergyBreakdownResponse(
            range=range_,
            unit=UNIT_BY_METRIC["kwh"],
            building_id=building_id or ALL_BUILDINGS,
            total=total,
            base_total=base_total,
            activity_total=activity_total,
            lighting_total=lighting_total,
            other_total=other_total,
            base_share=round(base_total / total, 4) if total else 0.0,
            lighting_share=round(lighting_total / total, 4) if total else 0.0,
            series=series,
        )

    return await _cached(_cache, cache_key, _compute)


def _shift_start(start: datetime, range_: EnergyRange) -> datetime:
    if range_ == "day":
        return start - timedelta(hours=24)
    if range_ == "week":
        return start - timedelta(days=7)
    if range_ == "month":
        return start - timedelta(days=30)
    return _add_months(start, -12)  # year: same month of the previous year


async def build_compare(
    range_: EnergyRange, building_id: str, metric: EnergyMetric
) -> EnergyCompareResponse:
    cache_key = ("compare", range_, building_id, metric)

    async def _compute() -> EnergyCompareResponse:
        buckets = build_buckets(range_)
        scope = scope_buildings(building_id)
        # The provider must cover the previous period too (up to 12 months back).
        provider = await _load_provider(
            scope,
            _shift_start(buckets[0].start, range_),
            buckets[-1].end,
            include_site=_is_all_scope(scope),
        )

        points: list[EnergyComparePoint] = []
        current_total = previous_total = 0.0
        for bucket in buckets:
            current = _sum_scope(provider, scope, bucket.start, bucket.end)
            previous_start = _shift_start(bucket.start, range_)
            previous_end = previous_start + (bucket.end - bucket.start)
            previous = _sum_scope(provider, scope, previous_start, previous_end)
            current_total += current
            previous_total += previous
            points.append(
                EnergyComparePoint(
                    timestamp=bucket.start,
                    current=round(_convert(current, metric), 2),
                    previous=round(_convert(previous, metric), 2),
                )
            )

        delta_pct = (
            (current_total - previous_total) / previous_total * 100 if previous_total else 0.0
        )

        return EnergyCompareResponse(
            range=range_,
            metric=metric,
            unit=UNIT_BY_METRIC[metric],
            building_id=building_id or ALL_BUILDINGS,
            current_total=round(_convert(current_total, metric), 2),
            previous_total=round(_convert(previous_total, metric), 2),
            delta_pct=round(delta_pct, 1),
            series=points,
        )

    return await _cached(_cache, cache_key, _compute)


def _occupancy_person_hours(
    occupancy_provider: _OccupancyProvider,
    building: BuildingConfig,
    start: datetime,
    end: datetime,
) -> float:
    total = 0.0
    cursor = start
    while cursor < end:
        total += occupancy_provider.hour_occupancy(building, cursor)
        cursor += timedelta(hours=1)
    return total


async def build_efficiency(range_: EnergyRange) -> EnergyEfficiencyResponse:
    cache_key = ("efficiency", range_)

    async def _compute() -> EnergyEfficiencyResponse:
        buckets = build_buckets(range_)
        start = buckets[0].start
        end = buckets[-1].end
        scope = list(BUILDINGS)
        provider = await _load_provider(scope, start, end, include_site=True)
        occupancy_provider = await load_occupancy_provider(scope, start, end)

        buildings: list[BuildingEfficiency] = []
        spaces: list[SpaceEfficiency] = []
        submetered_kwh = 0.0

        for building in BUILDINGS:
            building_kwh = _sum_energy(provider, building, start, end)
            building_occupancy_hours = _occupancy_person_hours(
                occupancy_provider, building, start, end
            )
            area = BUILDINGS_AREA_M2[building.id]
            submetered_kwh += building_kwh

            buildings.append(
                BuildingEfficiency(
                    building_id=building.id,
                    label=building.label,
                    area_m2=area,
                    total=round(building_kwh, 2),
                    cost_eur=round(_convert(building_kwh, "cost"), 2),
                    occupancy_hours=round(building_occupancy_hours, 0),
                    kwh_per_m2=round(building_kwh / area, 2) if area else 0.0,
                    kwh_per_person_hour=round(
                        building_kwh / building_occupancy_hours, 3
                    )
                    if building_occupancy_hours
                    else 0.0,
                    share=0.0,
                )
            )

            weights = _space_weights(building.id, range_)
            area_total = BUILDINGS_AREA_M2[building.id] or 1.0
            for space in SPACES_BY_BUILDING.get(building.id, []):
                space_kwh = building_kwh * weights.get(space.id, 0.0)
                space_occupancy_hours = building_occupancy_hours * (space.area_m2 / area_total)
                spaces.append(
                    SpaceEfficiency(
                        space_id=space.id,
                        label=space.label,
                        building_id=building.id,
                        building_label=building.label,
                        kind=space.kind,
                        area_m2=space.area_m2,
                        total=round(space_kwh, 2),
                        cost_eur=round(_convert(space_kwh, "cost"), 2),
                        occupancy_hours=round(space_occupancy_hours, 0),
                        kwh_per_m2=round(space_kwh / space.area_m2, 2) if space.area_m2 else 0.0,
                        kwh_per_person_hour=round(space_kwh / space_occupancy_hours, 3)
                        if space_occupancy_hours
                        else 0.0,
                        share=0.0,
                    )
                )

        total_kwh = _sum_scope(provider, scope, start, end)
        if total_kwh <= 0:
            total_kwh = submetered_kwh
        unmetered_kwh = max(0.0, total_kwh - submetered_kwh)
        coverage = submetered_kwh / total_kwh if total_kwh else 0.0

        for building in buildings:
            building.share = round(building.total / total_kwh, 4) if total_kwh else 0.0
        for space in spaces:
            space.share = round(space.total / total_kwh, 4) if total_kwh else 0.0

        buildings.sort(key=lambda item: item.kwh_per_m2, reverse=True)
        spaces.sort(key=lambda item: item.kwh_per_m2, reverse=True)
        total_area = sum(BUILDINGS_AREA_M2[building.id] for building in BUILDINGS)

        return EnergyEfficiencyResponse(
            range=range_,
            unit=UNIT_BY_METRIC["kwh"],
            total=round(total_kwh, 2),
            submetered_total=round(submetered_kwh, 2),
            unmetered_total=round(unmetered_kwh, 2),
            coverage=round(coverage, 4),
            avg_kwh_per_m2=round(total_kwh / total_area, 2) if total_area else 0.0,
            buildings=buildings,
            spaces=spaces,
        )

    return await _cached(_cache, cache_key, _compute)


def clear_cache() -> None:
    _cache.clear()
    _cache_database.clear()
