"""Explicit mapping of catalogue entries to Home Assistant entities.

This is the equivalent of the project's ``energy_map.py`` for the *real* data:
it declares which Home Assistant entity/statistic corresponds to each building
and space, so the queries never guess. Entity ids were confirmed against the
recorder database (``statistics_meta`` and ``states``).

Mapped today: site-wide electricity (cuadro general), partial electricity
submeters per building, gas, outdoor/indoor temperature, humidity, CO2 (only the
four classrooms that have an air-quality sensor) and the building occupancy
counters. Lighting has no confirmed entity-to-space mapping yet, so it keeps
using the synthetic model (see ``docs/datos.md``).
"""

from __future__ import annotations

from dataclasses import dataclass

# Main electrical meter for the whole site (kWh, cumulative). In ``statistics``.
# This is the meter shown by Home Assistant's "cuadro general" energy card.
SITE_ENERGY_STATISTIC: str = "sensor.cuadro_general"

# Electrical submeters available per building (kWh, cumulative). In
# ``statistics``. They only cover part of the site load (~3-15 % of the main
# meter), so they must never be added up as if they were the site total.
BUILDING_ENERGY_STATISTIC: dict[str, str] = {
    "FerminCaballero": "sensor.edificio_a",
    "ModuloB": "sensor.edificio_b",
}

# Internal series key for the site-wide meter. It is not a real building id.
SITE_ENERGY_KEY: str = "__site__"

# Gas meter for the whole site (m3, cumulative, resets daily). In ``statistics``.
# There is a single gas meter, so per-building gas is not available yet.
SITE_GAS_STATISTIC: str = "sensor.daily_gas"

# Outdoor temperature used for the heating degree-days (°C). In ``states``.
OUTDOOR_TEMPERATURE_ENTITY: str = "sensor.temperatura_meteo"

# Indoor relative humidity of each space (%). In ``states``.
SPACE_HUMIDITY_ENTITY: dict[str, str] = {
    # --- Edificio Fermín Caballero ---
    "A11": "sensor.sensor_humedad_a11",
    "A12": "sensor.sensor_humedad_a12",
    "A21": "sensor.sensor_humedad_a21",
    "A22": "sensor.sensor_humedad_a22",
    "F0.1": "sensor.humedad_shelly1",
    "F0.2": "sensor.humedad_shelly4",
    "F1.1": "sensor.humedad_shelly5",
    "LD1": "sensor.humedad_shelly13",
    "LD2": "sensor.humedad_shelly14",
    "LD3": "sensor.humedad_shelly2",
    "LD4": "sensor.humedad_shelly3",
    "Grados": "sensor.humedad_shelly7",
    "Actos": "sensor.humedad_shelly8",
    "Calculo": "sensor.humedad_shelly9",
    # --- Módulo B ---
    "AnitaBorg": "sensor.humedad_shelly6",
    "Secretaria": "sensor.humedad_shelly16",
    "Direccion": "sensor.humedad_shelly17",
    "ColegioUniversitario": "sensor.humedad_shelly18",
    "MonicoSanchez": "sensor.humedad_shelly15",
}

# CO2 concentration (ppm) of the spaces that have an air-quality sensor. Only
# the four classrooms of the Fermín Caballero building are instrumented; the
# rest of the spaces fall back to the synthetic model.
SPACE_CO2_ENTITY: dict[str, str] = {
    "A11": "air_quality.co2_3",
    "A12": "air_quality.co2_1",
    "A21": "air_quality.co2_2",
    "A22": "air_quality.co2_4",
}


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

# Indoor temperature of each space (°C). In ``states``.
SPACE_TEMPERATURE_ENTITY: dict[str, str] = {
    # --- Edificio Fermín Caballero ---
    "A11": "sensor.sensor_temperatura_a11",
    "A12": "sensor.sensor_temperatura_a12",
    "A21": "sensor.sensor_temperatura_a21",
    "A22": "sensor.sensor_temperatura_a22",
    "F0.1": "sensor.temperatura_shelly1",
    "F0.2": "sensor.temperatura_shelly4",
    "F1.1": "sensor.temperatura_shelly5",
    "LD1": "sensor.temperatura_shelly13",
    "LD2": "sensor.temperatura_shelly14",
    "LD3": "sensor.temperatura_shelly2",
    "LD4": "sensor.temperatura_shelly3",
    "Grados": "sensor.temperatura_shelly7",
    "Actos": "sensor.temperatura_shelly8",
    "Calculo": "sensor.temperatura_shelly9",
    # --- Módulo B ---
    "AnitaBorg": "sensor.temperatura_shelly6",
    "Secretaria": "sensor.temperatura_shelly16",
    "Direccion": "sensor.temperatura_shelly17",
    "ColegioUniversitario": "sensor.temperatura_shelly18",
    "MonicoSanchez": "sensor.temperatura_shelly15",
}
