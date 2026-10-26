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
│   ├── meta.ts             Edificios
│   └── http.ts             fetch + errores
├── components/
│   ├── Header.tsx
│   ├── stats/electricity/  Dashboard, filtros, resumen y gráficas
│   ├── stats/lighting/     Consumo, ranking y despilfarro
│   └── ui/                 ChartCard, StatCard, ExportCsvButton, SelectField, RangeSelector
├── context/
│   └── RangeContext.tsx    Periodo global de Iluminación
├── hooks/
│   ├── useElectricity.ts
│   ├── useLighting.ts
│   └── useBuildings.ts
├── lib/
│   ├── electricity.ts      Fechas, periodos y granularidad automática
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

- `pages/Stats.tsx` renderiza la pestaña activa.
- `lib/sections.ts` define **Electricidad** e **Iluminación**; la pestaña por defecto es Electricidad.
- `lib/urlState.ts` sincroniza `?tab=` y `?range=`. Los valores desconocidos vuelven a los valores por defecto.
- El selector global de periodo se muestra **solo en Iluminación**.
- Electricidad mantiene sus propias fechas y su comparativa.

## Electricidad

Componentes:

| Componente | Responsabilidad |
| ---------- | --------------- |
| `ElectricityDashboard` | Carga metadatos/estadísticas, calcula granularidad y compone la vista. |
| `ElectricityFilters` | Fechas, edificio, sector y métrica. |
| `ElectricitySummary` | Total, media, mínimo, máximo, base y cobertura. |
| `ElectricityBuildingsChart` | Barras apiladas de los tres edificios + línea de base. |
| `ElectricitySectorsChart` | Sectores de Fermín, CPD y “No desglosado”. |
| `ElectricityComparisonChart` | Dos periodos independientes con dos líneas y base común. |

Reglas de interfaz:

- Fechas inclusivas y validación de fecha final.
- La agrupación se deduce del rango con `granularityForPeriod`: día hasta 31 días, semana hasta 120, mes hasta 3 años y año para rangos mayores.
- No hay selector “Agrupar por”.
- El indicador de origen muestra `mock` o `database`.
- Los avisos de cobertura y de intervalos parciales son explícitos.
- La comparativa exige el mismo número de intervalos y avisa si las fechas son inválidas o anteriores al inicio de los datos.

## Iluminación

| Componente | Responsabilidad |
| ---------- | --------------- |
| `LightingConsumptionChart` | Luminarias frente a otras cargas y horas de luz natural. |
| `LightingBySpaceChart` | Ranking de espacios y exportación CSV. |
| `LightingWasteChart` | Luz encendida sin ocupación y coste anualizado. |

El periodo y el edificio son globales para las tres gráficas.

## Hooks y caché

| Hook | Consulta | `staleTime` |
| ---- | -------- | ----------- |
| `useElectricityMeta` | `/energy/electricity/meta` | 30 min |
| `useElectricity` | `/energy/electricity` | 60 s |
| `useElectricityCompare` | `/energy/electricity/compare` | 60 s |
| `useLightingConsumption` | `/lighting/consumption` | 60 s |
| `useLightingBySpace` | `/lighting/by-space` | 60 s |
| `useLightingWaste` | `/lighting/waste` | 60 s |
| `useBuildings` | `/meta/buildings` | 30 min |

## Estilos

- La paleta institucional está en `styles/theme.css` y `lib/chartTheme.ts`.
- Electricidad tiene colores propios de edificios y sectores para no alterar Iluminación.
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
- Cliente API de Electricidad.
- Componente `ChartCard`.

`npm run typecheck` y `npm run build` deben pasar antes de entregar.
