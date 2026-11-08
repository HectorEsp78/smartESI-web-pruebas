"""Device catalogue and thresholds for the Maintenance tab.

Only devices whose entities are confirmed in the recorder are listed. The tab
is deliberately small: 18 Shelly H&T sensors, the four A11-A22 CO2/climate
sensors, the three presence sensors, the six Fleximodo parking sensors, the gas
pulse counter, the weather station, the five TRV valves and the key wired
meters/controllers/people counters.

The distinction between ``periodic`` and ``event`` is important:

- ``periodic`` devices write a heartbeat regularly (temperature, CO2, meter
  reading...). A long silence is a real signal.
- ``event`` devices only write when their state changes (presence, parking,
  people counters). A long gap can be perfectly normal, so they are not
  flagged as silent unless they are unavailable for several days.

Battery entities can also be stale without the device being offline: the Shelly
battery entity only changes when the percentage changes, while the temperature
heartbeat keeps arriving. The service therefore separates *battery age* from
*device silence*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MaintenanceMode = Literal["periodic", "event"]
BatteryUnit = Literal["percent", "millivolt"]

# --- Battery thresholds -------------------------------------------------------

BATTERY_CRITICAL_PCT = 20.0
BATTERY_LOW_PCT = 40.0
BATTERY_MEDIUM_PCT = 60.0

BATTERY_CRITICAL_MV = 3200.0
BATTERY_LOW_MV = 3400.0
BATTERY_MEDIUM_MV = 3500.0

# A jump of at least 20 points (or 5 % -> 80 %) is treated as a replacement.
BATTERY_REPLACEMENT_JUMP_PCT = 20.0
BATTERY_REPLACEMENT_LOW_PCT = 5.0
BATTERY_REPLACEMENT_HIGH_PCT = 80.0

# A battery reading older than this is shown as stale, but it is only turned
# into ``unknown`` when the device itself has also been offline for a long time.
BATTERY_STALE_HOURS = 24.0 * 7.0
BATTERY_UNKNOWN_OFFLINE_HOURS = 24.0 * 90.0

# Event-driven devices are considered offline after this many days without data.
EVENT_OFFLINE_HOURS = 24.0 * 7.0

# --- Transmission thresholds --------------------------------------------------

# Devices expected to report more often than this get a 2 h minimum silence
# threshold; slower devices get 24 h so a normal nightly gap is not an alert.
HIGH_FREQUENCY_MAX_MINUTES = 30.0
SILENCE_MIN_HOURS_HIGH_FREQ = 2.0
SILENCE_MIN_HOURS_LOW_FREQ = 24.0
SILENCE_MULTIPLIER = 3.0

# More than this multiple of the expected rate is shown as over-reporting.
OVER_REPORTING_FACTOR = 3.0

# At least this many non-global gaps in the period marks the device as unstable.
INTERMITTENT_MIN_GAPS = 2

# --- Outage correlation -------------------------------------------------------

GLOBAL_OUTAGE_MIN_SHARE = 0.5
GLOBAL_OUTAGE_MIN_DEVICES = 3
GROUP_OUTAGE_MIN_SHARE = 0.5
GROUP_OUTAGE_MIN_DEVICES = 2
OUTAGE_CLUSTER_TOLERANCE_HOURS = 3.0

# --- Trend and period ---------------------------------------------------------

BATTERY_TREND_DAYS = 30
BATTERY_HISTORY_DAYS = 90
DEFAULT_MAINTENANCE_DAYS = 30
ALLOWED_MAINTENANCE_DAYS = (7, 30, 90)

# Piecewise Li-SOCl2 / 3.6 V cell curve used only for an approximate percentage.
# The raw millivolts remain the authoritative value.
MV_PERCENT_CURVE: tuple[tuple[float, float], ...] = (
    (3600.0, 100.0),
    (3500.0, 80.0),
    (3400.0, 60.0),
    (3300.0, 40.0),
    (3200.0, 20.0),
    (3100.0, 10.0),
    (3000.0, 5.0),
    (2900.0, 0.0),
)


@dataclass(frozen=True)
class MaintenanceDevice:
    id: str
    label: str
    type: str
    location: str | None
    mode: MaintenanceMode
    heartbeat_entity: str
    expected_interval_min: float | None = None
    battery_entity: str | None = None
    battery_attribute: str | None = None
    battery_unit: BatteryUnit | None = None
    notes: str | None = None

    @property
    def has_battery(self) -> bool:
        return self.battery_entity is not None

    @property
    def is_periodic(self) -> bool:
        return self.mode == "periodic"


def _shelly(index: int) -> MaintenanceDevice:
    return MaintenanceDevice(
        id=f"shelly{index}",
        label=f"Shelly {index}",
        type="Shelly H&T",
        location=None,
        mode="periodic",
        heartbeat_entity=f"sensor.temperatura_shelly{index}",
        expected_interval_min=120.0,
        battery_entity=f"sensor.bateria_shelly{index}",
        battery_unit="percent",
        notes="Ubicación sin confirmar en el recorder.",
    )


def _room(room_id: str, co2_entity: str) -> MaintenanceDevice:
    return MaintenanceDevice(
        id=f"room_{room_id.lower()}",
        label=f"Sensor {room_id.upper()}",
        type="Sensor CO₂/clima",
        location=room_id.upper(),
        mode="periodic",
        heartbeat_entity=co2_entity,
        expected_interval_min=5.0,
        battery_entity=f"sensor.sensor_bateria_{room_id.lower()}",
        battery_unit="millivolt",
        notes="La batería es la del sensor de CO₂ (Vdd). El resto de magnitudes salen del mismo equipo.",
    )


def _presence(index: int, label: str, location: str) -> MaintenanceDevice:
    return MaintenanceDevice(
        id=f"presence_{location.lower().replace(' ', '_').replace('.', '')}",
        label=label,
        type="Sensor de presencia",
        location=location,
        mode="event",
        heartbeat_entity=f"sensor.presencia{index}",
        battery_entity=f"sensor.presencia{index}",
        battery_attribute="battery",
        battery_unit="percent",
        notes="Solo escribe cuando cambia la ocupación; su silencio no implica avería.",
    )


def _fleximodo(index: int) -> MaintenanceDevice:
    return MaintenanceDevice(
        id=f"fleximodo{index}",
        label=f"Fleximodo plaza {index}",
        type="Sensor de parking",
        location=f"Parking · plaza {index}",
        mode="event",
        heartbeat_entity=f"sensor.fleximodo{index}",
        battery_entity=f"sensor.fleximodo{index}",
        battery_attribute="battery_percent_est",
        battery_unit="percent",
        notes="Solo escribe cuando cambia la plaza. El atributo de batería puede no ser fiable.",
    )


def _valve(key: str, label: str, location: str, heartbeat: str) -> MaintenanceDevice:
    return MaintenanceDevice(
        id=f"valve_{key}",
        label=label,
        type="Válvula TRV",
        location=location,
        mode="event",
        heartbeat_entity=heartbeat,
        battery_entity=f"sensor.bateria_valvula_{key}",
        battery_unit="percent",
        notes="Batería no fiable y dispositivo sin datos desde hace días.",
    )


def _meter(key: str, label: str, entity: str) -> MaintenanceDevice:
    return MaintenanceDevice(
        id=f"meter_{key}",
        label=label,
        type="Contador eléctrico",
        location=label,
        mode="periodic",
        heartbeat_entity=entity,
        expected_interval_min=15.0,
    )


def _light_controller(index: int, label: str, entity: str) -> MaintenanceDevice:
    return MaintenanceDevice(
        id=f"light_controller_{index}",
        label=label,
        type="Controlador de iluminación",
        location=label,
        mode="periodic",
        heartbeat_entity=entity,
        expected_interval_min=20.0,
    )


DEVICES: tuple[MaintenanceDevice, ...] = (
    *(_shelly(index) for index in range(1, 19)),
    _room("A11", "air_quality.co2_3"),
    _room("A12", "air_quality.co2_1"),
    _room("A21", "air_quality.co2_2"),
    _room("A22", "air_quality.co2_4"),
    _presence(3, "Presencia F0.2", "F0.2"),
    _presence(2, "Presencia ALU", "ALU"),
    _presence(1, "Presencia Anita Borg", "Anita Borg"),
    *(_fleximodo(index) for index in range(1, 7)),
    MaintenanceDevice(
        id="gas",
        label="Contador de gas",
        type="Contador de pulsos",
        location="Edificio",
        mode="periodic",
        heartbeat_entity="sensor.gas",
        expected_interval_min=10.0,
        battery_entity="sensor.gas",
        battery_attribute="Battery",
        battery_unit="percent",
        notes="La batería y el pulso de gas llegan en el mismo mensaje.",
    ),
    MaintenanceDevice(
        id="meteo",
        label="Estación meteorológica",
        type="Estación meteorológica",
        location="Edificio",
        mode="periodic",
        heartbeat_entity="weather.meteo",
        expected_interval_min=15.0,
        battery_entity="weather.meteo",
        battery_attribute="Battery",
        battery_unit="percent",
        notes="La batería se publica como atributo del estado meteorológico.",
    ),
    _valve("f1_1", "Válvula F1.1", "Laboratorio F1.1", "sensor.temperatura_valvula_f1_1"),
    _valve("ld1", "Válvula LD1", "Laboratorio LD1", "sensor.bateria_valvula_ld1"),
    _valve("ld2", "Válvula LD2", "Laboratorio LD2", "sensor.temperatura_valvula_ld2"),
    _valve("ld3", "Válvula LD3", "Laboratorio LD3", "sensor.temperatura_valvula_ld3"),
    _valve("ld4", "Válvula LD4", "Laboratorio LD4", "sensor.temperatura_valvula_ld4"),
    _meter("general", "Cuadro General", "sensor.cuadro_general"),
    _meter("modulo_a", "Módulo A", "sensor.edificio_a"),
    _meter("modulo_b", "Módulo B", "sensor.edificio_b"),
    _meter("cpd", "CPD", "sensor.sala_computacion"),
    _light_controller(
        1,
        "Controlador 1 · P3 pasillo",
        "light.controller1_planta3_cuadro_luz_pasillo",
    ),
    _light_controller(
        2,
        "Controlador 2 · P3 impresoras",
        "light.controller2_planta3_sala_impresoras",
    ),
    _light_controller(
        3,
        "Controlador 3 · PB conserjería",
        "light.controller3_planta_baja_conserjeria",
    ),
    _light_controller(
        4,
        "Controlador 4 · PB aseos",
        "light.controller4_planta_baja_aseos",
    ),
    _light_controller(
        5,
        "Controlador 5 · P1 izquierda",
        "light.controller5_planta1_izquierda",
    ),
    _light_controller(
        6,
        "Controlador 6 · P2 izquierda",
        "light.controller6_planta_segunda_izquierda",
    ),
    _light_controller(
        7,
        "Controlador 7 · P2 derecha",
        "light.controller7_planta_segunda_derecha",
    ),
    MaintenanceDevice(
        id="people_fermin",
        label="Contador de personas Fermín",
        type="Contador de personas",
        location="Fermín Caballero",
        mode="event",
        heartbeat_entity="sensor.vs133",
        notes="Solo escribe cuando alguien cruza; no tiene latido periódico.",
    ),
    MaintenanceDevice(
        id="people_modulo_b",
        label="Contador de personas Módulo B",
        type="Contador de personas",
        location="Módulo B",
        mode="event",
        heartbeat_entity="sensor.contador_personas",
        notes="Solo escribe cuando alguien cruza; no tiene latido periódico.",
    ),
    MaintenanceDevice(
        id="ambient",
        label="Sensor ambiente",
        type="Sensor ambiental",
        location="Edificio",
        mode="periodic",
        heartbeat_entity="sensor.ambiente",
        expected_interval_min=15.0,
        notes="Referencia ambiental sin sala confirmada.",
    ),
)

DEVICES_BY_ID: dict[str, MaintenanceDevice] = {device.id: device for device in DEVICES}

# Entities whose last known value is very old (legacy valves) need a longer
# lookback than the rest of the catalogue.
LEGACY_DEVICE_IDS = frozenset({"valve_ld1"})


def device_label(device_id: str) -> str:
    device = DEVICES_BY_ID.get(device_id)
    return device.label if device else device_id


def expected_per_day(device: MaintenanceDevice) -> float | None:
    if device.expected_interval_min is None or device.expected_interval_min <= 0:
        return None
    return 24.0 * 60.0 / device.expected_interval_min


def silence_threshold_hours(
    device: MaintenanceDevice,
    p95_interval_hours: float | None = None,
) -> float | None:
    """Threshold above which a periodic device is considered silent.

    The threshold uses the observed p95 when available, the configured expected
    interval and a per-device minimum. Low-frequency devices (Shelly H&T) get a
    24 h floor so their normal nightly gap is not reported as an incident.
    """
    if not device.is_periodic or device.expected_interval_min is None:
        return None

    expected_hours = device.expected_interval_min / 60.0
    if expected_hours <= HIGH_FREQUENCY_MAX_MINUTES / 60.0:
        minimum = SILENCE_MIN_HOURS_HIGH_FREQ
    else:
        minimum = SILENCE_MIN_HOURS_LOW_FREQ

    candidates = [expected_hours * SILENCE_MULTIPLIER, minimum]
    if p95_interval_hours is not None and p95_interval_hours > 0:
        candidates.append(p95_interval_hours * SILENCE_MULTIPLIER)
    return max(candidates)


NOTES: tuple[str, ...] = (
    "La batería y el latido del dispositivo se miden por separado: una batería sin cambios no significa que el sensor esté caído.",
    "Los sensores de presencia, parking y contadores de personas solo escriben cuando cambia su estado; su silencio no se trata como avería.",
    "Los cortes globales o de grupo se separan de las caídas individuales para no convertir una caída del recorder en decenas de averías.",
    "La disponibilidad y el MTBF/MTTR son aproximados: se calculan a partir de huecos de datos, no de un registro de reparaciones.",
    "En A11-A22 el porcentaje de batería es una estimación a partir del voltaje (mV); el valor real es el mV.",
    "Las válvulas no tienen una lectura de batería fiable y llevan días sin datos.",
    "Shelly 1–18 no tienen una ubicación confirmada en el recorder.",
    "El atributo de batería de Fleximodo puede ser poco fiable (siempre 100 % / 13.000 mAh).",
)
