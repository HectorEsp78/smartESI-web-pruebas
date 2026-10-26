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

- Dos periodos independientes con el **mismo número de intervalos**.
- Se comparan intervalo a intervalo: periodo A frente a periodo B.
- `delta_pct` = (total A − total B) / total B × 100.
- La base es común: se calcula con las horas cerradas de ambos periodos.
- Si los periodos no tienen el mismo número de intervalos, la API devuelve 400.

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

## 3. Unidades y redondeo

- kWh con 2 decimales.
- € con 2 decimales.
- Porcentajes y cuotas con 1–4 decimales según el campo.
- Las fechas se muestran en `Europe/Madrid`.
- Los totales pueden no coincidir exactamente al sumar tarjetas redondeadas; el cálculo interno usa más precisión.
