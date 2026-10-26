from fastapi import APIRouter

from app.core.buildings import BUILDINGS
from app.schemas.meta import BuildingRef, MetaResponse

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/buildings", response_model=MetaResponse)
def get_meta() -> MetaResponse:
    """Buildings used to populate the chart selectors."""
    return MetaResponse(
        buildings=[BuildingRef(id=building.id, label=building.label) for building in BUILDINGS]
    )
