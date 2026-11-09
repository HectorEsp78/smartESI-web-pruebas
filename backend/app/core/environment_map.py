"""Confirmed room sensors for the Infrastructure tab.

Only rooms whose Home Assistant entities are known with certainty are listed.
The generic ``sensor.temperatura_shelly*`` / ``sensor.humedad_shelly*``
entities have no room name in the recorder database, so they are intentionally
excluded until the installation provides a mapping. ``sensor.ambiente`` is used
only as a building-level reference, not as a room sensor.

The mapping below was verified against the recorder:

- ``sensor.sensor_temperatura_aXX`` / ``sensor.sensor_humedad_aXX``: A11–A22.
- ``air_quality.co2_1`` is named ``A1.2`` → A12.
- ``air_quality.co2_2`` is named ``A2.1`` → A21.
- ``air_quality.co2_3`` is named ``A1.1`` → A11.
- ``air_quality.co2_4`` is named ``A2.2`` → A22.
- ``sensor.movimiento_aXX``: motion/presence in A11–A22.
- ``sensor.presencia3`` is the same signal as ``sensor.sensor_presencia_f02``.
- ``sensor.presencia2`` is the same signal as ``sensor.sensor_presencia_alu``.
- ``sensor.presencia1`` is the same signal as ``sensor.sensor_presencia_anitaborg``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.buildings import BUILDINGS_BY_ID, SPACES_BY_ID

EnvironmentQuality = Literal["good", "moderate", "poor", "bad", "unknown"]


_PRESENCE_ON = frozenset({"sí", "si", "1", "on", "yes", "true"})
_PRESENCE_OFF = frozenset({"no", "0", "off", "false"})


def parse_presence(state: str | None) -> bool | None:
    """Home Assistant binary and motion states → ``True``/``False``.

    ``sensor.movimiento_*`` uses ``Sí``/``No``; the generic ``sensor.presencia*``
    entities use ``1``/``0``. Unknown values are not treated as "empty".
    """
    if state is None:
        return None
    value = state.strip().lower()
    if value in _PRESENCE_ON:
        return True
    if value in _PRESENCE_OFF:
        return False
    return None


@dataclass(frozen=True)
class EnvironmentRoomConfig:
    id: str
    label: str
    building_id: str
    kind: str
    temperature_entity: str | None = None
    humidity_entity: str | None = None
    co2_entity: str | None = None
    presence_entity: str | None = None
    # Presence statistics exist for the generic ``sensor.presencia*`` entities.
    # The motion sensors are transition-only and are aggregated from raw states.
    presence_statistic_id: str | None = None


def _room(
    room_id: str,
    *,
    label: str | None = None,
    building_id: str = "FerminCaballero",
    kind: str = "CLASSROOM",
    temperature_entity: str | None = None,
    humidity_entity: str | None = None,
    co2_entity: str | None = None,
    presence_entity: str | None = None,
    presence_statistic_id: str | None = None,
) -> EnvironmentRoomConfig:
    label = label or (SPACES_BY_ID[room_id].label if room_id in SPACES_BY_ID else room_id)
    return EnvironmentRoomConfig(
        id=room_id,
        label=label,
        building_id=building_id,
        kind=kind,
        temperature_entity=temperature_entity,
        humidity_entity=humidity_entity,
        co2_entity=co2_entity,
        presence_entity=presence_entity,
        presence_statistic_id=presence_statistic_id,
    )


ENVIRONMENT_ROOMS: tuple[EnvironmentRoomConfig, ...] = (
    _room(
        "A11",
        temperature_entity="sensor.sensor_temperatura_a11",
        humidity_entity="sensor.sensor_humedad_a11",
        co2_entity="air_quality.co2_3",
        presence_entity="sensor.movimiento_a11",
    ),
    _room(
        "A12",
        temperature_entity="sensor.sensor_temperatura_a12",
        humidity_entity="sensor.sensor_humedad_a12",
        co2_entity="air_quality.co2_1",
        presence_entity="sensor.movimiento_a12",
    ),
    _room(
        "A21",
        temperature_entity="sensor.sensor_temperatura_a21",
        humidity_entity="sensor.sensor_humedad_a21",
        co2_entity="air_quality.co2_2",
        presence_entity="sensor.movimiento_a21",
    ),
    _room(
        "A22",
        temperature_entity="sensor.sensor_temperatura_a22",
        humidity_entity="sensor.sensor_humedad_a22",
        co2_entity="air_quality.co2_4",
        presence_entity="sensor.movimiento_a22",
    ),
    _room(
        "F0.2",
        presence_entity="sensor.presencia3",
        presence_statistic_id="sensor.presencia3",
    ),
    _room(
        "ALU",
        label="Aula de Libre Uso (ALU)",
        kind="COMMON",
        presence_entity="sensor.presencia2",
        presence_statistic_id="sensor.presencia2",
    ),
    _room(
        "AnitaBorg",
        building_id="ModuloB",
        kind="COMMON",
        presence_entity="sensor.presencia1",
        presence_statistic_id="sensor.presencia1",
    ),
)

ENVIRONMENT_ROOMS_BY_ID: dict[str, EnvironmentRoomConfig] = {
    room.id: room for room in ENVIRONMENT_ROOMS
}

# The recorder exposes a multi-sensor named ``ambiente`` with temperature,
# humidity, CO2 and TVOC. It has no confirmed room mapping, so it is used only
# as a reference for the room-vs-ambient cross, never as a room sensor.
AMBIENT_TEMPERATURE_ENTITY = "sensor.ambiente"
GAS_M3_ENTITY = "sensor.daily_gas"
GAS_COST_ENTITY = "sensor.daily_gas_cost"

DEFAULT_ENVIRONMENT_DAYS = 7
MAX_ENVIRONMENT_DAYS = 366


def building_label(building_id: str) -> str:
    building = BUILDINGS_BY_ID.get(building_id)
    return building.label if building else building_id


# --- Comfort thresholds -------------------------------------------------------

TEMPERATURE_GOOD = (18.0, 24.0)
TEMPERATURE_WARN = (16.0, 26.0)
HUMIDITY_GOOD = (30.0, 60.0)
HUMIDITY_WARN = (25.0, 70.0)
CO2_GOOD_MAX = 600.0
CO2_MODERATE_MAX = 800.0
CO2_POOR_MAX = 1000.0

# Values outside this range are sensor resets/errors, not measurements.
CO2_MIN_PPM = 300.0
CO2_MAX_PPM = 5000.0
# Indoor rooms: 0 °C / 0 % are written by Home Assistant while it restarts, so
# they are not credible measurements for this tab.
TEMPERATURE_MIN_C = 5.0
TEMPERATURE_MAX_C = 60.0
HUMIDITY_MIN_PCT = 5.0
HUMIDITY_MAX_PCT = 100.0

_QUALITY_RANK: dict[EnvironmentQuality, int] = {
    "good": 0,
    "moderate": 1,
    "poor": 2,
    "bad": 3,
    "unknown": -1,
}


def temperature_status(value: float | None) -> EnvironmentQuality:
    if value is None:
        return "unknown"
    if TEMPERATURE_GOOD[0] <= value <= TEMPERATURE_GOOD[1]:
        return "good"
    if TEMPERATURE_WARN[0] <= value <= TEMPERATURE_WARN[1]:
        return "moderate"
    return "bad"


def humidity_status(value: float | None) -> EnvironmentQuality:
    if value is None:
        return "unknown"
    if HUMIDITY_GOOD[0] <= value <= HUMIDITY_GOOD[1]:
        return "good"
    if HUMIDITY_WARN[0] <= value <= HUMIDITY_WARN[1]:
        return "moderate"
    return "bad"


def co2_status(value: float | None) -> EnvironmentQuality:
    if value is None:
        return "unknown"
    if value <= CO2_GOOD_MAX:
        return "good"
    if value <= CO2_MODERATE_MAX:
        return "moderate"
    if value <= CO2_POOR_MAX:
        return "poor"
    return "bad"


def worst_status(*statuses: EnvironmentQuality) -> EnvironmentQuality:
    known = [status for status in statuses if status != "unknown"]
    if not known:
        return "unknown"
    return max(known, key=lambda status: _QUALITY_RANK[status])
