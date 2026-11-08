# Gráficas

La web tiene cinco pestañas y varias gráficas por pestaña.

## 1. Cabecera y periodo

- **Electricidad** usa fechas propias.
- **Iluminación** usa el selector global de periodo: día, semana, mes o año.
- **Infraestructura** usa fechas propias: últimos 7 días por defecto, máximo un año.
- **Medio Ambiente** usa una ventana de 7, 30 o 90 días (`?days=`).
- **Mantenimiento** usa una ventana de 7, 30 o 90 días (`?days=`).
- La agrupación de Electricidad e Infraestructura es automática; no hay selector “Agrupar por”.

## 2. Electricidad

### 2.1 Indicadores

No es una gráfica, pero fija la lectura:

- **Total:** gasto del periodo.
- **Media:** nivel típico por intervalo.
- **Mínimo / máximo:** valles y picos.
- **Base:** consumo esperado con el centro cerrado.
- **Cobertura:** porcentaje de Fermín medido por los cuadros.

### 2.2 Reparto por edificios

**Componente:** `ElectricityBuildingsChart` · **Endpoint:** `/energy/electricity`

Barras apiladas por intervalo con:

- Módulo A.
- Módulo B.
- Fermín Caballero.

La línea de base muestra cuánto se mantiene el consumo incluso sin actividad. Si las barras se pegan a la base en noches y fines de semana, hay carga permanente.

**Uso:**

- Ver qué edificio concentra el gasto.
- Detectar periodos con consumo anómalo.
- Comparar la forma de la curva con el horario del centro.

### 2.3 Sectores de Fermín

**Componente:** `ElectricitySectorsChart` · **Endpoint:** `/energy/electricity`

- Barras de cuadros D, E, F, G, H, I, J, K y CPD.
- Porcentaje sobre el total de Fermín.
- Segmento gris “No desglosado”.
- Aviso de cobertura parcial.

**Uso:**

- Localizar los cuadros que más pesan.
- Ver si el CPD tiene un consumo estable y alto.
- Detectar cuadros sin datos o con comportamiento raro.

> El cuadro E aparece sin datos porque su contador no se mueve desde 2023.

### 2.4 Comparativa de periodos

**Componente:** `ElectricityComparisonChart` · **Endpoint:** `/energy/electricity/compare-many`

Una línea de color por periodo (se pueden comparar muchos a la vez):

- Periodo 1, que actúa como referencia para la variación.
- Periodos 2..N, con sus propias fechas.

La base común se calcula con las horas cerradas de todos los periodos. Las series se alinean desde la fecha inicial de cada periodo; si tienen distinta duración, los intervalos que faltan quedan vacíos. La tabla superior muestra el total y la variación de cada periodo frente al primero.

**Uso:**

- Comparar el mismo mes en varios años.
- Comparar varios años completos.
- Ver si una actuación redujo el consumo.
- Separar el efecto del horario del efecto de la carga base.

## 3. Iluminación

### 3.1 Consumo de luminarias

**Componente:** `LightingConsumptionChart` · **Endpoint:** `/lighting/consumption`

- Barras apiladas: luminarias y otras cargas.
- Línea: horas de luz natural.
- KPIs: total, luminarias, cuota, coste y CO₂.

**Uso:**

- Comprobar si el encendido sigue al día.
- Ver cuánto pesa la iluminación en el total.
- Detectar noches con demasiada luz.

### 3.2 Ranking por espacio

**Componente:** `LightingBySpaceChart` · **Endpoint:** `/lighting/by-space`

Barras horizontales con los espacios que más luminarias consumen. La tabla añade superficie, tipo, cuota y coste.

**Uso:**

- Priorizar sustitución o zonificación.
- Comparar espacios similares.
- Justificar inversiones con el coste estimado.

### 3.3 Luz encendida sin ocupación

**Componente:** `LightingWasteChart` · **Endpoint:** `/lighting/waste`

- kWh de luminarias en horas vacías.
- Porcentaje sobre el total de luminarias.
- Horas vacías.
- Coste del periodo y €/año estimado.

**Uso:**

- Ajustar horarios o sensores de presencia.
- Detectar espacios con luces encendidas de noche o en fin de semana.
- Estimar el retorno de una actuación.

## 4. Infraestructura

La pestaña se divide en un índice y una página por estancia. Las fechas se eligen con `start` y `end`, ambas inclusive; por defecto se cargan los últimos 7 días y el máximo es de 366 días.

### 4.1 Índice compacto

**Componentes:** `EnvironmentIndex` · `EnvironmentSummary` · `EnvironmentRoomList` · **Endpoint:** `/environment/overview`

- Filtro de fechas propio de Infraestructura.
- Resumen compacto con temperatura media, CO₂ medio, ocupación media y estancias ocupadas ahora.
- Lista de cuatro columnas: espacio, ambiente actual, uso y estado.
- Enlace a `/infraestructura/{room_id}`.

**Uso:**

- Ver de un vistazo qué salas están peor.
- Detectar sensores caídos, valores congelados o datos sin actualizar.
- Entrar en la estancia que necesita una revisión.

### 4.2 Página de estancia

**Componente:** `EnvironmentRoomPage` · **Endpoint:** `/environment/rooms/{room_id}`

- Valores actuales de temperatura, humedad, CO₂ y presencia en una fila compacta.
- Cuatro KPIs del periodo: temperatura media, humedad media, CO₂ medio y ocupación media.
- Series visibles de temperatura (con ambiente de referencia) y CO₂ frente a presencia.
- Aviso de dato ambiental sin actualizar si supera 6 horas.
- “Análisis avanzado” plegado por defecto: humedad, mapas horarios, CO₂ frente a ocupación, recuperación térmica, comparativa y gas.
- Las estancias de solo presencia muestran ocupación, horas y mapa horario dentro del análisis avanzado.

### 4.3 Temperatura, humedad y ambiente de referencia

**Componentes:** `EnvironmentRoomTemperatureChart` · `EnvironmentRoomHumidityChart`

- Temperatura de la estancia y `sensor.ambiente` como referencia, visible en la página.
- Humedad con bandas de confort 30–60 %, dentro de “Análisis avanzado”.
- Bandas de confort 18–24 °C y 30–60 %.
- Tooltip con fecha y valor.

**Uso:**

- Ver si la estancia se calienta o enfría más rápido que la referencia.
- Detectar sobrecalentamiento, sequedad o falta de ventilación.
- Relacionar confort con ocupación.

### 4.4 Mapa horario de ocupación y CO₂

**Componente:** `EnvironmentHeatmap`

- Rejilla 7×24: día de la semana y hora local.
- Una celda para ocupación media y otra para CO₂ medio.
- Colores más intensos indican más ocupación o más CO₂.

**Uso:**

- Detectar las franjas en las que se concentra el uso.
- Comprobar si el CO₂ sube en las horas punta.
- Ajustar ventilación, climatización y horarios.

### 4.5 CO₂ frente a ocupación

**Componente:** `EnvironmentCo2OccupancyCard`

- CO₂ medio con presencia y sin presencia.
- Incremento porcentual y correlación de Pearson.
- Dispersión por intervalo: eje X ocupación, eje Y CO₂.

Si los puntos suben hacia la derecha, la ventilación no acompaña a la ocupación. Si se mantienen bajos con ocupación alta, la sala ventila bien.

### 4.6 Recuperación térmica

**Componente:** `EnvironmentThermalRecoveryCard`

- Temperatura de reposo de la estancia.
- Tiempo mediano hasta volver a esa temperatura tras desocupar.
- Cambio medio en la primera hora sin presencia.
- Transiciones que no recuperan en 6 horas.

**Uso:**

- Detectar salas que retienen calor o frío demasiado tiempo.
- Valorar si la climatización sigue funcionando con la sala vacía.
- Priorizar aislamiento, programación o apagado automático.

### 4.7 Comparación con la media

**Componente:** `EnvironmentBenchmarkCard`

- Temperatura, humedad, CO₂ y ocupación de la estancia.
- Media del resto de estancias con dato para el mismo periodo.
- Diferencia y número de estancias usadas.

### 4.8 Gas y calefacción

**Componente:** `EnvironmentGasContextChart`

- Temperatura de la estancia y ambiente de referencia.
- Coste y consumo de gas del edificio.
- Coste medio diario y diferencia media estancia–ambiente.

El gas es una medida del edificio y puede incluir usos distintos de la calefacción. `sensor.ambiente` no tiene una sala confirmada; se usa solo como referencia.

## 5. Medio Ambiente

La pestaña se centra en `weather.meteo` y en sus cruces. La estación no publica viento ni lluvia.

- **Estado actual:** temperatura exterior, humedad, presión a nivel del mar, PM1/PM2.5/PM10, batería, edad del dato y tendencia de presión.
- **Resumen:** cobertura, intervalo mediano, horas sin datos, extremos, amplitud diaria, horas de calor/frío, noches tropicales y grados-día.
- **Temperatura y humedad:** estación, `sensor.ambiente` como referencia interior y AEMET como referencia externa. La línea de AEMET es discontinua para no confundirla con la estación.
- **Presión:** solo la estación, reducida al nivel del mar. La comparación con AEMET se hace aparte porque AEMET publica presión a la altitud del observatorio.
- **Partículas:** PM1, PM2.5 y PM10 como índice relativo; no hay unidad declarada ni umbrales sanitarios.
- **Cruce interior:** salto térmico y de humedad, y correlaciones con `sensor.ambiente`.
- **Cruce AEMET:** sesgo, MAE, correlación y barras de sesgo por hora. Un sesgo diurno mucho mayor que el nocturno apunta a exposición solar.
- **Cruce energía:** gas y electricidad frente a temperatura, HDD y CDD. Se excluyen días con saltos anómalos de los contadores.
- **Tabla diaria:** cobertura, extremos, PM, temperatura interior y energía por día; queda plegada para no saturar.

## 6. Mantenimiento

No es una pestaña de series largas: prioriza estado y decisión.

- **Matriz 3×2:** batería (OK / baja / sin lectura) × transmisión (datos OK / sin datos). Cada celda resume qué hacer.
- **Tabla de dispositivos:** prioridad, batería, transmisión y disponibilidad. Al expandir una fila se carga el detalle.
- **Historial de batería:** línea del porcentaje estimado con referencias en 20 % (crítica) y 40 % (baja). En sensores en mV se muestra también el valor bruto.
- **Transmisión diaria:** barras de datos recibidos frente a la línea de esperados. Un hueco de varios días se ve como caída.
- **Mapa avanzado:** una fila por dispositivo periódico y una columna por día; el color resume la disponibilidad. Un corte global baja todas las filas a la vez; una fila roja aislada apunta a un dispositivo concreto.
- **Cortes:** se listan aparte los globales y de grupo para no confundirlos con averías individuales.

## 7. Cómo leer las gráficas

- **kWh** mide energía; **€** aplica 0,20 €/kWh.
- Una barra más alta no siempre es un problema: puede ser un periodo más largo o un intervalo parcial. Los indicadores y las fechas ayudan a interpretarlo.
- La base de centro cerrado es una referencia, no un objetivo.
- En Fermín, la suma de sectores no es el total del edificio: mirar siempre la cobertura.
- En Iluminación, el consumo es sintético; sirve para validar el método y la interfaz.
- En Infraestructura, un valor actual puede ser el último dato válido si el sensor se reinició; la fecha aparece en la cabecera y el dato ambiental se marca en ámbar si supera las 6 horas.
- El CO₂ alto con ocupación baja puede indicar ventilación insuficiente o un pico previo; comparar con la curva.
- La temperatura de referencia de Infraestructura procede de un sensor sin sala confirmada. No es una temperatura exterior.
- El gas es del edificio y puede incluir otros usos además de la calefacción; úsalo como contexto, no como consumo de una estancia concreta.
- En Medio Ambiente, AEMET es una referencia de Ciudad Real, no la estación del centro. Un sesgo diurno alto puede ser sol directo sobre el sensor.
- Los valores de PM de la estación son un índice relativo sin unidad: no los compares con umbrales sanitarios.
- En Mantenimiento, un dispositivo de eventos sin datos no está necesariamente averiado; mira su modo y la matriz antes de decidir.
