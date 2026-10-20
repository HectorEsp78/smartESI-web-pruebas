"""Decision-support service: turns the data crossings into ranked opportunities.

It reuses the other services (energy, lighting, climate) to build a short list of
concrete, money-quantified actions, so the dashboard can answer "where do I spend
less and how much do I save?" instead of just showing raw series:

- lights left on while the building is empty;
- heating rooms that are empty;
- wasted base load outside working hours;
- spaces far above the average consumption per m²;
- a growing year-on-year consumption trend.
"""

from __future__ import annotations

from app.core.config import settings
from app.schemas.decisions import DecisionRange, DecisionsResponse, Opportunity
from app.services import climate_service, energy_service, lighting_service

DAYS_BY_RANGE: dict[DecisionRange, int] = {"day": 1, "week": 7, "month": 30, "year": 365}
# Conservative share of the base load that is assumed addressable.
_BASE_LOAD_SAVING_FACTOR = 0.10


def _priority(savings_eur_year: float) -> str:
    if savings_eur_year >= 1000:
        return "alta"
    if savings_eur_year >= 300:
        return "media"
    return "baja"


async def build_opportunities(range_: DecisionRange, building_id: str) -> DecisionsResponse:
    days = DAYS_BY_RANGE[range_]
    annualization = 365.0 / days
    items: list[Opportunity] = []

    # 1. Luces encendidas sin ocupación --------------------------------------
    waste = await lighting_service.build_waste(range_, building_id)
    if waste.annualized_cost_eur > 0:
        items.append(
            Opportunity(
                id="luces-sin-ocupacion",
                category="iluminacion",
                title="Apagar luminarias en espacios vacíos",
                description=(
                    "Hay luminarias encendidas fuera de horario y en espacios sin "
                    "ocupación. Una programación por horarios/ocupación las apagaría."
                ),
                evidence=(
                    f"{waste.waste_lighting:.0f} kWh ({waste.waste_share * 100:.0f} % del "
                    f"consumo de luminarias) con los espacios vacíos."
                ),
                metric_value=round(waste.waste_lighting, 1),
                metric_unit="kWh",
                savings_kwh_year=round(waste.waste_lighting * annualization, 1),
                savings_eur_year=waste.annualized_cost_eur,
                priority=_priority(waste.annualized_cost_eur),
            )
        )

    # 2. Calefacción de aulas vacías -----------------------------------------
    empty = await climate_service.build_empty_spaces(range_, building_id)
    if empty.total_annualized_cost_eur > 0:
        items.append(
            Opportunity(
                id="calefaccion-aulas-vacias",
                category="calefaccion",
                title="No calentar espacios sin ocupación",
                description=(
                    "Algunas electroválvulas calientan aulas vacías (noches, fines de "
                    "semana o fuera de horario). Revisar el control y cerrarlas."
                ),
                evidence=(
                    f"{empty.total_gas_estimate:.0f} kWh de gas y "
                    f"{empty.total_heated_unoccupied_hours:.0f} h de válvula abierta sin "
                    "ocupación."
                ),
                metric_value=round(empty.total_gas_estimate, 1),
                metric_unit="kWh gas",
                savings_kwh_year=round(empty.total_gas_estimate * annualization, 1),
                savings_eur_year=empty.total_annualized_cost_eur,
                priority=_priority(empty.total_annualized_cost_eur),
            )
        )

    # 3. Carga base fuera de horario -----------------------------------------
    breakdown = await energy_service.build_breakdown(range_, building_id)
    if breakdown.base_total > 0:
        base_savings = breakdown.base_total * _BASE_LOAD_SAVING_FACTOR
        eur = base_savings * annualization * settings.ENERGY_PRICE_EUR_PER_KWH
        items.append(
            Opportunity(
                id="carga-base-fuera-de-horario",
                category="electricidad",
                title="Reducir la carga base fuera de horario",
                description=(
                    "El consumo nocturno/fin de semana representa una parte notable del "
                    "total. Equipos en espera o climatización fuera de horario son candidatos."
                ),
                evidence=(
                    f"{breakdown.base_total:.0f} kWh fuera de horario "
                    f"({breakdown.base_share * 100:.0f} % del total)."
                ),
                metric_value=round(breakdown.base_total, 1),
                metric_unit="kWh",
                savings_kwh_year=round(base_savings * annualization, 1),
                savings_eur_year=round(eur, 2),
                priority=_priority(eur),
            )
        )

    # 4. Espacios con consumo por m² por encima de la media -------------------
    efficiency = await energy_service.build_efficiency(range_)
    worst = next(
        (
            space
            for space in efficiency.spaces
            if space.kwh_per_m2 > efficiency.avg_kwh_per_m2
        ),
        None,
    )
    if worst is not None:
        extra_kwh = (worst.kwh_per_m2 - efficiency.avg_kwh_per_m2) * worst.area_m2
        eur = extra_kwh * annualization * settings.ENERGY_PRICE_EUR_PER_KWH
        if eur > 0:
            items.append(
                Opportunity(
                    id="espacio-ineficiente",
                    category="electricidad",
                    title=f"Revisar {worst.label} (consumo por m² alto)",
                    description=(
                        "Un espacio consume mucho más por metro cuadrado que la media. "
                        "Puede haber equipos antiguos o mal uso."
                    ),
                    evidence=(
                        f"{worst.kwh_per_m2:.1f} kWh/m² frente a la media de "
                        f"{efficiency.avg_kwh_per_m2:.1f} kWh/m²."
                    ),
                    metric_value=round(worst.kwh_per_m2, 2),
                    metric_unit="kWh/m²",
                    savings_kwh_year=round(extra_kwh * annualization, 1),
                    savings_eur_year=round(eur, 2),
                    priority=_priority(eur),
                )
            )

    # 5. Tendencia interanual de la electricidad ------------------------------
    compare = await energy_service.build_compare("year", building_id, "kwh")
    if compare.previous_total > 0 and compare.delta_pct > 0:
        increase_kwh = compare.current_total - compare.previous_total
        eur = increase_kwh * settings.ENERGY_PRICE_EUR_PER_KWH
        items.append(
            Opportunity(
                id="tendencia-electrica",
                category="tendencia",
                title="Consumo eléctrico al alza",
                description=(
                    "El consumo de los últimos 12 meses supera al del año anterior. "
                    "Conviene revisar qué espacios crecen."
                ),
                evidence=(
                    f"{compare.delta_pct:+.0f} % interanual "
                    f"({compare.current_total:.0f} vs {compare.previous_total:.0f} kWh)."
                ),
                metric_value=round(compare.delta_pct, 1),
                metric_unit="% interanual",
                savings_kwh_year=round(increase_kwh, 1),
                savings_eur_year=round(eur, 2),
                priority=_priority(eur),
            )
        )

    items.sort(key=lambda item: item.savings_eur_year, reverse=True)
    total = sum(item.savings_eur_year for item in items if item.category != "tendencia")
    return DecisionsResponse(
        range=range_,
        building_id=building_id,
        total_savings_eur_year=round(total, 2),
        items=items,
    )


def clear_cache() -> None:
    energy_service.clear_cache()
    lighting_service.clear_cache()
    climate_service.clear_cache()
