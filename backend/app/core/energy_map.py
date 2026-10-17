"""Static catalogue of buildings and metered spaces used by the stats module.

This is the *placeholder* equivalent of the real ``sensor_map.py`` from the main
Smart ESI project. Names and capacities are taken from the real installation so
the synthetic data looks familiar, but the energy figures are simulated until
``DATA_SOURCE=database`` is enabled and a real mapping is wired in.

Each building also declares the data needed by the climate/lighting charts:

- ``setpoint_c``  heating comfort setpoint (°C) used by the valve/temperature model.
- ``gas_base_kw`` nominal boiler gas input (kW) when every heating valve is open.

Each space declares:

- ``area_m2``     useful floor area, used for the kWh/m² efficiency ratio and to
                  distribute the building occupancy across its rooms.
- ``lighting_kw`` installed lighting power, used to split the electrical
  consumption between lighting (luminarias) and the rest of the loads.
- ``has_valve``   whether the space has a heating solenoid valve (electroválvula).

To add a space, add an entry to ``SPACES`` with the building it belongs to and a
``weight`` (its share, ~0..1, of the building's base consumption). Weights do not
need to be exact: the service normalises them per building.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuildingConfig:
    id: str
    label: str
    max_capacity: int
    # Baseline electrical load of the whole building (common areas included), in kW.
    base_kw: float
    # Heating comfort setpoint (°C) and nominal boiler gas input (kW).
    setpoint_c: float = 21.0
    gas_base_kw: float = 40.0


@dataclass(frozen=True)
class SpaceConfig:
    id: str
    label: str
    building_id: str
    kind: str  # "CLASSROOM" | "LABORATORY" | "COMMON"
    weight: float
    area_m2: float = 60.0
    # Installed lighting power in kW (used to split electricity into luminarias + rest).
    lighting_kw: float = 0.6
    # Whether this space has a heating solenoid valve (electroválvula).
    has_valve: bool = True


BUILDINGS: tuple[BuildingConfig, ...] = (
    BuildingConfig(
        id="FerminCaballero",
        label="Edificio Fermín Caballero",
        max_capacity=300,
        base_kw=22.0,
        setpoint_c=21.0,
        gas_base_kw=55.0,
    ),
    BuildingConfig(
        id="ModuloB",
        label="Módulo B",
        max_capacity=160,
        base_kw=12.0,
        setpoint_c=21.0,
        gas_base_kw=28.0,
    ),
)

SPACES: tuple[SpaceConfig, ...] = (
    # --- Edificio Fermín Caballero ---
    SpaceConfig("A11", "Aula A11", "FerminCaballero", "CLASSROOM", 0.09, 70.0, 0.62),
    SpaceConfig("A12", "Aula A12", "FerminCaballero", "CLASSROOM", 0.08, 68.0, 0.60),
    SpaceConfig("A21", "Aula A21", "FerminCaballero", "CLASSROOM", 0.07, 72.0, 0.64),
    SpaceConfig("A22", "Aula A22", "FerminCaballero", "CLASSROOM", 0.07, 72.0, 0.64),
    SpaceConfig("F0.1", "Aula F0.1", "FerminCaballero", "CLASSROOM", 0.06, 60.0, 0.54),
    SpaceConfig("F0.2", "Aula F0.2", "FerminCaballero", "CLASSROOM", 0.06, 60.0, 0.54),
    SpaceConfig("F1.1", "Aula F1.1", "FerminCaballero", "CLASSROOM", 0.05, 55.0, 0.50),
    SpaceConfig("LD1", "Lab. Ignacio Cirac", "FerminCaballero", "LABORATORY", 0.10, 95.0, 0.85),
    SpaceConfig("LD2", "Lab. Dennis Ritchie", "FerminCaballero", "LABORATORY", 0.09, 95.0, 0.85),
    SpaceConfig("LD3", "Lab. Bill Gates", "FerminCaballero", "LABORATORY", 0.09, 90.0, 0.80),
    SpaceConfig("LD4", "Lab. John Carmack", "FerminCaballero", "LABORATORY", 0.09, 90.0, 0.80),
    SpaceConfig("Grados", "Salón de Grados", "FerminCaballero", "COMMON", 0.05, 120.0, 0.95),
    SpaceConfig("Actos", "Salón de Actos", "FerminCaballero", "COMMON", 0.05, 220.0, 1.60),
    SpaceConfig("Calculo", "Centro de Cálculo", "FerminCaballero", "COMMON", 0.05, 110.0, 0.90),
    # --- Módulo B ---
    SpaceConfig("AnitaBorg", "Sala Anita Borg", "ModuloB", "COMMON", 0.22, 90.0, 1.20),
    SpaceConfig("Secretaria", "Secretaría", "ModuloB", "COMMON", 0.15, 60.0, 0.55),
    SpaceConfig("Direccion", "Dirección", "ModuloB", "COMMON", 0.12, 40.0, 0.40),
    SpaceConfig(
        "ColegioUniversitario",
        "Colegio Universitario",
        "ModuloB",
        "COMMON",
        0.26,
        150.0,
        1.35,
    ),
    SpaceConfig("MonicoSanchez", "Mónico Sánchez", "ModuloB", "COMMON", 0.25, 140.0, 1.25),
)

BUILDINGS_BY_ID: dict[str, BuildingConfig] = {b.id: b for b in BUILDINGS}

SPACES_BY_BUILDING: dict[str, list[SpaceConfig]] = {
    building.id: [space for space in SPACES if space.building_id == building.id]
    for building in BUILDINGS
}

SPACES_BY_ID: dict[str, SpaceConfig] = {s.id: s for s in SPACES}

# Installed lighting power per building (kW) and total useful area (m²).
BUILDINGS_LIGHTING_KW: dict[str, float] = {
    building.id: sum(space.lighting_kw for space in SPACES_BY_BUILDING[building.id])
    for building in BUILDINGS
}

BUILDINGS_AREA_M2: dict[str, float] = {
    building.id: sum(space.area_m2 for space in SPACES_BY_BUILDING[building.id])
    for building in BUILDINGS
}
