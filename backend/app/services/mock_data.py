"""Synthetic data generator for the statistics prototype.

Everything here is *deterministic*: the value for a given building/space and a
given hour is always the same, so responses are stable across requests (and easy
to test) without needing a database. The shapes are realistic (activity during
the working day, quieter nights/weekends, seasonal HVAC peaks) but the numbers
are invented.

When ``DATA_SOURCE=database`` is enabled, these functions are replaced by real
queries against the Home Assistant recorder database.
"""

from __future__ import annotations

import hashlib
import math
import zlib
from datetime import datetime, timedelta
from functools import lru_cache

from app.core.clock import local_tz
from app.core.energy_map import (
    BUILDINGS_BY_ID,
    SPACES_BY_BUILDING,
    SPACES_BY_ID,
    BuildingConfig,
    SpaceConfig,
)

# --- Deterministic pseudo-random helpers --------------------------------------


def _seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _uniform(*parts: object) -> float:
    """Deterministic pseudo-random value in ``[0, 1)`` derived from the inputs.

    Uses CRC32 (fast and stable across processes) instead of constructing a
    ``random.Random`` on every call, which was the hot spot of the aggregation.
    """
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return zlib.crc32(payload) / 0x100000000


def _jitter(*parts: object, amplitude: float) -> float:
    """Multiplicative-ish noise in ``[-amplitude, +amplitude]``."""
    return (_uniform(*parts) * 2.0 - 1.0) * amplitude


def stable_noise(*parts: object, amplitude: float = 1.0) -> float:
    """Public, deterministic noise helper (used for per-space shares)."""
    return _jitter(*parts, amplitude=amplitude)


@lru_cache(maxsize=60_000)
def _hour_key(local: datetime) -> str:
    return local.strftime("%Y-%m-%dT%H")


# --- Energy --------------------------------------------------------------------


def _activity_profile(local: datetime) -> float:
    """Fraction of the building's nominal load that is being drawn (0..1+)."""
    hour = local.hour + local.minute / 60.0
    weekday = local.weekday()  # 0 = Monday

    if weekday >= 5:  # weekend
        return 0.22 if 9 <= hour < 14 else 0.15

    if 8 <= hour < 21:
        return 0.55 + 0.45 * math.sin(math.pi * (hour - 8) / 13.0)
    if 7 <= hour < 8:
        return 0.35
    if 21 <= hour < 23:
        return 0.32
    return 0.18


def _season_factor(month: int) -> float:
    if month in (12, 1, 2):  # winter heating
        return 1.18
    if month in (6, 7, 8):  # summer cooling
        return 1.28
    if month in (5, 9):
        return 1.10
    return 1.0


def hour_energy_kwh(building: BuildingConfig, when: datetime) -> float:
    """Electrical energy consumed by ``building`` during the hour of ``when``."""
    return _hour_energy_cached(building.id, _floor_local(when))


@lru_cache(maxsize=100_000)
def _hour_energy_cached(building_id: str, local: datetime) -> float:
    building = BUILDINGS_BY_ID[building_id]
    profile = _activity_profile(local)
    season = _season_factor(local.month)
    jitter = 1.0 + _jitter(building_id, _hour_key(local), amplitude=0.08)
    standby = 0.10  # baseline load even when the building is empty
    return building.base_kw * (profile + standby) * season * jitter


# --- Occupancy -----------------------------------------------------------------


def _occupancy_ratio(local: datetime) -> float:
    """Fraction of the building capacity that is occupied (0..1)."""
    hour = local.hour + local.minute / 60.0
    weekday = local.weekday()

    if weekday >= 5:  # weekend
        return 0.03 if 10 <= hour < 14 else 0.01

    if 8 <= hour < 21:
        base = 0.12 + 0.58 * math.sin(math.pi * (hour - 8) / 13.0)
        if 14 <= hour < 15.5:  # lunch dip
            base *= 0.6
        return base
    if 7 <= hour < 8:
        return 0.06
    if 21 <= hour < 22:
        return 0.05
    return 0.01


def hour_occupancy(building: BuildingConfig, when: datetime) -> int:
    """Number of people inside ``building`` during the hour of ``when``."""
    return _hour_occupancy_cached(building.id, _floor_local(when))


@lru_cache(maxsize=100_000)
def _hour_occupancy_cached(building_id: str, local: datetime) -> int:
    building = BUILDINGS_BY_ID[building_id]
    ratio = _occupancy_ratio(local)
    jitter = 1.0 + _jitter("occ", building_id, _hour_key(local), amplitude=0.15)
    return max(0, round(building.max_capacity * ratio * jitter))


# --- Air quality ---------------------------------------------------------------


def hour_co2(building: BuildingConfig, occupancy: int, when: datetime) -> float:
    """Estimated CO2 concentration (ppm) given the current occupancy."""
    return _hour_co2_cached(building.id, _floor_local(when))


@lru_cache(maxsize=100_000)
def _hour_co2_cached(building_id: str, local: datetime) -> float:
    building = BUILDINGS_BY_ID[building_id]
    occupancy = _hour_occupancy_cached(building_id, local)
    ratio = occupancy / building.max_capacity if building.max_capacity else 0.0
    value = 415.0 + 950.0 * ratio
    if local.hour < 7:  # windows / ventilation flush the air overnight
        value *= 0.85
    jitter = 1.0 + _jitter("co2", building_id, _hour_key(local), amplitude=0.06)
    return round(value * jitter, 1)


def hour_temperature(building: BuildingConfig, occupancy: int, when: datetime) -> float:
    """Estimated indoor temperature (°C)."""
    return _hour_temperature_cached(building.id, _floor_local(when))


@lru_cache(maxsize=100_000)
def _hour_temperature_cached(building_id: str, local: datetime) -> float:
    building = BUILDINGS_BY_ID[building_id]
    occupancy = _hour_occupancy_cached(building_id, local)
    ratio = occupancy / building.max_capacity if building.max_capacity else 0.0
    value = 21.0 + 2.5 * ratio
    if local.month in (6, 7, 8):
        value += 1.5
    if local.month in (12, 1, 2):
        value -= 0.8
    jitter = _jitter("temp", building_id, _hour_key(local), amplitude=0.06)
    return round(value * (1 + jitter), 1)


def hour_humidity(building: BuildingConfig, occupancy: int, when: datetime) -> float:
    """Estimated relative humidity (%)."""
    return _hour_humidity_cached(building.id, _floor_local(when))


@lru_cache(maxsize=100_000)
def _hour_humidity_cached(building_id: str, local: datetime) -> float:
    building = BUILDINGS_BY_ID[building_id]
    occupancy = _hour_occupancy_cached(building_id, local)
    ratio = occupancy / building.max_capacity if building.max_capacity else 0.0
    value = 44.0 + 12.0 * ratio
    jitter = _jitter("hum", building_id, _hour_key(local), amplitude=0.10)
    return round(min(95.0, max(20.0, value * (1 + jitter))), 1)


# --- Weather & daylight --------------------------------------------------------

# Below this occupancy ratio a space/building is considered "empty" for the
# lighting-waste analysis (lights on with nobody inside).
EMPTY_OCCUPANCY_RATIO = 0.05

# Approximate daylight hours for the latitude of Ciudad Real (Spain), by month.
_DAYLIGHT_HOURS_BY_MONTH: dict[int, float] = {
    1: 9.7,
    2: 10.7,
    3: 11.9,
    4: 13.2,
    5: 14.4,
    6: 15.1,
    7: 14.8,
    8: 13.7,
    9: 12.4,
    10: 11.1,
    11: 9.9,
    12: 9.3,
}


def daylight_hours(when: datetime) -> float:
    """Nominal hours of daylight for the day of ``when``."""
    local = when.astimezone(local_tz())
    return _DAYLIGHT_HOURS_BY_MONTH[local.month]


def outdoor_temperature(when: datetime) -> float:
    """Synthetic outdoor temperature (°C): seasonal + daily cycle + noise."""
    return _outdoor_temperature_for_hour(when.astimezone(local_tz()).replace(
        minute=0, second=0, microsecond=0
    ))


@lru_cache(maxsize=20_000)
def _outdoor_temperature_for_hour(local: datetime) -> float:
    day_of_year = local.timetuple().tm_yday
    # ~4 °C around mid-January, ~26 °C around mid-July.
    seasonal = 15.0 - 11.0 * math.cos(2 * math.pi * (day_of_year - 15) / 365.0)
    hour = local.hour + local.minute / 60.0
    daily = 6.0 * math.sin(2 * math.pi * (hour - 9) / 24.0)  # peak ~15h, min ~3h
    noise = 2.5 * _jitter("outdoor", _hour_key(local), amplitude=1.0)
    return round(seasonal + daily + noise, 1)


# --- Lighting (luminarias) -----------------------------------------------------


def _empty_lighting_floor(building: BuildingConfig) -> float:
    """Share of the load still drawn by lights when the building is empty."""
    return 0.10 + 0.10 * abs(_jitter("empty-light", building.id, amplitude=1.0))


def lighting_fraction(building: BuildingConfig, when: datetime, occupancy_ratio: float) -> float:
    """Fraction of the building's electricity that goes to lighting.

    Lower during bright daylight (natural light is enough), higher at night, and
    a small residual floor when the building is empty (lights left on).
    """
    local = when.astimezone(local_tz())
    hour = local.hour + local.minute / 60.0
    daylight = daylight_hours(local)

    if occupancy_ratio <= EMPTY_OCCUPANCY_RATIO:
        fraction = _empty_lighting_floor(building)
    elif 11 <= hour < 16 and daylight >= 12.0:
        fraction = 0.20  # natural light is enough in the central hours
    elif hour < 8 or hour >= 20:
        fraction = 0.40
    else:
        fraction = 0.33

    noise = 1.0 + _jitter("light-frac", building.id, _hour_key(local), amplitude=0.08)
    return min(0.60, max(0.03, fraction * noise))


def space_lighting_kw_share(space: SpaceConfig) -> float:
    """Share of the building's lighting power installed in ``space``."""
    spaces = SPACES_BY_BUILDING.get(space.building_id, [])
    total = sum(item.lighting_kw for item in spaces)
    return space.lighting_kw / total if total > 0 else 0.0


# --- Heating: solenoid valves (electroválvulas) and gas -------------------------


VALVE_STUCK_THRESHOLD = 0.8


def valve_health(space: SpaceConfig) -> float:
    """Deterministic valve condition in [-1, 1].

    Negative values model a valve stuck closed (the room never heats); positive
    values model a valve stuck open (the room heats even when it is empty and out
    of schedule). Near zero is a correctly working valve.
    """
    return _valve_health_for_space(space.id)


@lru_cache(maxsize=2048)
def _valve_health_for_space(space_id: str) -> float:
    return stable_noise("valve-health", space_id, amplitude=1.0)


def _floor_local(when: datetime) -> datetime:
    return when.astimezone(local_tz()).replace(minute=0, second=0, microsecond=0)


@lru_cache(maxsize=250_000)
def _valve_open_for(space_id: str, local: datetime) -> bool:
    space = SPACES_BY_ID[space_id]
    if not space.has_valve:
        return False

    outdoor = _outdoor_temperature_for_hour(local)
    if outdoor >= 18.0:
        return False  # no heating needed at all

    hour = local.hour + local.minute / 60.0
    active = local.weekday() < 5 and 7.0 <= hour < 21.0
    health = _valve_health_for_space(space_id)

    if health < -VALVE_STUCK_THRESHOLD:
        return False  # stuck closed
    if health > VALVE_STUCK_THRESHOLD:
        return True  # stuck open (heats even at night / weekends)
    return active and outdoor < 17.0


def space_valve_open(space: SpaceConfig, building: BuildingConfig, when: datetime) -> bool:
    """Whether the heating valve of ``space`` is open (demanding heat) at ``when``."""
    return _valve_open_for(space.id, _floor_local(when))


@lru_cache(maxsize=250_000)
def _space_occupancy_for(space_id: str, local: datetime) -> int:
    space = SPACES_BY_ID[space_id]
    building = BUILDINGS_BY_ID[space.building_id]
    building_occupancy = hour_occupancy(building, local)
    spaces = SPACES_BY_BUILDING.get(building.id, [])
    area_total = sum(item.area_m2 for item in spaces) or 1.0
    share = space.area_m2 / area_total
    jitter = 1.0 + _jitter("space-occ", space_id, _hour_key(local), amplitude=0.30)
    return max(0, round(building_occupancy * share * jitter))


def space_occupancy(building: BuildingConfig, space: SpaceConfig, when: datetime) -> int:
    """Approximate number of people in ``space`` (building occupancy by area)."""
    return _space_occupancy_for(space.id, _floor_local(when))


def building_space_occupancy(building: BuildingConfig, when: datetime) -> dict[str, int]:
    """Occupancy of every space of ``building`` at ``when`` (computed once)."""
    local = _floor_local(when)
    return {
        space.id: _space_occupancy_for(space.id, local)
        for space in SPACES_BY_BUILDING.get(building.id, [])
    }


@lru_cache(maxsize=250_000)
def _space_temperature_for(space_id: str, local: datetime) -> float:
    space = SPACES_BY_ID[space_id]
    building = BUILDINGS_BY_ID[space.building_id]
    outdoor = _outdoor_temperature_for_hour(local)
    occupancy = _space_occupancy_for(space_id, local)
    occupancy_factor = min(1.0, occupancy / 15.0)

    if _valve_open_for(space_id, local):
        base = building.setpoint_c + 0.35 + 0.9 * occupancy_factor
    elif outdoor >= 18.0:
        base = 21.5 + 0.55 * (outdoor - 18.0)
    elif _valve_open_for(space_id, local - timedelta(hours=1)):
        base = 18.2 + 0.25 * outdoor + 0.5 * occupancy_factor  # recently heated
    else:
        base = 15.0 + 0.30 * outdoor + 0.6 * occupancy_factor  # cold room

    noise = 0.5 * _jitter("space-temp", space_id, _hour_key(local), amplitude=1.0)
    return round(base + noise, 1)


def space_temperature(
    building: BuildingConfig, space: SpaceConfig, when: datetime, occupancy: int
) -> float:
    """Indoor temperature of ``space`` (°C) from valve state, weather and occupancy.

    ``occupancy`` is accepted for readability at the call site but recomputed
    internally so the result can be cached per (space, hour).
    """
    return _space_temperature_for(space.id, _floor_local(when))


def hour_gas_kwh(building: BuildingConfig, when: datetime) -> float:
    """Gas consumed by the boiler(s) of ``building`` during the hour of ``when``.

    Proportional to the number of open heating valves and to the heating demand
    (how far the outdoor temperature is below the base temperature).
    """
    return _hour_gas_cached(building.id, _floor_local(when))


@lru_cache(maxsize=100_000)
def _hour_gas_cached(building_id: str, local: datetime) -> float:
    building = BUILDINGS_BY_ID[building_id]
    spaces = SPACES_BY_BUILDING.get(building_id, [])
    if not spaces:
        return 0.0

    open_count = sum(1 for space in spaces if _valve_open_for(space.id, local))
    if open_count == 0:
        return 0.0

    outdoor = _outdoor_temperature_for_hour(local)
    demand = max(0.0, 18.0 - outdoor)
    ratio = open_count / len(spaces)
    noise = 1.0 + _jitter("gas", building_id, _hour_key(local), amplitude=0.06)
    return round(building.gas_base_kw * ratio * (demand / 8.0) * noise, 4)
