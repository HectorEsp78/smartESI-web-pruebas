# Arquitectura

## Visión general

```text
navegador
  │
  ├── React + Vite (frontend)
  │      └── /api/*  (proxy de desarrollo o nginx)
  │
  └── FastAPI (backend)
         ├── Electricidad ── SELECT ──► MariaDB del recorder de Home Assistant
         ├── Iluminación ─── modelo sintético + ocupación real si existe
         └── Metadatos de edificios
```

- El backend **nunca escribe** en la base de datos: solo ejecuta `SELECT`.
- El frontend no conoce credenciales ni SQL; solo consume JSON.
- La caché en memoria evita repetir agregaciones costosas durante 30 segundos.

## Pestañas

| Pestaña | Qué resuelve | Datos |
| ------- | ------------ | ----- |
| **Electricidad** | Consumo/coste por edificio y sector, base de centro cerrado y comparativa de periodos. | Reales si `DATA_SOURCE=database`; sintéticos en `mock`. |
| **Iluminación** | Reparto luminarias/otras cargas, ranking por espacio y luz encendida sin ocupación. | Consumo sintético; ocupación real si hay contadores. |

La cabecera mantiene un selector de periodo global **solo en Iluminación**. Electricidad usa fechas propias porque su comparativa necesita dos periodos independientes.

## Capas del backend

```text
app/
├── api/          Rutas HTTP y validación de parámetros
├── services/     Agregación, comparativas, cobertura y modelo sintético
├── core/         Configuración, catálogo de edificios y mapa eléctrico
├── db/           Consultas SELECT y carga de series horarias
├── models/       Tablas del recorder de Home Assistant
└── schemas/      Contratos Pydantic de respuesta
```

- `api/electricity.py` expone `/api/v1/energy/electricity`.
- `api/lighting.py` expone `/api/v1/lighting`.
- `api/meta.py` expone los edificios para los selectores.
- `services/electricity_service.py` calcula series, totales, base y comparativa.
- `services/lighting_service.py` calcula luminarias, ranking y despilfarro.
- `core/electricity_map.py` declara los contadores eléctricos reales.
- `core/buildings.py` es el catálogo compartido por el modelo sintético y las gráficas.
- `db/repository.py` contiene las únicas consultas SQL.
- `db/database_data.py` convierte filas acumuladas en series horarias.

## Endpoints

| Método | Ruta | Uso |
| ------ | ---- | --- |
| GET | `/api/v1/energy/electricity/meta` | Edificios, sectores, fecha mínima, precio y origen (`mock`/`database`). |
| GET | `/api/v1/energy/electricity` | Serie y resumen de Electricidad. |
| GET | `/api/v1/energy/electricity/compare` | Dos periodos con el mismo número de intervalos. |
| GET | `/api/v1/lighting/consumption` | Serie de luminarias y otras cargas. |
| GET | `/api/v1/lighting/by-space` | Ranking de espacios por consumo de luminarias. |
| GET | `/api/v1/lighting/waste` | Luz encendida sin ocupación y coste anualizado. |
| GET | `/api/v1/meta/buildings` | Lista de edificios para los selectores. |
| GET | `/health/live` | Estado y origen de datos. |
| GET | `/health/ready` | Comprueba la conexión a la base de datos en modo `database`. |

### Electricidad

Parámetros principales:

- `start`, `end`: fechas `YYYY-MM-DD`, ambas inclusive.
- `granularity`: `day`, `week`, `month` o `year`. La UI lo deduce del rango.
- `metric`: `kwh` o `cost`.
- `building`: `all`, `ModuloA`, `ModuloB` o `FerminCaballero`.
- `sector`: id de cuadro o `CPD`, opcional.

La comparativa usa `start_a`, `end_a`, `start_b`, `end_b` y los mismos filtros. Rechaza periodos con distinto número de intervalos.

### Iluminación

Parámetros: `range` (`day`, `week`, `month`, `year`) y `building`.

## Frontend

```text
src/app/
├── api/          Cliente HTTP
├── components/
│   ├── Header.tsx
│   ├── stats/electricity/
│   ├── stats/lighting/
│   └── ui/       Tarjetas, gráficas, selectores y exportación CSV
├── context/      Periodo global de Iluminación
├── hooks/        Consultas con TanStack Query
├── lib/          Fechas, formato, paletas, CSV y URL
├── pages/        Stats y NotFound
└── types/        Contratos TypeScript
```

- `pages/Stats.tsx` decide qué pestaña renderizar.
- `lib/sections.ts` contiene las dos pestañas y la pestaña por defecto.
- `lib/urlState.ts` sincroniza pestaña y periodo con la URL.
- Las paletas de Electricidad son propias y no alteran las de Iluminación.

## Flujo de una consulta de Electricidad

1. El usuario elige fechas, edificio, sector y métrica.
2. El hook calcula la granularidad automática según el número de días.
3. El backend valida fechas y ámbito.
4. `database_data.load_hourly_statistics` lee los `sum` acumulados y los convierte a kWh por hora.
5. `electricity_service` agrupa por intervalos, calcula la base de centro cerrado, la cobertura de Fermín y la comparativa.
6. El frontend pinta resumen, barras, sectores y comparativa.

## Criterios de diseño

- **Fermín Caballero** se deriva de `Cuadro General − Módulo A − Módulo B`; no existe un contador único del edificio.
- Los sectores de Fermín son **parciales**; la UI muestra siempre cobertura y “No desglosado”.
- La base de centro cerrado usa **L-V 7:00–21:00** como horario laborable; noches y fines de semana cuentan como cierre.
- El coste se calcula con **0,20 €/kWh**.
- La agrupación temporal es automática para no añadir un selector confuso.
- La fecha mínima solo se exige en modo `database`, porque en `mock` los datos son sintéticos.
