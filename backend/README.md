# Backend · Smart ESI Stats

API FastAPI que sirve las estadísticas (consumo energético, consumo por edificio/espacio y cruce
ocupación–calidad del aire). Con `DATA_SOURCE=mock` (por defecto) no necesita base de datos: genera
datos sintéticos de forma determinista. Con `DATA_SOURCE=database` lee la base de datos real del
*recorder* de Home Assistant **solo con `SELECT`** (ya implementado para Electricidad,
Climatización/gas, Ocupación y CO₂/aire; la iluminación sigue en mock).

## Arranque

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"   # ".[database]" para leer la BD real
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8010
```

- API: http://127.0.0.1:8010
- Swagger: http://127.0.0.1:8010/docs

Para leer la BD real: instala `.[database]`, pon `DATA_SOURCE=database` y rellena las variables
`DB_*` en `.env`. Detalle en [`../docs/backend.md`](../docs/backend.md).

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -t . -v
```

> El `-t .` hace que `tests/__init__.py` fuerce `DATA_SOURCE=mock`, así los tests no tocan la BD real.

## Documentación

Consulta [`../docs/backend.md`](../docs/backend.md) (módulos, endpoints y migración a la base de
datos real) y [`../docs/arquitectura.md`](../docs/arquitectura.md).
