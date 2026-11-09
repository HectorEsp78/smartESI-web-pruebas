"""Battery sensors shown in the Maintenance tab, grouped by sub-page.

Shelly and valve batteries are published as a percentage. The classroom sensors
publish the cell voltage in millivolts, so their percentage is only an estimate
(see ``MV_PERCENT_CURVE``) and the raw value stays authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BatteryUnit = Literal["percent", "millivolt"]

# Readings outside these ranges are glitches: the classroom sensors have written
# 0 and values above 65 000 mV, which no cell can produce.
PERCENT_RANGE = (0.0, 100.0)
MILLIVOLT_RANGE = (2000.0, 4000.0)

# Without a valid reading for this long, the level is no longer "current".
CURRENT_READING_MAX_HOURS = 24.0 * 7.0
# Batteries only write when the value changes, so short silences are normal. A
# longer one is drawn as a gap instead of a line between two distant readings.
HISTORY_GAP_HOURS = 24.0 * 7.0
DEFAULT_HISTORY_DAYS = 90
HOURLY_HISTORY_MAX_DAYS = 31
# Far enough back to find the last reading of a sensor retired years ago.
LATEST_READING_LOOKBACK_DAYS = 3650


@dataclass(frozen=True)
class BatterySensor:
    id: str
    label: str
    entity_id: str


@dataclass(frozen=True)
class BatteryGroup:
    id: str
    label: str
    unit: BatteryUnit
    sensors: tuple[BatterySensor, ...]

    @property
    def valid_range(self) -> tuple[float, float]:
        return MILLIVOLT_RANGE if self.unit == "millivolt" else PERCENT_RANGE


def _shelly(index: int) -> BatterySensor:
    return BatterySensor(
        id=f"shelly{index}",
        label=f"Shelly {index}",
        entity_id=f"sensor.bateria_shelly{index}",
    )


def _valve(key: str, label: str) -> BatterySensor:
    return BatterySensor(
        id=f"valvula_{key}",
        label=f"Válvula {label}",
        entity_id=f"sensor.bateria_valvula_{key}",
    )


def _classroom(room: str) -> BatterySensor:
    return BatterySensor(
        id=room,
        label=f"Aula {room.upper()}",
        entity_id=f"sensor.sensor_bateria_{room}",
    )


BATTERY_GROUPS: dict[str, BatteryGroup] = {
    group.id: group
    for group in (
        BatteryGroup(
            id="shellys",
            label="Shellys",
            unit="percent",
            sensors=tuple(_shelly(index) for index in range(1, 19)),
        ),
        BatteryGroup(
            id="valvulas",
            label="Válvulas",
            unit="percent",
            sensors=(
                _valve("f1_1", "F1.1"),
                _valve("ld1", "LD1"),
                _valve("ld2", "LD2"),
                _valve("ld3", "LD3"),
                _valve("ld4", "LD4"),
            ),
        ),
        BatteryGroup(
            id="aulas",
            label="Aulas",
            unit="millivolt",
            sensors=(
                _classroom("a11"),
                _classroom("a12"),
                _classroom("a21"),
                _classroom("a22"),
            ),
        ),
    )
}
