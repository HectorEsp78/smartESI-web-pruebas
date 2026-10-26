# Smart ESI · Estadísticas (prototipo local)

Módulo **independiente** de estadísticas para la página web de Smart ESI. Su objetivo es servir
como banco de pruebas para las **nuevas gráficas orientadas a la toma de decisiones** antes de
incorporarlas a la web pública.

El panel se organiza en **seis pestañas**. La mayoría usa un selector de **periodo global**; la
pestaña de **Electricidad** tiene fechas propias y agrupación temporal automática:

- **Resumen** — KPIs del centro (electricidad, gas, aire y ahorro potencial).
- **Electricidad** — rango de fechas propio, consumo o coste, reparto Módulo A / Módulo B / Fermín,
  sectores de Fermín (cuadros de planta y CPD), comparativa de dos periodos y base de centro cerrado.
- **Iluminación** — luminarias frente a luz natural y despilfarro con los espacios vacíos.
- **Climatización y gas** — gas frente a grados-día, electroválvulas vs. temperatura y aulas vacías.
- **Ocupación y aire** — cruce de ocupación con CO₂.
- **Decisiones** — oportunidades de ahorro priorizadas, con su €/año estimado.

Se ha construido replicando **el mismo stack** y el **mismo estilo visual** del proyecto original
([`pagina-web-Smart-ESI`](../pagina-web-Smart-ESI)), pero vive en un proyecto aparte para no
tocarlo:

- Paleta institucional UCLM/ESI y tipografías Manrope / Montserrat / Source Sans 3.
- Gráficas con Recharts, estilos con Tailwind CSS 4 y el mismo lenguaje visual (tarjetas de borde
  fino, títulos de sección con `border-l-4 border-accent`, etc.).
- Frontend React + Vite + TypeScript + TanStack Query; backend FastAPI + Pydantic.

> **Datos**: el backend puede trabajar en dos modos con el mismo contrato de API:
> `DATA_SOURCE=database` lee la base de datos real del *recorder* de Home Assistant **solo con
> `SELECT`** (ya implementado para **Electricidad**, **Climatización/gas**, **Ocupación** y
> **CO₂/aire**: energía, gas, grados-día, temperaturas, humedad, contadores de personas y cuatro
> sondas de CO₂), y `DATA_SOURCE=mock` (por defecto) genera datos sintéticos para el resto de
> pestañas y para poder ejecutar sin VPN ni base de datos. La iluminación sigue en mock porque aún
> no hay un mapeo confirmado de sus controladores. En Electricidad, el total del centro es
> `sensor.cuadro_general`; Módulo A y Módulo B son contadores directos; Fermín Caballero se deriva
> como `Cuadro General − Módulo A − Módulo B`, y sus cuadros de planta/CPD se muestran como
> subcontadores parciales con su cobertura.

## Puesta en marcha rápida

Requiere **Node 18+** y **Python 3.10+**. Con el modo por defecto (`mock`) no requiere VPN ni base
de datos; para leer los datos reales hace falta acceso a la BD del *recorder* (ver
[`docs/backend.md`](docs/backend.md)).

```bash
# 1) Backend  ->  http://127.0.0.1:8010
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"   # añade ".[database]" para leer la BD real
cp .env.example .env                            # opcional: los valores por defecto ya funcionan
.venv/bin/uvicorn app.main:app --reload --port 8010

# 2) Frontend ->  http://localhost:5174
cd frontend
npm install
npm run dev
```

Abre **http://localhost:5174/** en el navegador.

Detalle completo en [`docs/puesta-en-marcha.md`](docs/puesta-en-marcha.md).

## Puertos

| Servicio | Puerto | URL |
| -------- | ------ | --- |
| Backend (FastAPI) | `8010` | http://127.0.0.1:8010 · docs en `/docs` |
| Frontend (Vite) | `5174` | http://localhost:5174 |

Se usan puertos distintos a los del proyecto original (8000 / 5173) para poder ejecutar ambos a la
vez sin conflictos.

## Despliegue

[`deploy/`](deploy/README.md) incluye un `docker-compose.yml` con el backend y un nginx que sirve el
frontend y hace de *reverse proxy* de `/api`:

```bash
cd deploy
cp .env.example .env     # ajusta DB_* (o DATA_SOURCE=mock) y CORS
docker compose up -d --build
# http://localhost:8080
```

## Estructura

```text
smartesi-stats/
├── backend/          API FastAPI (modo mock o BD real de Home Assistant)
│   └── app/
│       ├── api/          Routers: energy, lighting, climate, decisions, correlation, meta
│       ├── core/         Config, reloj, caché y catálogo buildings/spaces
│       ├── db/           Modelos HA, repositorio de consultas y sesión (DATA_SOURCE=database)
│       ├── schemas/      Modelos Pydantic (contrato de la API)
│       └── services/     Generador de datos + servicios de agregación y decisiones
├── frontend/         SPA React + Vite
│   └── src/app/
│       ├── api/          Llamadas fetch tipadas
│       ├── context/      Periodo global compartido (RangeContext)
│       ├── hooks/        Hooks de TanStack Query
│       ├── components/   Header, UI reutilizable y las gráficas (stats/ por dominio)
│       ├── pages/        Stats (pestañas), NotFound
│       ├── lib/          Formateo, colores de gráficas, pestañas
│       └── types/        DTOs de la API
├── docs/             Documentación
└── deploy/           Docker Compose + nginx para publicar el prototipo
```

## Documentación

- [Puesta en marcha](docs/puesta-en-marcha.md) — requisitos, comandos, puertos y resolución de problemas.
- [Arquitectura](docs/arquitectura.md) — cómo encajan las piezas y la API.
- [Backend](docs/backend.md) — módulos, endpoints y paso a la base de datos real.
- [Frontend](docs/frontend.md) — estructura, estilos y cómo añadir una gráfica.
- [Datos](docs/datos.md) — origen de los datos y modelo sintético.
- [Estadísticos](docs/estadisticos.md) — qué estadístico se calcula y para qué decisión sirve.
- [Componentes](docs/componentes.md) — cada pieza de la web por pestañas.
- [Gráficas](docs/graficas.md) — qué muestra cada gráfica y qué decisiones ayuda a tomar.
- [Backlog](docs/backlog.md) — ideas y cruces de datos pendientes.

## Relación con el proyecto original

Este repositorio es **independiente** y no modifica el original. La idea es que, una vez validadas
las gráficas aquí, se puedan portar a la web pública reutilizando los mismos componentes de estilo
y la misma capa de datos.
