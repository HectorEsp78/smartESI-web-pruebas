import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api import electricity, environment, lighting, maintenance, meta, weather
from app.core.config import settings
from app.schemas.health import HealthLiveResponse, HealthReadyResponse

logger = logging.getLogger(__name__)


def _service_version() -> str:
    return os.getenv("APP_VERSION", "dev")


def _trusted_hosts() -> list[str]:
    trusted = {"localhost", "127.0.0.1", "::1"}
    if not settings.is_production:
        # Host names used by the HTTP test clients.
        trusted |= {"testserver", "test"}
    for origin in settings.cors_allow_origins:
        host = urlparse(origin).hostname
        if host:
            trusted.add(host)
    return sorted(trusted)


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    # Close the pooled connections when running against the recorder DB.
    if settings.DATA_SOURCE == "database":
        from app.db.session import engine

        await engine.dispose()


app = FastAPI(
    title="Smart ESI Stats API",
    description=(
        "Read-only API of the Smart ESI statistics module: electricity, lighting, "
        "room environment, weather station and device maintenance."
    ),
    lifespan=_lifespan,
)

# The API is public and read-only: it uses no cookies and only answers GET.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["GET"],
    allow_headers=["Accept"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_trusted_hosts())

app.include_router(electricity.router, prefix="/api/v1")
app.include_router(environment.router, prefix="/api/v1")
app.include_router(lighting.router, prefix="/api/v1")
app.include_router(maintenance.router, prefix="/api/v1")
app.include_router(meta.router, prefix="/api/v1")
app.include_router(weather.router, prefix="/api/v1")


@app.get("/")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Smart ESI Stats API. Documentation at /docs.",
    }


@app.get("/health/live", response_model=HealthLiveResponse)
async def health_live() -> HealthLiveResponse:
    return HealthLiveResponse(version=_service_version(), data_source=settings.DATA_SOURCE)


@app.get(
    "/health/ready",
    response_model=HealthReadyResponse,
    responses={503: {"model": HealthReadyResponse}},
)
async def health_ready() -> HealthReadyResponse | JSONResponse:
    """Readiness probe: in database mode it really pings the recorder DB."""
    if settings.DATA_SOURCE != "database":
        return HealthReadyResponse(status="ok", checks={"data_source": "ok"})

    try:
        from sqlalchemy import text

        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database readiness check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "checks": {"data_source": "fail"}},
        )

    return HealthReadyResponse(status="ok", checks={"data_source": "ok"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Los parámetros de la petición no son válidos."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Keep the details out of the response, but never lose them.
    logger.error(
        "Unhandled error in %s %s", request.method, request.url.path, exc_info=exc
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor."},
    )
