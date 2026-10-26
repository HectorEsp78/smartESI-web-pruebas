"""Electricity-specific catalogue: buildings, sectors and their HA statistics.

This map is intentionally separate from :mod:`app.core.energy_map`. The
Electricity tab has a different scope than the rest of the prototype:

- It works with **three buildings**: Módulo A, Módulo B and Fermín Caballero.
- Fermín Caballero has **partial** submetering by floor panel and the CPD.
- The three buildings reconcile against the site-wide ``Cuadro General`` meter.

Home Assistant entities were verified against the recorder database:

``sensor.cuadro_general``
    Main incoming meter for the whole site. It is the reference total.
``sensor.edificio_a`` / ``sensor.edificio_b``
    Direct meters for Módulo A and Módulo B.
``sensor.planta_*`` / ``sensor.sala_computacion``
    Partial submeters inside Fermín Caballero. They do **not** cover the whole
    building, so they are never presented as Fermín's total.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

# Main site meter (kWh, cumulative). The Electricity tab always reconciles
# against this value.
SITE_ELECTRICITY_STATISTIC: str = "sensor.cuadro_general"

# First date with usable long-term statistics in the recorder database.
ELECTRICITY_DATA_START: date = date(2023, 12, 22)

ELECTRICITY_ALL = "all"


@dataclass(frozen=True)
class ElectricityBuildingConfig:
    id: str
    label: str
    statistic_id: str | None
    kind: Literal["direct", "residual"]
    note: str = ""


@dataclass(frozen=True)
class ElectricitySectorConfig:
    id: str
    label: str
    building_id: str
    statistic_id: str
    floor: str
    order: int
    available: bool = True
    note: str = ""


# Módulo A and Módulo B have a direct meter. Fermín Caballero does not have a
# single meter: its total is derived as Cuadro General - Módulo A - Módulo B.
# The floor panels and the CPD are partial submeters inside Fermín.
ELECTRICITY_BUILDINGS: tuple[ElectricityBuildingConfig, ...] = (
    ElectricityBuildingConfig(
        id="ModuloA",
        label="Módulo A",
        statistic_id="sensor.edificio_a",
        kind="direct",
        note="Contador directo del edificio.",
    ),
    ElectricityBuildingConfig(
        id="ModuloB",
        label="Módulo B",
        statistic_id="sensor.edificio_b",
        kind="direct",
        note="Contador directo del edificio.",
    ),
    ElectricityBuildingConfig(
        id="FerminCaballero",
        label="Fermín Caballero",
        statistic_id=None,
        kind="residual",
        note=(
            "Total calculado como Cuadro General − Módulo A − Módulo B. "
            "Los cuadros de planta y el CPD son subcontadores parciales."
        ),
    ),
)

ELECTRICITY_BUILDINGS_BY_ID: dict[str, ElectricityBuildingConfig] = {
    building.id: building for building in ELECTRICITY_BUILDINGS
}

# Partial submeters inside Fermín Caballero. The order follows the building's
# floors, then the CPD. ``sensor.planta_baja_cuadro_e`` is kept in the catalogue
# but marked unavailable: its cumulative sum has not moved since 2023.
ELECTRICITY_SECTORS: tuple[ElectricitySectorConfig, ...] = (
    ElectricitySectorConfig(
        id="PB_D",
        label="Planta Baja · Cuadro D",
        building_id="FerminCaballero",
        statistic_id="sensor.planta_baja_red_cuadro_d",
        floor="Planta Baja",
        order=10,
    ),
    ElectricitySectorConfig(
        id="PB_E",
        label="Planta Baja · Cuadro E",
        building_id="FerminCaballero",
        statistic_id="sensor.planta_baja_cuadro_e",
        floor="Planta Baja",
        order=11,
        available=False,
        note="Sin consumo registrado en el periodo disponible.",
    ),
    ElectricitySectorConfig(
        id="P1_F",
        label="Planta Primera · Cuadro F",
        building_id="FerminCaballero",
        statistic_id="sensor.planta_primera_cuadro_f",
        floor="Planta Primera",
        order=20,
    ),
    ElectricitySectorConfig(
        id="P1_G",
        label="Planta Primera · Cuadro G",
        building_id="FerminCaballero",
        statistic_id="sensor.planta_primera_cuadro_g",
        floor="Planta Primera",
        order=21,
    ),
    ElectricitySectorConfig(
        id="P2_H",
        label="Planta Segunda · Cuadro H",
        building_id="FerminCaballero",
        # The entity id says "planta_primera", but its device name is
        # P2_Cuadro_H and it is physically on the second floor.
        statistic_id="sensor.planta_primera_cuadro_h",
        floor="Planta Segunda",
        order=30,
    ),
    ElectricitySectorConfig(
        id="P2_I",
        label="Planta Segunda · Cuadro I",
        building_id="FerminCaballero",
        statistic_id="sensor.planta_segunda_cuadro_i",
        floor="Planta Segunda",
        order=31,
    ),
    ElectricitySectorConfig(
        id="P3_J",
        label="Planta Tercera · Cuadro J",
        building_id="FerminCaballero",
        statistic_id="sensor.planta_tercera_cuadro_j",
        floor="Planta Tercera",
        order=40,
    ),
    ElectricitySectorConfig(
        id="P3_K",
        label="Planta Tercera · Cuadro K",
        building_id="FerminCaballero",
        statistic_id="sensor.planta_tercera_cuadro_k",
        floor="Planta Tercera",
        order=41,
    ),
    ElectricitySectorConfig(
        id="CPD",
        label="CPD · Sala de Computación",
        building_id="FerminCaballero",
        statistic_id="sensor.sala_computacion",
        floor="CPD",
        order=50,
    ),
)

ELECTRICITY_SECTORS_BY_ID: dict[str, ElectricitySectorConfig] = {
    sector.id: sector for sector in ELECTRICITY_SECTORS
}

ELECTRICITY_SECTORS_BY_BUILDING: dict[str, list[ElectricitySectorConfig]] = {
    building.id: sorted(
        [sector for sector in ELECTRICITY_SECTORS if sector.building_id == building.id],
        key=lambda sector: sector.order,
    )
    for building in ELECTRICITY_BUILDINGS
}
