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
- Mantiene el periodo en la URL al cambiar de aula.

### `EnvironmentIndex`

- Selector Día / Semana / Mes, con el día actual por defecto.
- Rejilla de tarjetas de A11, A12, A21 y A22.
- Enlaces al detalle de cada aula conservando `start` y `end`.

### `EnvironmentRangeSelector`

- Botones de periodo y fechas visibles.
- Escribe el periodo en la URL para compartir o volver desde el detalle.

### `EnvironmentRoomCard`

- Tarjeta con la estética del proyecto Smart ESI: imagen, categoría «Aula», código, nombre y presencia.
- Métricas actuales: temperatura, humedad y presencia (Sí/No).
- El color de la insignia indica si hay presencia ahora.

### `EnvironmentRoomPage`

- Enlace de vuelta, cabecera con valores actuales y selector de periodo.
- Tres gráficas: temperatura, humedad y presencia.

### `EnvironmentRoomCharts`

- `EnvironmentRoomTemperatureChart`: línea de temperatura y banda de confort 18–24 °C.
- `EnvironmentRoomHumidityChart`: línea de humedad y banda de confort 30–60 %.
- `EnvironmentRoomPresenceChart`: escalón 0/1 con eje «Sí/No» por intervalo.

Las fechas son propias de Infraestructura; no dependen del selector global de Iluminación.

## 6. Medio Ambiente

### `WeatherDashboard`

- Compone filtros, valores actuales, aviso de AEMET, comparación, gráficas, resumen y notas.
- Si el periodo no tiene datos de AEMET, oculta la comparación y muestra solo la estación.

### `WeatherFilters`

- Fechas Desde/Hasta y atajos de 7, 30 y 90 días, guardados en la URL.

### `WeatherCurrent`

- Última lectura de la estación y última observación guardada de AEMET, con su antigüedad.

### `WeatherAemetNotice`

- Indica si no hay datos de AEMET, si la cobertura es parcial y si AEMET ha dejado de actualizarse.

### `WeatherComparison`

- Diferencia media (estación − AEMET), error absoluto medio y correlación de temperatura, humedad y presión.
- Temperatura separa día y noche y avisa de una posible exposición solar.
- Humedad muestra las horas con el sensor saturado y la diferencia sin ellas.

### `WeatherTemperatureChart` / `WeatherHumidityChart` / `WeatherPressureChart`

- Estación continua y AEMET discontinua en la misma gráfica. Los huecos se dejan sin unir.
- La presión de ambas está a la altitud del observatorio de AEMET.

### `WeatherHourlyBiasChart`

- Diferencia de temperatura por hora local.

### `WeatherRainChart` / `WeatherPmChart` / `WeatherBatteryChart`

- Lluvia de AEMET, partículas de la estación como índice relativo y batería de la estación.

### `WeatherSummary`

- Medias y extremos de la estación, cobertura, partículas, batería mínima y lluvia total.

## 7. Mantenimiento

### `BatteryDashboard`

- Lee el grupo de la ruta `/mantenimiento/:groupId` y muestra sus sensores en tarjetas.

### `BatterySensorCard`

- Muestra el último valor válido, su estado y su fecha. Las aulas añaden el % estimado.

### `BatteryHistoryDialog` y `BatteryHistoryChart`

- Muestran el histórico del sensor con fechas libres y accesos a 30 días, 90 días, 1 año y todo.

> Los componentes siguientes pertenecen al panel anterior y no están montados en la interfaz.


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
