# Frontend

SPA en **React + TypeScript + Vite**. Usa **TanStack Query** para las consultas, **Recharts** para las gráficas y **Tailwind CSS** para los estilos.

## Arranque

```bash
cd frontend
npm install
npm run dev        # http://localhost:5174
```

Comandos:

```bash
npm run typecheck
npm run test:run
npm run build
npm run preview
```

El proxy de desarrollo envía `/api/*` a `http://127.0.0.1:8010`.

## Estructura

```text
frontend/src/app/
├── api/
│   ├── electricity.ts      Consultas de Electricidad
│   ├── lighting.ts         Consultas de Iluminación
│   ├── environment.ts      Consultas de Infraestructura
│   ├── maintenance.ts      Consultas de Mantenimiento
│   ├── weather.ts          Consultas de Medio Ambiente
│   ├── meta.ts             Edificios
│   └── http.ts             fetch + errores
├── components/
│   ├── Header.tsx
│   ├── stats/electricity/  Dashboard, filtros, resumen y gráficas
│   ├── stats/environment/  Índice, página por estancia y cruces ambientales
│   ├── stats/lighting/     Consumo, ranking y despilfarro
│   ├── stats/maintenance/  Resumen, matriz, cortes, tabla y detalle por dispositivo
│   ├── stats/weather/      Estación, resumen, gráficas, cruces y notas
│   └── ui/                 ChartCard, StatCard, ExportCsvButton, SelectField, RangeSelector
├── context/
│   └── RangeContext.tsx    Periodo global de Iluminación
├── hooks/
│   ├── useElectricity.ts
│   ├── useLighting.ts
│   ├── useEnvironment.ts
│   ├── useEnvironmentPeriod.ts
│   ├── useMaintenance.ts
│   ├── useMaintenanceDays.ts
│   ├── useWeather.ts
│   ├── useWeatherDays.ts
│   └── useBuildings.ts
├── lib/
│   ├── electricity.ts      Fechas, periodos y granularidad automática
│   ├── environment.ts      Colores, periodo, formato y mapa horario
│   ├── maintenance.ts      Filtros, formato, matriz y mapa de transmisión
│   ├── weather.ts          Periodo, formato y avisos de la estación
│   ├── format.ts           Números, kWh, € y porcentajes
│   ├── chartTheme.ts       Paletas y estilos de ejes
│   ├── csv.ts              Exportación CSV
│   ├── sections.ts         Pestañas
│   └── urlState.ts         Pestaña y periodo en la URL
├── pages/
│   ├── Stats.tsx
│   └── NotFound.tsx
└── types/                  Contratos TypeScript
```

## Pestañas y estado

- `pages/Stats.tsx` renderiza la pestaña activa y resuelve las rutas `/infraestructura` y `/infraestructura/{room_id}`.
- `lib/sections.ts` define **Electricidad**, **Iluminación**, **Infraestructura**, **Medio Ambiente** y **Mantenimiento**; la pestaña por defecto es Electricidad.
- `lib/urlState.ts` sincroniza `?tab=` y `?range=`. Los valores desconocidos vuelven a los valores por defecto.
- El selector global de periodo se muestra solo en **Iluminación**.
- Electricidad usa sus propias fechas y su comparativa.
- Infraestructura usa `?start=&end=` (7 días por defecto, máximo un año) y mantiene las fechas al navegar entre el índice y cada estancia.
- Mantenimiento usa `?tab=mantenimiento&days=7|30|90`; no necesita una ruta nueva.
- Medio Ambiente usa `?tab=medio-ambiente&days=7|30|90`; tampoco necesita una ruta nueva.

## Electricidad

Componentes:

| Componente | Responsabilidad |
| ---------- | --------------- |
| `ElectricityDashboard` | Carga metadatos/estadísticas, calcula granularidad y compone la vista. |
| `ElectricityFilters` | Fechas, edificio, sector y métrica. |
| `ElectricitySummary` | Total, media, mínimo, máximo, base y cobertura. |
| `ElectricityBuildingsChart` | Barras apiladas de los tres edificios + línea de base. |
| `ElectricitySectorsChart` | Sectores de Fermín, CPD y “No desglosado”. |
| `ElectricityComparisonChart` | N periodos independientes en una misma gráfica, tabla de totales y base común. |

Reglas de interfaz:

- Fechas inclusivas y validación de fecha final.
- La agrupación se deduce del rango con `granularityForPeriod`: día hasta 31 días, semana hasta 120, mes hasta 3 años y año para rangos mayores.
- No hay selector “Agrupar por”.
- El indicador de origen muestra `mock` o `database`.
- Los avisos de cobertura y de intervalos parciales son explícitos.
- La comparativa permite añadir y quitar periodos, avisa si las fechas son inválidas o anteriores al inicio de los datos y alinea las series desde el inicio cuando tienen distinta duración.

## Iluminación

| Componente | Responsabilidad |
| ---------- | --------------- |
| `LightingConsumptionChart` | Luminarias frente a otras cargas y horas de luz natural. |
| `LightingBySpaceChart` | Ranking de espacios y exportación CSV. |
| `LightingWasteChart` | Luz encendida sin ocupación y coste anualizado. |

El periodo y el edificio son globales para las tres gráficas.

## Infraestructura

Rutas:

- `/infraestructura`: índice compacto de estancias, medias del periodo y enlaces a cada estancia.
- `/infraestructura/{room_id}`: página de una estancia con sus gráficas y cruces.

| Componente | Responsabilidad |
| ---------- | --------------- |
| `EnvironmentDashboard` | Decide entre índice y detalle según la ruta. |
| `EnvironmentIndex` | Filtro de fechas, resumen y lista compacta de estancias. |
| `EnvironmentFilters` | Fechas personalizadas, validación y máximo de un año. |
| `EnvironmentSummary` | Tira compacta con temperatura media, CO₂ medio, ocupación media y estancias ocupadas ahora. |
| `EnvironmentRoomList` | Lista compacta con ambiente actual, uso y estado por estancia. |
| `EnvironmentRoomPage` | Página de una estancia: cabecera, KPIs, gráficas principales y análisis avanzado plegado. |
| `EnvironmentRoomHeader` | Valores actuales en una fila compacta y aviso de dato obsoleto. |
| `EnvironmentRoomStats` | Cuatro KPIs del periodo: temperatura, humedad, CO₂ y ocupación. |
| `EnvironmentRoomTemperatureChart` / `EnvironmentRoomHumidityChart` | Temperatura con ambiente de referencia y humedad con bandas de confort (esta última en análisis avanzado). |
| `EnvironmentRoomCo2Chart` | CO₂ frente a ocupación con umbrales de 800/1.000 ppm. |
| `EnvironmentHeatmap` | Mapa horario 7×24 de ocupación o CO₂. |
| `EnvironmentCo2OccupancyCard` | CO₂ con/sin presencia, incremento, correlación y dispersión. |
| `EnvironmentThermalRecoveryCard` | Vuelta a la temperatura de reposo tras desocupar. |
| `EnvironmentBenchmarkCard` | Comparación con la media del resto de estancias. |
| `EnvironmentGasContextChart` | Temperatura de la estancia, ambiente de referencia y coste de gas del edificio. |

Reglas de interfaz:

- Solo se muestran estancias con sensores confirmados; no se inventan salas.
- F0.2, ALU y Anita Borg solo tienen presencia: muestran ocupación y horas; el mapa horario queda en análisis avanzado, sin rellenar temperatura, humedad o CO₂.
- El detalle evita saturar la pantalla: solo temperatura y CO₂ están visibles; humedad, mapas, cruces, comparativa y gas se pliegan en “Análisis avanzado”.
- Los valores actuales pueden ser el último dato válido si el sensor se reinició.
- Si el último dato ambiental tiene más de 6 horas, se marca en ámbar como “sin actualizar”.
- La temperatura/humedad de referencia es `sensor.ambiente`, sin sala confirmada. El gas es del edificio y puede incluir usos distintos de la calefacción.
- El CO₂ se muestra en ppm y la ocupación como porcentaje del intervalo.
- Los umbrales son orientativos y se explican en las notas de la pestaña.

## Mantenimiento

Se abre con `?tab=mantenimiento&days=7|30|90` (30 por defecto). Es una vista de solo lectura: no registra intervenciones.

| Componente | Responsabilidad |
| ---------- | --------------- |
| `MaintenanceDashboard` | Carga el resumen y compone filtros, tarjetas, matriz, cortes, tabla, mapa avanzado y notas. |
| `MaintenanceFilters` | Selector de periodo de 7, 30 o 90 días. |
| `MaintenanceSummary` | Baterías bajas, dispositivos sin datos, cortes, disponibilidad, cambios detectados y previsión de sustitución. |
| `MaintenanceMatrix` | Cruce 3×2 de batería (OK / baja / sin lectura) por transmisión (datos OK / sin datos). |
| `MaintenanceOutages` | Cortes globales y de grupo, separados de las averías individuales. |
| `MaintenanceDeviceTable` | Tabla ordenada por prioridad con filtros y filas expandibles. |
| `MaintenanceDeviceDetail` | Historial de batería, transmisión diaria y cortes del dispositivo. |
| `MaintenanceHeatmap` | Mapa diario de datos recibidos frente a esperados (análisis avanzado). |
| `MaintenanceNotes` | Criterios y limitaciones de los datos. |

Reglas de interfaz:

- La pantalla principal no se satura: el mapa diario queda plegado en “análisis avanzado”.
- La tabla filtra por **todos**, **prioritarios**, **batería baja** y **sin datos**, y muestra el recuento de cada opción.
- Al pulsar una fila se carga el detalle bajo demanda; no se piden 52 detalles de golpe.
- Un dispositivo de eventos no se marca como silencioso solo porque no haya emitido; se distingue de un latido periódico perdido.
- Los cortes globales y de grupo se muestran aparte para no confundirlos con 30 averías individuales.
- La batería en mV se muestra con su porcentaje aproximado y se avisa de lecturas antiguas.
- La decisión de la matriz responde a “si no envía datos y la batería está OK, revisar el dispositivo”.

## Medio Ambiente

Se abre con `?tab=medio-ambiente&days=7|30|90` (30 por defecto). Es una vista de solo lectura.

| Componente | Responsabilidad |
| ---------- | --------------- |
| `WeatherDashboard` | Carga el resumen y compone filtros, estado actual, tarjetas, gráficas, cruces, tabla diaria y notas. |
| `WeatherFilters` | Selector de periodo de 7, 30 o 90 días. |
| `WeatherCurrent` | Última lectura: temperatura, humedad, presión, PM, batería, edad del dato y tendencia. |
| `WeatherSummary` | Cobertura, temperatura, amplitud, humedad, presión, horas de calor/frío, grados-día y PM. |
| `WeatherTemperatureChart` / `WeatherHumidityChart` | Estación, interior de referencia y AEMET. |
| `WeatherPressureChart` | Presión de la estación reducida al nivel del mar. |
| `WeatherPmChart` | PM1, PM2.5 y PM10 como índice relativo. |
| `WeatherIndoorCross` | Salto térmico/húmedo y correlaciones con `sensor.ambiente`. |
| `WeatherAemetCross` | Sesgo, MAE, correlación y sesgo por hora frente a AEMET. |
| `WeatherEnergyCross` | Gas/electricidad frente a temperatura y grados-día. |
| `WeatherPmCross` | Ratios y correlaciones de partículas. |
| `WeatherDailyTable` | Resumen diario con cobertura, extremos, PM y energía. |
| `WeatherNotes` | Criterios y limitaciones de los datos. |

Reglas de interfaz:

- La pantalla principal no se satura: la tabla diaria queda plegada en “ver resumen diario”.
- La estación no publica viento ni lluvia; no se inventan esas gráficas.
- PM1/PM2.5/PM10 se muestran como **índice relativo**, nunca como µg/m³ ni frente a umbrales sanitarios.
- AEMET se etiqueta como referencia externa de Ciudad Real y se marca si está desactualizada.
- La presión se muestra a nivel del mar; el cruce con AEMET usa la presión reducida a la altitud del observatorio.
- Los cruces energéticos avisan de los días excluidos por saltos anómalos de los contadores.
- Las correlaciones solo se muestran cuando hay suficientes horas comunes.

## Hooks y caché

| Hook | Consulta | `staleTime` |
| ---- | -------- | ----------- |
| `useElectricityMeta` | `/energy/electricity/meta` | 30 min |
| `useElectricity` | `/energy/electricity` | 60 s |
| `useElectricityCompareMany` | `/energy/electricity/compare-many` | 60 s |
| `useLightingConsumption` | `/lighting/consumption` | 60 s |
| `useLightingBySpace` | `/lighting/by-space` | 60 s |
| `useLightingWaste` | `/lighting/waste` | 60 s |
| `useEnvironmentOverview` | `/environment/overview` | 60 s |
| `useEnvironmentRoom` | `/environment/rooms/{room_id}` | 60 s |
| `useEnvironmentPeriod` | Estado local de fechas en la URL | — |
| `useMaintenanceOverview` | `/maintenance/overview` | 60 s |
| `useMaintenanceDevice` | `/maintenance/devices/{device_id}` | 60 s |
| `useMaintenanceDays` | Estado de `?days=` en la URL | — |
| `useWeatherOverview` | `/weather/overview` | 60 s |
| `useWeatherDays` | Estado de `?days=` en la URL | — |
| `useBuildings` | `/meta/buildings` | 30 min |

## Estilos

- La paleta institucional está en `styles/theme.css` y `lib/chartTheme.ts`.
- Electricidad tiene colores propios de edificios y sectores; Iluminación e Infraestructura usan sus propias paletas.
- Las tarjetas usan `ChartCard` y `StatCard`.
- Los estados de carga, error y vacío son explícitos y tienen botón **Reintentar** cuando aplica.

## Tests

```bash
npm run test:run
```

Cubren:

- URL y pestañas.
- Fechas, comparativa y granularidad automática.
- Formato y CSV.
- Clientes API de Electricidad, Infraestructura, Mantenimiento y Medio Ambiente.
- Helpers de Infraestructura (periodo, formato, mapa horario y datos obsoletos).
- Helpers de Mantenimiento (periodo, batería, filtros, matriz y mapa de transmisión).
- Helpers de Medio Ambiente (periodo, formato, estados y aviso de exposición solar).
- Componentes `ChartCard` y utilidades de UI.

`npm run typecheck` y `npm run build` deben pasar antes de entregar.
