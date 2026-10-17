# Estadísticos y cruces de datos

Catálogo de los **estadísticos** que calcula el backend, **de dónde salen**, **cómo se agregan** y
**para qué decisión sirven**. El objetivo del panel no es solo mostrar series, sino **cruzar
variables para tomar decisiones** sobre el gasto eléctrico y de gas.

- La materia prima (datos sintéticos o reales) se describe en [`datos.md`](datos.md).
- Cómo se pintan estos estadísticos en la web está en [`componentes.md`](componentes.md) y
  [`graficas.md`](graficas.md).

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

## 2. Los ocho cruces con intención de decisión

Cada cruce se implementa en un servicio, expone un endpoint y alimenta una o varias gráficas.

### 2.1 Consumo frente a ocupación y superficie — *eficiencia*

- **Endpoint:** `GET /api/v1/energy/efficiency` · **Servicio:** `energy_service.build_efficiency`
- **Cruza:** electricidad (kWh) ↔ superficie (m²) ↔ ocupación (personas·hora).
- **Cálculo:** por edificio y por espacio, `kWh/m² = total / area` y
  `kWh/persona·hora = total / (personas·hora)`. La ocupación del espacio se reparte por superficie.
- **Decisión:** detectar espacios **ineficientes** (mucho kWh por m²) que merecen revisión, y
  comparar edificios con criterios homogéneos.
- **Gráfica:** `EnergyEfficiencyChart` (pestaña *Electricidad*).

### 2.2 Carga base frente a actividad — *horario*

- **Endpoint:** `GET /api/v1/energy/breakdown` · **Servicio:** `energy_service.build_breakdown`
- **Cruza:** consumo eléctrico ↔ franja horaria.
- **Cálculo:** `base` = consumo **fuera** de horario laborable (noches y fines de semana);
  `activity` = consumo en horario laborable (L–V, 7–21 h). `base + activity = total`.
- **Decisión:** cuantificar el gasto **fuera de horario** (equipos en espera, climatización
  desatendida), la palanca de ahorro más habitual.
- **Gráfica:** `EnergyBreakdownChart` (pestaña *Electricidad*).

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

### 2.6 Interanual y tendencia — *evolución*

- **Endpoint:** `GET /api/v1/energy/compare` · **Servicio:** `energy_service.build_compare`
- **Cruza:** periodo actual ↔ **periodo anterior equivalente**.
- **Cálculo:** cada bucket se compara con el mismo intervalo desplazado 24 h / 7 días / 30 días /
  12 meses según el rango. Devuelve `current`, `previous` y `delta_pct`.
- **Decisión:** saber si el consumo **sube o baja** y cuánto; la tendencia interanual positiva se
  convierte además en una oportunidad de ahorro (apartado 3).
- **Gráfica:** `EnergyCompareChart` (pestaña *Electricidad*).

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
| Revisar el espacio con más kWh/m² | 2.1 | Exceso sobre la media por m² · precio electricidad. |
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
| Electricidad | `/energy/consumption`, `/energy/by-building` | total, media, pico, reparto por edificio/espacio. |
| Electricidad | `/energy/breakdown` | carga base, actividad, luz, resto, cuotas. |
| Electricidad | `/energy/compare` | actual, anterior, `delta_pct`. |
| Electricidad | `/energy/efficiency` | kWh/m², kWh/persona·hora, media global. |
| Iluminación | `/lighting/consumption` | luz total, cuota, coste, CO₂, luz natural. |
| Iluminación | `/lighting/by-space` | ranking por luminarias y cuota por edificio. |
| Iluminación | `/lighting/waste` | luz sin ocupación, `%` despilfarro, €/año. |
| Climatización | `/climate/gas` | gas, grados-día, correlación, kWh/grado-día, temperaturas. |
| Climatización | `/climate/valves` | % válvula abierta, desviación de consigna, estado. |
| Climatización | `/climate/empty-spaces` | gas sin ocupación, horas calentadas, €/año. |
| Ocupación y aire | `/correlation/occupancy-air-quality` | Pearson, medias, reparto CO₂ bueno/moderado/pobre. |
| Decisiones | `/decisions/opportunities` | oportunidades priorizadas con €/año. |
