from fastapi import APIRouter, HTTPException, Query, status

from app.core.energy_map import BUILDINGS_BY_ID
from app.schemas.decisions import DecisionRange, DecisionsResponse
from app.services import decisions_service
from app.services.energy_service import ALL_BUILDINGS

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get("/opportunities", response_model=DecisionsResponse)
def get_opportunities(
    range_: DecisionRange = Query("month", alias="range"),
    building: str = ALL_BUILDINGS,
) -> DecisionsResponse:
    if building not in (None, "", ALL_BUILDINGS) and building not in BUILDINGS_BY_ID:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown building '{building}'",
        )
    return decisions_service.build_opportunities(range_, building)
