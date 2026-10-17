from fastapi import APIRouter

from app.core.energy_map import (
    BUILDINGS,
    BUILDINGS_AREA_M2,
    BUILDINGS_LIGHTING_KW,
    SPACES,
)
from app.schemas.meta import BuildingRef, MetaResponse, SpaceRef

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/buildings", response_model=MetaResponse)
def get_meta() -> MetaResponse:
    """Buildings and metered spaces, used to populate the chart selectors."""
    return MetaResponse(
        buildings=[
            BuildingRef(
                id=b.id,
                label=b.label,
                max_capacity=b.max_capacity,
                area_m2=BUILDINGS_AREA_M2[b.id],
                lighting_kw=BUILDINGS_LIGHTING_KW[b.id],
                setpoint_c=b.setpoint_c,
            )
            for b in BUILDINGS
        ],
        spaces=[
            SpaceRef(
                id=s.id,
                label=s.label,
                building_id=s.building_id,
                kind=s.kind,
                area_m2=s.area_m2,
                lighting_kw=s.lighting_kw,
                has_valve=s.has_valve,
            )
            for s in SPACES
        ],
    )
