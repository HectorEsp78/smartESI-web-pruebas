# Gráficas

Todas las gráficas son **interactivas**: tooltips al pasar el ratón y controles para cambiar el
periodo (en la cabecera, global), el edificio y/o la métrica. Los colores siguen la identidad
institucional (azul UCLM `#0497d7`, granate ESI `#b30139`, y verdes/naranjas para estados).

El panel está organizado en **seis pestañas**. Aquí se resume **qué muestra cada gráfica y para qué
decisión es útil**; el detalle de cómo está construida cada pieza está en
[`componentes.md`](componentes.md) y el de los estadísticos en [`estadisticos.md`](estadisticos.md).

| Pestaña | Gráficas |
| ------- | -------- |
| Resumen | KPIs (`OverviewSection`). |
| Electricidad | Consumo, desglose, comparativa, eficiencia, por edificio. |
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

### 2.1 Evolución del consumo

**Componente:** `EnergyConsumptionChart` · **Endpoint:** `/energy/consumption`

Gráfica de área con la evolución del consumo. **Controles:** edificio y métrica
(`Consumo` kWh, `Coste` €, `Emisiones` kg CO₂). **KPIs:** total, media por periodo y pico (con su
fecha).

**Decisiones:** detectar picos y su franja; comparar el gasto entre periodos; traducir kWh a euros o
emisiones para justificar inversiones.

### 2.2 Carga base vs. actividad y luz vs. resto

**Componente:** `EnergyBreakdownChart` · **Endpoint:** `/energy/breakdown`

Dos gráficas de barras apiladas: **carga base** (fuera de horario) frente a **actividad**, y
**luminarias** frente al **resto de cargas**. **KPIs:** cuota de carga base y cuota de iluminación.

**Decisiones:** cuantificar el gasto en noches/fines de semana (equipos en espera, climatización
desatendida) y cuánto peso tiene la iluminación.

### 2.3 Comparativa con el periodo anterior

**Componente:** `EnergyCompareChart` · **Endpoint:** `/energy/compare`

Líneas del **periodo actual** frente al **periodo anterior equivalente**. **KPIs:** actual, anterior
y variación (`delta_pct`).

**Decisiones:** saber si el consumo sube o baja de un periodo a otro y cuánto.

### 2.4 Eficiencia por superficie y ocupación

**Componente:** `EnergyEfficiencyChart` · **Endpoint:** `/energy/efficiency`

Barras horizontales de **kWh/m²** por espacio (top) y tabla con kWh/persona·hora, coste y cuota.
**KPIs:** consumo total, media por m² y espacio menos eficiente.

**Decisiones:** detectar espacios anómalamente altos por metro cuadrado (equipos antiguos o mal uso).

### 2.5 Consumo por edificio y espacio

**Componente:** `EnergyByBuildingChart` · **Endpoint:** `/energy/by-building`

Barras por edificio, barras horizontales (top de espacios) y tabla de detalle con el **% sobre el
total**. Comparte los selectores de edificio y métrica. El total procede de `sensor.cuadro_general`;
los contadores A/B son parciales, así que la gráfica añade **“No desglosado”** y muestra el
porcentaje de cobertura (`coverage`) para que el reparto sume el total real.

**Decisiones:** repartir el esfuerzo de eficiencia donde más impacto tiene y detectar espacios fuera
de lo normal.

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
