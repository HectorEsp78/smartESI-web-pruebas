"""Static catalogue of buildings and spaces used by the statistics module.

The catalogue is shared by the Electricity mock generator and the Lighting
charts. Real electricity data comes from the Home Assistant recorder; the
catalogue only supplies names, capacities and the synthetic load model.

Each building declares its nominal electrical load. Each space declares its
useful area, installed lighting power and its share of the building load.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuildingConfig:
    id: str
    label: str
    max_capacity: int
    # Baseline electrical load of the whole building (common areas included), in kW.
    base_kw: float


@dataclass(frozen=True)
class SpaceConfig:
    id: str
    label: str
    building_id: str
    kind: str  # "CLASSROOM" | "LABORATORY" | "COMMON"
    weight: float
    area_m2: float = 60.0
    # Installed lighting power in kW (used to split electricity into lighting + rest).
    lighting_kw: float = 0.6


BUILDINGS: tuple[BuildingConfig, ...] = (
    BuildingConfig(
        id="FerminCaballero",
        label="Edificio Fermín Caballero",
        max_capacity=300,
        base_kw=22.0,
    ),
    BuildingConfig(
        id="ModuloB",
        label="Módulo B",
        max_capacity=160,
        base_kw=12.0,
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

BUILDINGS_BY_ID: dict[str, BuildingConfig] = {building.id: building for building in BUILDINGS}

SPACES_BY_BUILDING: dict[str, list[SpaceConfig]] = {
    building.id: [space for space in SPACES if space.building_id == building.id]
    for building in BUILDINGS
}

SPACES_BY_ID: dict[str, SpaceConfig] = {space.id: space for space in SPACES}
