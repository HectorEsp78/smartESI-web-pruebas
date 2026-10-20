"""Business logic for the lighting (luminarias) endpoints.

Electricity is split into lighting (luminarias) and the rest of the loads using
the deterministic model in :mod:`app.services.mock_data`. From that split we
derive:

- the lighting series (with occupancy and daylight for context);
- the ranking of spaces by lighting consumption;
- the "lights on while empty" waste, expressed in kWh and €/year.

The heavy aggregation is computed once per (range, building) and cached.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from app.core.cache import TTLCache
from app.core.config import settings
from app.core.energy_map import SPACES_BY_BUILDING, SPACES_BY_ID
from app.schemas.lighting import (
    LightingBySpaceResponse,
    LightingConsumptionResponse,
    LightingPoint,
    LightingRange,
    LightingSpace,
    LightingWasteResponse,
    LightingWasteSpace,
)
from app.services import mock_data
from app.services.energy_service import (
    ALL_BUILDINGS,
    build_buckets,
    load_occupancy_provider,
    scope_buildings,
)

DAYS_BY_RANGE: dict[LightingRange, int] = {"day": 1, "week": 7, "month": 30, "year": 365}

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS)


@dataclass
class _SpaceAcc:
    total_lighting: float = 0.0
    empty_lighting: float = 0.0
    empty_hours: float = 0.0


@dataclass
class _Accumulated:
    series: list[LightingPoint] = field(default_factory=list)
    lighting_total: float = 0.0
    other_total: float = 0.0
    total: float = 0.0
    building_totals: dict[str, float] = field(default_factory=dict)
    spaces: dict[str, _SpaceAcc] = field(default_factory=dict)


async def _accumulate(range_: LightingRange, building_id: str) -> _Accumulated:
    cache_key = ("lighting", range_, building_id)
    hit = _cache.get(cache_key)
    if hit is not None:
        return hit
    value = await _compute(range_, building_id)
    _cache.set(cache_key, value)
    return value


async def _compute(range_: LightingRange, building_id: str) -> _Accumulated:
    buckets = build_buckets(range_)
    scope = scope_buildings(building_id)
    capacity_total = sum(building.max_capacity for building in scope)
    occupancy_provider = await load_occupancy_provider(
        scope, buckets[0].start, buckets[-1].end
    )

    result = _Accumulated()
    for building in scope:
        result.building_totals[building.id] = 0.0
        for space in SPACES_BY_BUILDING.get(building.id, []):
            result.spaces.setdefault(space.id, _SpaceAcc())

    space_shares = {
        space.id: mock_data.space_lighting_kw_share(space)
        for building in scope
        for space in SPACES_BY_BUILDING.get(building.id, [])
    }

    for bucket in buckets:
        bucket_lighting = bucket_other = bucket_total = 0.0
        bucket_occupancy_hours = 0.0
        bucket_daylight = 0.0
        bucket_hours = (bucket.end - bucket.start) / timedelta(hours=1)

        for building in scope:
            spaces = SPACES_BY_BUILDING.get(building.id, [])
            cursor = bucket.start
            while cursor < bucket.end:
                occupancy = occupancy_provider.hour_occupancy(building, cursor)
                ratio = occupancy / building.max_capacity if building.max_capacity else 0.0
                total = mock_data.hour_energy_kwh(building, cursor)
                fraction = mock_data.lighting_fraction(building, cursor, ratio)
                lighting = total * fraction
                empty = ratio <= mock_data.EMPTY_OCCUPANCY_RATIO

                bucket_lighting += lighting
                bucket_other += total - lighting
                bucket_total += total
                bucket_occupancy_hours += occupancy
                result.building_totals[building.id] += total

                for space in spaces:
                    share = space_shares.get(space.id, 0.0)
                    space_lighting = lighting * share
                    acc = result.spaces[space.id]
                    acc.total_lighting += space_lighting
                    if empty:
                        acc.empty_lighting += space_lighting
                        acc.empty_hours += 1.0
                cursor += timedelta(hours=1)

        # Daylight is a property of the hour, independent of the building.
        cursor = bucket.start
        while cursor < bucket.end:
            bucket_daylight += mock_data.daylight_hours(cursor)
            cursor += timedelta(hours=1)

        occupancy_pct = (
            (bucket_occupancy_hours / bucket_hours) / capacity_total * 100
            if capacity_total and bucket_hours
            else 0.0
        )
        result.series.append(
            LightingPoint(
                timestamp=bucket.start,
                lighting=round(bucket_lighting, 2),
                other=round(bucket_other, 2),
                total=round(bucket_total, 2),
                occupancy_pct=round(occupancy_pct, 1),
                daylight_hours=round(bucket_daylight / bucket_hours, 1) if bucket_hours else 0.0,
            )
        )
        result.lighting_total += bucket_lighting
        result.other_total += bucket_other
        result.total += bucket_total

    return result


async def build_consumption(
    range_: LightingRange, building_id: str
) -> LightingConsumptionResponse:
    data = await _accumulate(range_, building_id)
    return LightingConsumptionResponse(
        range=range_,
        building_id=building_id or ALL_BUILDINGS,
        unit="kWh",
        total=round(data.total, 2),
        lighting_total=round(data.lighting_total, 2),
        other_total=round(data.other_total, 2),
        lighting_share=round(data.lighting_total / data.total, 4) if data.total else 0.0,
        cost_eur=round(data.lighting_total * settings.ENERGY_PRICE_EUR_PER_KWH, 2),
        co2_kg=round(data.lighting_total * settings.CO2_KG_PER_KWH, 2),
        series=data.series,
    )


async def build_by_space(
    range_: LightingRange, building_id: str
) -> LightingBySpaceResponse:
    data = await _accumulate(range_, building_id)
    lighting_total = data.lighting_total

    spaces: list[LightingSpace] = []
    for space_id, acc in data.spaces.items():
        space = SPACES_BY_ID.get(space_id)
        if space is None:
            continue
        building_total = data.building_totals.get(space.building_id, 0.0)
        spaces.append(
            LightingSpace(
                space_id=space.id,
                label=space.label,
                building_id=space.building_id,
                building_label=_building_label(space.building_id),
                kind=space.kind,
                area_m2=space.area_m2,
                lighting=round(acc.total_lighting, 2),
                share_of_lighting=round(acc.total_lighting / lighting_total, 4)
                if lighting_total
                else 0.0,
                share_of_building=round(acc.total_lighting / building_total, 4)
                if building_total
                else 0.0,
                cost_eur=round(acc.total_lighting * settings.ENERGY_PRICE_EUR_PER_KWH, 2),
            )
        )

    spaces.sort(key=lambda item: item.lighting, reverse=True)
    return LightingBySpaceResponse(
        range=range_,
        building_id=building_id or ALL_BUILDINGS,
        unit="kWh",
        lighting_total=round(lighting_total, 2),
        spaces=spaces,
    )


async def build_waste(
    range_: LightingRange, building_id: str
) -> LightingWasteResponse:
    data = await _accumulate(range_, building_id)
    days = DAYS_BY_RANGE[range_]
    price = settings.ENERGY_PRICE_EUR_PER_KWH

    spaces: list[LightingWasteSpace] = []
    waste_total = 0.0
    for space_id, acc in data.spaces.items():
        space = SPACES_BY_ID.get(space_id)
        if space is None:
            continue
        waste_total += acc.empty_lighting
        cost = acc.empty_lighting * price
        spaces.append(
            LightingWasteSpace(
                space_id=space.id,
                label=space.label,
                building_id=space.building_id,
                building_label=_building_label(space.building_id),
                kind=space.kind,
                total_lighting=round(acc.total_lighting, 2),
                empty_lighting=round(acc.empty_lighting, 2),
                waste_pct=round(acc.empty_lighting / acc.total_lighting, 4)
                if acc.total_lighting
                else 0.0,
                cost_eur=round(cost, 2),
                annualized_cost_eur=round(cost * (365.0 / days), 2),
                empty_hours=round(acc.empty_hours, 0),
                avg_daily_empty_cost=round(cost / days, 2) if days else 0.0,
            )
        )

    spaces.sort(key=lambda item: item.empty_lighting, reverse=True)
    waste_cost = waste_total * price
    return LightingWasteResponse(
        range=range_,
        building_id=building_id or ALL_BUILDINGS,
        total_lighting=round(data.lighting_total, 2),
        waste_lighting=round(waste_total, 2),
        waste_share=round(waste_total / data.lighting_total, 4) if data.lighting_total else 0.0,
        waste_cost_eur=round(waste_cost, 2),
        annualized_cost_eur=round(waste_cost * (365.0 / days), 2),
        avg_daily_empty_cost=round(waste_cost / days, 2) if days else 0.0,
        spaces=spaces,
    )


def _building_label(building_id: str) -> str:
    from app.core.energy_map import BUILDINGS_BY_ID

    building = BUILDINGS_BY_ID.get(building_id)
    return building.label if building else building_id


def clear_cache() -> None:
    _cache.clear()
