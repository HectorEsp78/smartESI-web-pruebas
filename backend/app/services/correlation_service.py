"""Business logic for the "occupancy vs. air quality" data-crossing chart.

Returns paired, aggregated points (occupancy, CO₂, temperature, humidity) plus a
few summary statistics (Pearson correlation, linear regression, and the share of
time the air quality is good/moderate/poor) that are useful for decision-making.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.cache import TTLCache
from app.core.clock import local_now
from app.core.config import settings
from app.core.energy_map import BUILDINGS, BUILDINGS_BY_ID, BuildingConfig
from app.schemas.correlation import (
    CorrelationPoint,
    CorrelationRange,
    CorrelationStats,
    OccupancyAirQualityResponse,
)
from app.services import mock_data, stats

# Thresholds aligned with the main Smart ESI project (ppm).
CO2_GOOD_MAX = 800.0
CO2_MODERATE_MAX = 1200.0

ALL_BUILDINGS = "all"

_STEP_HOURS: dict[CorrelationRange, int] = {
    "day": 1,
    "week": 3,
    "month": 12,
    "year": 24,
}

_SPAN_HOURS: dict[CorrelationRange, int] = {
    "day": 24,
    "week": 7 * 24,
    "month": 30 * 24,
    "year": 365 * 24,
}

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS)


def _floor_hour(value: datetime) -> datetime:
    return value.replace(minute=0, second=0, microsecond=0)


def _scope(building_id: str | None) -> list[BuildingConfig]:
    if building_id in (None, "", ALL_BUILDINGS):
        return list(BUILDINGS)
    building = BUILDINGS_BY_ID.get(building_id)
    return [building] if building else []


def _regression(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Return (r, slope, intercept) of the least-squares fit of ys on xs."""
    fit = stats.least_squares(xs, ys)
    return fit.r, fit.slope, fit.intercept


def build_occupancy_air_quality(
    range_: CorrelationRange, building_id: str
) -> OccupancyAirQualityResponse:
    cache_key = ("occupancy-air-quality", range_, building_id)

    def _compute() -> OccupancyAirQualityResponse:
        now = local_now()
        step = _STEP_HOURS[range_]
        end = _floor_hour(now) + timedelta(hours=1)
        start = end - timedelta(hours=_SPAN_HOURS[range_])
        scope = _scope(building_id)
        capacity_total = sum(building.max_capacity for building in scope)

        points: list[CorrelationPoint] = []
        cursor = start
        while cursor < end:
            bucket_end = min(cursor + timedelta(hours=step), end)

            occ_acc = 0.0
            co2_acc = 0.0
            temp_acc = 0.0
            hum_acc = 0.0
            hours = 0

            hour_cursor = cursor
            while hour_cursor < bucket_end:
                occ_hour = 0
                co2_num = 0.0
                temp_num = 0.0
                hum_num = 0.0
                weight_sum = 0.0
                for building in scope:
                    occupancy = mock_data.hour_occupancy(building, hour_cursor)
                    occ_hour += occupancy
                    weight = occupancy + 1.0
                    co2_num += mock_data.hour_co2(building, occupancy, hour_cursor) * weight
                    temp_num += mock_data.hour_temperature(building, occupancy, hour_cursor) * weight
                    hum_num += mock_data.hour_humidity(building, occupancy, hour_cursor) * weight
                    weight_sum += weight

                occ_acc += occ_hour
                co2_acc += co2_num / weight_sum
                temp_acc += temp_num / weight_sum
                hum_acc += hum_num / weight_sum
                hours += 1
                hour_cursor += timedelta(hours=1)

            hours = max(hours, 1)
            occupancy_avg = occ_acc / hours
            occupancy_pct = (occupancy_avg / capacity_total * 100) if capacity_total else 0.0

            points.append(
                CorrelationPoint(
                    timestamp=cursor,
                    occupancy=round(occupancy_avg),
                    capacity=capacity_total,
                    occupancy_pct=round(occupancy_pct, 1),
                    co2=round(co2_acc / hours, 1),
                    temperature=round(temp_acc / hours, 1),
                    humidity=round(hum_acc / hours, 1),
                )
            )

            cursor = bucket_end

        xs = [point.occupancy for point in points]
        ys = [point.co2 for point in points]
        r, slope, intercept = _regression([float(x) for x in xs], ys)

        sample_size = len(points)
        avg_occupancy = sum(xs) / sample_size if sample_size else 0.0
        avg_pct = (
            sum(point.occupancy_pct for point in points) / sample_size if sample_size else 0.0
        )
        avg_co2 = sum(ys) / sample_size if sample_size else 0.0
        max_co2 = max(ys) if ys else 0.0

        good = sum(1 for value in ys if value < CO2_GOOD_MAX)
        moderate = sum(1 for value in ys if CO2_GOOD_MAX <= value <= CO2_MODERATE_MAX)
        poor = sum(1 for value in ys if value > CO2_MODERATE_MAX)

        def _pct(count: int) -> float:
            return round(count / sample_size * 100, 1) if sample_size else 0.0

        stats = CorrelationStats(
            sample_size=sample_size,
            pearson_r=round(r, 3),
            slope=round(slope, 4),
            intercept=round(intercept, 1),
            avg_occupancy=round(avg_occupancy, 1),
            avg_occupancy_pct=round(avg_pct, 1),
            avg_co2=round(avg_co2, 1),
            max_co2=round(max_co2, 1),
            good_pct=_pct(good),
            moderate_pct=_pct(moderate),
            poor_pct=_pct(poor),
        )

        return OccupancyAirQualityResponse(
            range=range_,
            building_id=building_id or ALL_BUILDINGS,
            points=points,
            stats=stats,
        )

    return _cache.get_or_set(cache_key, _compute)


def clear_cache() -> None:
    _cache.clear()
