# Gráficas

La web tiene cinco pestañas y varias gráficas por pestaña.

## 1. Cabecera y periodo

- **Electricidad** usa fechas propias.
- **Iluminación** usa el selector global de periodo: día, semana, mes o año.
- **Infraestructura** usa fechas propias: día actual por defecto y máximo un año.
- **Medio Ambiente** usa fechas propias (`?start=&end=`): últimos 30 días por defecto y un máximo de un año.
- **Mantenimiento** muestra el histórico de batería con fechas libres. Por defecto, 90 días, o los 90 días previos a su última lectura si dejó de informar antes.
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

La pestaña se divide en un índice de tarjetas y una página por aula. El periodo se elige con los botones Día / Semana / Mes y se guarda en `start` y `end`, ambas inclusive; por defecto se carga el día actual y el máximo es de 366 días.

### 4.1 Índice de aulas

**Componentes:** `EnvironmentIndex` · `EnvironmentRoomCard` · `EnvironmentRangeSelector` · **Endpoint:** `/environment/overview`

- Tarjetas de A11, A12, A21 y A22 con la estética del proyecto Smart ESI.
- Cada tarjeta muestra imagen, código, nombre, temperatura, humedad y presencia actual.
- Selector Día / Semana / Mes, con el día actual por defecto.
- Enlace a `/infraestructura/{room_id}` conservando el periodo.

**Uso:**

- Ver de un vistazo el estado de las cuatro aulas.
- Entrar en el aula que se quiere analizar.
- Cambiar el periodo sin perder el contexto.

### 4.2 Página de aula

**Componente:** `EnvironmentRoomPage` · **Endpoint:** `/environment/rooms/{room_id}`

- Cabecera con imagen, código, nombre y valores actuales.
- Tres gráficas: temperatura, humedad y presencia.
- El periodo se mantiene al volver al índice.

### 4.3 Temperatura y humedad

**Componentes:** `EnvironmentRoomTemperatureChart` · `EnvironmentRoomHumidityChart`

- Temperatura con banda de confort 18–24 °C.
- Humedad con banda de confort 30–60 %.
- La serie procede de `statistics.mean`; los huecos no se rellenan.
- Tooltip con fecha y valor.

### 4.4 Presencia

**Componente:** `EnvironmentRoomPresenceChart`

- Escalón 0/1 por intervalo con eje «Sí/No».
- Se calcula a partir de las transiciones de `sensor.movimiento_aXX` en `states`.
- Un intervalo con algo de movimiento se marca como «Sí».

## 5. Medio Ambiente

La pestaña compara `weather.meteo` con el observatorio de AEMET en Ciudad Real. La estación no publica viento ni lluvia.

- **Temperatura, humedad y presión:** dos líneas, estación continua y AEMET discontinua. Si falta un dato, la línea se corta en lugar de unir el hueco. La presión de ambas está a la altitud del observatorio.
- **Diferencia de temperatura por hora del día:** barras de estación − AEMET en hora local. Un pico en las horas de sol apunta al efecto del sol sobre el sensor.
- **Lluvia en Ciudad Real:** barras con los datos de AEMET.
- **Partículas:** PM1, PM2.5 y PM10 como índice relativo, sin umbrales sanitarios.
- **Batería de la estación:** evolución en el periodo.

## 6. Mantenimiento

### Histórico de batería

Se abre al pulsar la tarjeta de un sensor. Es una línea con la media por hora (hasta 31 días) o por día, con líneas de referencia en los niveles «Baja» y «Crítica»: 40 % y 20 % para Shellys y válvulas, y 3400 y 3200 mV para las aulas.

Las aulas se dibujan en mV y el tooltip añade el % estimado. Los cortes de la línea indican más de 7 días sin lecturas válidas.

### Panel anterior (no montado en la interfaz)


No es una pestaña de series largas: prioriza estado y decisión.

- **Matriz 3×2:** batería (OK / baja / sin lectura) × transmisión (datos OK / sin datos). Cada celda resume qué hacer.
- **Tabla de dispositivos:** prioridad, batería, transmisión y disponibilidad. Al expandir una fila se carga el detalle.
- **Historial de batería:** línea del porcentaje estimado con referencias en 20 % (crítica) y 40 % (baja). En sensores en mV se muestra también el valor bruto.
- **Transmisión diaria:** barras de datos recibidos frente a la línea de esperados. Un hueco de varios días se ve como caída.
- **Mapa avanzado:** una fila por dispositivo periódico y una columna por día; el color resume la disponibilidad. Un corte global baja todas las filas a la vez; una fila roja aislada apunta a un dispositivo concreto.
- **Cortes:** se listan aparte los globales y de grupo para no confundirlos con averías individuales.

## 7. Cómo leer las gráficas

- **kWh** mide energía; **€** aplica la tarifa real deducida de `sensor.cuadro_general_cost` (con `ENERGY_PRICE_EUR_PER_KWH` como respaldo).
- Una barra más alta no siempre es un problema: puede ser un periodo más largo o un intervalo parcial. Los indicadores y las fechas ayudan a interpretarlo.
- La base de centro cerrado es una referencia, no un objetivo.
- En Fermín, la suma de sectores no es el total del edificio: mirar siempre la cobertura.
- En Iluminación, el consumo es sintético; sirve para validar el método y la interfaz.
- En Infraestructura, los huecos de temperatura o humedad indican que el sensor no publicó datos en ese intervalo; no se rellenan.
- La presencia se marca como «Sí» si hubo movimiento durante el intervalo; no mide cuántas personas hay.
- En Medio Ambiente, AEMET es una referencia de Ciudad Real, no la estación del centro. Un sesgo diurno alto puede ser sol directo sobre el sensor.
- Los valores de PM de la estación son un índice relativo sin unidad: no los compares con umbrales sanitarios.
- En Mantenimiento, un dispositivo de eventos sin datos no está necesariamente averiado; mira su modo y la matriz antes de decidir.
