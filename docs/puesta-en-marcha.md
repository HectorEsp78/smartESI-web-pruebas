# Puesta en marcha

## Requisitos

- **Python 3.10+** (probado con 3.14).
- **Node.js 18+** y npm (probado con Node 22).
- No se necesita VPN ni base de datos: el backend genera datos sintéticos.

## 1. Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[test]"
cp .env.example .env          # opcional: los valores por defecto ya funcionan
.venv/bin/uvicorn app.main:app --reload --port 8010
```

- API: **http://127.0.0.1:8010**
- Documentación interactiva (Swagger): **http://127.0.0.1:8010/docs**
- Comprobación rápida: `curl http://127.0.0.1:8010/health/live`

Para ejecutar los tests:

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v
```

## 2. Frontend (React + Vite)

En **otra terminal**:

```bash
cd frontend
npm install
npm run dev
```

- Página: **http://localhost:5174/**
- El servidor de desarrollo redirige `/api/*` al backend (`http://127.0.0.1:8010`) gracias al
  proxy definido en [`vite.config.ts`](../frontend/vite.config.ts). No hay que configurar nada.

Otros comandos del frontend:

```bash
npm run typecheck      # comprobación de tipos
npm run test:run       # tests una pasada
npm run build          # build de producción -> dist/
npm run preview        # sirve el build
```

## Puertos

| Servicio | Puerto | Notas |
| -------- | ------ | ----- |
| Backend | `8010` | Distinto del original (8000) para poder convivir. |
| Frontend | `5174` | Distinto del original (5173) para poder convivir. |

Si cambias el puerto del backend, actualiza el `proxy` en
[`frontend/vite.config.ts`](../frontend/vite.config.ts) (y el `CORS_ALLOW_ORIGINS` del backend si
cambias el del frontend).

## Orden de arranque

1. Backend (debe estar escuchando en `8010`).
2. Frontend (`npm run dev`).

Si arrancas solo el frontend, las gráficas mostrarán su estado de error con un botón
**Reintentar**.

## Resolución de problemas

| Síntoma | Causa probable | Solución |
| ------- | -------------- | -------- |
| Las gráficas muestran "No se pudieron cargar los datos" | El backend no está arrancado o está en otro puerto | Arranca `uvicorn` en `8010` y pulsa *Reintentar*. |
| `EADDRINUSE` en `8010` o `5174` | Ya hay algo usando ese puerto | Libera el puerto o cambia el número (y el proxy). |
| Error de CORS en la consola del navegador | Frontend en un puerto/origen distinto | Añade el origen a `CORS_ALLOW_ORIGINS` en `backend/.env`. |
| Las tipografías se ven distintas | Sin acceso a `fonts.googleapis.com` | Es una dependencia externa; el diseño usa Manrope/Montserrat/Source Sans 3 con alternativas del sistema. |
| `No module named 'app'` | Ejecutas `uvicorn` desde otro directorio | Lánzalo desde `backend/` (o usa `--app-dir backend`). |
