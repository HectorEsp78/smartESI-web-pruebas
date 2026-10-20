# Despliegue (Docker Compose)

Contenedores para publicar el prototipo en un servidor de la UCLM (o en cualquier máquina con
Docker). El frontend se sirve con **nginx**, que además hace de *reverse proxy* de `/api` hacia el
backend; así el navegador usa el mismo origen y no hace falta configurar CORS ni `VITE_API_BASE_URL`.

```text
navegador ──► nginx :8080 ──/api/──► FastAPI :8010 ──SELECT──► MariaDB (recorder de HA)
```

## Arranque

```bash
cd deploy
cp .env.example .env
# Edita .env: puertos, CORS y credenciales DB_* (o DATA_SOURCE=mock para probar sin BD)
docker compose up -d --build
```

- Web: <http://localhost:8080>
- API directa (opcional): <http://localhost:8010/docs>
- Estado: `curl http://localhost:8080/health/ready` (en modo `database` hace `SELECT 1` real)

Para parar: `docker compose down`. Si cambias código: `docker compose up -d --build`.

## Variables

Las variables del backend se leen de `deploy/.env` (el mismo nombre que en
[`backend/.env.example`](../backend/.env.example)). Las principales:

| Variable | Por defecto | Uso |
| -------- | ----------- | --- |
| `FRONTEND_PORT` | `8080` | Puerto público de nginx. |
| `BACKEND_PORT` | `8010` | Puerto publicado del backend (para depurar; la web no lo necesita). |
| `CORS_ALLOW_ORIGINS` | `http://localhost:8080` | Origen exacto con el que se abre la web. |
| `DATA_SOURCE` | `database` | `mock` o `database`. |
| `DB_*` | — | Conexión a MariaDB; requiere VPN de la UCLM si la BD es interna. |
| `USE_STATISTICS_FOR_STATES` | `true` | Usa `statistics` para temperaturas/humedad (más rápido en `year`). |

> Con `DATA_SOURCE=mock` no hace falta base de datos: sirve para comprobar que la imagen y el
> *proxy* funcionan antes de conectarse a la red interna.

## Detalles

- **Backend**: imagen `python:3.12-slim`, instala el extra `.[database]` y corre como usuario sin
  privilegios. La imagen define un `HEALTHCHECK` con `/health/live`; en Compose se sustituye por
  `/health/ready`, que comprueba la BD cuando `DATA_SOURCE=database`.
- **Frontend**: build multi-etapa (`node:22` → `nginx:1.27`). Las rutas de la SPA caen en
  `index.html` y los assets con hash se cachean un año.
- **Proxy**: `frontend/nginx.conf` resuelve el contenedor `backend` con el DNS de Docker, así nginx
  puede arrancar antes que la API.
- **TLS**: para producción real, pon nginx detrás del *reverse proxy* corporativo o añade un
  certificado en `frontend/nginx.conf`; el prototipo no gestiona certificados.
- **Secretos**: `deploy/.env` está en `.gitignore`; no lo subas al repositorio.

## Comprobaciones

```bash
docker compose config          # valida el YAML y muestra las variables resueltas
docker compose ps              # estado y healthchecks
docker compose logs -f backend
```
