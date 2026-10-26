# Gráficas

La web tiene dos pestañas y cinco gráficas principales.

## 1. Cabecera y periodo

- **Electricidad** usa fechas propias.
- **Iluminación** usa el selector global de periodo: día, semana, mes o año.
- La agrupación de Electricidad es automática; no hay selector “Agrupar por”.

## 2. Electricidad

### 2.1 Indicadores

No es una gráfica, pero fija la lectura:

- **Total:** gasto del periodo.
- **Media:** nivel típico por intervalo.
- **Mínimo / máximo:** valles y picos.
- **Base:** consumo esperado con el centro cerrado.
- **Cobertura:** porcentaje de Fermín medido por los cuadros.

### 2.2 Reparto por edificios

**Componente:** `ElectricityBuildingsChart` · **Endpoint:** `/energy/electricity`

Barras apiladas por intervalo con:

- Módulo A.
- Módulo B.
- Fermín Caballero.

La línea de base muestra cuánto se mantiene el consumo incluso sin actividad. Si las barras se pegan a la base en noches y fines de semana, hay carga permanente.

**Uso:**

- Ver qué edificio concentra el gasto.
- Detectar periodos con consumo anómalo.
- Comparar la forma de la curva con el horario del centro.

### 2.3 Sectores de Fermín

**Componente:** `ElectricitySectorsChart` · **Endpoint:** `/energy/electricity`

- Barras de cuadros D, E, F, G, H, I, J, K y CPD.
- Porcentaje sobre el total de Fermín.
- Segmento gris “No desglosado”.
- Aviso de cobertura parcial.

**Uso:**

- Localizar los cuadros que más pesan.
- Ver si el CPD tiene un consumo estable y alto.
- Detectar cuadros sin datos o con comportamiento raro.

> El cuadro E aparece sin datos porque su contador no se mueve desde 2023.

### 2.4 Comparativa de periodos

**Componente:** `ElectricityComparisonChart` · **Endpoint:** `/energy/electricity/compare`

Dos líneas de color:

- Periodo A.
- Periodo B.

La base común se calcula con las horas cerradas de ambos periodos. Los periodos deben tener el mismo número de intervalos.

**Uso:**

- Comparar un mes con el mismo mes del año anterior.
- Ver si una actuación redujo el consumo.
- Separar el efecto del horario del efecto de la carga base.

## 3. Iluminación

### 3.1 Consumo de luminarias

**Componente:** `LightingConsumptionChart` · **Endpoint:** `/lighting/consumption`

- Barras apiladas: luminarias y otras cargas.
- Línea: horas de luz natural.
- KPIs: total, luminarias, cuota, coste y CO₂.

**Uso:**

- Comprobar si el encendido sigue al día.
- Ver cuánto pesa la iluminación en el total.
- Detectar noches con demasiada luz.

### 3.2 Ranking por espacio

**Componente:** `LightingBySpaceChart` · **Endpoint:** `/lighting/by-space`

Barras horizontales con los espacios que más luminarias consumen. La tabla añade superficie, tipo, cuota y coste.

**Uso:**

- Priorizar sustitución o zonificación.
- Comparar espacios similares.
- Justificar inversiones con el coste estimado.

### 3.3 Luz encendida sin ocupación

**Componente:** `LightingWasteChart` · **Endpoint:** `/lighting/waste`

- kWh de luminarias en horas vacías.
- Porcentaje sobre el total de luminarias.
- Horas vacías.
- Coste del periodo y €/año estimado.

**Uso:**

- Ajustar horarios o sensores de presencia.
- Detectar espacios con luces encendidas de noche o en fin de semana.
- Estimar el retorno de una actuación.

## 4. Cómo leer las gráficas

- **kWh** mide energía; **€** aplica 0,20 €/kWh.
- Una barra más alta no siempre es un problema: puede ser un periodo más largo o un intervalo parcial. Los indicadores y las fechas ayudan a interpretarlo.
- La base de centro cerrado es una referencia, no un objetivo.
- En Fermín, la suma de sectores no es el total del edificio: mirar siempre la cobertura.
- En Iluminación, el consumo es sintético; sirve para validar el método y la interfaz.
