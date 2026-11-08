# Consultas SQL

El backend lee el *recorder* de Home Assistant en modo **solo lectura**. Todas las consultas son `SELECT`; la aplicación no ejecuta `INSERT`, `UPDATE` ni `DELETE`.

Las sentencias están centralizadas en [`backend/app/db/repository.py`](../backend/app/db/repository.py). La carga y conversión de las filas se hace en [`backend/app/db/database_data.py`](../backend/app/db/database_data.py) para Electricidad/Iluminación y en [`backend/app/db/environment_data.py`](../backend/app/db/environment_data.py) para Infraestructura.

## Conexión

La conexión se configura en `backend/.env`:

```dotenv
DATA_SOURCE=database
DB_HOST=172.20.48.17
DB_PORT=3306
DB_NAME=smartesi
DB_USER=...
DB_PASSWORD=...
DB_SSL=true
DB_SSL_CA=
```

Con `DATA_SOURCE=mock` no se abre ninguna conexión: los datos son sintéticos.

## Tablas utilizadas

| Tabla | Uso |
| ----- | --- |
| `statistics_meta` | Identificador de cada contador de Home Assistant. |
| `statistics` | Valores acumulados (`sum`) de electricidad y medias (`mean`) de temperatura, humedad y presencia. |
| `states` | Último estado y atributos de contadores de personas, CO₂ y movimiento. |

La instalación actual usa el esquema de Home Assistant con `states.entity_id` y fechas UTC sin zona horaria (`last_updated`). No se usan las columnas `metadata_id` ni `last_updated_ts` de versiones más recientes.

## 1. Consumo eléctrico acumulado

La consulta obtiene las filas de `statistics` de los contadores seleccionados:

```sql
SELECT
    sm.statistic_id,
    s.start,
    s.`sum`
FROM `statistics_meta` AS sm
JOIN `statistics` AS s
    ON s.metadata_id = sm.id
WHERE sm.statistic_id IN (:statistic_ids)
  AND s.start >= :start_utc
  AND s.start < :end_utc
  AND s.`sum` IS NOT NULL
ORDER BY sm.statistic_id, s.start;
```

Parámetros:

| Parámetro | Significado |
| --------- | ----------- |
| `:statistic_ids` | Lista de IDs, por ejemplo `sensor.cuadro_general`, `sensor.edificio_a` o `sensor.planta_baja_red_cuadro_d`. Se obtienen de [`core/electricity_map.py`](../backend/app/core/electricity_map.py). |
| `:start_utc` | Inicio de la ventana en UTC, sin zona horaria. Es inclusivo. |
| `:end_utc` | Fin de la ventana en UTC, sin zona horaria. Es exclusivo. |

La consulta equivalente para revisar un contador concreto desde un cliente MySQL sería:

```sql
SELECT
    sm.statistic_id,
    s.start,
    s.`sum`
FROM `statistics_meta` AS sm
JOIN `statistics` AS s
    ON s.metadata_id = sm.id
WHERE sm.statistic_id = 'sensor.cuadro_general'
  AND s.start >= '2026-01-01 00:00:00'
  AND s.start <  '2026-01-02 00:00:00'
  AND s.`sum` IS NOT NULL
ORDER BY s.start;
```

El backend pide una hora adicional antes del inicio de la ventana. Así el primer intervalo tiene una lectura acumulada anterior con la que calcular la diferencia.

Esta consulta la ejecuta `fetch_statistics_sums` y la usa `load_hourly_statistics`.

## 2. Último estado antes de una ventana

Antes de cargar los contadores de personas se busca el último valor conocido anterior al inicio de la ventana. Ese valor sirve para rellenar las primeras horas si el contador no cambió:

```sql
SELECT
    st.entity_id,
    st.state,
    st.attributes
FROM `states` AS st
JOIN (
    SELECT MAX(state_id) AS max_id
    FROM `states`
    WHERE entity_id IN (:entity_ids)
      AND last_updated < :before_utc
      AND last_updated >= :lookback_start_utc
    GROUP BY entity_id
) AS latest
    ON st.state_id = latest.max_id;
```

Parámetros:

| Parámetro | Significado |
| --------- | ----------- |
| `:entity_ids` | Entidades de los contadores, por ejemplo `sensor.entrada_fermin_caballero` y `sensor.salida_fermin_caballero`. Se obtienen de [`db/entity_map.py`](../backend/app/db/entity_map.py). |
| `:before_utc` | Inicio de la ventana en UTC. Solo se aceptan filas anteriores a esta fecha. |
| `:lookback_start_utc` | Límite inferior de la búsqueda. En el código es `before_utc - 3 días`. |

La consulta la ejecuta `fetch_last_state_snapshots_before`. El resultado se usa en `_load_counter_series` para el relleno inicial de la serie de ocupación.

## 3. Último estado de cada hora

Los contadores de personas cambian con cada entrada o salida, así que no se promedian. Se toma la última fila de cada hora UTC:

```sql
SELECT
    st.entity_id,
    h.bucket_ts,
    st.state,
    st.attributes
FROM `states` AS st
JOIN (
    SELECT
        entity_id,
        FLOOR(UNIX_TIMESTAMP(last_updated) / 3600) * 3600 AS bucket_ts,
        MAX(state_id) AS max_id
    FROM `states`
    WHERE entity_id IN (:entity_ids)
      AND last_updated >= :start_utc
      AND last_updated < :end_utc
    GROUP BY entity_id, bucket_ts
) AS h
    ON st.state_id = h.max_id
ORDER BY st.entity_id, h.bucket_ts;
```

Parámetros:

| Parámetro | Significado |
| --------- | ----------- |
| `:entity_ids` | Entidades de los contadores de entrada y salida. |
| `:start_utc` | Inicio de la ventana en UTC. Inclusivo. |
| `:end_utc` | Fin de la ventana en UTC. Exclusivo. |

`bucket_ts` es el inicio de la hora en segundos UTC. El backend lo convierte después a la hora local de `Europe/Madrid`. Las columnas `state` y `attributes` se devuelven como texto porque algunos contadores guardan el valor en un atributo JSON, como `LTR_SUM` y `RTL_SUM` de Módulo B.

La consulta la ejecuta `fetch_hourly_state_snapshots`, dentro de `_load_counter_series`.

## 4. Medias de temperatura, humedad y presencia

La pestaña Infraestructura usa `statistics.mean` para los sensores que sí tienen estadísticos de larga duración:

```sql
SELECT
    sm.statistic_id,
    s.start,
    s.mean
FROM `statistics_meta` AS sm
JOIN `statistics` AS s
    ON s.metadata_id = sm.id
WHERE sm.statistic_id IN (:statistic_ids)
  AND s.start >= :start_utc
  AND s.start < :end_utc
  AND s.mean IS NOT NULL
ORDER BY sm.statistic_id, s.start;
```

`:statistic_ids` incluye `sensor.sensor_temperatura_a11..a22`, `sensor.sensor_humedad_a11..a22`, `sensor.presencia1..3` y `sensor.ambiente` (referencia, no estancia). Las filas se agrupan después por hora local.

La consulta la ejecuta `fetch_statistics_means`.

## 5. Medias horarias de CO₂

Los sensores `air_quality.co2_*` no tienen filas en `statistics_meta`, así que se leen de `states` y se filtran los valores no numéricos e imposibles antes de promediar:

```sql
SELECT
    st.entity_id,
    FLOOR(UNIX_TIMESTAMP(st.last_updated) / 3600) * 3600 AS bucket_ts,
    AVG(CAST(st.state AS DECIMAL(12, 3))) AS mean_value
FROM `states` AS st
WHERE st.entity_id IN (:entity_ids)
  AND st.last_updated >= :start_utc
  AND st.last_updated < :end_utc
  AND st.state REGEXP '^-?[0-9]+(\\.[0-9]+)?$'
  AND CAST(st.state AS DECIMAL(12, 3)) BETWEEN :min_value AND :max_value
GROUP BY st.entity_id, bucket_ts
ORDER BY st.entity_id, bucket_ts;
```

Para CO₂ se usa `min_value=300` y `max_value=5000` ppm. La consulta la ejecuta `fetch_hourly_numeric_state_means` y solo se lanza para las cuatro entidades `air_quality.co2_1..4`. En el código se ejecuta una consulta por entidad en sesiones independientes y en paralelo: en este servidor es más rápido que agrupar las cuatro en un único escaneo.

## 5 bis. Acumulados de gas

Para el contexto de calefacción se leen los `sum` acumulados de `sensor.daily_gas` (m³) y `sensor.daily_gas_cost` (€), con dos días de margen antes del inicio para calcular el primer incremento:

```sql
SELECT
    sm.statistic_id,
    s.start,
    s.sum
FROM `statistics_meta` AS sm
JOIN `statistics` AS s
    ON s.metadata_id = sm.id
WHERE sm.statistic_id IN ('sensor.daily_gas', 'sensor.daily_gas_cost')
  AND s.start >= :start_utc - INTERVAL 2 DAY
  AND s.start < :end_utc
  AND s.sum IS NOT NULL
ORDER BY sm.statistic_id, s.start;
```

El servicio convierte cada diferencia positiva entre filas consecutivas en un incremento horario. Es un dato del edificio: no se reparte por estancia. La consulta la ejecuta `fetch_statistics_sums`.

## 6. Transiciones de movimiento

Los sensores `sensor.movimiento_a11..a22` solo escriben cuando cambian de estado. Para estimar ocupación se leen las transiciones y se reparte el tiempo “encendido” entre las horas:

```sql
SELECT
    st.entity_id,
    st.last_updated,
    st.state
FROM `states` AS st
WHERE st.entity_id IN (:entity_ids)
  AND st.last_updated >= :start_utc
  AND st.last_updated < :end_utc
ORDER BY st.entity_id, st.last_updated;
```

El backend consulta también el último estado anterior a la ventana con la consulta de la sección 2, para saber si la sala ya estaba ocupada al empezar. La consulta la ejecuta `fetch_state_rows`.

## 7. Último valor para las tarjetas

Para el estado actual se toma el último `state_id` de cada entidad dentro de una ventana de 21 días:

```sql
SELECT
    st.entity_id,
    st.state,
    st.attributes,
    st.last_updated
FROM `states` AS st
JOIN (
    SELECT MAX(state_id) AS max_id
    FROM `states`
    WHERE entity_id IN (:entity_ids)
      AND last_updated < :before_utc
      AND last_updated >= :lookback_start_utc
    GROUP BY entity_id
) AS latest
    ON st.state_id = latest.max_id;
```

La consulta la ejecuta `fetch_latest_state_snapshots`. Los valores `0`, `unknown`, `unavailable` y los resets de temperatura se descartan en el servicio; si no hay un valor reciente, la tarjeta muestra el último válido o “Sin dato”.

## 8. Comprobación de salud

En modo `database`, `/health/ready` comprueba que la conexión responde con:

```sql
SELECT 1;
```

Esta sentencia se ejecuta directamente desde `app/main.py`, no desde `repository.py`.

## Resumen de acceso

| Función del backend | Consulta | Datos que obtiene |
| ------------------- | -------- | ----------------- |
| `fetch_statistics_sums` | `statistics_meta` + `statistics` | Acumulados horarios de electricidad y gas. |
| `fetch_statistics_means` | `statistics_meta` + `statistics` | Medias horarias de temperatura, humedad y presencia. |
| `fetch_hourly_numeric_state_means` | `states` | Medias horarias de CO₂. |
| `fetch_state_rows` | `states` | Transiciones de los sensores de movimiento. |
| `fetch_state_snapshots` | `states` | Series de `weather.meteo`, `sensor.ambiente` y AEMET. |
| `fetch_last_state_snapshots_before` | `states` | Último estado anterior a la ventana. |
| `fetch_latest_state_snapshots` | `states` | Último estado válido para las tarjetas. |
| `fetch_hourly_state_snapshots` | `states` | Último estado de cada hora para contadores de personas. |
| `health_ready` | `SELECT 1` | Conectividad con MariaDB. |

## Notas para consultas manuales

- Los parámetros `:...` son marcadores de SQLAlchemy. En un cliente MySQL hay que sustituirlos por valores reales o por listas `IN (...)`.
- Las fechas de `statistics.start` y `states.last_updated` se comparan en UTC sin zona horaria.
- La aplicación solo necesita permisos de lectura sobre `statistics_meta`, `statistics` y `states`.
- En Medio Ambiente, la temperatura de `weather.meteo` está en `states.state` y el resto de medidas en el JSON `attributes`; por eso se leen estados completos y se parsean en el servicio.
- Para comprobar los contadores disponibles:

```sql
SELECT statistic_id, source, unit_of_measurement
FROM `statistics_meta`
WHERE statistic_id LIKE 'sensor.%'
ORDER BY statistic_id;
```
