from typing import Literal

from pydantic import BaseModel, Field


class HealthLiveResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["smartesi-stats-backend"] = "smartesi-stats-backend"
    version: str = Field(min_length=1)
    data_source: Literal["mock", "database"]


class HealthReadyResponse(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, Literal["ok", "fail"]]
