# Smart ESI · Estadísticas

Prototipo local de la capa de estadísticas de Smart ESI. La web tiene **dos pestañas**:

- **Electricidad** — consumo o coste por edificio y por los cuadros de Fermín Caballero, comparativa de dos periodos y base de consumo del centro cerrado. Usa fechas propias (inicio y fin inclusivos) y calcula la agrupación temporal automáticamente.
- **Iluminación** — reparto entre luminarias y otras cargas, ranking de espacios y despilfarro de luz cuando el edificio está vacío.

El objetivo es convertir los datos del *recorder* de Home Assistant en gráficas sencillas para detectar gasto y decidir actuaciones.

## Datos

| Pestaña | Consumo | Ocupación | Coste |
| ------- | ------- | --------- | ----- |
| Electricidad | Real (`statistics`) si `DATA_SOURCE=database`; sintético en `mock` | No aplica | 0,20 €/kWh |
| Iluminación | Sintético determinista | Real si hay contadores; sintético si no | 0,20 €/kWh |

- **Solo lectura**: el backend únicamente ejecuta `SELECT` contra la base de datos del recorder.
- **Fermín Caballero** se obtiene como `Cuadro General − Módulo A − Módulo B`.
- Los cuadros de planta y el CPD son submedidas **parciales**: la web muestra siempre la cobertura y el importe no desglosado.
- Las fechas reales de Electricidad empiezan el **2023-12-22**.

## Puesta en marcha rápida

```bash
# 1) Backend -> http://127.0.0.1:8010
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
cp .env.example .env          # mock por defecto; pon DATA_SOURCE=database para datos reales
.venv/bin/uvicorn app.main:app --reload --port 8010

# 2) Frontend -> http://localhost:5174
cd frontend
npm install
npm run dev
```

Para leer la base de datos real instala también el extra de base de datos y rellena los valores `DB_*`:

```bash
cd backend
.venv/bin/python -m pip install -e ".[database]"
```

## Pruebas

```bash
cd backend && .venv/bin/python -m unittest discover -s tests -t . -v
cd frontend && npm run typecheck && npm run test:run && npm run build
```

Los tests del backend fuerzan `DATA_SOURCE=mock` y no tocan la base de datos real.

## Puertos

| Servicio | Puerto | Notas |
| -------- | ------ | ----- |
| Backend | `8010` | Distinto del proyecto original para poder convivir. |
| Frontend | `5174` | Distinto del proyecto original. |
| Docker | `8080` | nginx sirve la SPA y redirige `/api` al backend. |

## Despliegue

```bash
cd deploy
cp .env.example .env
docker compose up -d --build
# http://localhost:8080
```

Detalle en [`deploy/README.md`](deploy/README.md).

## Estructura

```text
backend/
  app/
    api/          Rutas HTTP (Electricidad, Iluminación y metadatos)
    core/         Configuración, catálogo de edificios y mapa eléctrico
    db/           Consultas SELECT y carga de series del recorder
    schemas/      Contratos de respuesta
    services/     Agregación, comparativas y modelo sintético
  tests/          Pruebas con unittest
frontend/
  src/app/
    api/          Cliente HTTP
    components/   Cabecera, UI reutilizable y gráficas
    context/      Periodo global de Iluminación
    hooks/        Consultas con TanStack Query
    lib/          Fechas, formato, CSV, paletas y estado de la URL
    pages/        Página principal
    types/        Tipos TypeScript
docs/             Documentación
```

## Documentación

- [Puesta en marcha](docs/puesta-en-marcha.md)
- [Arquitectura](docs/arquitectura.md)
- [Backend](docs/backend.md)
- [Frontend](docs/frontend.md)
- [Datos](docs/datos.md)
- [Estadísticos](docs/estadisticos.md)
- [Componentes](docs/componentes.md)
- [Gráficas](docs/graficas.md)
- [Backlog](docs/backlog.md)
