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

- **Migrar a la base de datos real** de Home Assistant (`DATA_SOURCE=database`): sustituir las
  funciones de `mock_data` por consultas al *recorder*. Ver [`backend.md`](backend.md).
- **Precio del gas configurable por contrato**: hoy es un factor único
  (`GAS_PRICE_EUR_PER_KWH`); podría leerse de una tabla de tarifas.
- **Factores de emisión por fuente** (gas natural, electricidad con mix horario).
- **Consigna real por aula** en lugar de una consigna por edificio.

## Producto / frontend

- **Enlace profundo a pestaña y periodo** en la URL (`#electricidad?range=month`) para compartir una
  vista concreta.
- **Exportar** una gráfica o la tabla de espacios a CSV/PNG.
- **Comparar dos periodos** elegidos a mano (no solo el anterior equivalente).
- **Objetivos y alertas**: fijar umbrales (p. ej. kWh/m², % de luz sin ocupación) y avisar cuando se
  superan.
- **Modo "solo incidencias"** en el panel de Decisiones (ocultar categorías sin hallazgos).

## Despliegue

- Carpeta [`deploy/`](../deploy) pendiente: contenedores y configuración de producción (puertos,
  CORS, *reverse proxy*).
