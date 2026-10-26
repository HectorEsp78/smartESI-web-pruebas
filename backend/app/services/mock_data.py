"""Deterministic synthetic data used when no recorder database is available.

Every value depends only on the building/space and the hour, so responses are
stable across requests and easy to test. The shapes are realistic (activity
during the working day, quieter nights/weekends) but the numbers are invented.

Electricity can run against the real recorder (``DATA_SOURCE=database``);
Lighting always uses this model for consumption and uses the real occupancy
counters when they are available.
"""

from __future__ import annotations

import math
import zlib
from datetime import datetime
from functools import lru_cache

from app.core.buildings import (
    BUILDINGS_BY_ID,
    SPACES_BY_BUILDING,
    BuildingConfig,
    SpaceConfig,
)
from app.core.clock import local_tz

# --- Deterministic pseudo-random helpers --------------------------------------


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


def _floor_local(when: datetime) -> datetime:
    return when.astimezone(local_tz()).replace(minute=0, second=0, microsecond=0)


# --- Electricity ---------------------------------------------------------------


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
    if month in (12, 1, 2):
        return 1.18
    if month in (6, 7, 8):
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


# --- Daylight and lighting -----------------------------------------------------

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
