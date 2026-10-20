# Guion de presentación · Smart ESI Estadísticas

> **Duración objetivo:** 25 minutos de exposición + 5 minutos de preguntas.
> **Idea central:** no presentar “otro panel de datos”, sino un **prototipo de gráficas para tomar decisiones** sobre electricidad, gas, ocupación y calidad del aire.

---

## 1. Mensajes que deben quedar claros

1. **Qué es:** módulo independiente de estadísticas para la web de Smart ESI, hecho para validar gráficas antes de integrarlas en la web pública.
2. **Para qué sirve:** convertir datos de sensores en decisiones: dónde gastar menos, qué espacios revisar, cuándo se desperdicia energía.
3. **Datos reales:** electricidad, gas, temperaturas, humedad, ocupación y CO₂ ya salen de la base de datos real de Home Assistant.
4. **Honestidad:** el total eléctrico es real y el reparto parcial se marca como tal; lo que sigue siendo estimado se documenta y se avisa en la interfaz.
5. **Siguiente paso:** validar con negocio qué gráficas aportan valor y conseguir los mapeos que faltan (iluminación, contadores por edificio, ocupación por aula).

---

## 2. Reparto del tiempo

| Minutos | Bloque | Qué decir |
| --- | --- | --- |
| 0–2 | Apertura | Qué es el proyecto y por qué existe. |
| 2–5 | Problema y objetivo | Los datos existen, pero no están orientados a decidir. |
| 5–8 | Solución y arquitectura | Seis pestañas, API, datos reales/mock, mismo stack. |
| 8–20 | Demo guiada | Recorrido por las seis pestañas. |
| 20–23 | Estado de los datos | Qué es real, qué es estimado y la corrección del cuadro general. |
| 23–26 | Validación y resultados | Tests, build, lectura segura, utilidad. |
| 26–28 | Limitaciones y siguientes pasos | Qué falta y qué se necesita. |
| 28–30 | Cierre y preguntas | Pedir validación y prioridades. |

> Si hay retraso, recortar la demo de Iluminación y Climatización a una frase cada una. No recortar la parte de “qué es real y qué no”.

---

## 3. Apertura (2 min)

### Qué decir

- “Esto es un **prototipo independiente** de estadísticas para Smart ESI.”
- “No modifica la web actual: vive en un proyecto aparte para probar gráficas nuevas sin riesgo.”
- “El objetivo no es enseñar más datos, sino **ayudar a decidir** con ellos.”

### Por qué se hizo

- La web ya recoge datos de sensores, pero faltaba una capa que los cruzara y los tradujera a decisiones.
- Se quería comprobar si merece la pena integrar estas gráficas en la web pública.
- Se ha replicado el mismo stack y el mismo estilo visual para que la integración posterior sea sencilla.

---

## 4. Problema y objetivo (3 min)

### Problema

- Los datos están repartidos: electricidad, gas, ocupación, temperatura, CO₂.
- Ver un dato suelto no dice qué hacer.
- Ejemplos de preguntas que el panel intenta responder:
  - ¿Cuánto consume el centro y cuándo?
  - ¿Qué parte del gasto es carga base fuera de horario?
  - ¿Qué edificio o espacio es menos eficiente?
  - ¿Se calienta cuando no hay nadie?
  - ¿La calidad del aire empeora cuando sube la ocupación?
  - ¿Qué actuación tiene más impacto económico?

### Objetivo del prototipo

- Un panel único, con **seis pestañas**, un **periodo global** y filtros por edificio/métrica.
- Gráficas interactivas, exportables y compartibles por URL.
- Contrato de API estable y posibilidad de cambiar entre datos reales y simulados.

---

## 5. Solución y arquitectura (3 min)

### Qué se ha construido

- **Resumen:** KPIs del centro.
- **Electricidad:** consumo, carga base vs. actividad, comparativa, eficiencia y reparto por edificio.
- **Iluminación:** luminarias vs. luz natural, ranking por espacio y despilfarro.
- **Climatización y gas:** gas vs. grados-día, válvulas vs. temperatura y aulas vacías.
- **Ocupación y aire:** cruce ocupación ↔ CO₂.
- **Decisiones:** oportunidades de ahorro priorizadas con €/año estimado.

### Arquitectura, en una frase

> “Navegador → React/Vite → API FastAPI → base de datos del recorder de Home Assistant, en modo solo lectura; o generador de datos sintéticos si no hay acceso.”

### Piezas técnicas

- **Frontend:** React 18 + TypeScript + Vite + TanStack Query + Recharts + Tailwind.
- **Backend:** FastAPI + Pydantic, servicios de agregación y caché TTL.
- **Datos:** `DATA_SOURCE=database` lee Home Assistant; `DATA_SOURCE=mock` permite funcionar sin VPN ni BD.
- **Despliegue:** carpeta `deploy/` con Docker Compose + nginx como reverse proxy.
- **Calidad:** API tipada, tests de backend y frontend, documentación por dominio.

### Decisiones de diseño que merece la pena mencionar

- **Mismo contrato de API** en modo real y mock: el frontend no cambia.
- **Periodo global** compartido por todas las gráficas.
- **Mock determinista:** los mismos filtros devuelven siempre los mismos valores.
- **Caché** para no repetir agregaciones costosas.
- **Solo `SELECT`** sobre la base de datos de Home Assistant.

---

## 6. Demo guiada (12 min)

> Abrir la aplicación en `http://localhost:5174/`.
> Tener Home Assistant abierto en otra ventana para comparar el cuadro general si preguntan.

### 6.1 Cabecera y periodo global (1 min)

- Cambiar de **Día → Semana → Mes → Año**.
- Señalar que el cambio afecta a todas las gráficas.
- Enseñar que la URL guarda `tab` y `range`: se puede recargar o compartir la vista.
- Mencionar el **export CSV** en las tablas.

### 6.2 Resumen (1–2 min)

- Enseñar las seis tarjetas:
  - consumo eléctrico,
  - edificio con mayor consumo medido,
  - gas,
  - ahorro potencial,
  - porcentaje de aire bueno,
  - CO₂ medio.
- Mensaje: “Esto es la foto rápida para una reunión; el detalle está en las pestañas.”

### 6.3 Electricidad (4 min)

Orden recomendado:

1. **Consumo:** elegir “Todos los edificios”; cambiar métrica kWh/€/CO₂.
   - Señalar total, media y pico.
   - Comparar con Home Assistant en el mismo intervalo.
   - Decir: “El total sale de `sensor.cuadro_general`, el mismo contador del cuadro general de HA.”
2. **Carga base vs. actividad:** explicar noches y fines de semana.
3. **Comparativa:** periodo actual frente al anterior.
4. **Eficiencia:** kWh/m² y kWh/persona·hora; aviso de cobertura parcial.
5. **Por edificio:** enseñar “No desglosado” y el porcentaje de cobertura.
   - Seleccionar un edificio y enseñar el aviso: su contador es un subcontador parcial.
6. **Mensaje clave:** “El total es real; el reparto por edificio es parcial y lo decimos claramente.”

### 6.4 Iluminación (1–2 min)

- Enseñar luminarias vs. luz natural.
- Enseñar ranking por espacio y despilfarro con espacios vacíos.
- **Aviso obligatorio:** el consumo de iluminación sigue siendo **estimado** porque falta confirmar el mapeo de controladores y potencia por circuito.
- Valor: la ocupación que usa el cálculo sí es real.

### 6.5 Climatización y gas (1–2 min)

- Gas frente a grados-día.
- Válvulas frente a temperatura.
- Aulas vacías y coste estimado.
- **Avisos:**
  - el gas es real, pero **solo del centro completo** (hay un único contador);
  - las válvulas siguen siendo simuladas porque no hay entidad real.

### 6.6 Ocupación y aire (1–2 min)

- Enseñar ocupación real por edificio.
- Enseñar CO₂ y la relación con la ocupación.
- **Avisos:**
  - CO₂ real solo en A11, A12, A21 y A22;
  - el reparto de ocupación por aula es estimado.

### 6.7 Decisiones (2 min)

- Enseñar el ranking de oportunidades y el ahorro €/año.
- Explicar que es una **herramienta de priorización**, no una auditoría contable.
- Mensaje: “Sirve para decidir qué mirar primero, no para certificar un ahorro.”

---

## 7. Estado de los datos (3 min)

### Tabla mental para la reunión

| Dato | Estado | Comentario |
| --- | --- | --- |
| Electricidad total del centro | **Real** | `sensor.cuadro_general`, mismo que HA. |
| Electricidad por edificio | **Real parcial** | `sensor.edificio_a/b` cubren aprox. 3–15 % del total. |
| Gas | **Real** | Solo centro completo; no hay contador por edificio. |
| Grados-día y temperatura exterior | **Real** | Sensor meteorológico. |
| Temperatura/humedad interior | **Real** | Sensores por espacio. |
| Ocupación por edificio | **Real** | Contadores de entrada/salida. |
| CO₂ | **Real en 4 aulas** | A11, A12, A21, A22. |
| Iluminación | **Estimada** | Falta mapeo y potencia por circuito. |
| Válvulas | **Estimada** | No hay entidad real. |
| Ocupación por aula | **Estimada** | Los contadores son por edificio. |
| Reparto eléctrico por espacio | **Estimado** | Se reparte por superficie/peso. |
| Ahorro potencial | **Estimación** | Combina datos reales y modelos. |

### Corrección importante que ya está aplicada

- Antes el total eléctrico sumaba A+B y daba una fracción del consumo real.
- Ahora:
  - el total usa `sensor.cuadro_general`;
  - los edificios A/B se muestran como subcontadores parciales;
  - se añade “No desglosado” y un porcentaje de cobertura;
  - se corrigió el desfase de una hora al interpretar `statistics.sum`.
- Resultado: el total del panel coincide con el gráfico de HA para el mismo contador e intervalo.

> Explicación corta si preguntan: “HA guarda el acumulado al final del periodo; la diferencia entre dos filas pertenece a la hora de la fila actual, no a la anterior.”

---

## 8. Validación y resultados (3 min)

### Lo que ya está comprobado

- Backend: **39 tests** superados.
- Frontend: **18 tests** superados.
- `typecheck` de TypeScript correcto.
- Build de producción correcto.
- `/health/live` confirma el modo de datos activo.
- `/health/ready` comprueba la conexión real.
- Lectura de base de datos **solo con `SELECT`**.

### Valor que aporta

- Unifica varias fuentes en una sola vista.
- Traduce kWh a € y CO₂.
- Permite comparar periodos y edificios.
- Detecta patrones: carga base, picos, espacios ineficientes, aire deficiente.
- Deja una base extensible para integrar nuevas gráficas.

---

## 9. Limitaciones y siguientes pasos (2 min)

### Limitaciones actuales

- Iluminación y válvulas siguen siendo estimadas.
- No hay gas por edificio: solo hay un contador.
- No hay ocupación real por aula.
- El reparto eléctrico por espacio es aproximado.
- El CO₂ solo es real en cuatro aulas.
- El despliegue Docker está preparado, pero falta validarlo en el entorno final.
- Depende del esquema de la base de datos del recorder de HA.

### Qué necesitamos para el siguiente salto

1. Confirmar el mapeo de **controladores de iluminación → espacios**.
2. Confirmar potencia/consumo por circuito de iluminación.
3. Identificar contadores generales fiables por edificio.
4. Valorar contadores de ocupación por aula o estimación más fina.
5. Validar qué gráficas son realmente útiles para la web pública.
6. Probar el despliegue en el entorno definitivo.

---

## 10. Cierre (1–2 min)

### Frase de cierre

> “El prototipo ya demuestra que se pueden cruzar datos reales de Smart ESI y convertirlos en decisiones. Lo que falta no es principalmente técnico: falta confirmar qué datos queremos medir y qué decisiones queremos priorizar.”

### Peticiones concretas

- Validar las gráficas que más valor aportan.
- Decidir qué pestañas pasan a la web pública.
- Facilitar los mapeos pendientes de iluminación y contadores.
- Acordar una prueba piloto con datos reales durante varias semanas.

---

## 11. Preguntas previsibles y respuestas cortas

### “¿Por qué no coincide con Home Assistant?”

- Ya coincide para el total: usamos `sensor.cuadro_general` y la misma convención temporal.
- Si se comparaba con A+B, era porque esos son subcontadores parciales, no el total.
- En la pestaña de edificios se muestra “No desglosado” y la cobertura.

### “¿Por qué hay datos simulados?”

- Porque todavía no existen entidades o mapeos confirmados para iluminación, válvulas u ocupación por aula.
- Se marcan como estimados; no se presentan como reales.

### “¿Se puede poner ya en producción?”

- El prototipo está validado funcionalmente y el despliegue está preparado.
- Antes de publicarlo hay que cerrar los mapeos pendientes y validar el entorno final.

### “¿Eso supone mucho coste?”

- Los datos ya están en Home Assistant.
- El prototipo es ligero: una API y una SPA.
- El coste principal es el tiempo de integración y validación, no la infraestructura.

### “¿Es seguro leer la base de datos de HA?”

- Se usa un usuario de solo lectura.
- Todas las consultas son `SELECT`.
- No se escribe ni se modifica nada en el recorder.

### “¿Cómo se añade una gráfica nueva?”

- Endpoint + esquema + servicio en backend.
- DTO + función de API + hook + componente en frontend.
- Test e integración en la pestaña correspondiente.

### “¿Qué es lo más importante que falta?”

- El mapeo de iluminación y los contadores generales por edificio.
- Sin eso, el detalle por edificio/espacio seguirá siendo parcial.

---

## 12. Checklist antes de la reunión

- [ ] Backend arrancado en `127.0.0.1:8010`.
- [ ] Frontend arrancado en `localhost:5174`.
- [ ] `DATA_SOURCE=database` y conexión VPN/BD comprobada.
- [ ] `/health/live` muestra `database`.
- [ ] `/health/ready` responde correctamente.
- [ ] Home Assistant abierto en otra ventana para comparar el cuadro general.
- [ ] Pestaña de Resumen cargada antes de empezar.
- [ ] Capturas de respaldo por si falla la red.
- [ ] Un CSV exportado de ejemplo.
- [ ] URL de una vista concreta preparada para enseñar que se puede compartir.
- [ ] Cerrar sesión de pruebas y dejar la aplicación en la pestaña de inicio.

---

## 13. Frases que conviene evitar

- “Esto ya es producción.” → Mejor: “Es un prototipo validado, preparado para dar el salto.”
- “Todos los datos son reales.” → Mejor: “Estos son reales y estos son estimados, y se distingue en la interfaz.”
- “El ahorro es exactamente X €.” → Mejor: “El ahorro estimado permite priorizar; no es una auditoría.”
- “Falta poco.” → Mejor: “Falta confirmar los mapeos y validar el despliegue final.”

---

## 14. Resumen de una frase por pestaña

| Pestaña | Frase para la reunión |
| --- | --- |
| Resumen | “La foto rápida del centro en el periodo elegido.” |
| Electricidad | “Dónde, cuándo y con qué eficiencia se consume la electricidad.” |
| Iluminación | “Cuánto pesa la luz y cuánto se enciende sin necesidad.” |
| Climatización | “Gas, grados-día y calor en aulas vacías.” |
| Ocupación y aire | “Cómo se relaciona la gente con la calidad del aire.” |
| Decisiones | “Qué actuaciones priorizar y cuánto podrían ahorrar.” |
