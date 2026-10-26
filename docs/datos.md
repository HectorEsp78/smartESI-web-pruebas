# Datos

## Dos orígenes

| Modo | Qué hace |
| ---- | -------- |
| `DATA_SOURCE=database` | Electricidad lee el *recorder* real de Home Assistant. Iluminación usa ocupación real si hay contadores y consumo sintético. |
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
- Los festivos no se excluyen de la base de centro cerrado.
- La base de centro cerrado usa L-V de 7:00 a 21:00 como horario laborable.
