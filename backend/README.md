# Backend · Smart ESI Stats

API FastAPI para las pestañas **Electricidad** e **Iluminación**.

- **Electricidad** lee contadores reales del *recorder* de Home Assistant cuando `DATA_SOURCE=database`; en `mock` genera datos sintéticos.
- **Iluminación** usa un modelo determinista para el consumo y, si hay datos, la ocupación real de los contadores de personas.
- Todas las consultas a la base de datos son **`SELECT`**.

## Arranque

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"   # ".[database]" para leer la BD real
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8010
```

- API: <http://127.0.0.1:8010>
- Swagger: <http://127.0.0.1:8010/docs>

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -t . -v
```

`tests/__init__.py` fuerza `DATA_SOURCE=mock`: las pruebas no tocan la base de datos real.

## Documentación

- [Backend](../docs/backend.md)
- [Arquitectura](../docs/arquitectura.md)
- [Datos](../docs/datos.md)
