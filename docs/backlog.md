# Backlog: ideas pendientes

Notas y propuestas **no implementadas** en esta iteración. Sirven de guía para siguientes pasos del
prototipo. Nada de aquí está en la web actual.

## Cruces de datos propuestos y descartados (por ahora)

- **Perfil horario / *heatmap* hora × día.** Un mapa de calor con la media de consumo por hora y día
  de la semana. Útil, pero en parte redundante con la carga base (`/energy/breakdown`) y la
  ocupación; se retomará si hace falta afinar horarios.
- **Detección de anomalías por z-score.** Marcar horas o días con consumo anómalo respecto a su
  propia distribución. Necesita un histórico más largo y un umbral calibrado con datos reales;
  cuando existan, es la evolución natural del ranking de oportunidades.
- **Ranking de ahorro en € por edificio/espacio** (variante del panel de Decisiones segmentada por
  edificio en formato tabla comparativa).

## Datos

- **Iluminación real**: mapear `light.controller1..7` y `sensor.sensor_luz_aXX` a cada
  edificio/espacio y obtener potencia o consumo por circuito. Hoy la pestaña de iluminación sigue
  en mock (la ocupación que usa para detectar despilfarro sí es real). Ver
  [`datos.md`](datos.md#43-pendiente).
- **Reparto real de la ocupación por aula**: los contadores son por edificio. Con presencia por
  aula se podría afinar el gas en aulas vacías y la eficiencia por espacio.
- **Más sondas de CO₂**: hoy solo A11/A12/A21/A22; el resto de espacios usa el modelo.
- **Precio del gas configurable por contrato**: hoy es un factor único
  (`GAS_PRICE_EUR_PER_KWH`); podría leerse de una tabla de tarifas.
- **Factores de emisión por fuente** (gas natural, electricidad con mix horario).
- **Consigna real por aula** en lugar de una consigna por edificio.

## Producto / frontend

- **Comparar dos periodos** elegidos a mano (no solo el anterior equivalente).
- **Objetivos y alertas**: fijar umbrales (p. ej. kWh/m², % de luz sin ocupación) y avisar cuando se
  superan.
- **Modo "solo incidencias"** en el panel de Decisiones (filtrar por prioridad y ocultar el detalle
  de las medidas ya en curso).
- **Exportar PNG**: hoy se puede exportar a CSV (Decisiones, eficiencia y luminarias por espacio);
  falta la imagen de la gráfica.
- **Enlace profundo con edificio/métrica**: la URL ya guarda pestaña y periodo
  (`?tab=electricidad&range=month`); faltan los selectores locales de cada gráfica.

## Despliegue

- **TLS y dominio público**: [`deploy/`](../deploy) ya trae Docker Compose + nginx; falta decidir el
  dominio final, el certificado y el *reverse proxy* corporativo.
- **CI**: ejecutar tests de backend/frontend y `docker build` en cada *push*.
