# Componentes

## 1. Estructura de la web

`pages/Stats.tsx` contiene la cabecera y decide qué pestaña mostrar. Solo hay dos:

| id | Etiqueta |
| -- | -------- |
| `electricidad` | Electricidad |
| `iluminacion` | Iluminación |

La pestaña por defecto es `electricidad`. La URL guarda `?tab=` y `?range=`.

## 2. Cabecera

`components/Header.tsx`:

- Logos institucionales.
- Pestañas.
- Selector de periodo global, visible **solo en Iluminación**.
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

- Dos periodos independientes A/B.
- Dos líneas de color y base común.
- Botones para reutilizar el periodo principal o el año anterior.
- Validación de fechas y de igual número de intervalos.
- Exportación CSV.

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

## 5. UI reutilizable

| Componente | Uso |
| ---------- | --- |
| `SectionHeading` | Título y subtítulo de la pestaña. |
| `ChartCard` | Marco de gráfica con estados de carga, error y vacío. |
| `StatCard` | Tarjeta de KPI. |
| `SelectField` | Selector con etiqueta. |
| `RangeSelector` | Botones de periodo global. |
| `ExportCsvButton` | Descarga CSV con BOM UTF-8 para Excel. |

## 6. Estados

Todas las gráficas contemplan:

- **Cargando:** esqueleto o mensaje.
- **Error:** texto y botón **Reintentar**.
- **Vacío:** mensaje sin datos para el periodo.
- **Datos:** gráfica y detalle.

## 7. Estilos

- Tailwind CSS y variables institucionales.
- `lib/chartTheme.ts` centraliza paletas y estilos de ejes.
- Electricidad tiene paletas propias de edificios y sectores; Iluminación conserva la suya.
- El diseño es responsive: una columna en móvil y varias en escritorio.
