"""Response models for the metadata endpoint (buildings and spaces)."""

from pydantic import BaseModel


class BuildingRef(BaseModel):
    id: str
    label: str
    max_capacity: int
    area_m2: float
    lighting_kw: float
    setpoint_c: float


class SpaceRef(BaseModel):
    id: str
    label: str
    building_id: str
    kind: str
    area_m2: float
    lighting_kw: float
    has_valve: bool


class MetaResponse(BaseModel):
    buildings: list[BuildingRef]
    spaces: list[SpaceRef]
