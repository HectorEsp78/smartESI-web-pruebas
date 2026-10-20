# Componentes de la web

Catálogo de las **piezas que se ven en la página** y de cómo están construidas: pestañas, selector
de periodo global, componentes de UI reutilizables y cada gráfica con su endpoint.

- Qué estadístico hay detrás de cada gráfica: [`estadisticos.md`](estadisticos.md).
- Estructura y stack del frontend: [`frontend.md`](frontend.md).
- Origen de los datos: [`datos.md`](datos.md).

La página es **una sola SPA** (`pages/Stats.tsx`) organizada en **seis pestañas**. Encima de todas
hay un **selector de periodo global** en la cabecera.

---

## 1. Estructura de la página

```text
Stats.tsx
└── <RangeProvider>            (contexto del periodo global)
    ├── Header                 (logos + pestañas + selector de periodo)
    └── <main>
        ├── SectionHeading     (título de la pestaña activa)
        └── <contenido de la pestaña>
```

### Pestañas (`lib/sections.ts`)

| id | Etiqueta | Contenido |
| -- | -------- | --------- |
| `resumen` | Resumen | `OverviewSection` (KPIs). |
| `electricidad` | Electricidad | Consumo, desglose, comparativa, eficiencia y por edificio. |
| `iluminacion` | Iluminación | Luz vs. natural, ranking por espacio y despilfarro. |
| `climatizacion` | Climatización y gas | Gas/grados-día, válvulas y aulas vacías. |
| `ocupacion-aire` | Ocupación y aire | Cruce ocupación ↔ CO₂. |
| `decisiones` | Decisiones | `DecisionsPanel`. |

El estado de la pestaña activa vive en `Stats.tsx`; `Header` lo recibe por props y lo pinta.

### Periodo global (`context/RangeContext.tsx`)

- `RangeProvider` guarda el rango (`day` / `week` / `month` / `year`) en un contexto.
- `useGlobalRange()` lo consumen la cabecera (para el selector) y **todas** las gráficas.
- Al cambiar el periodo en la cabecera, todas las pestañas se recalculan a la vez.
- Los controles **de edificio y de métrica siguen siendo locales** a cada gráfica.

### Cabecera (`components/Header.tsx`)

- Logos UCLM / ESI y banner Smart ESI (identidad institucional).
- **Pestañas** con la línea activa animada (`motion`).
- **Selector de periodo** global (`RangeSelector`), visible en todo momento.

---

## 2. Componentes de UI reutilizables (`components/ui/`)

| Componente | Para qué sirve |
| ---------- | -------------- |
| `ChartCard` | Tarjeta de gráfica: título, subtítulo, unidad, controles (`headerExtra`) y estados *cargando* / *error* / *vacío* con botón de reintento. |
| `RangeSelector` | Grupo de botones tipo "segmented control" (se usa para métrica y para el periodo global). |
| `SelectField` | Desplegable etiquetado (se usa para el edificio). |
| `StatCard` | Tarjeta de KPI con etiqueta, valor, pista y tono (`primary` / `accent` / `success` / `warning` / `neutral`). |
| `SectionHeading` | Título de sección con la barra granate institucional (`border-l-4 border-accent`). |

Los colores y estilos de gráfica se centralizan en `lib/chartTheme.ts` (paleta institucional, color
por edificio y estilos de ejes/tooltip).

---

## 3. Resumen (`OverviewSection`)

- **Endpoints:** reutiliza `/energy/by-building`, `/correlation/...`, `/climate/gas` y
  `/decisions/opportunities`.
- **Qué muestra:** seis KPIs — consumo eléctrico del periodo, edificio que más consume, gas
  (kWh, € y grados-día), ahorro potencial anual, % de aire bueno y CO₂ medio.
- **Decisión:** foto rápida de la salud energética antes de bajar al detalle.

---

## 4. Electricidad

| Componente | Endpoint | Qué muestra |
| ---------- | -------- | ----------- |
| `EnergyConsumptionChart` | `/energy/consumption` | Área con la evolución del consumo + métrica (kWh/€/CO₂) y edificio. |
| `EnergyBreakdownChart` | `/energy/breakdown` | Barras apiladas **carga base vs. actividad** y **luz vs. resto**, con cuotas. |
| `EnergyCompareChart` | `/energy/compare` | Líneas **periodo actual vs. anterior** + `delta_pct`. |
| `EnergyEfficiencyChart` | `/energy/efficiency` | Barras horizontales de **kWh/m²** + tabla con kWh/persona·hora y coste; avisa de la cobertura parcial del desglose. |
| `EnergyByBuildingChart` | `/energy/by-building` | Barras por edificio, top de espacios y tabla con `%` sobre el total; añade «No desglosado» para cuadrar con el cuadro general. |

**Controles:** edificio (`SelectField`) y métrica (`RangeSelector`); el periodo lo fija la cabecera.

---

## 5. Iluminación

| Componente | Endpoint | Qué muestra |
| ---------- | -------- | ----------- |
| `LightingConsumptionChart` | `/lighting/consumption` | Barras de luz y otras cargas + línea de **horas de luz natural**. |
| `LightingBySpaceChart` | `/lighting/by-space` | Barras horizontales del consumo de **luminarias por espacio** + tabla. |
| `LightingWasteChart` | `/lighting/waste` | Luz **sin ocupación** por espacio y **€/año** ahorrable. |

**KPIs destacados:** peso de la iluminación sobre el total, cuota de despilfarro y ahorro anualizado.

---

## 6. Climatización y gas

| Componente | Endpoint | Qué muestra |
| ---------- | -------- | ----------- |
| `GasConsumptionChart` | `/climate/gas` | Barras de gas + línea de **grados-día**, y temperaturas interior/exterior. KPIs de correlación y kWh/grado-día. |
| `ValvesTemperatureChart` | `/climate/valves` | % de electroválvulas abiertas + temperatura media con la **consigna** de referencia; tabla de estado por aula. |
| `EmptySpacesHeatingChart` | `/climate/empty-spaces` | Gas gastado **sin ocupación** por espacio + €/año. |

**Estados por aula** (`status`): `ok`, `fria` (válvula cerrada de más), `valvula_abierta`,
mostrados como etiquetas con color.

---

## 7. Ocupación y aire (`OccupancyAirQualityChart`)

- **Endpoint:** `/correlation/occupancy-air-quality`.
- **Qué muestra:** dispersión ocupación ↔ CO₂ con recta de regresión, evolución conjunta (ocupación
  por área y CO₂ por línea) y KPIs (Pearson, CO₂ medio/máximo, % aire bueno, ocupación media).
- **Umbrales CO₂:** bueno < 800 ppm, moderado 800–1200 ppm, pobre > 1200 ppm.

---

## 8. Decisiones (`DecisionsPanel`)

- **Endpoint:** `/decisions/opportunities`.
- **Qué muestra:** tarjetas de oportunidades ordenadas por **ahorro €/año**, con categoría, prioridad,
  descripción, **evidencia** (los datos que la sustentan) y energía asociada.
- **KPIs:** ahorro potencial total, número de oportunidades y medida prioritaria.
- **Categorías:** `iluminacion`, `calefaccion`, `electricidad`, `tendencia`.

---

## 9. Capa de datos del frontend

```text
components/*  →  hooks/use*  →  api/*  →  fetch /api/v1/...
                     │
        context/RangeContext  ·  lib/  ·  types/
```

- **`types/`**: un DTO por respuesta de la API (en `snake_case`, igual que el backend):
  `energy.ts`, `lighting.ts`, `climate.ts`, `decisions.ts`, `correlation.ts`, `meta.ts`.
- **`api/`**: una función `fetch*` por endpoint, con `signal` de cancelación.
- **`hooks/`**: envuelven la API en `useQuery` (`staleTime` 60 s, `placeholderData` para no
  parpadear): `useEnergyConsumption`, `useEnergyByBuilding`, `useEnergyStats`
  (breakdown/compare/efficiency), `useLighting`, `useClimate`, `useDecisions`,
  `useOccupancyAirQuality`, `useBuildings`.

---

## 10. Cómo añadir un componente nuevo

1. Añade el **endpoint** en el backend (router + schema + servicio) si hacen falta datos.
2. Añade el **DTO** en `src/app/types/`, la función `fetch*` en `src/app/api/` y el hook en
   `src/app/hooks/`.
3. Crea el **componente** en `src/app/components/stats/<dominio>/` usando `ChartCard` para la tarjeta
   y `RangeSelector` / `SelectField` para los controles. Reutiliza `lib/chartTheme.ts` y `lib/format.ts`.
4. Añádelo al contenido de la pestaña correspondiente en `pages/Stats.tsx`.
5. Añade un test si la lógica lo merece.
