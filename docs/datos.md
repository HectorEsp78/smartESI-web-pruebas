# Datos

## Dos orígenes

| Modo | Qué hace |
| ---- | -------- |
| `DATA_SOURCE=database` | Electricidad e Infraestructura leen el *recorder* real. Iluminación usa ocupación real si hay contadores y consumo sintético. |
| `DATA_SOURCE=mock` | Todo se genera de forma determinista, sin base de datos. |

El modo activo se muestra en `/health/live` y en los metadatos de Electricidad.

## Catálogo de edificios y espacios

Está en [`backend/app/core/buildings.py`](../backend/app/core/buildings.py). Cada edificio declara:

- `id`, `label` y aforo.
- `base_kw`: carga eléctrica nominal usada por el modelo sintético.

Cada espacio declara:

- `id`, `label`, edificio y tipo.
- `weight`: peso dentro del edificio.
- `area_m2`.
- `lighting_kw`: potencia instalada de luminarias.

Los espacios se usan para el ranking y el reparto de Iluminación. El catálogo solo contiene datos eléctricos y de luminarias.

## Electricidad real

El mapa está en [`backend/app/core/electricity_map.py`](../backend/app/core/electricity_map.py).

- **Centro:** `sensor.cuadro_general`.
- **Módulo A:** `sensor.edificio_a`.
- **Módulo B:** `sensor.edificio_b`.
- **Fermín Caballero:** no tiene contador único; se calcula como `Cuadro General − Módulo A − Módulo B`.
- **Sectores de Fermín:** cuadros D, E, F, G, H, I, J, K y CPD.

Los sectores son submedidas **parciales**. La web calcula:

```text
sectors_total   = suma de los sectores con datos
unmetered_total = Fermín − sectors_total
sector_coverage = sectors_total / Fermín
```

La cobertura cambia con el periodo. En la prueba de 7 días fue del **38,0 %**; es habitual que esté en torno al 30–38 %.

> El cuadro E (`sensor.planta_baja_cuadro_e`) aparece sin datos porque su acumulado no se mueve desde 2023. El cuadro H usa `sensor.planta_primera_cuadro_h`, pero físicamente es **Planta Segunda · Cuadro H**.

La fecha mínima con datos reales es **2023-12-22**.

Las consultas SQL exactas contra `statistics_meta`, `statistics` y `states` están en
[Consultas SQL](sql.md).

## Electricidad sintética

El modelo de `services/mock_data.py` genera kWh por hora a partir de:

- perfil de actividad (día laborable, noche, fin de semana),
- estacionalidad,
- carga base del edificio,
- ruido determinista.

En modo `mock` se generan también los sectores de Fermín con pesos fijos que suman el 30 %. El resto del edificio queda como “No desglosado”.

## Iluminación

El consumo de luminarias es sintético. Para cada hora:

1. Se estima la ocupación del edificio.
2. Se calcula la fracción de electricidad que va a luminarias según ocupación, hora y luz natural.
3. Se reparte esa fracción entre los espacios según `lighting_kw`.
4. Se marca como vacío si la ocupación está por debajo de `EMPTY_OCCUPANCY_RATIO` (5 %).

La ocupación puede ser real:

- Fermín Caballero: `sensor.entrada_fermin_caballero` − `sensor.salida_fermin_caballero`.
- Módulo B: atributos `LTR_SUM` y `RTL_SUM` de `sensor.contador_personas`.

Si faltan contadores, se usa el modelo sintético.

## Infraestructura

El mapa está en [`backend/app/core/environment_map.py`](../backend/app/core/environment_map.py). Solo contiene estancias con sensores identificados. La interfaz usa fechas personalizadas (7 días por defecto y máximo un año) y una ruta por estancia.

| Estancia | Temperatura / humedad | CO₂ | Presencia |
| -------- | --------------------- | --- | --------- |
| A11 | `sensor.sensor_temperatura_a11` / `sensor.sensor_humedad_a11` | `air_quality.co2_3` | `sensor.movimiento_a11` |
| A12 | `sensor.sensor_temperatura_a12` / `sensor.sensor_humedad_a12` | `air_quality.co2_1` | `sensor.movimiento_a12` |
| A21 | `sensor.sensor_temperatura_a21` / `sensor.sensor_humedad_a21` | `air_quality.co2_2` | `sensor.movimiento_a21` |
| A22 | `sensor.sensor_temperatura_a22` / `sensor.sensor_humedad_a22` | `air_quality.co2_4` | `sensor.movimiento_a22` |
| F0.2 | — | — | `sensor.presencia3` |
| ALU | — | — | `sensor.presencia2` |
| Anita Borg | — | — | `sensor.presencia1` |

- **ALU** es el Aula de Libre Uso de Fermín Caballero.
- `sensor.presencia3`, `sensor.presencia2` y `sensor.presencia1` son las mismas señales que `sensor.sensor_presencia_f02`, `sensor.sensor_presencia_alu` y `sensor.sensor_presencia_anitaborg`.
- Temperatura, humedad y presencia genérica se leen de `statistics.mean`.
- El CO₂ y los sensores de movimiento no tienen estadísticos de larga duración: se leen de `states`.
- Los laboratorios (LD1–LD4), `sensor.temperatura_shelly1..18` y `sensor.humedad_shelly1..18` quedan fuera porque el recorder no permite asignarlos a una sala con certeza.
- `sensor.ambiente` no se asigna a una estancia: se usa como **ambiente de referencia** en la página de cada estancia.
- El gas se lee de `sensor.daily_gas` (m³) y `sensor.daily_gas_cost` (€). Es una medida del edificio y puede incluir usos distintos de la calefacción.

Limpieza de datos:

- Se descartan `0`, `unknown`, `unavailable` y valores fuera de rango.
- En temperatura se exige un mínimo de 5 °C para no confundir reinicios con medidas.
- El CO₂ válido está entre 300 y 5.000 ppm.
- Para las tarjetas actuales se usa el último valor válido de las últimas 24 horas.

Umbrales orientativos:

| Magnitud | Bueno | Moderado | Alto / malo |
| -------- | ----- | -------- | ----------- |
| Temperatura | 18–24 °C | 16–18 / 24–26 °C | <16 / >26 °C |
| Humedad | 30–60 % | 25–30 / 60–70 % | <25 / >70 % |
| CO₂ | ≤600 ppm | 600–800 ppm | 800–1.000 ppm alto; >1.000 ppm muy alto |

La ocupación de A11–A22 se calcula con las transiciones de movimiento: se reparte el tiempo “encendido” entre las horas del intervalo. Para F0.2, ALU y Anita Borg se usa la media horaria del sensor de presencia.

## Medio Ambiente

El mapa está en [`backend/app/core/weather_map.py`](../backend/app/core/weather_map.py).

| Elemento | Entidad | Contenido |
| -------- | ------- | --------- |
| Estación | `weather.meteo` | `state` = temperatura exterior; atributos `Humidity`, `Pressure` (nivel del mar), `PM1`, `PM2.5`, `PM10` y `Battery`. |
| Interior | `sensor.ambiente` | Temperatura, humedad, presión, CO₂ y TVOC. |
| AEMET | `sensor.aemet_temperature`, `_humidity`, `_pressure`, `_precipitation`, `_visibility`, `_snow` | Referencia externa de Ciudad Real. |
| Energía | `sensor.daily_gas`, `sensor.daily_gas_cost`, `sensor.cuadro_general` | Cruce con temperatura y grados-día. |

- La estación no publica viento, lluvia ni radiación solar.
- `weather.meteo_2` es una entidad duplicada no disponible y `sensor.temperatura_meteo` duplica la temperatura; no se usan.
- La presión de la estación se publica a nivel del mar; para compararla con AEMET se reduce a 626,17 m.
- Los valores de PM no declaran unidad: se muestran como índice relativo.
- Se descartan reinicios con `state=0` y sin atributos útiles.
- La ventana es de 7, 30 o 90 días; 7 días usa serie horaria y 30/90 usan serie diaria.

## Mantenimiento

El mapa está en [`backend/app/core/maintenance_map.py`](../backend/app/core/maintenance_map.py). Solo incluye dispositivos con entidades confirmadas en el recorder: 18 Shelly H&T, los sensores CO₂ A11–A22, tres sensores de presencia, seis Fleximodo, el contador de gas, la estación meteorológica, cinco válvulas TRV y los contadores/controladores cableados principales.

- Los **latidos** se leen de `states` (marcas de tiempo), no de `statistics`.
- La **batería** se lee de `states` o de un atributo del último estado; en A11–A22 llega en mV.
- Se consulta también el último valor anterior a la ventana para no perder el estado inicial.
- Los dispositivos `periodic` tienen una frecuencia esperada; los `event` solo escriben al cambiar y no se marcan por silencio.
- La edad de la lectura de batería es independiente del silencio del dispositivo.
- Los cortes se agrupan por proximidad temporal: global (recorder/red), de grupo o individual.
- El modo `mock` genera baterías, latidos, cortes y cambios de pila deterministas para probar la interfaz.

## Agregación y conversión

- Electricidad carga `statistics.sum` acumulado y lo convierte a kWh por hora.
- La diferencia se atribuye a la hora en la que cierra el intervalo.
- Un salto negativo se interpreta como reinicio y vale 0.
- Un salto mayor que `ENERGY_MAX_KWH_PER_HOUR` se descarta.
- Los huecos se reparten entre las horas transcurridas.
- Todo se agrupa en la zona horaria `Europe/Madrid`.

## Coste

```text
coste = kWh × 0,20 €/kWh
```

Iluminación usa el mismo precio para el coste de luminarias. El CO₂ de Iluminación se calcula con `CO2_KG_PER_KWH` y es un indicador derivado.

## Límites conocidos

- La iluminación no tiene mapeo real de consumo por luminaria; el reparto es sintético.
- Infraestructura no incluye laboratorios ni sensores Shelly sin sala confirmada.
- `sensor.ambiente` no es una temperatura exterior: es un sensor interior sin sala confirmada y se usa como referencia en Infraestructura y Medio Ambiente.
- En Medio Ambiente, AEMET es una referencia externa de Ciudad Real y los valores de PM no tienen unidad declarada.
- El gas es del edificio y puede incluir usos distintos de la calefacción; no se reparte por estancia.
- El CO₂ no tiene estadísticos de larga duración: los rangos largos leen `states` y pueden tardar más la primera vez; la respuesta se cachea.
- Los festivos no se excluyen de la base de centro cerrado.
- La base de centro cerrado usa L-V de 7:00 a 21:00 como horario laborable.
