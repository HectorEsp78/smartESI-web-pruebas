# Componentes

## 1. Estructura de la web

`pages/Stats.tsx` contiene la cabecera y decide qué pestaña mostrar. Hay cinco:

| id | Etiqueta |
| -- | -------- |
| `electricidad` | Electricidad |
| `iluminacion` | Iluminación |
| `infraestructura` | Infraestructura |
| `medio-ambiente` | Medio Ambiente |
| `mantenimiento` | Mantenimiento |

La pestaña por defecto es `electricidad`. La URL guarda `?tab=` y `?range=`.

## 2. Cabecera

`components/Header.tsx`:

- Logos institucionales.
- Pestañas.
- Selector de periodo global, visible solo en **Iluminación**.
- Enlace al inicio.

## 3. Electricidad

### `ElectricityDashboard`

Orquesta la pestaña:

- Carga metadatos y estadísticas.
- Calcula la granularidad automática.
- Muestra avisos de origen, fechas, cobertura e intervalos parciales.
- Compone filtros, resumen y gráficas.

### `ElectricityFilters`

- Fecha inicial y final.
- Edificio: todos, Módulo A, Módulo B, Fermín Caballero.
- Sector: cuadros de Fermín y CPD.
- Métrica: consumo o coste.
- Validación de fechas y mensajes de error.

### `ElectricitySummary`

- Total, media, mínimo y máximo.
- Base de centro cerrado.
- Cobertura de sectores.
- Unidad activa (kWh o €).

### `ElectricityBuildingsChart`

- Barras apiladas de Módulo A, Módulo B y Fermín.
- Línea de base de centro cerrado.
- Tabla de detalle y exportación CSV.

### `ElectricitySectorsChart`

- Barras por sector de Fermín.
- CPD incluido.
- Segmento “No desglosado”.
- Aviso de cobertura parcial.
- Exportación CSV.

### `ElectricityComparisonChart`

- N periodos independientes, con el periodo 1 como referencia.
- Una línea de color por periodo y base común.
- Alta y baja de periodos; al añadir se propone el mismo rango un año antes.
- Tabla de totales y variación frente al periodo 1.
- Validación de fechas, periodos duplicados y alineación cuando las duraciones difieren.

## 4. Iluminación

### `LightingConsumptionChart`

- Barras de luminarias y otras cargas.
- Línea de horas de luz natural.
- KPIs: total, luminarias, cuota, coste y CO₂.

### `LightingBySpaceChart`

- Top de espacios por consumo de luminarias.
- Tabla con superficie, tipo, cuota y coste.
- Exportación CSV.

### `LightingWasteChart`

- Espacios con luz encendida sin ocupación.
- kWh, porcentaje, horas y €/año.
- Exportación CSV.

El selector global de periodo y edificio afecta a las tres gráficas.

## 5. Infraestructura

### `EnvironmentDashboard`

- Resuelve `/infraestructura` (índice) y `/infraestructura/{room_id}` (detalle).
- Mantiene las fechas en la URL al cambiar de estancia.
- Muestra las notas de origen y limitaciones.

### `EnvironmentIndex`

- Filtro de fechas con 7 días por defecto y máximo de un año.
- Resumen compacto del periodo y lista de estancias.
- Enlaces a la página de cada estancia.

### `EnvironmentRoomList`

- Una fila por estancia confirmada.
- Cuatro columnas: espacio, ambiente actual, uso y estado.
- El ambiente agrupa temperatura, humedad y CO₂ en una sola línea.
- En estancias de solo presencia se indica “solo presencia”.

### `EnvironmentRoomPage`

- Página de una estancia.
- Cabecera compacta con valores actuales, aviso de dato obsoleto y enlace de vuelta.
- Resumen del periodo y gráficas principales de temperatura y CO₂.
- El mapa horario, la humedad, los cruces, la comparativa y el gas se agrupan en “Análisis avanzado”, plegado por defecto.

### `EnvironmentRoomStats`

- Cuatro KPIs básicos: temperatura media, humedad media, CO₂ medio y ocupación media.
- Rangos de temperatura y humedad, pico de CO₂ y horas ocupadas como apoyo.

### `EnvironmentRoomClimateCharts`

- `EnvironmentRoomTemperatureChart`: temperatura de la estancia y ambiente de referencia.
- `EnvironmentRoomHumidityChart`: humedad con bandas de confort 30–60 %, dentro de “Análisis avanzado”.

### `EnvironmentRoomCo2Chart`

- CO₂ y presencia en el tiempo.
- Umbrales 800/1.000 ppm.

### `EnvironmentHeatmap`

- Mapa 7×24 de ocupación o CO₂ por día de la semana y hora.

### `EnvironmentCo2OccupancyCard`

- CO₂ con presencia frente a CO₂ sin presencia.
- Incremento, correlación y dispersión por intervalo.

### `EnvironmentThermalRecoveryCard`

- Temperatura de reposo.
- Tiempo mediano de recuperación tras desocupar.
- Cambio en la primera hora y transiciones que no recuperan en 6 horas.

### `EnvironmentBenchmarkCard`

- Comparación de temperatura, humedad, CO₂ y ocupación con la media del resto de estancias.

### `EnvironmentGasContextChart`

- Temperatura de la estancia y ambiente de referencia.
- Coste de gas del edificio en el periodo.
- Aviso: el gas es del edificio y puede incluir otros usos.

Las fechas son propias de Infraestructura; no dependen del selector global de Iluminación.

## 6. Medio Ambiente

### `WeatherDashboard`

- Carga `/weather/overview` con la ventana de 7, 30 o 90 días.
- Compone estado actual, resumen, gráficas, cruces, tabla diaria y notas.
- Muestra el origen (`mock`/`database`) y la hora de generación.

### `WeatherCurrent`

- Temperatura exterior, humedad, presión a nivel del mar, PM y batería.
- Estado `ok|stale|missing`, edad del dato y tendencia de presión.
- Punto de rocío, humedad absoluta y sensación térmica.

### `WeatherSummary`

- Cobertura, intervalo mediano y horas sin datos.
- Temperatura, amplitud diaria, humedad y presión.
- Horas de calor/frío, noches tropicales, grados-día y PM.

### `WeatherTemperatureChart` / `WeatherHumidityChart`

- Estación, `sensor.ambiente` como referencia interior y AEMET como referencia externa.
- AEMET se dibuja discontinua y se etiqueta como externa.

### `WeatherPressureChart`

- Presión de la estación reducida al nivel del mar.
- La comparación con AEMET se hace en su tarjeta, no en la misma escala.

### `WeatherPmChart`

- PM1, PM2.5 y PM10 como índice relativo.
- No se comparan con umbrales sanitarios.

### `WeatherIndoorCross` / `WeatherAemetCross` / `WeatherEnergyCross` / `WeatherPmCross`

- Cruces con el interior, AEMET, la energía y las partículas.
- AEMET incluye barras de sesgo por hora y aviso de exposición solar.
- Energía avisa de los días excluidos por saltos anómalos.

### `WeatherDailyTable`

- Resumen diario con cobertura, extremos, PM, temperatura interior y energía.
- Queda plegado en “ver resumen diario”.

## 7. Mantenimiento

### `MaintenanceDashboard`

- Carga `/maintenance/overview` con la ventana de 7, 30 o 90 días.
- Compone filtros, resumen, matriz, cortes, tabla, mapa avanzado y notas.
- Muestra el origen (`mock`/`database`) y la hora de generación.

### `MaintenanceFilters`

- Selector de periodo: 7, 30 o 90 días.

### `MaintenanceSummary`

- Seis tarjetas: baterías bajas/críticas, dispositivos sin datos, cortes, disponibilidad, cambios detectados y previsión de sustitución.

### `MaintenanceMatrix`

- Cruce 3×2: batería OK/baja/sin lectura × datos OK/sin datos.
- Cada celda resume la decisión de mantenimiento.

### `MaintenanceOutages`

- Cortes globales y de grupo, con duración, dispositivos afectados y si siguen en curso.

### `MaintenanceDeviceTable`

- Tabla ordenada por prioridad.
- Filtros: todos, prioritarios, batería baja y sin datos.
- Cada fila se expande para cargar el detalle del dispositivo.

### `MaintenanceDeviceDetail`

- Historial de batería con umbrales.
- Transmisión diaria frente a la esperada.
- Cortes individuales, de grupo y globales que afectan al dispositivo.

### `MaintenanceHeatmap`

- Mapa diario de disponibilidad por dispositivo, dentro de “análisis avanzado”.

## 8. UI reutilizable

| Componente | Uso |
| ---------- | --- |
| `SectionHeading` | Título y subtítulo de la pestaña. |
| `ChartCard` | Marco de gráfica con estados de carga, error y vacío. |
| `StatCard` | Tarjeta de KPI. |
| `SelectField` | Selector con etiqueta. |
| `RangeSelector` | Botones de periodo global. |
| `ExportCsvButton` | Descarga CSV con BOM UTF-8 para Excel. |

## 9. Estados

Todas las gráficas contemplan:

- **Cargando:** esqueleto o mensaje.
- **Error:** texto y botón **Reintentar**.
- **Vacío:** mensaje sin datos para el periodo.
- **Datos:** gráfica y detalle.

## 10. Estilos

- Tailwind CSS y variables institucionales.
- `lib/chartTheme.ts` centraliza paletas y estilos de ejes.
- Electricidad tiene paletas propias de edificios y sectores; Iluminación e Infraestructura conservan las suyas.
- El diseño es responsive: una columna en móvil y varias en escritorio.
