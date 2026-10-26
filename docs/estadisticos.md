# Estadísticos y cruces de datos

Catálogo de los **estadísticos** que calcula el backend, **de dónde salen**, **cómo se agregan** y
**para qué decisión sirven**. El objetivo del panel no es solo mostrar series, sino **cruzar
variables para tomar decisiones** sobre el gasto eléctrico y de gas.

- La materia prima (datos sintéticos o reales) se describe en [`datos.md`](datos.md).
- Cómo se pintan estos estadísticos en la web está en [`componentes.md`](componentes.md) y
  [`graficas.md`](graficas.md).

> **Origen (modo `DATA_SOURCE=database`)**: la energía horaria del centro, Módulo A, Módulo B y los
> cuadros de Fermín, el gas del centro, los grados-día, las temperaturas (exterior e interior por
> aula), la humedad, la ocupación por edificio (contadores de entrada/salida) y el CO₂ de
> A11/A12/A21/A22 son **reales** (BD de Home Assistant, solo `SELECT`). Fermín Caballero se deriva
> como `Cuadro General − Módulo A − Módulo B`; los cuadros de planta y el CPD son parciales. Las
> **electroválvulas**, el reparto de ocupación por aula y la iluminación siguen siendo sintéticos, así
> que los estadísticos que dependen de ellos (estado de válvulas, gas en aulas vacías y luz sin
> ocupación) son estimaciones. Detalle y estado por estadístico en
> [`datos.md`](datos.md#41-estado-por-estadístico).

---

## 1. Estadística descriptiva base

En [`backend/app/services/stats.py`](../backend/app/services/stats.py) hay una pequeña librería de
estadística en Python puro (sin dependencias numéricas) que reutilizan los servicios:

| Función | Qué calcula | Se usa para |
| ------- | ----------- | ----------- |
| `mean` | Media. | Medias de consumo, temperatura, CO₂. |
| `median` | Mediana. | Robustez frente a picos. |
| `stdev` | Desviación típica (poblacional). | Dispersión del consumo. |
| `percentile` | Percentil con interpolación. | Umbrales (p. ej. picos). |
| `coefficient_of_variation` | Desviación típica entre el valor absoluto de la media. | Variabilidad relativa. |
| `least_squares` | Ajuste mínimo-cuadrático + **Pearson**. | Recta de regresión y correlaciones. |
| `trend_slope` | Pendiente frente al índice temporal. | Tendencias. |

Estas funciones son la base del cruce **ocupación ↔ CO₂** (`/correlation/occupancy-air-quality`) y de
varias de las gráficas de decisión.

---

## 2. Los cruces con intención de decisión

Cada cruce se implementa en un servicio, expone un endpoint y alimenta una o varias gráficas.

### 2.1 Reparto por edificio y ámbito — *reparto*

- **Endpoint:** `GET /api/v1/energy/electricity` · **Servicio:** `electricity_service.build_electricity`
- **Cruza:** total del centro ↔ Módulo A ↔ Módulo B ↔ Fermín Caballero ↔ sectores de Fermín.
- **Cálculo:** para un rango de fechas absoluto (`start`–`end`) y una granularidad
  día/semana/mes/año, suma la energía horaria de cada ámbito. El total del centro es
  `sensor.cuadro_general`; Módulo A y Módulo B son contadores directos; Fermín se deriva como
  `Cuadro General − Módulo A − Módulo B`. Devuelve total, media, mínimo, máximo y base.
- **Métrica:** consumo (kWh) o coste (`kWh · 0,20 €/kWh`).
- **Decisión:** saber qué edificio concentra el gasto y cómo evoluciona en el intervalo elegido.
- **Gráfica:** `ElectricityBuildingsChart` (pestaña *Electricidad*).

### 2.2 Base de centro cerrado — *horario*

- **Endpoint:** `GET /api/v1/energy/electricity` · **Servicio:** `electricity_service.build_electricity`
- **Cruza:** consumo eléctrico ↔ horario de apertura.
- **Cálculo:** se consideran horas cerradas las **noches de lunes a viernes (21:00–07:00)** y los
  **fines de semana completos**. La base es la media de kWh/h en esas horas; para cada intervalo se
  proyecta al número de horas del intervalo. Los festivos no se excluyen (limitación conocida).
- **Decisión:** cuantificar el consumo de fondo y compararlo con la actividad real; si la base se
  acerca al total, el margen de ahorro está en equipos que siguen encendidos sin actividad.
- **Gráfica:** línea discontinua en `ElectricityBuildingsChart` y `ElectricityComparisonChart`.

### 2.3 Luz frente a luz natural y estacionalidad — *iluminación*

- **Endpoint:** `GET /api/v1/lighting/consumption` · **Servicio:** `lighting_service.build_consumption`
- **Cruza:** electricidad de luminarias ↔ horas de luz natural ↔ ocupación.
- **Cálculo:** la electricidad se divide en **luminarias** y **resto** con `lighting_fraction`, que
  baja cuando hay luz natural suficiente y sube de noche. Se acompaña de `daylight_hours` y
  `occupancy_pct`.
- **Decisión:** ver cuánto pesa la iluminación sobre el total y si el encendido sigue al día (en
  verano debería encenderse más tarde y apagarse antes).
- **Gráfica:** `LightingConsumptionChart` (pestaña *Iluminación*).

### 2.4 Luminarias encendidas sin ocupación — *despilfarro de luz*

- **Endpoint:** `GET /api/v1/lighting/waste` · **Servicio:** `lighting_service.build_waste`
- **Cruza:** luz encendida ↔ ocupación (vacío).
- **Cálculo:** se marca "vacío" cuando `ocupación/aforo ≤ EMPTY_OCCUPANCY_RATIO (0,05)`. Se suma la
  luz consumida en esas horas y se **anualiza** el coste (`coste · 365 / días_del_rango`).
- **Decisión:** apagar/dimmar luminarias por horario u ocupación; el € anualizado justifica la
  inversión en sensores o programación.
- **Gráfica:** `LightingWasteChart` (pestaña *Iluminación*).

### 2.5 Temperatura en aulas vacías — *despilfarro de gas*

- **Endpoint:** `GET /api/v1/climate/empty-spaces` · **Servicio:** `climate_service.build_empty_spaces`
- **Cruza:** gas ↔ temperatura ↔ ocupación (vacío).
- **Cálculo:** en las horas con `ocupación ≤ 0`, si la válvula está abierta se le asigna su parte del
  gas del edificio (`gas / nº válvulas abiertas`). Se guardan horas calentadas sin ocupación y el
  coste **anualizado**.
- **Decisión:** no calentar lo que está vacío (noches, fines de semana, fuera de horario); detecta
  válvulas y programaciones que se saltan el horario.
- **Gráfica:** `EmptySpacesHeatingChart` (pestaña *Climatización y gas*).

### 2.6 Comparativa de dos periodos — *evolución*

- **Endpoint:** `GET /api/v1/energy/electricity/compare` · **Servicio:**
  `electricity_service.build_electricity_compare`
- **Cruza:** periodo A ↔ periodo B, ambos independientes.
- **Cálculo:** se agregan los dos periodos con la misma granularidad y ámbito. Deben tener el mismo
  número de intervalos; se alinean por índice y se devuelve `period_a`, `period_b`, `baseline` y
  `delta_pct = (A − B) / B · 100`. La base común es la media de horas cerradas de ambos periodos.
- **Decisión:** comparar años, meses o semanas completas (por ejemplo, 2026 frente a 2025) y separar
  el efecto de la actividad del consumo de fondo.
- **Gráfica:** `ElectricityComparisonChart` (pestaña *Electricidad*).

### 2.7 Electroválvulas frente a temperatura de aula — *calefacción*

- **Endpoint:** `GET /api/v1/climate/valves` · **Servicio:** `climate_service.build_valves`
- **Cruza:** estado de las electroválvulas ↔ temperatura alcanzada ↔ consigna.
- **Cálculo:** por espacio, `% de horas` con la válvula abierta, temperatura media y **desviación**
  frente a la consigna. El estado se deriva de `valve_health`:
  `ok` / `fria` (atascada cerrada) / `valvula_abierta` (atascada abierta).
- **Decisión:** localizar aulas que **no llegan a consigna** (válvula cerrada, avería) y aulas que se
  **calientan de más** (válvula abierta), además de relacionar demanda de calor con temperatura.
- **Gráfica:** `ValvesTemperatureChart` (pestaña *Climatización y gas*).

### 2.8 Gas frente a grados-día y temperatura — *climatización*

- **Endpoint:** `GET /api/v1/climate/gas` · **Servicio:** `climate_service.build_gas`
- **Cruza:** gas ↔ **grados-día de calefacción** ↔ temperatura exterior/interior.
- **Cálculo:** `grados_día = Σ max(0, base − exterior) / 24`, con `base = HEATING_BASE_TEMPERATURE_C`.
  Se calcula la **correlación de Pearson** entre grados-día y gas, y el ratio `kWh por grado-día`.
- **Decisión:** verificar que el gas **sigue al frío** (si no, hay algo raro: fugas, horarios,
  consignas), y estimar el coste de un invierno más o menos frío.
- **Gráfica:** `GasConsumptionChart` (pestaña *Climatización y gas*).

### 2.9 Sectores de Fermín y cobertura — *desglose parcial*

- **Endpoint:** `GET /api/v1/energy/electricity` · **Servicio:** `electricity_service.build_electricity`
- **Cruza:** total de Fermín ↔ cuadros de planta ↔ CPD.
- **Cálculo:** suma los subcontadores `sensor.planta_*` y `sensor.sala_computacion`. Como no cubren
  todo el edificio, devuelve `sectors_total`, `unmetered_total = Fermín − sectores` y
  `sector_coverage = sectores / Fermín`. El cuadro E se marca `has_data=false` porque su suma
  acumulada no se ha movido desde 2023.
- **Decisión:** localizar los sectores que más pesan y detectar cuadros anómalos, sin confundir el
  total del edificio con la suma de los subcontadores.
- **Gráfica:** `ElectricitySectorsChart` (pestaña *Electricidad*).

### 2.10 Eficiencia eléctrica por superficie — *legacy*

- **Endpoint:** `GET /api/v1/energy/efficiency` · **Servicio:** `energy_service.build_efficiency`
- **Cruza:** consumo eléctrico ↔ superficie ↔ ocupación.
- **Cálculo:** kWh/m² y kWh/persona·hora a partir del total del centro y del reparto por
  edificio/espacio. Sigue usando el mapeo antiguo de energía y ya no se muestra en la pestaña de
  Electricidad; se conserva porque el panel de Decisiones lo reutiliza.
- **Decisión:** detectar espacios con un consumo por m² muy por encima de la media.
- **Gráfica:** `EnergyEfficiencyChart` (componente legacy, no visible en la nueva pestaña).

---

## 3. De los cruces a decisiones: el ranking de oportunidades

- **Endpoint:** `GET /api/v1/decisions/opportunities` · **Servicio:** `decisions_service.build_opportunities`
- **Qué hace:** reutiliza los cruces anteriores y los traduce a **oportunidades concretas con €/año**,
  ordenadas por impacto. Es la respuesta a *"¿dónde gasto menos y cuánto ahorro?"*.

| Oportunidad | Cruce de origen | Ahorro estimado |
| ----------- | --------------- | --------------- |
| Apagar luminarias en espacios vacíos | 2.4 | Coste anualizado de la luz sin ocupación. |
| No calentar espacios sin ocupación | 2.5 | Coste anualizado del gas sin ocupación. |
| Reducir la carga base fuera de horario | 2.2 | 10 % de la carga base (factor prudente) · precio electricidad. |
| Revisar el espacio con más kWh/m² | 2.10 | Exceso sobre la media por m² · precio electricidad. |
| Consumo eléctrico al alza | 2.6 | Diferencia interanual · precio electricidad. |

Detalles de cálculo:

- La **anualización** usa los días del rango (`day`=1, `week`=7, `month`=30, `year`=365).
- La **prioridad** es `alta` si el ahorro ≥ 1.000 €/año, `media` si ≥ 300 €/año, `baja` si no.
- El total de ahorro potencial **excluye** la categoría `tendencia` (es un aviso, no una medida
  accionable directa).

- **Gráfica:** `DecisionsPanel` (pestaña *Decisiones*).

---

## 4. Cruces descartados (por ahora)

Del análisis inicial se dejaron fuera, para no sobrecargar el panel:

- **Perfil horario / *heatmap* hora × día:** útil, pero redundante con la carga base y la ocupación.
- **Detección de anomalías por z-score:** potente, pero requiere histórico largo y un umbral bien
  calibrado; se retomará cuando haya datos reales.

Quedan anotados en [`backlog.md`](backlog.md).

---

## 5. Resumen estadístico por dominio

| Dominio | Endpoint | Estadísticos principales |
| ------- | -------- | ------------------------ |
| Electricidad (nueva) | `/energy/electricity` | total, media, mínimo, máximo, base, tres edificios, sectores y cobertura. |
| Electricidad (nueva) | `/energy/electricity/compare` | dos periodos, `delta_pct`, base común. |
| Electricidad (legacy) | `/energy/consumption`, `/energy/by-building`, `/energy/breakdown`, `/energy/compare`, `/energy/efficiency` | endpoints anteriores, aún disponibles para pestañas no migradas. |
| Iluminación | `/lighting/consumption` | luz total, cuota, coste, CO₂, luz natural. |
| Iluminación | `/lighting/by-space` | ranking por luminarias y cuota por edificio. |
| Iluminación | `/lighting/waste` | luz sin ocupación, `%` despilfarro, €/año. |
| Climatización | `/climate/gas` | gas, grados-día, correlación, kWh/grado-día, temperaturas. |
| Climatización | `/climate/valves` | % válvula abierta, desviación de consigna, estado. |
| Climatización | `/climate/empty-spaces` | gas sin ocupación, horas calentadas, €/año. |
| Ocupación y aire | `/correlation/occupancy-air-quality` | Pearson, medias, reparto CO₂ bueno/moderado/pobre. |
| Decisiones | `/decisions/opportunities` | oportunidades priorizadas con €/año. |
