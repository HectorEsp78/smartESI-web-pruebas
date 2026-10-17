# Backend (FastAPI + Pydantic)

Código en [`backend/app/`](../backend/app). Es una API de solo lectura que sirve estadísticas
agregadas. Con `DATA_SOURCE=mock` no necesita base de datos.

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
```

- **`api/`**: un router por dominio (`energy.py`, `lighting.py`, `climate.py`, `decisions.py`,
  `correlation.py`, `meta.py`). Valida el edificio y delega en el servicio; no contiene lógica de
  negocio. Todos se registran bajo `/api/v1` en `main.py`.
- **`services/`**:
  - `mock_data.py` genera los valores base por hora (energía, ocupación, CO₂, temperatura, humedad,
    meteorología, luz natural, luminarias, válvulas y gas) de forma determinista.
  - `stats.py` aporta la estadística descriptiva (media, mediana, desviación, percentiles,
    correlación y regresión) que comparten los demás servicios.
  - `energy_service.py` agrega consumo, por edificio, desglose (carga base/actividad/luz), comparativa
    con el periodo anterior y eficiencia (kWh/m² y kWh/persona·hora).
  - `lighting_service.py` separa luminarias del resto, reparte por espacio y calcula el despilfarro
    (luz sin ocupación) con su €/año.
  - `climate_service.py` calcula gas y grados-día, el estado de las electroválvulas frente a la
    temperatura de cada aula, y el gas gastado en espacios vacíos.
  - `decisions_service.py` traduce los cruces anteriores a un **ranking de oportunidades** con €/año.
  - `correlation_service.py` cruza ocupación y CO₂.
  - Todos los servicios exponen `clear_cache()`.
- **`core/`**: `config.py` (ajustes), `energy_map.py` (catálogo de edificios y espacios),
  `clock.py` (UTC local) y `cache.py` (caché TTL).
- **`schemas/`**: modelos Pydantic que definen exactamente lo que ve el frontend.

## Configuración (`backend/.env`)

Copia `.env.example` a `.env`. Variables principales:

| Variable | Por defecto | Descripción |
| -------- | ----------- | ----------- |
| `DATA_SOURCE` | `mock` | `mock` (sintético) o `database` (BD real). |
| `ENERGY_PRICE_EUR_PER_KWH` | `0.20` | Precio de la electricidad para la métrica de coste (€). |
| `CO2_KG_PER_KWH` | `0.15` | Factor de emisiones de la electricidad (kg CO₂/kWh). |
| `GAS_PRICE_EUR_PER_KWH` | `0.06` | Precio del gas (€/kWh). |
| `GAS_CO2_KG_PER_KWH` | `0.20` | Factor de emisiones del gas (kg CO₂/kWh). |
| `HEATING_BASE_TEMPERATURE_C` | `18.0` | Base para los grados-día de calefacción (°C). |
| `STATS_CACHE_TTL_SECONDS` | `30` | TTL de la caché de agregaciones. |
| `TIMEZONE` | `Europe/Madrid` | Zona para el cálculo de horas/días/meses. |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5174,...` | Orígenes permitidos. |
| `DB_*` | — | Conexión a MariaDB (solo `DATA_SOURCE=database`). |

## Añadir un edificio o un espacio

Todo el catálogo está en [`app/core/energy_map.py`](../backend/app/core/energy_map.py):

- `BUILDINGS`: un `BuildingConfig` por edificio (id, etiqueta, aforo, carga base en kW, consigna
  `setpoint_c` y `gas_base_kw` de la caldera).
- `SPACES`: un `SpaceConfig` por espacio (id, etiqueta, edificio, tipo, `weight`, `area_m2`,
  `lighting_kw` y `has_valve`). Los pesos se normalizan por edificio, así que no hace falta que
  sumen 1.

Al añadir entradas, el endpoint `/api/v1/meta/buildings`, los selectores del frontend y las gráficas
de edificio/espacio se actualizan solos.

El mapa de espacios y aforos se ha tomado del proyecto original (`sensor_map.py`) para que los
nombres resulten familiares; las cifras de consumo y de clima, en cambio, son simuladas.

## Añadir un estadístico nuevo

1. Añade la primitiva al generador sintético (`mock_data.py`) si hace falta un dato nuevo.
2. Implementa la agregación en el servicio del dominio correspondiente (o crea uno nuevo) y añade
   los campos al schema Pydantic.
3. Expón el endpoint en el router y regístralo (ya lo está si reutilizas el router existente).
4. Añade un test que compruebe las invariantes (cuántos puntos, coherencia de totales, 404…).

## Migrar a la base de datos real

El diseño ya contempla el cambio. Detalle en [`datos.md`](datos.md); resumen:

1. Instala el extra de base de datos:
   ```bash
   cd backend
   .venv/bin/python -m pip install -e ".[database]"
   ```
2. En `.env`, pon `DATA_SOURCE=database` y rellena `DB_*` (host, usuario, contraseña, TLS). Necesitas
   acceso a la red/VPN de la UCLM.
3. Sustituye las llamadas a `mock_data` en los servicios (`energy_service`, `lighting_service`,
   `climate_service`, `correlation_service`) por consultas a las tablas de Home Assistant (`states`,
   `statistics`). La sesión async ya está lista en
   [`app/db/session.py`](../backend/app/db/session.py). Para mapear entidades a espacios, sigue el
   patrón de `energy_map.py` (declarar explícitamente qué entidad corresponde a qué espacio).
4. El resto de la API (schemas, routers, frontend) no cambia.

> Referencia: el proyecto original ya hace esto en su `backend/app/db/` y `services/`. La idea es
> portar esas consultas cuando toque.

## Tests

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v
```

Cubren: número de puntos por rango, conversión de métricas (kWh→€/kg CO₂), 404 en edificio
desconocido, reparto de `share`, rangos de la correlación, endpoints de iluminación, clima y
decisiones (invariantes de totales y `€`), y salud/meta.
