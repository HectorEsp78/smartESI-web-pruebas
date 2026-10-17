"""Business logic for the climate endpoints (gas, degree-days and valves).

The synthetic model gives every space a heating solenoid valve (electroválvula)
and an indoor temperature. From that we compute, per bucket:

- gas consumed, heating degree-days and the outdoor/indoor temperature;
- the share of valves that are open (demand for heat).

And, per space over the whole range:

- the valve/temperature relation (is the room reaching the setpoint?);
- the gas burnt while the space is empty (calefacción de aulas vacías).

Everything is computed once per (range, building) and cached.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from app.core.cache import TTLCache
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

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS)


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


def _accumulate(range_: ClimateRange, building_id: str) -> _Acc:
    cache_key = ("climate", range_, building_id)
    return _cache.get_or_set(cache_key, lambda: _compute(range_, building_id))


def _compute(range_: ClimateRange, building_id: str) -> _Acc:
    buckets = build_buckets(range_)
    scope = scope_buildings(building_id)
    base_temp = settings.HEATING_BASE_TEMPERATURE_C

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
            outdoor = mock_data.outdoor_temperature(cursor)
            bucket_degree += max(0.0, base_temp - outdoor)
            bucket_outdoor_sum += outdoor
            hour_temp_sum = 0.0
            hour_temp_count = 0

            for building in scope:
                spaces = SPACES_BY_BUILDING.get(building.id, [])
                setpoint = building.setpoint_c
                gas = mock_data.hour_gas_kwh(building, cursor)
                bucket_gas += gas
                occupancy_map = mock_data.building_space_occupancy(building, cursor)

                # First pass: valve state, occupancy and temperature per space.
                details = []
                for space in spaces:
                    valve_open = mock_data.space_valve_open(space, building, cursor)
                    occupancy = occupancy_map.get(space.id, 0)
                    temperature = mock_data.space_temperature(
                        building, space, cursor, occupancy
                    )
                    details.append((space, valve_open, occupancy, temperature))
                    hour_temp_sum += temperature
                    hour_temp_count += 1

                open_count = sum(1 for _, valve_open, _, _ in details if valve_open)
                gas_per_open = gas / open_count if open_count else 0.0
                bucket_valve_open += open_count
                bucket_valve_sample += len(spaces)

                # Second pass: accumulate per-space statistics (gas share known now).
                for space, valve_open, occupancy, temperature in details:
                    acc = result.spaces[space.id]
                    acc.sample_hours += 1
                    acc.temp_sum += temperature
                    acc.outdoor_sum += outdoor
                    if valve_open:
                        acc.valve_open_hours += 1
                    if temperature < setpoint - _SETPOINT_TOLERANCE_C:
                        acc.below_setpoint_hours += 1

                    if occupancy <= 0:
                        acc.unoccupied_hours += 1
                        acc.unoccupied_temp_sum += temperature
                        if valve_open:
                            acc.heated_unoccupied_hours += 1
                            acc.unoccupied_gas += gas_per_open

            bucket_indoor_sum += hour_temp_sum / hour_temp_count if hour_temp_count else 0.0
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


def build_gas(range_: ClimateRange, building_id: str) -> GasResponse:
    data = _accumulate(range_, building_id)

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


def build_valves(range_: ClimateRange, building_id: str) -> ValvesResponse:
    data = _accumulate(range_, building_id)
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


def build_empty_spaces(range_: ClimateRange, building_id: str) -> EmptySpacesResponse:
    data = _accumulate(range_, building_id)
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
