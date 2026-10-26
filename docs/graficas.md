# Gráficas

Todas las gráficas son **interactivas**: tooltips al pasar el ratón y controles para cambiar el
periodo (global en la cabecera, salvo en Electricidad, que tiene fechas propias), el edificio y/o la
métrica. Los colores siguen la identidad institucional (azul UCLM `#0497d7`, granate ESI `#b30139`,
y verdes/naranjas para estados).

El panel está organizado en **seis pestañas**. Aquí se resume **qué muestra cada gráfica y para qué
decisión es útil**; el detalle de cómo está construida cada pieza está en
[`componentes.md`](componentes.md) y el de los estadísticos en [`estadisticos.md`](estadisticos.md).

| Pestaña | Gráficas |
| ------- | -------- |
| Resumen | KPIs (`OverviewSection`). |
| Electricidad | Filtros propios, KPIs, gasto por edificio, sectores de Fermín y comparativa de periodos. |
| Iluminación | Luz vs. natural, ranking por espacio, despilfarro. |
| Climatización y gas | Gas/grados-día, válvulas, aulas vacías. |
| Ocupación y aire | Ocupación ↔ CO₂. |
| Decisiones | Ranking de oportunidades. |

---

## 1. Resumen (KPIs)

Seis tarjetas con indicadores clave del periodo seleccionado:

| KPI | Fuente | Para qué sirve |
| --- | ------ | -------------- |
| Consumo eléctrico | `/energy/by-building` | Magnitud global del gasto. |
| Edificio con mayor consumo | `/energy/by-building` | Dónde concentrar medidas de eficiencia. |
| Gas | `/climate/gas` | Gasto de calefacción y grados-día. |
| Ahorro potencial anual | `/decisions/opportunities` | Cuánto se puede rascar, en €/año. |
| Aire bueno | `/correlation/...` | % de tiempo con CO₂ por debajo de 800 ppm. |
| CO₂ medio | `/correlation/...` | Calidad del aire media y ocupación media. |

---

## 2. Electricidad

La pestaña tiene **controles propios de fecha**; el selector global de periodo de la cabecera se
oculta para no duplicar estados. Todo se calcula con un rango de fechas absoluto (`start`–`end`,
ambos inclusive) y se puede ver en **consumo (kWh)** o **coste (€)** a **0,20 €/kWh**.

**Componentes:** `ElectricityDashboard`, `ElectricityFilters`, `ElectricitySummary`,
`ElectricityBuildingsChart`, `ElectricitySectorsChart`, `ElectricityComparisonChart`.
**Endpoints:** `/energy/electricity`, `/energy/electricity/compare`, `/energy/electricity/meta`.

### 2.1 Filtros y KPIs

**Componente:** `ElectricityFilters` + `ElectricitySummary`

- **Fechas:** día inicial y día final, sin ventana horaria diaria. Los datos empiezan el
  **22/12/2023**.
- **Agrupación automática:** la interfaz elige el intervalo según la duración del rango: día hasta
  31 días, semana hasta 120, mes hasta 3 años y año para rangos mayores. No hay selector «Agrupar
  por». Las semanas se alinean de lunes a domingo y los meses y años son naturales; el primer y
  último intervalo pueden ser parciales.
- **Métrica:** consumo o coste.
- **Ámbito:** todos los edificios, Módulo A, Módulo B o Fermín Caballero. En Fermín se puede elegir
  además un sector concreto (cuadro de planta o CPD).

Las tarjetas muestran **total**, **media por intervalo**, **mínimo**, **máximo**, **base fuera de
horario** y **cobertura de los sectores** de Fermín.

### 2.2 Reparto por edificio

**Componente:** `ElectricityBuildingsChart` · **Endpoint:** `/energy/electricity`

Barras apiladas por intervalo con el gasto de **Módulo A**, **Módulo B** y **Fermín Caballero**, más
una línea discontinua con la **base de centro cerrado**. Debajo, una tabla con total, media, mínimo,
máximo y **% sobre el centro** de cada edificio.

La reconciliación es explícita:

- `sensor.cuadro_general` es el total del centro.
- `sensor.edificio_a` y `sensor.edificio_b` son los contadores directos de los módulos.
- Fermín Caballero **no tiene un contador único**: se calcula como
  `Cuadro General − Módulo A − Módulo B`.

**Decisiones:** ver qué edificio concentra el gasto y comparar su evolución con la base de centro
cerrado.

### 2.3 Sectores de Fermín Caballero

**Componente:** `ElectricitySectorsChart` · **Endpoint:** `/energy/electricity`

Barras apiladas por intervalo con los **cuadros de planta** y el **CPD**, más una barra gris de
**“No desglosado”**. La tabla muestra total, media, mínimo, máximo y **% sobre Fermín** de cada
sector.

Los cuadros son **subcontadores parciales**: no suman el total de Fermín. La gráfica nunca reparte
el resto entre los sectores; lo muestra aparte y publica la **cobertura medida**. En los datos
actuales cubren aproximadamente el **30–38 %** de Fermín según el periodo. El cuadro E aparece como
**sin datos** porque su suma acumulada no se ha movido desde 2023.

**Decisiones:** localizar los sectores que más pesan y detectar cuadros con comportamiento anómalo,
sin confundir el total del edificio con la suma de los subcontadores.

### 2.4 Comparativa de dos periodos

**Componente:** `ElectricityComparisonChart` · **Endpoint:** `/energy/electricity/compare`

Dos periodos **independientes** (A y B) en la misma gráfica, con dos líneas de colores distintos y
una línea discontinua de **base de centro cerrado**. Se comparan con la misma granularidad y el mismo
ámbito que los filtros. Los dos periodos deben tener el mismo número de intervalos; si no, la API
devuelve un error explicativo.

**KPIs:** total del periodo A, total del periodo B, variación A−B y base/hora. Si las duraciones en
días no coinciden (por ejemplo, enero frente a febrero con granularidad mensual), se muestra un aviso
de que la comparación de totales es informativa.

**Decisiones:** comparar años, meses o semanas completas (por ejemplo, 2026 frente a 2025) y separar
el efecto de la actividad del consumo de fondo.

### 2.5 Base de centro cerrado

La base se calcula con las horas en las que la Escuela está **cerrada y sin actividad**:

- **Lunes–viernes:** de 21:00 a 07:00.
- **Sábados y domingos:** todo el día.
- **Festivos:** no se excluyen actualmente; se documenta como limitación.

Para cada intervalo se proyecta la media horaria de esas horas al número de horas del intervalo. En
la gráfica de edificios se suma la base de los tres edificios; en la comparativa se usa la media
conjunta de las horas cerradas de ambos periodos. Así la línea representa el consumo esperado **si el
centro estuviera cerrado** y permite ver cuánto se separa la actividad real.

---

## 3. Iluminación

### 3.1 Luz frente a luz natural

**Componente:** `LightingConsumptionChart` · **Endpoint:** `/lighting/consumption`

Barras de **luminarias** y **otras cargas**, más una línea de **horas de luz natural**. **KPIs:**
consumo de luminarias, su peso sobre la electricidad y su coste/emisiones.

**Decisiones:** ver si el encendido sigue al día (en verano debería encenderse más tarde) y cuánto
pesa la iluminación.

### 3.2 Luminarias por espacio

**Componente:** `LightingBySpaceChart` · **Endpoint:** `/lighting/by-space`

Barras horizontales del consumo de luminarias por espacio y tabla con el **% sobre la iluminación
total** y **% sobre el edificio**.

**Decisiones:** priorizar la sustitución/zonificación de luminarias por impacto.

### 3.3 Luminarias encendidas sin ocupación

**Componente:** `LightingWasteChart` · **Endpoint:** `/lighting/waste`

Barras horizontales de la luz consumida **con el espacio vacío** y tabla con horas vacías y **€/año**.
**KPIs:** luz sin ocupación, cuota de despilfarro y ahorro anualizado.

**Decisiones:** programar/dimmar por horario u ocupación; el €/año justifica la inversión.

---

## 4. Climatización y gas

### 4.1 Gas y grados-día

**Componente:** `GasConsumptionChart` · **Endpoint:** `/climate/gas`

Barras de **gas** y línea de **grados-día** (y una gráfica de temperaturas interior/exterior).
**KPIs:** gas total, coste/CO₂, **correlación con los grados-día** y **kWh por grado-día**.

**Decisiones:** comprobar que el gas **sigue al frío**; si no, hay fugas, horarios o consignas raras.

### 4.2 Electroválvulas vs. temperatura de aula

**Componente:** `ValvesTemperatureChart` · **Endpoint:** `/climate/valves`

Área del **% de válvulas abiertas** y línea de **temperatura media** con la **consigna** de
referencia. Tabla por aula con desviación de consigna, horas por debajo y **estado**
(`ok` / `fria` / `valvula_abierta`).

**Decisiones:** localizar aulas que no llegan a consigna (válvula cerrada, avería) y aulas que
calientan de más.

### 4.3 Calefacción de espacios vacíos

**Componente:** `EmptySpacesHeatingChart` · **Endpoint:** `/climate/empty-spaces`

Barras horizontales del **gas estimado sin ocupación** por espacio y tabla con horas calentadas y
**€/año**. **KPIs:** gas sin ocupación, horas y coste anualizado.

**Decisiones:** no calentar lo que está vacío; detecta válvulas y programaciones que se saltan el
horario.

---

## 5. Ocupación y calidad del aire

**Componente:** `OccupancyAirQualityChart` · **Endpoint:** `/correlation/occupancy-air-quality`

- **Dispersión ocupación vs. CO₂** con **recta de regresión** y líneas de referencia en 800 y
  1200 ppm.
- **Evolución conjunta**: ocupación (área, eje izquierdo) y CO₂ (línea, eje derecho).
- **KPIs**: coeficiente de **Pearson** (con interpretación), CO₂ medio y máximo, % de aire bueno y
  ocupación media.

**Decisiones:** estimar si la ventilación es suficiente para la ocupación típica; identificar franjas
y espacios con aire pobre; planificar horarios y uso de espacios.

### Umbrales de referencia (CO₂)

| Nivel | Rango | Color |
| ----- | ----- | ----- |
| Bueno | < 800 ppm | Verde |
| Moderado | 800–1200 ppm | Naranja |
| Pobre | > 1200 ppm | Rojo |

Coinciden con los del proyecto original para mantener la coherencia.

---

## 6. Decisiones

**Componente:** `DecisionsPanel` · **Endpoint:** `/decisions/opportunities`

Tarjetas de **oportunidades de ahorro** ordenadas por **€/año**, con categoría, prioridad,
descripción, **evidencia** y energía asociada. **KPIs:** ahorro potencial anual, número de
oportunidades y medida prioritaria.

**Decisiones:** es el resumen accionable del panel: *qué hacer primero y cuánto se ahorra*.
