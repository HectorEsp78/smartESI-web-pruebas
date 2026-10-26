"""Response model for the building metadata endpoint."""

from pydantic import BaseModel


class BuildingRef(BaseModel):
    id: str
    label: str


class MetaResponse(BaseModel):
    buildings: list[BuildingRef]
