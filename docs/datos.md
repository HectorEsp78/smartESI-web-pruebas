# Datos: origen, modelo sintético y migración

Este documento explica **de dónde salen los datos** que pinta el panel, **cómo se generan**
mientras no hay base de datos y **qué habría que cambiar** para usar la instalación real.

- Con `DATA_SOURCE=mock` (por defecto) el backend **inventa** los datos de forma determinista.
- Con `DATA_SOURCE=database` lee de la base de datos del *recorder* de Home Assistant **solo con
  `SELECT`**. Ya está implementado para **Electricidad**, **Climatización/gas**, **Ocupación** y
  **CO₂/aire**; la iluminación (y el reparto de ocupación por aula) sigue en sintético.
- El **contrato de la API no cambia** entre ambos modos: los *schemas* Pydantic y el frontend son
  los mismos. Solo cambia la capa de datos que usa cada servicio.

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
(`STATS_CACHE_TTL_SECONDS`, 30 s; el clima usa como mínimo 300 s porque un `year` real es costoso).
Ver [`docs/arquitectura.md`](arquitectura.md).

El detalle de qué estadístico sale de qué fuente está en
[`docs/estadisticos.md`](estadisticos.md).

---

## 4. Datos reales y mapa de migración

Con `DATA_SOURCE=database` el backend lee la BD del *recorder* de Home Assistant **solo con `SELECT`**
(ver [`docs/backend.md`](backend.md) para el detalle de conexión y consultas). La correspondencia
entidad → edificio/espacio se declara **explícitamente** en
[`backend/app/db/entity_map.py`](../backend/app/db/entity_map.py), igual que hoy hace `energy_map.py`.

### 4.1 Estado por estadístico

| Estadístico | Origen real | Estado |
| ----------- | ----------- | ------ |
| Electricidad del centro | `statistics.sum` de `sensor.cuadro_general` (kWh). Es el mismo contador del “cuadro general” de HA. | ✅ Real |
| Electricidad por edificio | `statistics.sum` de `sensor.edificio_a` / `sensor.edificio_b` (kWh). Son **subcontadores parciales** (≈3–15 % del total), no los contadores generales de cada edificio. | ✅ Real (parcial) |
| Gas del sitio | `statistics.sum` de `sensor.daily_gas` (m³ → kWh con `GAS_KWH_PER_M3`). Solo `building=all`. | ✅ Real |
| Grados-día | `statistics.mean`/`states` de `sensor.temperatura_meteo` + `HEATING_BASE_TEMPERATURE_C`. | ✅ Real |
| Temperatura interior por espacio | `statistics.mean`/`states` de `sensor.sensor_temperatura_aXX` y `sensor.temperatura_shellyN`. | ✅ Real |
| Humedad interior por espacio | `statistics.mean`/`states` de `sensor.sensor_humedad_aXX` y `sensor.humedad_shellyN`. | ✅ Real |
| Ocupación por edificio | Contadores de entrada/salida: estado de `sensor.entrada_fermin_caballero`/`sensor.salida_fermin_caballero`; atributos `LTR_SUM`/`RTL_SUM` de `sensor.contador_personas`. | ✅ Real |
| Reparto de ocupación por aula | Los contadores son por edificio; el reparto relativo entre aulas es sintético. | ⛔ Mock |
| Electroválvulas | No existe entidad de válvula en la BD. | ⛔ Mock |
| Iluminación | `light.controller1..7` y `sensor.sensor_luz_aXX` existen, pero falta confirmar el mapeo a espacios y la potencia por circuito. | ⛔ Mock |
| CO₂ / aire | `air_quality.co2_3`, `co2_1`, `co2_2` y `co2_4` (A11, A12, A21, A22). El resto de espacios, mock. | ✅ Real (4 aulas) |
| Eficiencia (kWh/persona·hora) | Total del cuadro general + ocupación real; el desglose por edificio/espacio usa los subcontadores A/B y se reparte por superficie. | ✅ Real (total) · ⚠️ Parcial (desglose) |

> El **total eléctrico** sale de `sensor.cuadro_general`, igual que en el panel de energía de HA.
> Los contadores `sensor.edificio_a` y `sensor.edificio_b` solo cubren una parte del consumo, así que
> `/energy/by-building` y `/energy/efficiency` devuelven también `submetered_total`,
> `unmetered_total` y `coverage`. La UI muestra el resto como **“No desglosado”** para que las barras
> sumen el total real sin inventar un reparto por edificio.
>
> El **gas** se sirve solo para el conjunto del centro porque en la instalación hay **un único
> contador**. Al pedir un edificio concreto, el gas es `0` (la temperatura y los grados-día sí son
> reales). La **ocupación** ya es real a nivel de edificio, pero las **válvulas** siguen siendo
> sintéticas: el gas estimado en aulas vacías (`/climate/empty-spaces`) reparte el gas real según
> ese modelo, así que es una **estimación**.
>
> El **CO₂** solo es real en las cuatro aulas instrumentadas; en el resto de espacios y en Módulo B
> la gráfica de ocupación–aire usa el modelo sintético para esas series. Los contadores de personas
> pueden descuadrarse si se reinician o pierden lecturas; se acotan al aforo del edificio.

### 4.2 Cómo se convierte la BD en series horarias

En [`backend/app/db/database_data.py`](../backend/app/db/database_data.py):

- **Contadores (`statistics.sum`)**: la energía de una hora es la diferencia entre dos lecturas
  acumuladas consecutivas. HA guarda el `sum` al **final** del periodo: la diferencia entre las filas
  de 10:00 y 11:00 es el consumo de 11:00–12:00 y se asigna a la hora **11:00** (la fila actual), no
  a la anterior. Es la misma convención del panel de energía de HA.
  - Los volcados de HA tras un corte (varios días planos y luego un salto) se **reparten** entre las
    horas del hueco: son consumo real.
  - Los valores negativos (reinicio del contador) y los que superan el tope
    (`ENERGY_MAX_KWH_PER_HOUR`, `GAS_MAX_M3_PER_HOUR`) se **descartan**.
  - El `sum` del gas tiene periodos con saltos corruptos: al ser irreales, se descartan en bloque.
- **Estados (`states`)**: media de las lecturas numéricas por hora. Como HA solo escribe al cambiar el
  valor, se rellena hacia delante con el último valor conocido (*fill-forward*), sembrado con el
  último estado anterior a la ventana.
- Los *timestamps* de HA son UTC sin zona; la conversión a hora local (Europe/Madrid) se hace en
  Python, con `SET time_zone='+00:00'` en la sesión.

### 4.3 Pendiente

- Mapear iluminación (`light.controller1..7`, `sensor.sensor_luz_aXX`) a edificios/espacios y
  obtener una medida de potencia o consumo por circuito; hasta entonces la pestaña sigue en mock.
- Reparto real de la ocupación por aula (los contadores actuales son por edificio).
- Electroválvulas: no existen como entidad; si se añaden, sustituir el modelo de válvulas.
- Ampliar el CO₂ a más espacios (hoy solo A11/A12/A21/A22).
- Optimizar `statistics.mean` para más sensores: ya se usa cuando existe, y queda el *fallback* a
  `states` para los que no tienen estadísticas de largo plazo.
