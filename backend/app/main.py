import os
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api import climate, correlation, decisions, energy, lighting, meta
from app.core.config import settings
from app.schemas.health import HealthLiveResponse, HealthReadyResponse

SERVICE_NAME = "smartesi-stats-backend"


def _service_version() -> str:
    return os.getenv("APP_VERSION", "dev")


def _trusted_hosts() -> list[str]:
    trusted = {"localhost", "127.0.0.1", "::1", "testserver", "test"}
    for origin in settings.cors_allow_origins:
        host = urlparse(origin).hostname
        if host:
            trusted.add(host)
    return sorted(trusted)


app = FastAPI(
    title="Smart ESI Stats API",
    description=(
        "Backend API for the Smart ESI statistics module (new charts prototype). "
        "Serves energy-consumption and occupancy/air-quality statistics."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_trusted_hosts())

app.include_router(energy.router, prefix="/api/v1")
app.include_router(lighting.router, prefix="/api/v1")
app.include_router(climate.router, prefix="/api/v1")
app.include_router(decisions.router, prefix="/api/v1")
app.include_router(correlation.router, prefix="/api/v1")
app.include_router(meta.router, prefix="/api/v1")


@app.get("/")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Smart ESI Stats API. Documentation at /docs.",
    }


@app.get("/health/live", response_model=HealthLiveResponse)
async def health_live() -> HealthLiveResponse:
    return HealthLiveResponse(version=_service_version(), data_source=settings.DATA_SOURCE)


@app.get("/health/ready", response_model=HealthReadyResponse)
async def health_ready() -> HealthReadyResponse:
    # In mock mode the service is always ready. When DATA_SOURCE=database this
    # should run `SELECT 1` against the recorder DB and report "degraded" on failure.
    return HealthReadyResponse(status="ok", checks={"data_source": "ok"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Validation failed"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
