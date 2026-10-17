# Frontend (React + Vite)

Código en [`frontend/src/`](../frontend/src). Réplica del stack y del estilo del proyecto original.

## Stack

| Pieza | Uso |
| ----- | --- |
| React 18 + TypeScript | UI. |
| Vite 6 | Dev server y build. `base: '/'`, puerto `5174`, proxy `/api` → `127.0.0.1:8010`. |
| React Router 7 | Rutas (`createBrowserRouter`). |
| TanStack Query 5 | Peticiones, caché, reintentos y refresco. |
| Tailwind CSS 4 | Estilos (utilidades en el JSX, tokens en `styles/theme.css`). |
| Recharts 3 | Gráficas (área, barras, líneas, dispersión y composed). |
| motion | Animación de la línea activa de las pestañas. |
| lucide-react | Iconos. |
| date-fns | Formateo de fechas en ejes y tooltips. |
| Vitest + Testing Library + jsdom | Tests. |

> `@mui/material` y `@emotion/*` están en `package.json` para reflejar el mismo stack declarado del
> original, pero las gráficas usan Tailwind + Recharts (igual que las gráficas del proyecto
> original). No se importan en el código, así que no entran en el bundle.

## Capas

```text
pages/Stats  →  components/stats/*  →  hooks/use*  →  api/*  →  fetch /api/v1/...
                     │                     │
     context/RangeContext (periodo)   lib/ (format, chartTheme, sections)  ·  types/ (DTOs)
```

- **`api/`**: una función `fetch*` por endpoint (`energy.ts`, `lighting.ts`, `climate.ts`,
  `decisions.ts`, `correlation.ts`, `meta.ts`). La resolución de la URL vive en `api/baseUrl.ts` y
  las utilidades compartidas en `api/http.ts`.
- **`context/RangeContext.tsx`**: `RangeProvider` guarda el **periodo global**; `useGlobalRange()` lo
  consumen la cabecera y todas las gráficas. Así un único selector temporal afecta a todo el panel.
- **`hooks/`**: envuelven la API en `useQuery` y devuelven `{ data, isLoading, isFetching, error,
  retry }`. Usan `placeholderData` para no parpadear al cambiar de rango.

  | Hook | Query key | `staleTime` |
  | ---- | --------- | ----------- |
  | `useBuildings` | `['meta','buildings']` | 30 min |
  | `useEnergyConsumption` | `['energyConsumption', range, building, metric]` | 60 s |
  | `useEnergyByBuilding` | `['energyByBuilding', range, metric]` | 60 s |
  | `useEnergyBreakdown` | `['energyBreakdown', range, building]` | 60 s |
  | `useEnergyCompare` | `['energyCompare', range, building, metric]` | 60 s |
  | `useEnergyEfficiency` | `['energyEfficiency', range]` | 60 s |
  | `useLightingConsumption` / `useLightingBySpace` / `useLightingWaste` | `['lighting*', range, building]` | 60 s |
  | `useGas` / `useValves` / `useEmptySpaces` | `['gas'/'valves'/'emptySpaces', range, building]` | 60 s |
  | `useDecisions` | `['decisions', range, building]` | 60 s |
  | `useOccupancyAirQuality` | `['occupancyAirQuality', range, building]` | 60 s |

- **`components/ui/`**: piezas reutilizables — `ChartCard` (tarjeta con cabecera y estados
  cargando/error/vacío), `RangeSelector`, `SelectField`, `StatCard` y `SectionHeading`.
- **`components/stats/`**: las gráficas, con una subcarpeta por dominio: `electricity/`,
  `lighting/`, `climate/`, `decisions/`, más las de nivel superior (`OverviewSection`,
  `EnergyConsumptionChart`, `EnergyByBuildingChart`, `OccupancyAirQualityChart`). Cada componente
  gestiona sus propios controles **de edificio y métrica** con los hooks; el **periodo** lo toma del
  contexto global.
- **`pages/Stats.tsx`**: envuelve todo en `RangeProvider`, pinta el `Header` y el **contenido de la
  pestaña activa**. Las pestañas se definen en `lib/sections.ts`.
- **`components/Header.tsx`**: logos y banner, la navegación por pestañas y el **selector de periodo
  global**.

En [`componentes.md`](componentes.md) hay el catálogo detallado de cada pieza de la web.

## Estilos y tokens

- [`styles/theme.css`](../frontend/src/styles/theme.css) define los tokens (variables CSS mapeadas a
  Tailwind con `@theme`): `primary` `#0497d7` (azul UCLM), `accent` `#b30139` (granate ESI),
  `success`, `warning`, `destructive`, y las fuentes `font-heading` (Manrope), `font-room-card`
  (Montserrat) y la del cuerpo (Source Sans 3).
- Las fuentes se cargan con `<link>` de Google Fonts desde [`index.html`](../frontend/index.html)
  (no con `@import` en el CSS, para que el bundler no las descarte).
- Usa siempre las clases de token (`text-primary`, `border-accent`…) en lugar de colores sueltos.
- Patrón de títulos de sección: `border-l-4 border-accent` con el título en mayúsculas y color
  `accent` (ver `SectionHeading`).
- Colores de las gráficas centralizados en [`lib/chartTheme.ts`](../frontend/src/app/lib/chartTheme.ts)
  (paleta institucional y color por edificio).

## Cómo añadir una gráfica nueva

1. Añade el endpoint en el backend (router + schema + servicio) si necesitas datos nuevos.
2. Añade el DTO en `src/app/types/`, la función `fetch*` en `src/app/api/` y el hook en
   `src/app/hooks/`.
3. Crea el componente en `src/app/components/stats/<dominio>/` usando `ChartCard` para la tarjeta y
   `RangeSelector`/`SelectField` para los controles **locales** (edificio, métrica). Para el periodo,
   usa `useGlobalRange()` y no añadas un selector propio.
4. Añádelo al contenido de la pestaña correspondiente en `pages/Stats.tsx`. Si creas una pestaña
   nueva, añádela a `lib/sections.ts` y a `TAB_HEADING`.
5. Añade un test si la lógica lo merece.

## Tests

```bash
cd frontend
npm run test:run        # una pasada
npm test                # modo watch
npm run test:coverage   # informe en coverage/
npm run typecheck       # comprobación de tipos
```
