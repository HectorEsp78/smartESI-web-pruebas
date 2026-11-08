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
         ├── Infraestructura ─ SELECT ─► temperatura, humedad, CO₂ y presencia
         ├── Medio Ambiente ── SELECT ─► estación meteorológica, interior, AEMET y energía
         ├── Mantenimiento ── SELECT ─► latidos, batería y cortes de dispositivos
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
| **Infraestructura** | Índice de estancias y página por estancia con confort, ocupación, CO₂, recuperación térmica y comparación con la media del resto. | Reales si `DATA_SOURCE=database`; sintéticos en `mock`. |
| **Medio Ambiente** | Estación meteorológica, cobertura, derivados, partículas y cruces con el interior, AEMET y la energía. | Reales si `DATA_SOURCE=database`; sintéticos en `mock`. |
| **Mantenimiento** | Batería, transmisión y cortes por dispositivo, con matriz de decisión y previsión de sustitución. | Reales si `DATA_SOURCE=database`; sintéticos en `mock`. |

La cabecera mantiene el selector global de periodo solo en **Iluminación**. Electricidad e Infraestructura usan fechas propias: Electricidad porque compara varios periodos y Infraestructura porque necesita un rango personalizado por estancia (7 días por defecto y máximo un año). Medio Ambiente y Mantenimiento usan `?days=7|30|90`.

## Capas del backend

```text
app/
├── api/          Rutas HTTP y validación de parámetros
├── services/     Agregación, comparativas, cobertura y modelo sintético
├── core/         Configuración, catálogo de edificios y mapas de datos
├── db/           Consultas SELECT y carga de series horarias
├── models/       Tablas del recorder de Home Assistant
└── schemas/      Contratos Pydantic de respuesta
```

- `api/electricity.py` expone `/api/v1/energy/electricity`.
- `api/lighting.py` expone `/api/v1/lighting`.
- `api/environment.py` expone `/api/v1/environment`.
- `api/maintenance.py` expone `/api/v1/maintenance`.
- `api/meta.py` expone los edificios para los selectores.
- `services/electricity_service.py` calcula series, totales, base y comparativa.
- `services/lighting_service.py` calcula luminarias, ranking y despilfarro.
- `services/environment_service.py` agrega estancias, construye el índice y el detalle, calcula cruces y cachea el conjunto de datos por periodo.
- `services/maintenance_service.py` evalúa batería, transmisión, cortes y prioridad, y construye el índice y el detalle.
- `core/electricity_map.py` declara los contadores eléctricos reales.
- `core/environment_map.py` declara las estancias, sensores ambientales confirmados y referencias de ambiente/gas.
- `core/maintenance_map.py` declara los dispositivos vigilados, umbrales y curva de batería.
- `core/buildings.py` es el catálogo compartido por el modelo sintético y las gráficas.
- `db/repository.py` contiene las únicas consultas SQL.
- `db/database_data.py` convierte filas acumuladas en series horarias.
- `db/environment_data.py` convierte estadísticas, estados crudos y acumulados de gas en series ambientales.
- `db/maintenance_data.py` carga latidos, batería y estados previos a la ventana para Mantenimiento.

## Endpoints

| Método | Ruta | Uso |
| ------ | ---- | --- |
| GET | `/api/v1/energy/electricity/meta` | Edificios, sectores, fecha mínima, precio y origen (`mock`/`database`). |
| GET | `/api/v1/energy/electricity` | Serie y resumen de Electricidad. |
| GET | `/api/v1/energy/electricity/compare` | Dos periodos con el mismo número de intervalos (compatibilidad). |
| GET | `/api/v1/energy/electricity/compare-many` | N periodos alineados en una sola gráfica. |
| GET | `/api/v1/lighting/consumption` | Serie de luminarias y otras cargas. |
| GET | `/api/v1/lighting/by-space` | Ranking de espacios por consumo de luminarias. |
| GET | `/api/v1/lighting/waste` | Luz encendida sin ocupación y coste anualizado. |
| GET | `/api/v1/environment/overview` | Índice compacto de estancias confirmadas y medias del periodo. |
| GET | `/api/v1/environment/rooms/{room_id}` | Detalle de una estancia con series, mapa horario y cruces. |
| GET | `/api/v1/maintenance/overview` | Estado de los dispositivos: batería, transmisión, cortes, matriz y mapa diario. |
| GET | `/api/v1/maintenance/devices/{device_id}` | Detalle de un dispositivo con historial de batería y cortes. |
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

La comparativa principal usa `/compare-many`, con `start` y `end` repetidos una vez por periodo (entre 2 y 12), y los mismos filtros. Las series se alinean desde el inicio y los intervalos que faltan en periodos más cortos se devuelven como `null`. `/compare` conserva el contrato A/B anterior y sigue rechazando distinto número de intervalos.

### Iluminación

Parámetros: `range` (`day`, `week`, `month`, `year`) y `building`.

### Infraestructura

- `start`, `end`: fechas `YYYY-MM-DD`, ambas inclusive. Por defecto, últimos 7 días; máximo, 366 días.
- `/overview` devuelve el índice compacto.
- `/rooms/{room_id}` devuelve una estancia con series, mapa horario y cruces.
- Granularidad automática: `hour` hasta 7 días, `day` hasta 120 y `week` para periodos mayores.
- Solo se incluyen A11, A12, A21, A22, F0.2, Aula de Libre Uso (ALU) y Sala Anita Borg. Los laboratorios y los Shelly genéricos no se incluyen hasta que exista un mapa fiable de sala.
- `sensor.ambiente` es una referencia sin sala; el gas es del edificio.

## Frontend

```text
src/app/
├── api/          Cliente HTTP
├── components/
│   ├── Header.tsx
│   ├── stats/electricity/
│   ├── stats/environment/
│   ├── stats/lighting/
│   └── ui/       Tarjetas, gráficas, selectores y exportación CSV
├── context/      Periodo global de Iluminación
├── hooks/        Consultas con TanStack Query y periodos en la URL
├── lib/          Fechas, formato, paletas, CSV y URL
├── pages/        Stats y NotFound
└── types/        Contratos TypeScript
```

- `pages/Stats.tsx` decide qué pestaña renderizar.
- `lib/sections.ts` contiene las cinco pestañas y la pestaña por defecto.
- `lib/urlState.ts` sincroniza pestaña y periodo con la URL.
- Las paletas de Electricidad son propias y no alteran las de Iluminación ni las de Infraestructura.

## Flujo de una consulta de Electricidad

1. El usuario elige fechas, edificio, sector y métrica.
2. El hook calcula la granularidad automática según el número de días.
3. El backend valida fechas y ámbito.
4. `database_data.load_hourly_statistics` lee los `sum` acumulados y los convierte a kWh por hora.
5. `electricity_service` agrupa por intervalos, calcula la base de centro cerrado, la cobertura de Fermín y la comparativa.
6. El frontend pinta resumen, barras, sectores y comparativa.

## Flujo de una consulta de Infraestructura

1. El usuario elige fechas de inicio y fin (por defecto, los últimos 7 días; máximo, 366 días).
2. `environment_service` valida las fechas, construye los intervalos locales y decide la granularidad (hora, día o semana).
3. `environment_data` lanza en paralelo las cuatro consultas de CO₂ y, en otra sesión, las estadísticas de temperatura/humedad/presencia, las transiciones de movimiento, los últimos valores y los acumulados de gas.
4. El servicio descarta ceros, `unknown`, `unavailable` y valores fuera de rango, calcula medias, ocupación, mapa horario, recuperación térmica y comparación con la media del resto de estancias.
5. El frontend pinta el índice compacto en `/infraestructura` o el detalle de una estancia en `/infraestructura/{room_id}`.

## Criterios de diseño

- **Fermín Caballero** se deriva de `Cuadro General − Módulo A − Módulo B`; no existe un contador único del edificio.
- Los sectores de Fermín son **parciales**; la UI muestra siempre cobertura y “No desglosado”.
- La base de centro cerrado usa **L-V 7:00–21:00** como horario laborable; noches y fines de semana cuentan como cierre.
- El coste se calcula con **0,20 €/kWh**.
- La agrupación temporal es automática para no añadir un selector confuso.
- La fecha mínima solo se exige en modo `database`, porque en `mock` los datos son sintéticos.
