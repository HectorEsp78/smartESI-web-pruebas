# Backend

API FastAPI que sirve las pestañas del panel. Está pensada para ejecutarse en local o en Docker y para leer el *recorder* de Home Assistant **solo con `SELECT`**.

## Estructura

```text
backend/
├── app/
│   ├── api/          Routers HTTP
│   ├── core/         Configuración, catálogo y mapas eléctrico/ambiental
│   ├── db/           SQL de solo lectura y conversión a series horarias
│   ├── models/       Tablas del recorder
│   ├── schemas/      Modelos Pydantic
│   ├── services/     Agregación y modelo sintético
│   └── main.py       Aplicación FastAPI
├── tests/            unittest
├── pyproject.toml
└── Dockerfile
```

## Arranque

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"     # añade ".[database]" para la BD real
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8010
```

- API: <http://127.0.0.1:8010>
- Swagger: <http://127.0.0.1:8010/docs>

## Endpoints

### Electricidad

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET | `/api/v1/energy/electricity/meta` | Edificios, sectores, fecha mínima, precio y `data_source`. |
| GET | `/api/v1/energy/electricity` | Serie, resumen, edificios, sectores, cobertura y base. |
| GET | `/api/v1/energy/electricity/compare` | Comparativa de dos periodos (compatibilidad). |
| GET | `/api/v1/energy/electricity/compare-many` | Comparativa de N periodos en una sola gráfica. |

Parámetros de `/energy/electricity`:

| Parámetro | Valores | Notas |
| --------- | ------- | ----- |
| `start` | `YYYY-MM-DD` | Inclusivo. |
| `end` | `YYYY-MM-DD` | Inclusivo. |
| `granularity` | `day`, `week`, `month`, `year` | La UI lo deduce del rango. |
| `metric` | `kwh`, `cost` | Coste a 0,20 €/kWh. |
| `building` | `all`, `ModuloA`, `ModuloB`, `FerminCaballero` | Por defecto `all`. |
| `sector` | id de cuadro o `CPD` | Opcional; debe pertenecer a Fermín. |

`/energy/electricity/compare` mantiene el contrato A/B (`start_a`, `end_a`, `start_b`, `end_b`) y sigue exigiendo el mismo número de intervalos. La interfaz usa `/energy/electricity/compare-many`, que recibe `start` y `end` repetidos una vez por periodo:

```
/energy/electricity/compare-many?start=2026-10-01&end=2026-10-31&start=2025-10-01&end=2025-10-31&...
```

Admite entre 2 y 12 periodos. Las series se alinean desde el inicio de cada periodo; si uno es más corto, sus intervalos restantes se devuelven como `null`. La base de centro cerrado es común y la variación de cada periodo se calcula frente al primero.

### Iluminación

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET | `/api/v1/lighting/consumption` | Serie de luminarias y otras cargas. |
| GET | `/api/v1/lighting/by-space` | Ranking de espacios. |
| GET | `/api/v1/lighting/waste` | Luz encendida sin ocupación y €/año. |

Parámetros: `range=day|week|month|year` y `building=all|<id>`.

### Infraestructura

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET | `/api/v1/environment/overview` | Índice compacto de estancias confirmadas con valores actuales y medias del periodo. |
| GET | `/api/v1/environment/rooms/{room_id}` | Detalle de una estancia: series, mapa horario y cruces para decisiones. |

Parámetros en ambas rutas:

- `start`, `end`: fechas `YYYY-MM-DD`, ambas inclusive. Por defecto, los últimos 7 días.
- El periodo máximo es de 366 días y la fecha final no puede ser futura.
- La granularidad se deduce del periodo: `hour` hasta 7 días, `day` hasta 120 días y `week` para periodos mayores.

Rutas de la interfaz:

- `/infraestructura`: índice compacto.
- `/infraestructura/{room_id}`: página de una estancia.

Devuelve solo las estancias con sensores identificados: **A11, A12, A21, A22, F0.2, Aula de Libre Uso (ALU)** y **Sala Anita Borg**. Los laboratorios y los Shelly genéricos (`sensor.temperatura_shelly*`, `sensor.humedad_shelly*`) no se incluyen mientras no exista un mapa fiable de sala.

Cada estancia incluye:

- valor actual y fecha del último dato;
- estado de confort (`good`, `moderate`, `poor`, `bad`, `unknown`);
- medias, mínimo/máximo, pico de CO₂, porcentaje de tiempo por encima de 800/1.000 ppm, ocupación, horas ocupadas y confort bueno.

El detalle añade:

- serie agregada con temperatura, humedad, CO₂, presencia y las referencias de ambiente y gas;
- mapa horario 7×24 de ocupación y CO₂;
- CO₂ con presencia frente a CO₂ sin presencia, incremento y correlación;
- recuperación térmica tras desocupar;
- comparación con la media del resto de estancias;
- contexto de gas del edificio y temperatura de referencia.

`GET /overview` mantiene el resumen del periodo (medias, estancias ocupadas, confort bueno, ocupación media) y la lista de estancias, sin series pesadas. `GET /rooms/{room_id}` reutiliza la misma carga cacheada y devuelve el detalle de una sola estancia.

`room_id` desconocido devuelve `404`. Un periodo inválido, invertido o mayor de 366 días devuelve `422`.

### Mantenimiento

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET | `/api/v1/maintenance/overview` | Estado de los dispositivos vigilados: batería, transmisión, cortes, matriz de decisión y mapa diario. |
| GET | `/api/v1/maintenance/devices/{device_id}` | Detalle de un dispositivo: historial de batería, transmisión diaria y cortes que le afectan. |

Parámetro `days`: `7`, `30` o `90`; por defecto `30`. Un valor distinto devuelve `422`. Un `device_id` desconocido devuelve `404`.

La pestaña es **solo lectura**: no escribe en el recorder ni guarda un registro de intervenciones. Cada dispositivo se clasifica como:

- `periodic`: escribe un latido con frecuencia conocida; un silencio largo es una señal real.
- `event`: solo escribe cuando cambia su estado (presencia, parking, contadores); su silencio no se interpreta como avería.

La batería y la transmisión se evalúan por separado. La entidad de batería puede llevar días sin cambiar aunque el dispositivo siga transmitiendo, así que se distingue **edad de la lectura** de **silencio del dispositivo**.

Los cortes se agrupan por proximidad temporal para separar:

- `global`: afecta a la mayoría de dispositivos a la vez; se atribuye al recorder o a la red, no a los equipos.
- `group`: afecta a varios dispositivos del mismo grupo.
- `individual`: solo afecta a ese dispositivo.

El resumen incluye baterías bajas/críticas, dispositivos sin datos, disponibilidad media (sin contar cortes globales), cambios de batería detectados y previsión de sustitución a 30/60/90 días.

### Medio Ambiente

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET | `/api/v1/weather/overview` | Estación meteorológica, resumen, series y cruces con el interior, AEMET y la energía. |

Parámetro `days`: `7`, `30` o `90`; por defecto `30`. Un valor distinto devuelve `422`.

La respuesta incluye:

- `current`: última lectura válida de `weather.meteo` (temperatura, humedad, presión, PM1/PM2.5/PM10 y batería), estado `ok|stale|missing`, edad del dato y derivados (punto de rocío, humedad absoluta, sensación térmica y tendencia de presión a 3/24 h).
- `summary`: cobertura, intervalo mediano, horas sin datos, medias/mínimos/máximos, amplitud diaria, horas de calor/frío, sequedad/humedad, noches tropicales, grados-día y PM.
- `series`: serie horaria para 7 días y diaria para 30/90 días. Incluye estación, interior, AEMET y energía.
- `daily`: resumen por día; siempre se calcula, aunque la serie sea horaria.
- `indoor_cross`: comparación con `sensor.ambiente`.
- `aemet_cross`: comparación con la referencia externa de Ciudad Real.
- `energy_cross`: gas y electricidad frente a temperatura y grados-día.
- `pm_cross`: ratios y correlaciones de las partículas.
- `notes`: criterios y limitaciones.

La pestaña es de **solo lectura**: no escribe en el recorder ni guarda un registro de intervenciones.

### Metadatos y salud

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET | `/api/v1/meta/buildings` | Edificios para los selectores. |
| GET | `/health/live` | Estado y origen de datos. |
| GET | `/health/ready` | `SELECT 1` real en modo `database`. |

## Configuración

Variables principales (`.env`):

| Variable | Defecto | Uso |
| -------- | ------- | --- |
| `DATA_SOURCE` | `database` | `mock` o `database`. |
| `DB_HOST`, `DB_PORT`, `DB_NAME` | — | Conexión al recorder. |
| `DB_USER`, `DB_PASSWORD` | — | Credenciales. |
| `DB_SSL`, `DB_SSL_CA` | `true`, vacío | TLS; sin CA se cifra sin verificar certificado. |
| `ENERGY_PRICE_EUR_PER_KWH` | `0.20` | Precio del kWh. |
| `CO2_KG_PER_KWH` | `0.15` | Factor de emisiones de la electricidad. |
| `ENERGY_MAX_KWH_PER_HOUR` | `150.0` | Tope de plausibilidad por hora. |
| `STATS_CACHE_TTL_SECONDS` | `30` | TTL de la caché. |
| `TIMEZONE` | `Europe/Madrid` | Zona de las agrupaciones. |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5174,...` | Orígenes permitidos. |

## Mapas de datos

### Electricidad — `core/electricity_map.py`

| Elemento | Estadístico | Cálculo |
| -------- | ----------- | ------- |
| Centro | `sensor.cuadro_general` | Total del sitio. |
| Módulo A | `sensor.edificio_a` | Contador directo. |
| Módulo B | `sensor.edificio_b` | Contador directo. |
| Fermín Caballero | — | `Cuadro General − Módulo A − Módulo B`. |

Sectores de Fermín:

| Sector | Estadístico | Nota |
| ------ | ----------- | ---- |
| Planta Baja · Cuadro D | `sensor.planta_baja_red_cuadro_d` | |
| Planta Baja · Cuadro E | `sensor.planta_baja_cuadro_e` | Sin datos desde 2023; `available=false`. |
| Planta Primera · Cuadro F | `sensor.planta_primera_cuadro_f` | |
| Planta Primera · Cuadro G | `sensor.planta_primera_cuadro_g` | |
| Planta Segunda · Cuadro H | `sensor.planta_primera_cuadro_h` | La entidad dice “primera”, pero el dispositivo es `P2_Cuadro_H`. |
| Planta Segunda · Cuadro I | `sensor.planta_segunda_cuadro_i` | |
| Planta Tercera · Cuadro J | `sensor.planta_tercera_cuadro_j` | |
| Planta Tercera · Cuadro K | `sensor.planta_tercera_cuadro_k` | |
| CPD | `sensor.sala_computacion` | Sala de computación. |

Los sectores son **parciales**: cubren aproximadamente el 30–38 % de Fermín según el periodo. La respuesta incluye `sectors_total`, `unmetered_total` y `sector_coverage`.

### Iluminación

- El consumo de luminarias es sintético y determinista (`services/mock_data.py`).
- La ocupación se lee de los contadores de entrada/salida cuando `DATA_SOURCE=database`; si faltan, se usa el modelo (`db/entity_map.py`).
- Los edificios del catálogo están en `core/buildings.py`.

### Infraestructura — `core/environment_map.py`

| Estancia | Temperatura / humedad | CO₂ | Presencia |
| -------- | --------------------- | --- | --------- |
| A11 | `sensor.sensor_temperatura_a11` / `sensor.sensor_humedad_a11` | `air_quality.co2_3` | `sensor.movimiento_a11` |
| A12 | `sensor.sensor_temperatura_a12` / `sensor.sensor_humedad_a12` | `air_quality.co2_1` | `sensor.movimiento_a12` |
| A21 | `sensor.sensor_temperatura_a21` / `sensor.sensor_humedad_a21` | `air_quality.co2_2` | `sensor.movimiento_a21` |
| A22 | `sensor.sensor_temperatura_a22` / `sensor.sensor_humedad_a22` | `air_quality.co2_4` | `sensor.movimiento_a22` |
| F0.2 | — | — | `sensor.presencia3` |
| ALU | — | — | `sensor.presencia2` |
| Anita Borg | — | — | `sensor.presencia1` |

- Temperatura, humedad y `sensor.presencia1..3` se leen de `statistics.mean`.
- El CO₂ y `sensor.movimiento_a11..a22` no tienen estadísticos de larga duración: se leen de `states`.
- `sensor.ambiente` se usa como referencia de temperatura, sin asignarlo a una estancia. `sensor.daily_gas` y `sensor.daily_gas_cost` dan el contexto de gas del edificio.
- Los valores `0`, `unknown`, `unavailable` y los picos imposibles se descartan.
- Umbrales de confort: temperatura 18–24 °C (moderado 16–18 / 24–26), humedad 30–60 % (moderado 25–30 / 60–70), CO₂ ≤600 ppm bueno, ≤800 moderado, ≤1.000 alto, >1.000 muy alto.

### Mantenimiento — `core/maintenance_map.py`

Catálogo de 52 dispositivos con entidad de latido, entidad de batería, unidad, intervalo esperado y notas:

| Grupo | Dispositivos | Latido | Batería |
| ----- | ------------ | ------ | ------- |
| Shelly H&T | `shelly1`–`shelly18` | `sensor.temperatura_shellyN` | `sensor.bateria_shellyN` (%) |
| Sensores CO₂/clima | A11, A12, A21, A22 | `air_quality.co2_1..4` | `sensor.sensor_bateria_a11..a22` (mV) |
| Presencia | F0.2, ALU, Anita Borg | `sensor.presencia1..3` | atributo `battery` (%) |
| Parking | `fleximodo1`–`fleximodo6` | `sensor.fleximodoN` | atributo `battery_percent_est` (%) |
| Gas | `gas` | `sensor.gas` | atributo `Battery` (%) |
| Válvulas TRV | F1.1, LD1–LD4 | temperatura/batería de válvula | `sensor.bateria_valvula_*` (%) |
| Contadores y controladores | Contadores eléctricos y controladores de iluminación | entidad de medida | Alimentados por red |

Umbrales:

- Batería: crítica ≤20 %, baja ≤40 %, media ≤60 %.
- En mV: crítica ≤3.200, baja ≤3.400, media ≤3.500.
- Silencio: 3× el intervalo esperado, con un mínimo de 2 h para equipos rápidos y 24 h para equipos lentos.
- Un salto de batería de al menos 20 puntos se interpreta como cambio de pila.
- Los dispositivos de eventos se consideran fuera de línea tras 7 días sin datos.

La curva mV → % es orientativa (Li-SOCl₂ 3,6 V); el valor en mV sigue siendo el dato autoritativo. La previsión de autonomía usa la tendencia de los últimos 30 días y solo se muestra cuando hay lecturas suficientes; no se inventan costes de sustitución.

### Medio Ambiente — `core/weather_map.py`

| Elemento | Entidad | Uso |
| -------- | ------- | --- |
| Estación | `weather.meteo` | `state` = temperatura exterior; atributos `Humidity`, `Pressure` (nivel del mar), `PM1`, `PM2.5`, `PM10` y `Battery`. |
| Interior | `sensor.ambiente` | Temperatura, humedad, CO₂, TVOC y presión para el cruce exterior-interior. |
| AEMET | `sensor.aemet_*` | Referencia externa de Ciudad Real: temperatura, humedad, presión, precipitación, visibilidad y nieve. |

- La estación no publica viento, lluvia ni radiación solar.
- `Pressure` se publica reducida al nivel del mar; para compararla con AEMET se reduce a la altitud del observatorio (626,17 m).
- Los valores de PM no declaran unidad: se tratan como índice relativo y no se comparan con umbrales sanitarios.
- `weather.meteo_2` es una entidad duplicada no disponible y no se usa.
- Se descartan reinicios con `state=0` y sin atributos útiles.
- Umbrales: calor ≥30 °C, frío ≤10 °C, noche tropical ≥20 °C, sequedad <30 %, humedad ≥80 %, HDD base 18 °C, CDD base 22 °C.
- La estación se marca `stale` si el último dato supera 2× su intervalo mediano (mínimo 2 h). AEMET se marca `stale` tras 24 h.
- Los cruces energéticos excluyen días con saltos anómalos por encima de `max(tope absoluto, 4 × mediana)`.

## Base de datos

Solo se consultan estas formas:

1. `statistics.sum` de los contadores acumulados de electricidad.
2. `statistics.mean` de temperatura, humedad y presencia.
3. `states` con el último valor por hora para los contadores de personas y para el CO₂.
4. `states` con las transiciones de los sensores de movimiento, convertidas en fracciones horarias.
5. El valor inmediatamente anterior a la ventana para rellenar el primer intervalo.
6. El último valor válido de cada entidad para las tarjetas de estado actual.
7. `statistics.sum` de `sensor.daily_gas` y `sensor.daily_gas_cost` para el contexto de calefacción.
8. `states` con las marcas de tiempo de los latidos y el último valor anterior a la ventana para Mantenimiento.
9. `states` de `weather.meteo`, `sensor.ambiente` y las entidades AEMET, más el último valor válido de cada una para Medio Ambiente.
10. `statistics.sum` de `sensor.daily_gas`, `sensor.daily_gas_cost` y `sensor.cuadro_general` para el cruce energético.

Todas las consultas filtran por `entity_id` y por el rango temporal para usar los índices del recorder. La agregación por hora/día/semana se hace con la zona `Europe/Madrid`. En Infraestructura, las cuatro consultas de CO₂ se lanzan en paralelo para que el rango anual no espere cuatro escaneos seguidos.

Las sentencias SQL completas, sus parámetros y los ejemplos de consulta manual están en
[Consultas SQL](sql.md).

La conversión de acumulado a consumo horario está en `db/database_data.py`:

- El incremento se atribuye a la hora en la que cierra el intervalo.
- Los saltos negativos se convierten en 0.
- Los saltos mayores que `ENERGY_MAX_KWH_PER_HOUR` se descartan.
- Los huecos se reparten entre las horas transcurridas.

## Tests

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -t . -v
```

`tests/__init__.py` fuerza `DATA_SOURCE=mock`, así que las pruebas no tocan la base de datos real. Cubren Electricidad, Iluminación, Infraestructura, Mantenimiento, Medio Ambiente, salud y metadatos.
