# Consultas SQL

El backend lee el *recorder* de Home Assistant en modo **solo lectura**. Todas las consultas son `SELECT`; la aplicación no ejecuta `INSERT`, `UPDATE` ni `DELETE`.

Las sentencias están centralizadas en [`backend/app/db/repository.py`](../backend/app/db/repository.py). La carga y conversión de las filas se hace en [`backend/app/db/database_data.py`](../backend/app/db/database_data.py).

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
| `statistics` | Valores acumulados (`sum`) de los contadores eléctricos, una fila por hora. |
| `states` | Último estado y atributos de los contadores de personas. |

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

## 4. Comprobación de salud

En modo `database`, `/health/ready` comprueba que la conexión responde con:

```sql
SELECT 1;
```

Esta sentencia se ejecuta directamente desde `app/main.py`, no desde `repository.py`.

## Resumen de acceso

| Función del backend | Consulta | Datos que obtiene |
| ------------------- | -------- | ----------------- |
| `fetch_statistics_sums` | `statistics_meta` + `statistics` | Acumulados horarios de electricidad. |
| `fetch_last_state_snapshots_before` | `states` | Último estado anterior a la ventana. |
| `fetch_hourly_state_snapshots` | `states` | Último estado de cada hora. |
| `health_ready` | `SELECT 1` | Conectividad con MariaDB. |

## Notas para consultas manuales

- Los parámetros `:...` son marcadores de SQLAlchemy. En un cliente MySQL hay que sustituirlos por valores reales o por listas `IN (...)`.
- Las fechas de `statistics.start` y `states.last_updated` se comparan en UTC sin zona horaria.
- La aplicación solo necesita permisos de lectura sobre `statistics_meta`, `statistics` y `states`.
- Para comprobar los contadores disponibles:

```sql
SELECT statistic_id, source, unit_of_measurement
FROM `statistics_meta`
WHERE statistic_id LIKE 'sensor.%'
ORDER BY statistic_id;
```
