# Guion de presentación · Smart ESI Estadísticas

> **Idea central:** la web convierte los datos de Smart ESI en dos vistas concretas para decidir: **Electricidad** (cuánto se gasta, dónde y frente a qué periodo) e **Iluminación** (cuánta luz se enciende sin necesidad).

## 1. Mensajes que deben quedar claros

1. **Qué es:** un prototipo de estadísticas sobre el *recorder* de Home Assistant.
2. **Para qué sirve:** detectar gasto, comparar periodos y localizar despilfarro.
3. **Qué es real:** el consumo eléctrico sale de los contadores reales del centro; la iluminación usa un modelo determinista y, si hay datos, la ocupación real.
4. **Qué no se pretende:** sustituir Home Assistant ni escribir en la base de datos. Todo es **solo lectura**.

## 2. Reparto del tiempo (20 min)

| Bloque | Tiempo |
| ------ | ------ |
| Apertura y objetivo | 3 min |
| Arquitectura y datos | 4 min |
| Demo: Electricidad | 6 min |
| Demo: Iluminación | 3 min |
| Límites, siguientes pasos y preguntas | 4 min |

Si hay prisa, mantener la demo de Electricidad y resumir Iluminación en una frase.

## 3. Apertura

- Smart ESI ya recoge datos de sensores, pero faltaba una capa que los convirtiera en información útil.
- Este prototipo se centra en dos preguntas:
  - **¿Cuánto gastamos y cuándo?**
  - **¿Qué luz dejamos encendida sin necesitarla?**
- La web no es un panel más: cada gráfica responde a una decisión concreta.

## 4. Arquitectura en una frase

```text
React + Vite  ──/api──►  FastAPI  ──SELECT──►  MariaDB (recorder de Home Assistant)
```

- **Frontend:** React, TypeScript, TanStack Query y Recharts.
- **Backend:** FastAPI con servicios de agregación y caché en memoria.
- **Datos:** realidad en Electricidad y ocupación de Iluminación; modelo sintético para el consumo de luminarias.
- **Seguridad:** la base de datos se consulta solo con `SELECT`.

## 5. Demo guiada

### 5.1 Cabecera y periodo

- La cabecera mantiene el periodo global **solo para Iluminación**.
- Electricidad tiene sus propias fechas porque necesita comparar periodos independientes.
- La URL guarda la pestaña y el periodo: se puede compartir un enlace.

### 5.2 Electricidad (6 min)

1. **Filtros**
   - Fecha inicial y final, ambas inclusivas.
   - Edificio: todos, Módulo A, Módulo B o Fermín Caballero.
   - Sector: cuadros de planta o CPD.
   - Métrica: **consumo (kWh)** o **coste (€)**.
   - La agrupación es automática: día, semana, mes o año según el rango.

2. **Indicadores**
   - Total, media, mínimo y máximo.
   - Base de centro cerrado: consumo medio en noches y fines de semana.
   - Cobertura de los sectores de Fermín y parte no desglosada.

3. **Gráfica por edificios**
   - Módulo A, Módulo B y Fermín Caballero.
   - La línea de base permite ver cuánto se separa el consumo real del nivel de centro cerrado.

4. **Sectores de Fermín**
   - Cuadros D, E, F, G, H, I, J, K y CPD.
   - Se muestra el porcentaje sobre Fermín y se avisa de que la cobertura es parcial.
   - El cuadro E aparece sin datos porque su acumulado no se mueve desde 2023.

5. **Comparativa**
   - Dos periodos independientes con el mismo número de intervalos.
   - Dos líneas de color y una base común de centro cerrado.
   - Botones para reutilizar el periodo principal o el año anterior.

**Mensaje:** “No solo vemos el total; vemos qué edificio o cuadro se separa de lo esperado y si el cambio es real o estacional.”

### 5.3 Iluminación (3 min)

1. **Consumo**
   - Barras de luminarias y otras cargas.
   - Línea de horas de luz natural.
   - KPIs de total, cuota de luminarias, coste y CO₂ asociado.

2. **Ranking por espacio**
   - Qué espacios concentran más consumo de luminarias.
   - Se puede exportar a CSV.

3. **Luz encendida sin ocupación**
   - kWh y €/año estimados.
   - Horas de edificio vacío con luminarias encendidas.

**Mensaje:** “El coste no está solo en encender más, sino en encender cuando no hay nadie.”

## 6. Qué es real y qué no

| Dato | Estado | Origen |
| ---- | ------ | ------ |
| Electricidad del centro | **Real** | `statistics.sum` de `sensor.cuadro_general` |
| Módulo A | **Real** | `sensor.edificio_a` |
| Módulo B | **Real** | `sensor.edificio_b` |
| Fermín Caballero | **Real (derivado)** | Cuadro General − Módulo A − Módulo B |
| Cuadros de Fermín y CPD | **Real (parcial)** | `sensor.planta_*`, `sensor.sala_computacion` |
| Ocupación para Iluminación | **Real si hay contadores** | Entradas − salidas |
| Consumo de luminarias | **Mock** | Modelo determinista |
| Coste eléctrico | **Calculado** | 0,20 €/kWh |

> El modo `mock` permite enseñar la web sin VPN ni base de datos. El indicador de la pestaña Electricidad muestra si el origen es `mock` o `database`.

## 7. Límites que conviene decir en voz alta

- Los cuadros de Fermín **no cubren todo el edificio**; la cobertura se muestra en pantalla y varía con el periodo.
- El alcance actual son Electricidad e Iluminación.
- Las fechas reales de Electricidad empiezan el **2023-12-22**.
- La base de centro cerrado considera **L-V de 7:00 a 21:00** como horario laborable; noches y fines de semana cuentan como cierre. Los festivos no se excluyen.
- El consumo de Iluminación es sintético: sirve para validar la interfaz y el método, no para auditorías.

## 8. Cierre

> “La web demuestra que los datos de Smart ESI ya permiten responder preguntas útiles. El siguiente paso no es añadir más gráficas, sino conectar más contadores y decidir qué actuaciones se quieren priorizar.”

## 9. Checklist antes de presentar

- [ ] Backend en `8010` y frontend en `5174` (o Docker en `8080`).
- [ ] `/health/live` responde `ok`.
- [ ] La pestaña Electricidad abre con datos y el indicador de origen es el esperado.
- [ ] Hay un rango con datos y otro con el año anterior para la comparativa.
- [ ] La pestaña Iluminación carga sus tres gráficas.
- [ ] Navegador sin zoom raro y CSV probado si se va a enseñar.

## 10. Una frase por pestaña

| Pestaña | Frase |
| ------- | ----- |
| Electricidad | “Cuánto gastamos, en qué edificio o cuadro y cómo se compara con otro periodo.” |
| Iluminación | “Cuánta luz se enciende y cuánta se desperdicia cuando no hay nadie.” |
