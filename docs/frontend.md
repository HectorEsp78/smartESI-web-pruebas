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
│   ├── battery.ts          Consultas de las páginas de batería
│   ├── weather.ts          Consultas de Medio Ambiente
│   ├── meta.ts             Edificios
│   └── http.ts             fetch + errores
├── components/
│   ├── Header.tsx
│   ├── stats/electricity/  Dashboard, filtros, resumen y gráficas
│   ├── stats/environment/  Índice, página por estancia y cruces ambientales
│   ├── stats/lighting/     Consumo, ranking y despilfarro
│   ├── stats/battery/      Páginas de batería: navegación, tarjetas, ventana e histórico
│   ├── stats/maintenance/  Panel anterior, no montado: resumen, matriz, cortes y detalle
│   ├── stats/weather/      Estación frente a AEMET: comparación, gráficas, resumen y notas
│   └── ui/                 ChartCard, StatCard, ExportCsvButton, SelectField, RangeSelector
├── context/
│   └── RangeContext.tsx    Periodo global de Iluminación
├── hooks/
│   ├── useElectricity.ts
│   ├── useLighting.ts
│   ├── useEnvironment.ts
│   ├── useEnvironmentPeriod.ts
│   ├── useMaintenance.ts
│   ├── useBattery.ts
│   ├── useMaintenanceDays.ts
│   ├── useWeather.ts
│   ├── useDatePeriod.ts
│   └── useBuildings.ts
├── lib/
│   ├── electricity.ts      Fechas, periodos y granularidad automática
│   ├── environment.ts      Colores, periodo, formato y mapa horario
│   ├── maintenance.ts      Filtros, formato, matriz y mapa de transmisión
│   ├── battery.ts          Páginas, periodos, formato y eje del histórico de batería
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
- Infraestructura usa `?start=&end=` (día actual por defecto, máximo un año) y mantiene las fechas al navegar entre el índice y cada estancia.
- Mantenimiento usa `/mantenimiento/shellys`, `/mantenimiento/valvulas` y `/mantenimiento/aulas`. `/mantenimiento` y `?tab=mantenimiento` redirigen a Shellys.
- Medio Ambiente usa `?tab=medio-ambiente&start=&end=`; tampoco necesita una ruta nueva.

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

- `/infraestructura`: tarjetas de las cuatro aulas monitorizadas.
- `/infraestructura/{room_id}`: gráficas de temperatura, humedad y presencia.

| Componente | Responsabilidad |
| ---------- | --------------- |
| `EnvironmentDashboard` | Decide entre índice y detalle según la ruta. |
| `EnvironmentIndex` | Selector de periodo y rejilla de tarjetas de aula. |
| `EnvironmentRangeSelector` | Botones Día / Semana / Mes; escribe `start` y `end` en la URL. |
| `EnvironmentRoomCard` | Tarjeta con imagen, código, nombre y valores actuales de temperatura, humedad y presencia. |
| `EnvironmentRoomPage` | Cabecera con valores actuales y las tres gráficas del periodo. |
| `EnvironmentRoomTemperatureChart` | Temperatura con banda de confort 18–24 °C. |
| `EnvironmentRoomHumidityChart` | Humedad con banda de confort 30–60 %. |
| `EnvironmentRoomPresenceChart` | Presencia sí/no por intervalo (`sensor.movimiento_aXX`). |

Reglas de interfaz:

- Solo se muestran A11, A12, A21 y A22; no se inventan salas.
- Las tarjetas siguen la estética del proyecto Smart ESI: imagen del aula, categoría, código y nombre.
- El periodo por defecto es el día actual; también se puede ver la última semana o el último mes.
- La temperatura y la humedad proceden de `statistics.mean`; la presencia, de las transiciones de `states`.
- Si una hora no tiene dato ambiental, la serie deja un hueco en lugar de inventar un valor.
- La presencia se representa como escalón 0/1 con eje «Sí/No»: indica si hubo movimiento en cada intervalo.

## Mantenimiento

Cada grupo tiene su página con tres indicadores y una tarjeta por sensor. El periodo del histórico es estado local de la ventana y no se guarda en la URL.

| Componente | Función |
|---|---|
| `BatteryDashboard` | Navegación entre grupos, resumen, avisos y tarjetas. |
| `BatterySensorCard` | Nivel actual, estado y fecha de lectura; al pulsarla abre el histórico. |
| `BatteryHistoryDialog` | Ventana (`<dialog>`) con fechas y periodos rápidos. Se cierra con Escape, con «Cerrar» o pulsando fuera. |
| `BatteryHistoryChart` | Línea del histórico con los umbrales de batería. |

### Panel anterior (no montado en la interfaz)


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

Se abre con `?tab=medio-ambiente&start=YYYY-MM-DD&end=YYYY-MM-DD` (últimos 30 días por defecto). Es una vista de solo lectura.

| Componente | Responsabilidad |
| ---------- | --------------- |
| `WeatherDashboard` | Carga los datos y compone filtros, valores actuales, aviso, comparación, gráficas, resumen y notas. |
| `WeatherFilters` | Fechas Desde/Hasta y atajos de 7, 30 y 90 días. |
| `WeatherCurrent` | Última lectura de la estación y última observación guardada de AEMET. |
| `WeatherAemetNotice` | Avisa si el periodo no tiene datos de AEMET, los tiene en parte o AEMET ha dejado de actualizarse. |
| `WeatherComparison` | Diferencia media, error absoluto y correlación de temperatura, humedad y presión. |
| `WeatherTemperatureChart` / `WeatherHumidityChart` / `WeatherPressureChart` | Estación y AEMET en la misma gráfica. |
| `WeatherHourlyBiasChart` | Diferencia de temperatura por hora del día. |
| `WeatherRainChart` | Lluvia de AEMET. |
| `WeatherPmChart` | PM1, PM2.5 y PM10 como índice relativo. |
| `WeatherBatteryChart` | Batería de la estación. |
| `WeatherSummary` | Estadísticas de la estación en el periodo y lluvia total. |
| `WeatherNotes` | Criterios y limitaciones de los datos. |

Reglas de interfaz:

- Los huecos de AEMET se avisan y se dibujan como huecos: nunca se rellenan.
- Sin datos de AEMET en el periodo se muestra solo la estación y no aparece la comparación.
- PM1/PM2.5/PM10 se muestran como **índice relativo**, nunca como µg/m³ ni frente a umbrales sanitarios.
- La presión se compara a la altitud del observatorio de AEMET.

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
| `useBatteryGroup` | `/maintenance/batteries/{group_id}` | 60 s |
| `useBatteryHistory` | `/maintenance/batteries/{group_id}/{sensor_id}/history` | 60 s |
| `useMaintenanceOverview` | `/maintenance/overview` | 60 s |
| `useMaintenanceDevice` | `/maintenance/devices/{device_id}` | 60 s |
| `useMaintenanceDays` | Estado de `?days=` en la URL | — |
| `useWeatherOverview` | `/weather/overview` | 60 s |
| `useDatePeriod` | Estado de `?start=&end=` en la URL | — |
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
- Helpers de Medio Ambiente (periodo, formato, avisos de cobertura de AEMET y de exposición solar).
- Componentes `ChartCard` y utilidades de UI.

`npm run typecheck` y `npm run build` deben pasar antes de entregar.
