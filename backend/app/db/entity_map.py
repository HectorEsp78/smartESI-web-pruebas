"""Home Assistant entities used by the real Lighting data path.

Electricity has its own verified mapping in :mod:`app.core.electricity_map`.
Lighting consumption is still synthetic, but occupancy can be read from the
real people counters to decide when a building is empty.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OccupancyCounter:
    """A cumulative people counter, either the state itself or a JSON attribute.

    Home Assistant writes the value as text in ``states.state``; some devices
    instead expose one counter per direction as an attribute of a single entity
    (Módulo B: ``LTR_SUM`` / ``RTL_SUM`` of ``sensor.contador_personas``).
    """

    entity_id: str
    attribute: str | None = None


# Per building: (entrance counter, exit counter). The current occupancy is
# ``max(0, entrance - exit)``; the counters reset at midnight, so the difference
# is also the occupancy of that moment.
BUILDING_OCCUPANCY_COUNTERS: dict[str, tuple[OccupancyCounter, OccupancyCounter]] = {
    "FerminCaballero": (
        OccupancyCounter("sensor.entrada_fermin_caballero"),
        OccupancyCounter("sensor.salida_fermin_caballero"),
    ),
    "ModuloB": (
        OccupancyCounter("sensor.contador_personas", "LTR_SUM"),
        OccupancyCounter("sensor.contador_personas", "RTL_SUM"),
    ),
}
