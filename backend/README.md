# Backend · Smart ESI Stats

API FastAPI que sirve las estadísticas (consumo energético, consumo por edificio/espacio y cruce
ocupación–calidad del aire). Con `DATA_SOURCE=mock` (por defecto) no necesita base de datos: genera
datos sintéticos de forma determinista.

## Arranque

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8010
```

- API: http://127.0.0.1:8010
- Swagger: http://127.0.0.1:8010/docs

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Documentación

Consulta [`../docs/backend.md`](../docs/backend.md) (módulos, endpoints y migración a la base de
datos real) y [`../docs/arquitectura.md`](../docs/arquitectura.md).
