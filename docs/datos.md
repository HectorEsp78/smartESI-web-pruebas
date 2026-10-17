# Datos: origen, modelo sintético y migración

Este documento explica **de dónde salen los datos** que pinta el panel, **cómo se generan**
mientras no hay base de datos y **qué habría que cambiar** para usar la instalación real.

- Con `DATA_SOURCE=mock` (por defecto) el backend **inventa** los datos de forma determinista.
- Con `DATA_SOURCE=database` (futuro) leerá de la base de datos del *recorder* de Home Assistant.
- El **contrato de la API no cambia** entre ambos modos: los *schemas* Pydantic y el frontend son
  los mismos. Solo cambia la implementación de la capa `services/`.

---

## 1. Catálogo de edificios y espacios

Todo el inventario está en [`backend/app/core/energy_map.py`](../backend/app/core/energy_map.py).
Es el equivalente *placeholder* del `sensor_map.py` del proyecto original: los nombres y aforos son
los reales, pero las magnitudes energéticas son simuladas.

**Edificios** (`BUILDINGS`): un `BuildingConfig` por edificio.

| Campo | Uso |
| ----- | --- |
| `id`, `label` | Identificador y etiqueta visible. |
| `max_capacity` | Aforo, usado para convertir ocupación a `%`. |
| `base_kw` | Carga eléctrica nominal del edificio (kW). |
| `setpoint_c` | Consigna de confort de calefacción (°C). |
| `gas_base_kw` | Potencia nominal de la caldera (kW) con todas las válvulas abiertas. |

Agregados derivados:

- `BUILDINGS_LIGHTING_KW`: potencia de luminarias instalada por edificio (suma de sus espacios).
- `BUILDINGS_AREA_M2`: superficie útil por edificio (suma de sus espacios).

**Espacios** (`SPACES`): un `SpaceConfig` por espacio.

| Campo | Uso |
| ----- | --- |
| `id`, `label`, `building_id`, `kind` | Identidad (`CLASSROOM` / `LABORATORY` / `COMMON`). |
| `weight` | Peso relativo (~0..1) del espacio en la carga base del edificio. Se **normaliza** por edificio, así que no hace falta que sume 1. |
| `area_m2` | Superficie, para el ratio kWh/m² y para repartir la ocupación del edificio. |
| `lighting_kw` | Potencia de luminarias instalada, para separar luz del resto de cargas. |
| `has_valve` | Si el espacio tiene electroválvula de calefacción. |

Añadir un edificio o espacio aquí actualiza solo `/api/v1/meta/buildings`, los selectores del
frontend y todas las gráficas.

---

## 2. Generador de datos sintéticos

Vive en [`backend/app/services/mock_data.py`](../backend/app/services/mock_data.py). Todo es
**determinista**: el valor para un edificio/espacio y una hora concretos es siempre el mismo, así
que las respuestas son estables y fáciles de testear sin base de datos.

### 2.1 Aleatoriedad reproducible

No se usa `random`: cada valor "aleatorio" es un hash del contexto.

- `_uniform(*partes)`: valor en `[0, 1)` calculado con `zlib.crc32` del contexto (rápido y estable
  entre procesos).
- `_jitter(*partes, amplitude=a)`: ruido en `[-a, +a]`.
- `stable_noise` / `valve_health`: ruido público estable por espacio.
- `lru_cache` sobre las funciones clave (energía, ocupación, CO₂, temperatura, gas…) para que cada
  hora se calcule una sola vez.

### 2.2 Primitivas por hora

| Función | Qué devuelve | Modelo (resumen) |
| ------- | ------------ | ---------------- |
| `hour_energy_kwh` | kWh eléctricos del edificio en la hora | `base_kw · (perfil + 0,10) · estación · ruido(±8 %)`. |
| `hour_occupancy` | Personas en el edificio | `max_capacity · ratio · ruido(±15 %)`. |
| `hour_co2` | CO₂ (ppm) | `415 + 950·ratio` (×0,85 de madrugada) · ruido(±6 %). |
| `hour_temperature` | Temperatura interior (°C) a nivel edificio | `21 + 2,5·ratio` + estación. |
| `hour_humidity` | Humedad relativa (%) | `44 + 12·ratio`, recortada a 20–95. |
| `outdoor_temperature` | Temperatura exterior (°C) | Estacional (~4 °C en enero, ~26 °C en julio) + ciclo diario (pico ~15 h) + ruido. |
| `daylight_hours` | Horas de luz natural del día | Tabla por mes para la latitud de Ciudad Real. |
| `lighting_fraction` | Fracción de la electricidad que va a luminarias | 0,20 con luz natural suficiente (11–16 h, ≥12 h de día), 0,40 de noche, 0,33 el resto; suelo de 0,10–0,20 si está vacío. |
| `space_valve_open` | ¿La electroválvula pide calor? | `False` si exterior ≥18 °C; `False`/`True` si está atascada cerrada/abierta; si no, horario laborable (L–V, 7–21 h) y exterior <17 °C. |
| `space_occupancy` | Personas en el espacio | Ocupación del edificio repartida por superficie · ruido(±30 %). |
| `space_temperature` | Temperatura del aula (°C) | Según válvula abierta, calor reciente o aula fría, más ocupación y ruido. |
| `hour_gas_kwh` | Gas del edificio en la hora | `gas_base_kw · (válvulas abiertas / total) · (max(0, 18−exterior)/8) · ruido(±6 %)`. |

### 2.3 "Historia" que cuentan los datos

El modelo sintético está pensado para que las gráficas de decisión tengan algo que detectar:

- Algunas electroválvulas están **atascadas abiertas** (`valve_health > 0,8`): calientan aulas vacías
  de noche y en fin de semana → gas despilfarrado.
- Otras están **atascadas cerradas** (`valve_health < −0,8`): aulas frías, estado `fria`.
- Las luminarias quedan **encendidas en espacios vacíos** una fracción del tiempo → despilfarro de
  luz detectable.
- El **verano** sube la electricidad (climatización) y el **invierno** dispara el gas: los cruces
  estacionales son visibles.

### 2.4 Constantes del modelo

| Constante | Valor | Significado |
| --------- | ----- | ----------- |
| `EMPTY_OCCUPANCY_RATIO` | `0.05` | Por debajo de este ratio (ocupación/aforo) el edificio se considera **vacío**. |
| `VALVE_STUCK_THRESHOLD` | `0.8` | Umbral de `valve_health` para marcar una válvula como atascada. |
| `HEATING_BASE_TEMPERATURE_C` | `18.0` | Base para calcular los **grados-día** de calefacción. |
| Ventana laborable | L–V, 7:00–21:00 | Separa **actividad** de **carga base**. |

---

## 3. Agregación (buckets) y métricas

La agregación temporal es común a todos los dominios:

| `range` | Periodo | Buckets |
| ------- | ------- | ------- |
| `day` | últimas 24 h | 24 puntos **por hora** |
| `week` | últimos 7 días | 7 puntos **por día** |
| `month` | últimos 30 días | 30 puntos **por día** |
| `year` | últimos 12 meses | 12 puntos **por mes natural** |

Conversión de métricas (electricidad): `cost = kWh · ENERGY_PRICE_EUR_PER_KWH`,
`co2 = kWh · CO2_KG_PER_KWH`. El gas usa sus propios factores
(`GAS_PRICE_EUR_PER_KWH`, `GAS_CO2_KG_PER_KWH`).

Cada agregación pesada se calcula **una vez por (rango, edificio)** y se cachea con TTL
(`STATS_CACHE_TTL_SECONDS`, 30 s). Ver [`docs/arquitectura.md`](arquitectura.md).

El detalle de qué estadístico sale de qué fuente está en
[`docs/estadisticos.md`](estadisticos.md).

---

## 4. Mapa de migración a datos reales

Cuando se habilite `DATA_SOURCE=database`, hay que sustituir las funciones de `mock_data` por
consultas a las tablas de Home Assistant (`states`, `statistics`). El patrón es **declarar
explícitamente qué entidad corresponde a qué espacio**, igual que hoy hace `energy_map.py`.

| Estadístico sintético | Origen real previsto |
| --------------------- | -------------------- |
| Electricidad por edificio | Sensor de potencia/energía del cuadro del edificio (`statistics`). |
| Ocupación | Sensor de aforo / contador de personas. |
| CO₂, temperatura, humedad | Sensores ambientales por aula. |
| Luminarias | Submedida de alumbrado o estimación por horario y potencia instalada. |
| Electroválvulas | Entidad *switch* de la válvula de calefacción. |
| Gas | Contador de gas de la caldera. |
| Temperatura exterior y luz natural | Meteorología / integración solar. |

Pasos completos en [`docs/backend.md`](backend.md) (sección *Migrar a la base de datos real*).

> Mientras no exista el mapeo real, cualquier estadístico nuevo se añade primero al generador
> sintético; el resto de la API (schemas, routers, frontend) no se toca.
