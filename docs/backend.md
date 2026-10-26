# Backend

API FastAPI que sirve las dos pestañas. Está pensada para ejecutarse en local o en Docker y para leer el *recorder* de Home Assistant **solo con `SELECT`**.

## Estructura

```text
backend/
├── app/
│   ├── api/          Routers HTTP
│   ├── core/         Configuración, catálogo y mapa eléctrico
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
| GET | `/api/v1/energy/electricity/compare` | Comparativa de dos periodos. |

Parámetros de `/energy/electricity`:

| Parámetro | Valores | Notas |
| --------- | ------- | ----- |
| `start` | `YYYY-MM-DD` | Inclusivo. |
| `end` | `YYYY-MM-DD` | Inclusivo. |
| `granularity` | `day`, `week`, `month`, `year` | La UI lo deduce del rango. |
| `metric` | `kwh`, `cost` | Coste a 0,20 €/kWh. |
| `building` | `all`, `ModuloA`, `ModuloB`, `FerminCaballero` | Por defecto `all`. |
| `sector` | id de cuadro o `CPD` | Opcional; debe pertenecer a Fermín. |

La comparativa recibe `start_a`, `end_a`, `start_b`, `end_b` y exige el mismo número de intervalos en ambos periodos. Si no coincide, devuelve **400**.

### Iluminación

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET | `/api/v1/lighting/consumption` | Serie de luminarias y otras cargas. |
| GET | `/api/v1/lighting/by-space` | Ranking de espacios. |
| GET | `/api/v1/lighting/waste` | Luz encendida sin ocupación y €/año. |

Parámetros: `range=day|week|month|year` y `building=all|<id>`.

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

## Base de datos

Solo se consultan tres formas:

1. `statistics.sum` de los contadores acumulados de electricidad.
2. `states` con el último valor por hora para los contadores de personas.
3. El valor inmediatamente anterior a la ventana para rellenar el primer intervalo.

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

`tests/__init__.py` fuerza `DATA_SOURCE=mock`, así que las pruebas no tocan la base de datos real.
