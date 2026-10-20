"""Business logic for the climate endpoints (gas, degree-days and valves).

With ``DATA_SOURCE=mock`` the synthetic model gives every space a heating valve
and an indoor temperature. With ``DATA_SOURCE=database`` the gas, the outdoor
temperature and the indoor temperatures come from the real Home Assistant data;
the valves (which have no entity in the recorder DB yet) and the occupancy keep
using the model. From that we compute, per bucket:

- gas consumed, heating degree-days and the outdoor/indoor temperature;
- the share of valves that are open (demand for heat).

And, per space over the whole range:

- the valve/temperature relation (is the room reaching the setpoint?);
- the gas burnt while the space is empty (calefacción de aulas vacías).

Everything is computed once per (range, building) and cached.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.core.cache import TTLCache
from app.core.clock import local_tz
from app.core.config import settings
from app.core.energy_map import BUILDINGS_BY_ID, SPACES_BY_BUILDING, SPACES_BY_ID
from app.schemas.climate import (
    ClimateRange,
    EmptySpace,
    EmptySpacesResponse,
    GasPoint,
    GasResponse,
    GasStats,
    ValvePoint,
    ValveSpace,
    ValvesResponse,
)
from app.services import mock_data, stats
from app.services.energy_service import ALL_BUILDINGS, build_buckets, scope_buildings

_SETPOINT_TOLERANCE_C = 1.0

# Climate reads can touch a year of per-space ``states`` rows, which is slow on
# the recorder DB; keep the result cached for a bit longer than the default TTL.
_cache = TTLCache(ttl_seconds=max(settings.STATS_CACHE_TTL_SECONDS, 300))


@dataclass
class _SpaceAcc:
    temp_sum: float = 0.0
    outdoor_sum: float = 0.0
    sample_hours: int = 0
    valve_open_hours: int = 0
    below_setpoint_hours: int = 0
    unoccupied_temp_sum: float = 0.0
    unoccupied_hours: int = 0
    heated_unoccupied_hours: int = 0
    unoccupied_gas: float = 0.0


@dataclass
class _Acc:
    series: list[GasPoint] = field(default_factory=list)
    spaces: dict[str, _SpaceAcc] = field(default_factory=dict)
    total_gas: float = 0.0
    total_degree_days: float = 0.0
    outdoor_sum: float = 0.0
    indoor_sum: float = 0.0
    hours: float = 0.0
    valve_open_count: float = 0.0
    valve_sample_count: float = 0.0


@dataclass(frozen=True)
class _DatabaseSeries:
    """Real hourly series (keyed by local hour) used when DATA_SOURCE=database."""

    outdoor: dict[datetime, float]
    gas: dict[datetime, float]
    space_temps: dict[str, dict[datetime, float]]
    occupancy: dict[str, dict[datetime, int]]


class _ClimateProvider:
    """Real/synthetic source for outdoor temperature, gas and indoor temps.

    Gas is site-wide in the real installation (there is a single meter), so the
    caller only loads it for the ``all`` scope; for a specific building the gas
    series is empty and the gas values are 0.
    """

    def __init__(self, database: _DatabaseSeries | None) -> None:
        self._database = database

    def outdoor_temperature(self, when: datetime) -> float | None:
        if self._database is None:
            return mock_data.outdoor_temperature(when)
        return self._database.outdoor.get(_floor_hour_local(when))

    def space_temperature(self, space_id: str, when: datetime) -> float | None:
        if self._database is None:
            return None  # signals the caller to use the synthetic model
        return self._database.space_temps.get(space_id, {}).get(_floor_hour_local(when))

    def gas_kwh(self, when: datetime, scope: list[Any]) -> float:
        if self._database is None:
            return sum(mock_data.hour_gas_kwh(building, when) for building in scope)
        return self._database.gas.get(_floor_hour_local(when), 0.0)

    def building_occupancy(self, building: Any, when: datetime) -> int | None:
        """People inside the building, or ``None`` to keep using the model."""
        if self._database is None:
            return None
        return self._database.occupancy.get(building.id, {}).get(
            _floor_hour_local(when)
        )


def _floor_hour_local(value: datetime) -> datetime:
    return value.astimezone(local_tz()).replace(minute=0, second=0, microsecond=0)


def _scale_occupancy(
    occupancy_map: dict[str, int], target: int | None
) -> dict[str, int]:
    """Rescale a per-space occupancy map to the real building total.

    The door counters only know how many people are inside the building, not
    which room they are in. The synthetic model provides the relative
    distribution, which is rescaled so its sum matches the real total (0 marks
    every room as empty). ``None`` keeps the original map.
    """
    if target is None:
        return occupancy_map
    if target <= 0:
        return {space_id: 0 for space_id in occupancy_map}

    total = sum(occupancy_map.values())
    if total <= 0:
        return occupancy_map
    scaled = {
        space_id: int(round(value * target / total))
        for space_id, value in occupancy_map.items()
    }
    # Rounding can lose/gain a person; keep the building total exact by fixing
    # the largest room.
    if scaled:
        largest = max(scaled, key=scaled.get)
        scaled[largest] += target - sum(scaled.values())
        scaled[largest] = max(0, scaled[largest])
    return scaled


async def _load_provider(
    scope: list[Any],
    building_id: str,
    start: datetime,
    end: datetime,
) -> _ClimateProvider:
    if settings.DATA_SOURCE != "database":
        return _ClimateProvider(None)

    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import database_data
    from app.db.session import AsyncSessionLocal

    space_ids = [
        space.id for building in scope for space in SPACES_BY_BUILDING.get(building.id, [])
    ]

    async with AsyncSessionLocal() as session:
        outdoor = await database_data.load_hourly_outdoor_temperature(session, start, end)
        space_temps = await database_data.load_hourly_space_temperatures(
            session, space_ids, start, end
        )
        occupancy = await database_data.load_hourly_occupancy(
            session, [building.id for building in scope], start, end
        )
        if building_id in (None, "", ALL_BUILDINGS):
            gas = await database_data.load_hourly_gas(session, start, end)
        else:
            gas = {}

    return _ClimateProvider(
        _DatabaseSeries(
            outdoor=outdoor,
            gas=gas,
            space_temps=space_temps,
            occupancy=occupancy,
        )
    )


async def _accumulate(range_: ClimateRange, building_id: str) -> _Acc:
    cache_key = ("climate", range_, building_id)
    hit = _cache.get(cache_key)
    if hit is not None:
        return hit
    value = await _compute(range_, building_id)
    _cache.set(cache_key, value)
    return value


async def _compute(range_: ClimateRange, building_id: str) -> _Acc:
    buckets = build_buckets(range_)
    scope = scope_buildings(building_id)
    base_temp = settings.HEATING_BASE_TEMPERATURE_C
    provider = await _load_provider(scope, building_id, buckets[0].start, buckets[-1].end)

    result = _Acc()
    for building in scope:
        for space in SPACES_BY_BUILDING.get(building.id, []):
            result.spaces.setdefault(space.id, _SpaceAcc())

    for bucket in buckets:
        bucket_gas = bucket_degree = 0.0
        bucket_outdoor_sum = bucket_indoor_sum = 0.0
        bucket_valve_open = bucket_valve_sample = 0.0
        bucket_hours = (bucket.end - bucket.start) / timedelta(hours=1)

        cursor = bucket.start
        while cursor < bucket.end:
            outdoor = provider.outdoor_temperature(cursor)
            if outdoor is None:
                outdoor = mock_data.outdoor_temperature(cursor)
            bucket_degree += max(0.0, base_temp - outdoor)
            bucket_outdoor_sum += outdoor

            # Gather (space, building, valve, occupancy, temperature) for the hour.
            details = []
            for building in scope:
                occupancy_map = mock_data.building_space_occupancy(building, cursor)
                occupancy_map = _scale_occupancy(
                    occupancy_map, provider.building_occupancy(building, cursor)
                )
                for space in SPACES_BY_BUILDING.get(building.id, []):
                    valve_open = mock_data.space_valve_open(space, building, cursor)
                    occupancy = occupancy_map.get(space.id, 0)
                    temperature = provider.space_temperature(space.id, cursor)
                    if temperature is None:
                        temperature = mock_data.space_temperature(
                            building, space, cursor, occupancy
                        )
                    details.append((space, building, valve_open, occupancy, temperature))

            gas = provider.gas_kwh(cursor, scope)
            bucket_gas += gas
            open_count = sum(1 for _, _, valve_open, _, _ in details if valve_open)
            gas_per_open = gas / open_count if open_count else 0.0
            bucket_valve_open += open_count
            bucket_valve_sample += len(details)

            if details:
                bucket_indoor_sum += sum(item[4] for item in details) / len(details)

            # Second pass: accumulate per-space statistics (gas share known now).
            for space, building, valve_open, occupancy, temperature in details:
                acc = result.spaces[space.id]
                acc.sample_hours += 1
                acc.temp_sum += temperature
                acc.outdoor_sum += outdoor
                if valve_open:
                    acc.valve_open_hours += 1
                if temperature < building.setpoint_c - _SETPOINT_TOLERANCE_C:
                    acc.below_setpoint_hours += 1

                if occupancy <= 0:
                    acc.unoccupied_hours += 1
                    acc.unoccupied_temp_sum += temperature
                    if valve_open:
                        acc.heated_unoccupied_hours += 1
                        acc.unoccupied_gas += gas_per_open

            cursor += timedelta(hours=1)

        result.series.append(
            GasPoint(
                timestamp=bucket.start,
                gas=round(bucket_gas, 2),
                degree_days=round(bucket_degree / 24.0, 2),
                outdoor_temperature=round(bucket_outdoor_sum / bucket_hours, 1)
                if bucket_hours
                else 0.0,
                indoor_temperature=round(bucket_indoor_sum / bucket_hours, 1)
                if bucket_hours
                else 0.0,
                valve_open_pct=round(bucket_valve_open / bucket_valve_sample * 100, 1)
                if bucket_valve_sample
                else 0.0,
            )
        )
        result.total_gas += bucket_gas
        result.total_degree_days += bucket_degree / 24.0
        result.outdoor_sum += bucket_outdoor_sum
        result.indoor_sum += bucket_indoor_sum
        result.hours += bucket_hours
        result.valve_open_count += bucket_valve_open
        result.valve_sample_count += bucket_valve_sample

    return result


async def build_gas(range_: ClimateRange, building_id: str) -> GasResponse:
    data = await _accumulate(range_, building_id)

    gas_values = [point.gas for point in data.series]
    degree_values = [point.degree_days for point in data.series]
    correlation = stats.least_squares(degree_values, gas_values).r if len(gas_values) > 1 else 0.0

    gas_per_degree_day = (
        data.total_gas / data.total_degree_days if data.total_degree_days else 0.0
    )
    avg_outdoor = data.outdoor_sum / data.hours if data.hours else 0.0
    avg_indoor = data.indoor_sum / data.hours if data.hours else 0.0
    avg_valve = (
        data.valve_open_count / data.valve_sample_count * 100 if data.valve_sample_count else 0.0
    )

    return GasResponse(
        range=range_,
        building_id=building_id or ALL_BUILDINGS,
        unit="kWh",
        stats=GasStats(
            total_gas=round(data.total_gas, 2),
            cost_eur=round(data.total_gas * settings.GAS_PRICE_EUR_PER_KWH, 2),
            co2_kg=round(data.total_gas * settings.GAS_CO2_KG_PER_KWH, 2),
            total_degree_days=round(data.total_degree_days, 1),
            gas_per_degree_day=round(gas_per_degree_day, 3),
            correlation_degree_days=correlation,
            avg_outdoor_temperature=round(avg_outdoor, 1),
            avg_indoor_temperature=round(avg_indoor, 1),
            avg_valve_open_pct=round(avg_valve, 1),
        ),
        series=data.series,
    )


async def build_valves(range_: ClimateRange, building_id: str) -> ValvesResponse:
    data = await _accumulate(range_, building_id)
    scope = scope_buildings(building_id)
    setpoint = scope[0].setpoint_c if scope else 21.0

    spaces: list[ValveSpace] = []
    for space_id, acc in data.spaces.items():
        space = SPACES_BY_ID.get(space_id)
        if space is None or acc.sample_hours == 0:
            continue
        building = BUILDINGS_BY_ID.get(space.building_id)
        space_setpoint = building.setpoint_c if building else setpoint
        avg_temperature = acc.temp_sum / acc.sample_hours
        deviation = avg_temperature - space_setpoint
        health = mock_data.valve_health(space)

        if health < -mock_data.VALVE_STUCK_THRESHOLD:
            status = "fria"
        elif health > mock_data.VALVE_STUCK_THRESHOLD:
            status = "valvula_abierta"
        else:
            status = "ok"

        spaces.append(
            ValveSpace(
                space_id=space.id,
                label=space.label,
                building_id=space.building_id,
                kind=space.kind,
                setpoint_c=space_setpoint,
                avg_temperature=round(avg_temperature, 1),
                avg_outdoor_temperature=round(acc.outdoor_sum / acc.sample_hours, 1),
                valve_open_pct=round(acc.valve_open_hours / acc.sample_hours * 100, 1),
                sample_hours=acc.sample_hours,
                hours_valve_open=acc.valve_open_hours,
                hours_below_setpoint=acc.below_setpoint_hours,
                deviation_c=round(deviation, 1),
                status=status,
            )
        )

    spaces.sort(key=lambda item: item.deviation_c)

    series = [
        ValvePoint(
            timestamp=point.timestamp,
            valve_open_pct=point.valve_open_pct,
            avg_temperature=point.indoor_temperature,
            setpoint_c=setpoint,
            outdoor_temperature=point.outdoor_temperature,
        )
        for point in data.series
    ]

    return ValvesResponse(
        range=range_,
        building_id=building_id or ALL_BUILDINGS,
        setpoint_c=setpoint,
        series=series,
        spaces=spaces,
    )


async def build_empty_spaces(range_: ClimateRange, building_id: str) -> EmptySpacesResponse:
    data = await _accumulate(range_, building_id)
    days = {"day": 1, "week": 7, "month": 30, "year": 365}[range_]
    price = settings.GAS_PRICE_EUR_PER_KWH

    spaces: list[EmptySpace] = []
    total_gas = total_cost = total_hours = 0.0
    for space_id, acc in data.spaces.items():
        space = SPACES_BY_ID.get(space_id)
        if space is None or acc.sample_hours == 0:
            continue
        building = BUILDINGS_BY_ID.get(space.building_id)
        avg_unoccupied = (
            acc.unoccupied_temp_sum / acc.unoccupied_hours if acc.unoccupied_hours else 0.0
        )
        cost = acc.unoccupied_gas * price
        total_gas += acc.unoccupied_gas
        total_cost += cost
        total_hours += acc.heated_unoccupied_hours
        spaces.append(
            EmptySpace(
                space_id=space.id,
                label=space.label,
                building_id=space.building_id,
                building_label=building.label if building else space.building_id,
                kind=space.kind,
                avg_temperature_unoccupied=round(avg_unoccupied, 1),
                outdoor_temperature=round(acc.outdoor_sum / acc.sample_hours, 1),
                heated_unoccupied_hours=float(acc.heated_unoccupied_hours),
                gas_estimate=round(acc.unoccupied_gas, 2),
                cost_eur=round(cost, 2),
                annualized_cost_eur=round(cost * (365.0 / days), 2),
            )
        )

    spaces.sort(key=lambda item: item.gas_estimate, reverse=True)
    return EmptySpacesResponse(
        range=range_,
        building_id=building_id or ALL_BUILDINGS,
        heat_base_temperature_c=settings.HEATING_BASE_TEMPERATURE_C,
        total_gas_estimate=round(total_gas, 2),
        total_cost_eur=round(total_cost, 2),
        total_annualized_cost_eur=round(total_cost * (365.0 / days), 2),
        total_heated_unoccupied_hours=total_hours,
        spaces=spaces,
    )


def clear_cache() -> None:
    _cache.clear()
