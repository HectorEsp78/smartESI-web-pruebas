# Estadísticos

Este documento resume qué se calcula en cada pestaña y para qué sirve.

## 1. Electricidad

### 1.1 Serie temporal

- **Unidad:** kWh o €.
- **Intervalo:** día, semana, mes o año, calculado automáticamente.
- **Regla:** los intervalos son naturales y se recortan al rango elegido; el primer y el último pueden ser parciales.
- **Cálculo:** suma de los kWh horarios de cada intervalo. En coste se multiplica por 0,20 €/kWh.

### 1.2 Indicadores del ámbito

| Estadístico | Cálculo | Para qué sirve |
| ----------- | ------- | -------------- |
| Total | Suma de todos los intervalos. | Magnitud del gasto. |
| Media | Total / número de intervalos. | Nivel típico, sin depender de la longitud del rango. |
| Mínimo | Intervalo con menor valor. | Detectar valles o periodos sin actividad. |
| Máximo | Intervalo con mayor valor. | Detectar picos. |
| Base horaria | Media de kWh/h en horas de centro cerrado. | Nivel de consumo que se mantiene sin actividad. |
| Base total | Base horaria × horas del rango. | Comparar el consumo real con el nivel de cierre. |

**Centro cerrado:** sábados, domingos y días laborables fuera de 7:00–21:00.

### 1.3 Edificios

- Se muestran **Módulo A**, **Módulo B** y **Fermín Caballero**.
- `share` = total del edificio / total del centro.
- Fermín se deriva del cuadro general menos los otros dos módulos.
- Cada edificio tiene su propia base de centro cerrado.

### 1.4 Sectores de Fermín

- Sectores: cuadros D, E, F, G, H, I, J, K y CPD.
- `share_of_building` = total del sector / total de Fermín.
- `has_data` indica si el sector tiene datos utilizables.
- `coverage` = suma de sectores con datos / total de Fermín.
- `unmetered_total` = Fermín − suma de sectores. Se muestra como **“No desglosado”**.

La cobertura no es 100 % y debe interpretarse junto al aviso de la interfaz.

### 1.5 Comparativa

- Dos o más periodos independientes (hasta 12), cada uno con sus fechas.
- Se comparan intervalo a intervalo, alineando las series desde el inicio de cada periodo.
- `delta_pct` de cada periodo = (total del periodo − total del periodo 1) / total del periodo 1 × 100.
- La base es común: se calcula con las horas cerradas de todos los periodos.
- Si los periodos tienen distinta duración, los intervalos que faltan se devuelven como `null`; la comparación de totales es informativa.

### 1.6 Agrupación automática

| Días del rango | Agrupación |
| -------------- | ---------- |
| Hasta 31 | Día |
| 32–120 | Semana |
| 121–1095 | Mes |
| Más de 1095 | Año |

## 2. Iluminación

### 2.1 Consumo

- **Luminarias:** kWh estimados de iluminación.
- **Otras cargas:** total del edificio − luminarias.
- **Cuota de luminarias:** luminarias / total.
- **Horas de luz natural:** referencia para saber si el encendido sigue al día.
- **Coste:** luminarias × 0,20 €/kWh.
- **CO₂:** luminarias × 0,15 kg/kWh.

### 2.2 Ranking por espacio

- Reparte la iluminación del edificio según la potencia instalada (`lighting_kw`).
- `share_of_lighting` = luminarias del espacio / luminarias del ámbito.
- `share_of_building` = luminarias del espacio / consumo total del edificio.
- `cost_eur` = luminarias del espacio × precio.

### 2.3 Luz encendida sin ocupación

Un edificio se considera vacío cuando la ocupación estimada es ≤ 5 % del aforo.

| Estadístico | Cálculo |
| ----------- | ------- |
| `waste_lighting` | Suma de luminarias en horas vacías. |
| `waste_share` | `waste_lighting / total_lighting`. |
| `waste_cost_eur` | `waste_lighting × 0,20`. |
| `annualized_cost_eur` | Coste del periodo extrapolado a 365 días. |
| `avg_daily_empty_cost` | Coste del periodo / días del periodo. |
| `empty_hours` | Horas con el espacio vacío y luz encendida. |

La extrapolación anual es una estimación, no una factura.

## 3. Infraestructura

### 3.1 Serie temporal

- Intervalo: hora hasta 7 días, día hasta 120 días y semana para periodos mayores.
- Temperatura: media de las medias horarias disponibles.
- Humedad: media de las medias horarias disponibles.
- CO₂: media horaria calculada desde `states` y media del intervalo.
- Presencia: porcentaje del intervalo con ocupación.
- Ambiente de referencia y gas: media o suma del intervalo, según la magnitud.

### 3.2 Indicadores por estancia

| Estadístico | Cálculo | Para qué sirve |
| ----------- | ------- | -------------- |
| Media / mínimo / máximo | De las horas con dato. | Nivel y variabilidad térmica. |
| CO₂ medio y pico | Media y máximo del periodo. | Detectar ventilación insuficiente. |
| `co2_above_800_pct` | Horas con CO₂ >800 / horas con dato. | Exposición al CO₂ moderado-alto. |
| `co2_above_1000_pct` | Horas con CO₂ >1.000 / horas con dato. | Exposición alta. |
| Ocupación media | Horas ocupadas / horas con presencia. | Uso real de la sala. |
| `occupied_hours` / `empty_hours` | Suma de fracciones horarias. | Tiempo útil y tiempo vacío. |
| `comfort_good_pct` | Horas dentro de 18–24 °C y 30–60 % HR. | Confort térmico real. |
| `occupied_co2_ppm` | CO₂ medio en horas con presencia ≥50 %. | CO₂ atribuible a ocupación. |
| `empty_co2_ppm` | CO₂ medio en horas con presencia ≤5 %. | Nivel de fondo y ventilación. |
| `lift_pct` | (ocupado − vacío) / vacío × 100. | Sensibilidad del CO₂ a la ocupación. |
| `correlation` | Pearson entre ocupación y CO₂. | Fuerza de la relación. |

El resumen de la pestaña usa medias del periodo y separa los denominadores: `rooms_with_climate` para el confort evaluable y `rooms_with_co2` para las alertas de CO₂.

### 3.3 Estado de confort

- Temperatura: bueno 18–24 °C; moderado 16–18 / 24–26; malo fuera.
- Humedad: bueno 30–60 %; moderado 25–30 / 60–70; malo fuera.
- CO₂: bueno ≤600 ppm; moderado ≤800; alto ≤1.000; muy alto >1.000.
- El estado global es el peor de los tres; si no hay datos, `unknown`.

### 3.4 Cruce CO₂–ocupación

Cada punto de la dispersión es un intervalo de una estancia. La relación esperada es positiva: más ocupación, más CO₂. Si el CO₂ sube mucho con poca ocupación, conviene revisar la ventilación o el sensor.

### 3.5 Mapa horario

Se agrupan las horas del periodo por día de la semana y hora local. Cada celda devuelve la ocupación media y el CO₂ medio. Sirve para detectar franjas de uso y picos de CO₂.

### 3.6 Recuperación térmica

Para cada transición de ocupado (≥50 %) a vacío (≤5 %):

- se calcula la temperatura de reposo como la mediana de las horas vacías del día;
- se busca la primera hora, hasta 6, en la que la temperatura vuelve a ±0,5 °C de esa referencia;
- se guarda el tiempo de recuperación y el cambio en la primera hora.

El resultado es la mediana de las transiciones, el número de transiciones y cuántas no recuperan en 6 horas.

### 3.7 Comparación con la media

Cada estancia se compara con la media del resto de estancias que tienen dato para el mismo periodo. Se muestran temperatura, humedad, CO₂ y ocupación, junto con el número de estancias usadas.

### 3.8 Gas y ambiente de referencia

- `sensor.ambiente` aporta una temperatura de referencia, pero no tiene sala confirmada; no es una temperatura exterior.
- `sensor.daily_gas` y `sensor.daily_gas_cost` aportan consumo y coste de gas del edificio.
- El coste medio diario se calcula dividiendo el gasto del periodo entre sus días.
- La diferencia estancia−ambiente es la media de las horas con ambos datos.

## 4. Mantenimiento

### 4.1 Universo y modos

Se vigilan 52 dispositivos con entidades confirmadas en el recorder. Cada uno se clasifica como:

- **Periódico**: envía un latido con intervalo conocido (Shelly, CO₂, contadores, gas).
- **Por eventos**: solo escribe cuando cambia su estado (presencia, parking, válvulas). Un hueco largo puede ser normal.

### 4.2 Salud de transmisión

| Estadístico | Cálculo | Para qué sirve |
| ----------- | ------- | -------------- |
| `updates_per_day` | Número de latidos / días del periodo. | Frecuencia real. |
| `expected_per_day` | 1.440 / intervalo esperado en minutos. | Referencia de frecuencia. |
| `ratio` | `updates_per_day / expected_per_day`. | Detectar infrarreporte o sobrerreporte. |
| `median_interval_hours` / `p95_interval_hours` | Mediana y percentil 95 de los huecos. | Cadencia típica y cola de retrasos. |
| `threshold_hours` | 3× intervalo esperado, mínimo 2 h (rápidos) o 24 h (lentos). | Umbral de silencio. |
| `silence_hours` | Tiempo desde el último latido. | Detectar un dispositivo caído. |

Estados: `ok`, `late` (por encima del umbral pero con actividad reciente), `silent`, `event` y `unknown`.

### 4.3 Batería

- Se guarda el valor bruto y su unidad (`percent` o `millivolt`).
- En mV se estima el porcentaje con una curva Li-SOCl₂ 3,6 V; el mV sigue siendo el dato autoritativo.
- Umbrales: crítica ≤20 %, baja ≤40 %, media ≤60 %.
- `age_hours` mide la edad de la **lectura**, no el silencio del dispositivo. Una lectura antigua se marca como `stale` sin convertirla automáticamente en desconocida.
- `trend_30d_pct` es la pendiente de los últimos 30 días en puntos porcentuales.
- La previsión a 30/60/90 días extrapola esa tendencia; `days_to_critical` indica cuándo llegaría al umbral crítico.
- Un salto de al menos 20 puntos (o de ≤5 % a ≥80 %) se interpreta como cambio de batería y se marca `replacement_detected`.

### 4.4 Estado de los datos y cortes

| Estado | Significado |
| ------ | ----------- |
| `ok` | El dispositivo transmite con normalidad. |
| `device_silent` | Silencio propio del dispositivo, sin corte común. |
| `global_outage` | La mayoría de dispositivos callan a la vez; se atribuye al recorder o a la red. |
| `group_outage` | Callan varios dispositivos del mismo grupo. |
| `unknown` | Sin datos suficientes para decidir. |

Los huecos se agrupan con una tolerancia de 3 horas. Un corte global exige al menos 3 dispositivos y el 50 % del total; uno de grupo, al menos 2 dispositivos y el 50 % del grupo. Los cortes globales y de grupo **no** cuentan como averías individuales.

### 4.5 Matriz de decisión

| Batería \ Datos | Datos OK | Sin datos |
| --------------- | -------- | --------- |
| OK | Correcto | Revisar dispositivo |
| Baja | Cambiar batería | Batería y dispositivo |
| Sin lectura | Batería sin lectura | Revisión urgente |

La lógica responde a las preguntas de mantenimiento: si no envía datos y la batería está OK, el problema es del dispositivo; si la batería está baja y sigue enviando, basta con cambiarla.

### 4.6 Prioridad

Puntuación de 0 a 100:

- batería crítica +45, baja +30, media +10, sin lectura +5;
- dispositivo silencioso +35, corte de grupo +10, estado desconocido +15;
- hasta +15 por cortes individuales;
- hasta +15 por previsión de batería crítica a 30/60/90 días;
- +10 si el latido está silencioso, +5 si va retrasado;
- +5 si es periódico, tiene batería OK y no envía datos.

Etiquetas: urgente ≥70, alta ≥45, media ≥25, baja por debajo.

### 4.7 Disponibilidad, MTBF y MTTR

- `availability_pct` = tiempo con datos / tiempo esperado, sin contar cortes globales.
- `outages_individual`, `outages_global` y `outages_group` separan las causas.
- `downtime_hours` suma los cortes individuales.
- `mtbf_hours` ≈ tiempo observado / número de cortes individuales.
- `mttr_hours` = duración media de los cortes individuales.

Son aproximaciones del periodo: con pocos cortes, MTBF y MTTR son solo orientativos.

### 4.8 Mapa diario

Cada celda compara los datos recibidos con los esperados para ese día. Un corte global baja todas las filas a la vez; una fila roja aislada apunta a un dispositivo concreto. Solo se incluyen dispositivos periódicos.

### 4.9 Limitaciones

- No se inventan costes de sustitución ni ubicaciones físicas de los Shelly.
- La curva mV → % y la previsión de autonomía son estimaciones.
- Un sensor de eventos puede pasar días sin escribir sin estar averiado.
- El periodo de 90 días es el máximo para tendencias y comparaciones estables.

## 5. Medio Ambiente

### 5.1 Fuente y ventana

- `weather.meteo`: temperatura exterior en `state`; humedad, presión, PM1/PM2.5/PM10 y batería en los atributos.
- `sensor.ambiente`: referencia interior (temperatura, humedad, CO₂, TVOC y presión).
- AEMET: referencia externa de Ciudad Real, **no** la estación del centro.
- Ventana: 7, 30 o 90 días. La serie es horaria para 7 días y diaria para 30/90; `daily` siempre se calcula.
- La estación no publica viento, lluvia ni radiación solar.

### 5.2 Cobertura y resumen

| Estadístico | Cálculo |
| ----------- | ------- |
| `samples` | Lecturas válidas de la estación en la ventana. |
| `median_interval_hours` | Mediana de los huecos entre lecturas. |
| `coverage_pct` | `min(100, samples / (horas del periodo / intervalo mediano) × 100)`. |
| `outage_hours` | `max(0, horas del periodo − samples × intervalo mediano)`. |
| `temperature_amplitude_avg_c` | Media de (máx − mín) de los días con al menos 2 muestras. |
| `pressure_range_hpa` | Presión máxima − mínima. |
| `battery_min_pct` / `battery_avg_pct` | Mínimo y media de la batería. |
| `heat_index_max_c` | Máximo de la sensación térmica calculada. |

### 5.3 Derivados

- **Punto de rocío:** fórmula de Magnus con `a = 17,62` y `b = 243,12`.
- **Humedad absoluta:** `(HR/100) × 6,112 × exp(17,67·T/(T+243,5)) × 216,7/(T+273,15)`.
- **Sensación térmica:** la temperatura si `T < 27 °C` o `HR < 40 %`; en caso contrario, el índice de calor de Rothfusz.
- **Tendencia de presión:** diferencia entre la última presión y la lectura más cercana a 3 o 24 horas antes.

### 5.4 Eventos y grados-día

| Estadístico | Regla |
| ----------- | ----- |
| `hot_hours` | Suma del intervalo mediano de las lecturas con temperatura ≥30 °C. |
| `cold_hours` | Suma del intervalo mediano de las lecturas con temperatura ≤10 °C. |
| `dry_hours` | Suma del intervalo mediano con humedad <30 %. |
| `humid_hours` | Suma del intervalo mediano con humedad ≥80 %. |
| `tropical_nights` | Días con temperatura mínima ≥20 °C y al menos 2 muestras. |
| `heating_degree_days` | Suma de `max(0, 18 − media diaria)`. |
| `cooling_degree_days` | Suma de `max(0, media diaria − 22)`. |

La media diaria usa las lecturas disponibles del día; el primer y el último día pueden ser parciales.

### 5.5 Cruce exterior-interior

- Se comparan las medias horarias comunes de `weather.meteo` y `sensor.ambiente`.
- `outdoor_minus_indoor_c` = media de (exterior − interior).
- `outdoor_minus_indoor_humidity_pct` = media de (HR exterior − HR interior).
- `pressure_bias_hpa` = media de (presión interior − presión exterior reducida a la altitud de la estación).
- Las correlaciones son de Pearson y exigen al menos 3 horas comunes.
- El sensor interior es una referencia, no una segunda estación exterior.

### 5.6 Cruce con AEMET

- Se comparan las medias horarias comunes.
- Sesgo = estación − AEMET; MAE = media del valor absoluto del sesgo.
- La presión de la estación se reduce a la altitud del observatorio de AEMET (626,17 m) antes de comparar.
- Sesgo diurno: horas locales 9–18; nocturno: el resto.
- `hourly_bias` repite el sesgo medio para cada una de las 24 horas.
- `stale` se activa si la última lectura de AEMET tiene más de 24 horas.
- Un sesgo diurno mucho mayor que el nocturno sugiere exposición solar directa.

### 5.7 Cruce con energía

- Gas: `sensor.daily_gas`; coste: `sensor.daily_gas_cost`; electricidad: `sensor.cuadro_general`.
- Se usan días con temperatura media y al menos un contador.
- Se excluyen días con gas > `max(200 m³, 4 × mediana)` o electricidad > `max(3.000 kWh, 4 × mediana)` para evitar saltos de restauración.
- `gas_per_degree_day` solo se calcula si hay al menos 5 HDD; `electricity_per_degree_day`, si hay al menos 5 CDD.
- Las correlaciones relacionan temperatura, HDD y CDD con el consumo diario.
- Son orientativas: el gas puede incluir otros usos y la electricidad tiene carga base.

### 5.8 Partículas

- PM1, PM2.5 y PM10 se muestran como **índice relativo** porque la estación no declara unidad.
- Ratios: PM2.5/PM10 y PM1/PM2.5.
- Correlaciones con humedad, temperatura, CO₂ interior y TVOC interior.
- No se convierten a µg/m³ ni se comparan con umbrales sanitarios.

### 5.9 Limitaciones

- Sin viento, lluvia ni radiación solar.
- La temperatura exterior puede estar afectada por el sol directo.
- AEMET es de Ciudad Real y puede estar desactualizada.
- La cobertura puede bajar por cortes del recorder o de la estación.
- Los valores de PM no tienen unidad declarada.
- Los cruces energéticos son orientativos y excluyen días anómalos.

## 6. Unidades y redondeo

- kWh con 2 decimales.
- € con 2 decimales.
- Temperatura con 1 decimal y °C.
- Humedad con 1 decimal y %.
- CO₂ con 0 decimales y ppm.
- Porcentajes y cuotas con 1–4 decimales según el campo.
- Las fechas se muestran en `Europe/Madrid`.
- Los totales pueden no coincidir exactamente al sumar tarjetas redondeadas; el cálculo interno usa más precisión.
