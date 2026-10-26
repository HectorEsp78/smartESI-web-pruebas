# Backend (FastAPI + Pydantic)

Código en [`backend/app/`](../backend/app). Es una API de solo lectura que sirve estadísticas
agregadas. Con `DATA_SOURCE=mock` (por defecto) no necesita base de datos; con
`DATA_SOURCE=database` lee la base de datos real del *recorder* de Home Assistant **solo con
`SELECT`**.

## Stack

| Pieza | Uso |
| ----- | --- |
| FastAPI | Framework HTTP y validación de parámetros. |
| Uvicorn | Servidor ASGI. |
| Pydantic v2 | Modelos de respuesta (contrato de la API) y validación de query params. |
| pydantic-settings | Configuración desde variables de entorno / `.env`. |
| SQLAlchemy + aiomysql | Solo con `DATA_SOURCE=database` (extra `database`). |

## Capas

```text
api/ (routers)  →  services/ (lógica + agregación)  →  core/ (config, energy_map, clock, cache)
                                    ↘  schemas/ (respuestas Pydantic)
                                    ↘  db/ (solo DATA_SOURCE=database: modelos HA + repositorio)
```

- **`api/`**: un router por dominio (`energy.py`, `electricity.py`, `lighting.py`, `climate.py`,
  `decisions.py`, `correlation.py`, `meta.py`). Valida el edificio y delega en el servicio; no contiene lógica de
  negocio. Todos se registran bajo `/api/v1` en `main.py`. Son `async` para poder esperar a la BD.
- **`services/`**:
  - `mock_data.py` genera los valores base por hora (energía, ocupación, CO₂, temperatura, humedad,
    meteorología, luz natural, luminarias, válvulas y gas) de forma determinista.
  - `stats.py` aporta la estadística descriptiva (media, mediana, desviación, percentiles,
    correlación y regresión) que comparten los demás servicios.
  - `energy_service.py` agrega consumo, por edificio, desglose (carga base/actividad/luz), comparativa
    con el periodo anterior y eficiencia (kWh/m² y kWh/persona·hora). En modo BD, la energía horaria
    y la ocupación de cada edificio salen del repositorio; el reparto por espacio sigue en mock.
  - `electricity_service.py` implementa la pestaña nueva de Electricidad: rangos de fechas
    absolutos, granularidad día/semana/mes/año, métrica consumo/coste, tres edificios, sectores
    parciales de Fermín, base de centro cerrado y comparativa de dos periodos.
  - `lighting_service.py` separa luminarias del resto, reparte por espacio y calcula el despilfarro
    (luz sin ocupación) con su €/año. La energía sigue siendo sintética, pero la ocupación es real
    en modo BD.
  - `climate_service.py` calcula gas y grados-día, el estado de las electroválvulas frente a la
    temperatura de cada aula, y el gas gastado en espacios vacíos. En modo BD, el gas, las
    temperaturas y la ocupación del edificio son reales; las válvulas y el reparto por aula siguen
    en mock.
  - `decisions_service.py` traduce los cruces anteriores a un **ranking de oportunidades** con €/año.
  - `correlation_service.py` cruza ocupación (real por edificio) y CO₂ (real en A11/A12/A21/A22).
  - Todos los servicios exponen `clear_cache()`.
- **`core/`**: `config.py` (ajustes), `energy_map.py` (catálogo general de edificios y espacios),
  `electricity_map.py` (mapa específico de la pestaña de Electricidad: edificios, cuadros y CPD),
  `clock.py` (UTC local) y `cache.py` (caché TTL).
- **`db/`** (solo se importa con `DATA_SOURCE=database`):
  - `session.py`: engine async (`mysql+aiomysql`) con TLS y `SET time_zone='+00:00'`.
  - `models/ha.py`: mapeo SQLAlchemy de `states`, `statistics` y `statistics_meta`.
  - `entity_map.py`: qué entidad de Home Assistant corresponde a cada edificio/espacio.
  - `repository.py`: las consultas `SELECT` (agregación horaria en SQL).
  - `database_data.py`: convierte las filas en series horarias en hora local (deltas, *fill-forward*).
- **`schemas/`**: modelos Pydantic que definen exactamente lo que ve el frontend.

## Configuración (`backend/.env`)

Copia `.env.example` a `.env`. Variables principales:

| Variable | Por defecto | Descripción |
| -------- | ----------- | ----------- |
| `DATA_SOURCE` | `mock` | `mock` (sintético) o `database` (BD real). |
| `ENERGY_PRICE_EUR_PER_KWH` | `0.20` | Precio de la electricidad para la métrica de coste (€). |
| `CO2_KG_PER_KWH` | `0.15` | Factor de emisiones de la electricidad (kg CO₂/kWh). |
| `ENERGY_MAX_KWH_PER_HOUR` | `150.0` | Tope de plausibilidad del consumo eléctrico horario (saltos mayores se ignoran). |
| `GAS_PRICE_EUR_PER_KWH` | `0.06` | Precio del gas (€/kWh). |
| `GAS_CO2_KG_PER_KWH` | `0.20` | Factor de emisiones del gas (kg CO₂/kWh). |
| `GAS_KWH_PER_M3` | `10.35` | Conversión m³ → kWh del contador real de gas. |
| `GAS_MAX_M3_PER_HOUR` | `50.0` | Tope de plausibilidad del gas horario (saltos mayores se ignoran). |
| `HEATING_BASE_TEMPERATURE_C` | `18.0` | Base para los grados-día de calefacción (°C). |
| `USE_STATISTICS_FOR_STATES` | `true` | Lee temperaturas/humedad de `statistics` (media horaria) en vez de recorrer `states`; si un sensor no tiene estadísticas, cae a `states`. |
| `STATS_CACHE_TTL_SECONDS` | `30` | TTL de la caché de agregaciones (clima usa como mínimo 300 s). |
| `TIMEZONE` | `Europe/Madrid` | Zona para el cálculo de horas/días/meses. |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5174,...` | Orígenes permitidos. |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSL`, `DB_SSL_CA` | — | Conexión a MariaDB (solo `DATA_SOURCE=database`). Con `DB_SSL=true` y `DB_SSL_CA` vacío se cifra sin verificar el certificado. |

## Añadir un edificio o un espacio

Todo el catálogo está en [`app/core/energy_map.py`](../backend/app/core/energy_map.py):

- `BUILDINGS`: un `BuildingConfig` por edificio (id, etiqueta, aforo, carga base en kW, consigna
  `setpoint_c` y `gas_base_kw` de la caldera).
- `SPACES`: un `SpaceConfig` por espacio (id, etiqueta, edificio, tipo, `weight`, `area_m2`,
  `lighting_kw` y `has_valve`). Los pesos se normalizan por edificio, así que no hace falta que
  sumen 1.

Al añadir entradas, el endpoint `/api/v1/meta/buildings`, los selectores del frontend y las gráficas
de edificio/espacio se actualizan solos. **La pestaña de Electricidad es independiente**: su catálogo
está en `app/core/electricity_map.py` y se publica en `/api/v1/energy/electricity/meta`.

El mapa de espacios y aforos se ha tomado del proyecto original (`sensor_map.py`) para que los
nombres resulten familiares; las cifras de consumo y de clima, en cambio, son simuladas.

## Añadir un estadístico nuevo

1. Añade la primitiva al generador sintético (`mock_data.py`) si hace falta un dato nuevo.
2. Implementa la agregación en el servicio del dominio correspondiente (o crea uno nuevo) y añade
   los campos al schema Pydantic.
3. Expón el endpoint en el router y regístralo (ya lo está si reutilizas el router existente).
4. Añade un test que compruebe las invariantes (cuántos puntos, coherencia de totales, 404…).

## API de Electricidad

La pestaña nueva usa tres endpoints bajo `/api/v1`:

| Endpoint | Uso |
| -------- | --- |
| `GET /energy/electricity/meta` | Catálogo de edificios, sectores, fecha de inicio de datos, precio aplicado y origen (`mock`/`database`). |
| `GET /energy/electricity` | Serie, KPIs, desglose por edificio y sectores para un rango de fechas. |
| `GET /energy/electricity/compare` | Dos periodos independientes alineados por número de intervalos, con base común. |

Parámetros principales de `/energy/electricity`:

- `start`, `end` (`YYYY-MM-DD`, ambos inclusive; máximo 6 años).
- `granularity`: `day`, `week`, `month` o `year`.
- `metric`: `kwh` o `cost` (coste = kWh × `ENERGY_PRICE_EUR_PER_KWH`).
- `building`: `all`, `ModuloA`, `ModuloB` o `FerminCaballero`.
- `sector`: opcional, solo si pertenece a Fermín (`PB_D`, `P1_F`, `CPD`, etc.).

La respuesta separa siempre:

- `stats`: total, media, mínimo, máximo y base del ámbito seleccionado;
- `buildings`: los tres edificios, con su serie y su porcentaje sobre el centro;
- `sectors`: cuadros de Fermín y CPD, con `has_data` y `share_of_building`;
- `sectors_total`, `unmetered_total` y `sector_coverage`, para que el desglose parcial reconciliable
  con el total de Fermín sea explícito.

`/energy/electricity/compare` añade `start_a/end_a/start_b/end_b` y exige el mismo número de
intervalos en ambos periodos. Devuelve series alineadas (`period_a`, `period_b`, `baseline`), KPIs
por periodo y `delta_pct`.

> **Solo lectura.** Todos los accesos al recorder son `SELECT`. La caché TTL evita repetir la
> misma agregación; `electricity_service.clear_cache()` la vacía en tests.

## Base de datos real (estado de la migración)

El modo `DATA_SOURCE=database` está implementado para **Electricidad**, **Climatización/gas**,
**Ocupación** y **CO₂/aire**. Todo es **solo lectura** (`SELECT`): el backend nunca escribe en las
tablas de Home Assistant. La iluminación sigue en mock porque no hay un mapeo confirmado
controlador → edificio/espacio (ver más abajo).

### Qué es real y qué sigue en mock

| Dato | Modo BD | Fuente |
| ---- | ------- | ------ |
| Energía eléctrica del centro | **Real** | `statistics.sum` de `sensor.cuadro_general` (el “cuadro general” de HA). |
| Energía Módulo A | **Real** | `statistics.sum` de `sensor.edificio_a`. |
| Energía Módulo B | **Real** | `statistics.sum` de `sensor.edificio_b`. |
| Energía Fermín Caballero | **Real derivada** | `sensor.cuadro_general − sensor.edificio_a − sensor.edificio_b`; no existe un contador único de Fermín. |
| Sectores de Fermín | **Real parcial** | `statistics.sum` de los cuadros `sensor.planta_*` y de `sensor.sala_computacion` (CPD). Cubren ≈30–38 % de Fermín; el resto se expone como `unmetered_total` y `sector_coverage`. |
| Gas (sitio completo) | **Real** | `statistics.sum` de `sensor.daily_gas` (m³ → kWh con `GAS_KWH_PER_M3`). Solo se sirve para `building=all`; en un edificio concreto el gas es `0` (hay un único contador). |
| Temperatura exterior (grados-día) | **Real** | `statistics.mean` o, si no hay, `states` de `sensor.temperatura_meteo`. |
| Temperatura interior por espacio | **Real** | `statistics.mean`/`states` de `sensor.sensor_temperatura_aXX` y `sensor.temperatura_shellyN`. |
| Humedad interior por espacio | **Real** | `statistics.mean`/`states` de `sensor.sensor_humedad_aXX` y `sensor.humedad_shellyN`. |
| CO₂ de A11/A12/A21/A22 | **Real** | `states` de `air_quality.co2_3`, `co2_1`, `co2_2` y `co2_4`. |
| Ocupación por edificio | **Real** | Diferencia de los contadores de entrada/salida (`max(0, entrada − salida)`); Módulo B usa los atributos `LTR_SUM`/`RTL_SUM` de `sensor.contador_personas`. |
| Reparto de la ocupación por aula | Mock | Los contadores son por edificio; el reparto relativo entre aulas sigue el modelo por superficie. |
| Electroválvulas | Mock | No existe entidad de válvula en la BD. |
| Iluminación | Mock | `light.controller1..7` / `sensor.sensor_luz_aXX` existen, pero no hay un mapeo confirmado a cada espacio ni una medida de potencia por circuito. |
| CO₂ de espacios sin sonda | Mock | Solo A11/A12/A21/A22 tienen sonda; el resto usa el modelo (se documenta así en la respuesta). |
| Eficiencia (kWh/persona·hora) | **Real (total) / parcial (desglose)** | El total eléctrico sale del cuadro general y la ocupación de los contadores; el reparto por edificio/espacio usa los subcontadores A/B y se distribuye por superficie. |

### Cómo se leen los datos

- `db/session.py` fija `SET time_zone='+00:00'`: HA guarda *timestamps* UTC sin zona y la conversión a
  hora local (Europe/Madrid) se hace en Python.
- `db/repository.py` contiene las consultas `SELECT`:
  1. `statistics.sum` por estadístico y rango (energía y gas);
  2. `statistics.mean` por estadístico y rango (temperaturas/humedad con estadísticas de largo plazo);
  3. media horaria de un `states` numérico, agrupando con `FLOOR(UNIX_TIMESTAMP(last_updated)/3600)`;
  4. último valor (numérico o `state` + `attributes`) antes de la ventana, para el *fill-forward*;
  5. último `state`/`attributes` de cada hora, para los contadores de personas (que no se pueden
     promediar porque cambian en cada cruce de puerta).
- `db/database_data.py` convierte esas filas en series `{hora local: valor}`:
  - **energía**: la diferencia entre dos `sum` consecutivos, asignada a la hora de la fila actual
    (HA guarda el `sum` al final del periodo); si hay un hueco, se reparte entre las horas que cierran
    el intervalo (los volcados de HA tras un corte son reales); los valores negativos (reinicio del
    contador) y los que superan `ENERGY_MAX_KWH_PER_HOUR` se descartan;
  - **gas**: la diferencia se descarta si supera `GAS_MAX_M3_PER_HOUR` (el `sum` del gas tiene saltos
    corruptos en algunos periodos) y se convierte a kWh;
  - **temperaturas/humedad**: media horaria y *fill-forward* del último valor conocido; se prefiere
    `statistics` y solo se recorre `states` para los sensores sin estadísticas;
  - **ocupación**: `max(0, entrada − salida)`, acotada al aforo; un contador roto (`unavailable`,
    atributo ausente) se trata como dato no disponible, no como 0.
- `db/entity_map.py` declara explícitamente qué entidad corresponde a cada edificio y espacio.
- En `DATA_SOURCE=mock` nada de esto se importa: no hace falta SQLAlchemy ni driver.

### Rendimiento

Las agregaciones se cachean por `(rango, edificio)`. La lectura del rango `year` en clima se acelera
con `USE_STATISTICS_FOR_STATES=true`: usa la media horaria ya calculada en `statistics` para las
temperaturas y evita recorrer un año de `states` de ~22 sensores. Los sensores sin estadísticas
caen automáticamente a `states`. El clima mantiene además un TTL mínimo de 300 s.

> Referencia: el proyecto original (`pagina-web-Smart-ESI`) hace lo mismo en su `backend/app/db/` y
> `services/`. Las consultas de aquí son una versión reducida a lo que necesitan estas pestañas.

## Tests

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -t . -v
```

Cubren: número de puntos por rango, conversión de métricas (kWh→€/kg CO₂), 404 en edificio
desconocido, reparto de `share`, rangos de la correlación, endpoints de iluminación, clima y
decisiones (invariantes de totales y `€`), salud/meta, la conversión de series acumuladas a
consumo horario (reinicios y saltos irreales de los contadores) y la lectura de los contadores de
ocupación (estado/atributo JSON, reset diario y aforo).
