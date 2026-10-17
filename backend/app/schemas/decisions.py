"""Response models for the decision-support endpoint (savings opportunities)."""

from typing import Literal

from pydantic import BaseModel

DecisionRange = Literal["day", "week", "month", "year"]


class Opportunity(BaseModel):
    id: str
    category: str  # "iluminacion" | "calefaccion" | "electricidad" | "tendencia"
    title: str
    description: str
    evidence: str
    metric_value: float
    metric_unit: str
    savings_kwh_year: float
    savings_eur_year: float
    priority: str  # "alta" | "media" | "baja"


class DecisionsResponse(BaseModel):
    """Ranking de oportunidades de ahorro en luz y gas, con su € estimado/año."""

    range: DecisionRange
    building_id: str
    total_savings_eur_year: float
    items: list[Opportunity]
