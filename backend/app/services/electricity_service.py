"""Business logic for the new Electricity tab.

The tab works with explicit dates (``start``/``end`` inclusive) and a
building/sector scope. Unlike the older range-based endpoints, it does not use
"last 24 hours" windows: the user chooses the exact period and the bucket size.

Data sources:

- ``DATA_SOURCE=database``: Home Assistant recorder statistics, always read-only.
- ``DATA_SOURCE=mock``: deterministic synthetic data, used by tests and local
  development without VPN/database access.

Fermín Caballero does not have a single meter. Its total is derived as
``Cuadro General - Módulo A - Módulo B``. The floor panels and the CPD are
partial submeters, so the response exposes ``sectors_total``,
``unmetered_total`` and ``sector_coverage`` instead of pretending that the
panels are the whole building.
"""

from __future__ import annotations

import asyncio
import bisect
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Awaitable, Callable, Hashable

from app.core.cache import TTLCache
from app.core.clock import local_tz
from app.core.config import settings
from app.core.electricity_map import (
    ELECTRICITY_ALL,
    ELECTRICITY_BUILDINGS,
    ELECTRICITY_BUILDINGS_BY_ID,
    ELECTRICITY_DATA_START,
    ELECTRICITY_SECTORS,
    ELECTRICITY_SECTORS_BY_BUILDING,
    ELECTRICITY_SECTORS_BY_ID,
    SITE_ELECTRICITY_STATISTIC,
)
from app.core.energy_map import BUILDINGS_BY_ID
from app.schemas.electricity import (
    ElectricityBuildingStats,
    ElectricityComparePoint,
    ElectricityCompareResponse,
    ElectricityGranularity,
    ElectricityMetric,
    ElectricityPoint,
    ElectricityResponse,
    ElectricitySectorStats,
    ElectricityStats,
)
from app.services import mock_data

METRICS: tuple[ElectricityMetric, ...] = ("kwh", "cost")
GRANULARITIES: tuple[ElectricityGranularity, ...] = ("day", "week", "month", "year")
UNIT_BY_METRIC: dict[ElectricityMetric, str] = {"kwh": "kWh", "cost": "€"}
# Six years is enough for the available recorder data and keeps a single request
# from scanning an unbounded number of rows.
MAX_RANGE_DAYS = 366 * 6

# Mock mode: share of Fermín's consumption represented by each partial panel.
# The values sum to 0.30, mirroring the real coverage (~30 %) measured in the
# recorder database.
_MOCK_SECTOR_WEIGHTS: dict[str, float] = {
    "PB_D": 0.08,
    "P1_F": 0.05,
    "P1_G": 0.02,
    "P2_H": 0.04,
    "P2_I": 0.03,
    "P3_J": 0.01,
    "P3_K": 0.02,
    "CPD": 0.05,
}

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS)
_data_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS)


@dataclass(frozen=True)
class _Bucket:
    start: datetime
    end: datetime

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0


@dataclass
class _HourlySeries:
    """Sorted hourly values with prefix sums for fast bucket aggregation."""

    hours: list[datetime]
    values: list[float]
    prefix: list[float]

    @classmethod
    def from_mapping(cls, data: dict[datetime, float] | None) -> "_HourlySeries":
        if not data:
            return cls([], [], [0.0])
        items = sorted((hour, value) for hour, value in data.items())
        hours = [hour for hour, _ in items]
        values = [float(value) for _, value in items]
        prefix = [0.0]
        for value in values:
            prefix.append(prefix[-1] + value)
        return cls(hours, values, prefix)

    def _indices(self, start: datetime, end: datetime) -> tuple[int, int]:
        return bisect.bisect_left(self.hours, start), bisect.bisect_left(self.hours, end)

    def sum_between(self, start: datetime, end: datetime) -> float:
        first, last = self._indices(start, end)
        return self.prefix[last] - self.prefix[first]

    def closed_totals(self, start: datetime, end: datetime) -> tuple[float, int]:
        """Sum and count of closed-hour values in ``[start, end)``."""
        first, last = self._indices(start, end)
        total = 0.0
        count = 0
        for hour, value in zip(self.hours[first:last], self.values[first:last]):
            if _is_closed_hour(hour):
                total += value
                count += 1
        return total, count

    def has_values(self) -> bool:
        return bool(self.hours)


@dataclass
class _ElectricityData:
    site: dict[datetime, float]
    buildings: dict[str, dict[datetime, float]]
    sectors: dict[str, dict[datetime, float]]


async def _cached(
    cache: TTLCache, key: Hashable, factory: Callable[[], Awaitable[Any]]
) -> Any:
    hit = cache.get(key)
    if hit is not None:
        return hit
    value = await factory()
    cache.set(key, value)
    return value


def _convert(value_kwh: float, metric: ElectricityMetric) -> float:
    if metric == "cost":
        return value_kwh * settings.ENERGY_PRICE_EUR_PER_KWH
    return value_kwh


def _midnight(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=local_tz())


def _range_bounds(start: date, end: date) -> tuple[datetime, datetime]:
    """Local-aware ``[start 00:00, day after end 00:00)`` bounds."""
    return _midnight(start), _midnight(end + timedelta(days=1))


def _add_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _add_year(value: date) -> date:
    return date(value.year + 1, 1, 1)


def _build_buckets(
    start: date, end: date, granularity: ElectricityGranularity
) -> list[_Bucket]:
    """Calendar buckets clipped to the requested inclusive date range.

    - day: one bucket per calendar day.
    - week: Monday-Sunday buckets; the first/last bucket may be partial.
    - month: calendar months; the first/last month may be partial.
    - year: calendar years; the first/last year may be partial.
    """
    range_start, range_end = _range_bounds(start, end)
    buckets: list[_Bucket] = []

    def append(bucket_start: datetime, bucket_end: datetime) -> None:
        clipped_start = max(bucket_start, range_start)
        clipped_end = min(bucket_end, range_end)
        if clipped_start < clipped_end:
            buckets.append(_Bucket(clipped_start, clipped_end))

    if granularity == "day":
        cursor = start
        while cursor <= end:
            append(_midnight(cursor), _midnight(cursor + timedelta(days=1)))
            cursor += timedelta(days=1)
        return buckets

    if granularity == "week":
        cursor = start - timedelta(days=start.weekday())
        while cursor <= end:
            next_cursor = cursor + timedelta(days=7)
            append(_midnight(cursor), _midnight(next_cursor))
            cursor = next_cursor
        return buckets

    if granularity == "month":
        cursor = date(start.year, start.month, 1)
        while cursor <= end:
            next_cursor = _add_month(cursor)
            append(_midnight(cursor), _midnight(next_cursor))
            cursor = next_cursor
        return buckets

    cursor = date(start.year, 1, 1)
    while cursor <= end:
        next_cursor = _add_year(cursor)
        append(_midnight(cursor), _midnight(next_cursor))
        cursor = next_cursor
    return buckets


def _is_closed_hour(hour: datetime) -> bool:
    """Closed = weekend or outside the weekday 07:00-21:00 schedule."""
    local = hour.astimezone(local_tz())
    minutes = local.hour * 60 + local.minute
    return local.weekday() >= 5 or minutes < 7 * 60 or minutes >= 21 * 60


def _validate_range(start: date, end: date) -> None:
    if end < start:
        raise ValueError("La fecha final no puede ser anterior a la fecha inicial.")
    if (end - start).days > MAX_RANGE_DAYS:
        raise ValueError("El rango de fechas es demasiado amplio (máximo 6 años).")


def _validate_scope(building: str | None, sector: str | None) -> tuple[str | None, str | None]:
    """Return ``(building_id, sector_id)`` after validating the requested scope."""
    building_value = building or ELECTRICITY_ALL
    sector_value = sector or None

    if sector_value is not None:
        sector_config = ELECTRICITY_SECTORS_BY_ID.get(sector_value)
        if sector_config is None:
            raise ValueError(f"Sector desconocido: {sector_value}")
        if building_value not in (ELECTRICITY_ALL, sector_config.building_id):
            raise ValueError("El sector no pertenece al edificio seleccionado.")
        return sector_config.building_id, sector_config.id

    if building_value == ELECTRICITY_ALL:
        return None, None
    if building_value not in ELECTRICITY_BUILDINGS_BY_ID:
        raise ValueError(f"Edificio desconocido: {building_value}")
    return building_value, None


def _build_fermin_residual(
    site: dict[datetime, float],
    modulo_a: dict[datetime, float],
    modulo_b: dict[datetime, float],
) -> dict[datetime, float]:
    """Fermín = Cuadro General - Módulo A - Módulo B, hour by hour."""
    return {
        hour: max(0.0, site.get(hour, 0.0) - modulo_a.get(hour, 0.0) - modulo_b.get(hour, 0.0))
        for hour in site
    }


def _assemble_data(raw: dict[str, dict[datetime, float]]) -> _ElectricityData:
    site = raw.get("site", {})
    modulo_a = raw.get("ModuloA", {})
    modulo_b = raw.get("ModuloB", {})
    buildings = {
        "ModuloA": modulo_a,
        "ModuloB": modulo_b,
        "FerminCaballero": _build_fermin_residual(site, modulo_a, modulo_b),
    }
    sectors = {sector.id: raw.get(sector.id, {}) for sector in ELECTRICITY_SECTORS}
    return _ElectricityData(site=site, buildings=buildings, sectors=sectors)


def _iter_local_hours(start: datetime, end: datetime):
    """Yield local-aware hours between two aware datetimes (DST-safe)."""
    cursor = start.astimezone(timezone.utc)
    end_utc = end.astimezone(timezone.utc)
    while cursor < end_utc:
        yield cursor.astimezone(local_tz()).replace(minute=0, second=0, microsecond=0)
        cursor += timedelta(hours=1)


def _mock_data(start: datetime, end: datetime) -> _ElectricityData:
    """Deterministic synthetic series for the new Electricity tab."""
    raw: dict[str, dict[datetime, float]] = {
        "site": {},
        "ModuloA": {},
        "ModuloB": {},
        "FerminCaballero": {},
        **{sector.id: {} for sector in ELECTRICITY_SECTORS},
    }
    fermin_base = BUILDINGS_BY_ID["FerminCaballero"]
    modulo_b_base = BUILDINGS_BY_ID["ModuloB"]

    for hour in _iter_local_hours(start, end):
        modulo_b = mock_data.hour_energy_kwh(modulo_b_base, hour)
        modulo_a = modulo_b * 0.55
        fermin = mock_data.hour_energy_kwh(fermin_base, hour)
        site = modulo_a + modulo_b + fermin

        raw["ModuloA"][hour] = modulo_a
        raw["ModuloB"][hour] = modulo_b
        raw["FerminCaballero"][hour] = fermin
        raw["site"][hour] = site

        # Allocate exactly 30 % of Fermín's hourly load to the partial panels.
        weighted = {
            sector_id: weight
            * (1.0 + mock_data.stable_noise("elec-sector", sector_id, hour, amplitude=0.08))
            for sector_id, weight in _MOCK_SECTOR_WEIGHTS.items()
        }
        weight_total = sum(weighted.values())
        if weight_total > 0:
            for sector_id, weight in weighted.items():
                raw[sector_id][hour] = fermin * 0.30 * (weight / weight_total)

    return _assemble_data(raw)


async def _load_database_data(start: datetime, end: datetime) -> _ElectricityData:
    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import database_data
    from app.db.session import AsyncSessionLocal

    statistic_to_key: dict[str, str] = {SITE_ELECTRICITY_STATISTIC: "site"}
    statistic_to_key.update(
        {
            building.statistic_id: building.id
            for building in ELECTRICITY_BUILDINGS
            if building.statistic_id is not None
        }
    )
    statistic_to_key.update(
        {sector.statistic_id: sector.id for sector in ELECTRICITY_SECTORS}
    )

    async with AsyncSessionLocal() as session:
        raw = await database_data.load_hourly_statistics(
            session, statistic_to_key, start, end
        )
    return _assemble_data(raw)


async def _load_data(start: datetime, end: datetime) -> _ElectricityData:
    key = ("electricity-data", settings.DATA_SOURCE, start.isoformat(), end.isoformat())
    if settings.DATA_SOURCE != "database":
        return await _cached(_data_cache, key, lambda: _mock_data_async(start, end))
    return await _cached(_data_cache, key, lambda: _load_database_data(start, end))


async def _mock_data_async(start: datetime, end: datetime) -> _ElectricityData:
    # Kept async so both branches have the same cache factory signature.
    return _mock_data(start, end)


def _resolve_scope(
    data: _ElectricityData,
    building_id: str | None,
    sector_id: str | None,
) -> tuple[dict[datetime, float], str, str, str | None, str | None]:
    """Return ``(hourly, scope, label, building_id, sector_id)``."""
    if sector_id is not None:
        sector = ELECTRICITY_SECTORS_BY_ID[sector_id]
        building = ELECTRICITY_BUILDINGS_BY_ID[sector.building_id]
        return (
            data.sectors.get(sector.id, {}),
            sector.id,
            f"{sector.label} · {building.label}",
            sector.building_id,
            sector.id,
        )
    if building_id is None:
        return data.site, ELECTRICITY_ALL, "Todos los edificios", None, None
    building = ELECTRICITY_BUILDINGS_BY_ID[building_id]
    return data.buildings.get(building.id, {}), building.id, building.label, building.id, None


def _base_stats(
    series: _HourlySeries,
    buckets: list[_Bucket],
    metric: ElectricityMetric,
    range_start: datetime,
    range_end: datetime,
) -> tuple[ElectricityStats, float]:
    """Stats for a scope plus its raw closed-hour baseline (kWh/h)."""
    values = [_convert(series.sum_between(bucket.start, bucket.end), metric) for bucket in buckets]
    total = sum(values)
    average = total / len(values) if values else 0.0
    minimum = min(values) if values else 0.0
    maximum = max(values) if values else 0.0

    closed_total, closed_count = series.closed_totals(range_start, range_end)
    baseline_kwh_hour = closed_total / closed_count if closed_count else 0.0
    baseline_hourly = _convert(baseline_kwh_hour, metric)
    total_hours = sum(bucket.hours for bucket in buckets)
    baseline_total = baseline_hourly * total_hours

    return (
        ElectricityStats(
            total=round(total, 2),
            average=round(average, 2),
            minimum=round(minimum, 2),
            maximum=round(maximum, 2),
            baseline_hourly=round(baseline_hourly, 4),
            baseline_total=round(baseline_total, 2),
            buckets=len(buckets),
            unit=UNIT_BY_METRIC[metric],
        ),
        baseline_kwh_hour,
    )


def _building_stats(
    data: _ElectricityData,
    buckets: list[_Bucket],
    metric: ElectricityMetric,
    range_start: datetime,
    range_end: datetime,
) -> list[ElectricityBuildingStats]:
    site_series = _HourlySeries.from_mapping(data.site)
    site_kwh = site_series.sum_between(range_start, range_end)
    site_total_value = _convert(site_kwh, metric)

    result: list[ElectricityBuildingStats] = []
    for building in ELECTRICITY_BUILDINGS:
        series = _HourlySeries.from_mapping(data.buildings.get(building.id))
        values = [
            _convert(series.sum_between(bucket.start, bucket.end), metric) for bucket in buckets
        ]
        total = sum(values)
        closed_total, closed_count = series.closed_totals(range_start, range_end)
        baseline_kwh_hour = closed_total / closed_count if closed_count else 0.0
        baseline_total = _convert(baseline_kwh_hour, metric) * sum(
            bucket.hours for bucket in buckets
        )
        result.append(
            ElectricityBuildingStats(
                building_id=building.id,
                label=building.label,
                kind=building.kind,
                total=round(total, 2),
                average=round(total / len(values) if values else 0.0, 2),
                minimum=round(min(values) if values else 0.0, 2),
                maximum=round(max(values) if values else 0.0, 2),
                baseline_total=round(baseline_total, 2),
                share=round(total / site_total_value, 4) if site_total_value else 0.0,
                note=building.note,
                series=_series_points(series, buckets, metric, baseline_kwh_hour),
            )
        )
    return result


def _sector_stats(
    data: _ElectricityData,
    buckets: list[_Bucket],
    metric: ElectricityMetric,
    range_start: datetime,
    range_end: datetime,
) -> tuple[list[ElectricitySectorStats], float, float, float, float]:
    """Return ``(sectors, fermin_total, sectors_total, unmetered_total, coverage)``."""
    fermin_series = _HourlySeries.from_mapping(data.buildings.get("FerminCaballero"))
    fermin_kwh = fermin_series.sum_between(range_start, range_end)
    fermin_total = _convert(fermin_kwh, metric)

    result: list[ElectricitySectorStats] = []
    sectors_kwh = 0.0
    for sector in ELECTRICITY_SECTORS_BY_BUILDING["FerminCaballero"]:
        series = _HourlySeries.from_mapping(data.sectors.get(sector.id))
        has_data = sector.available and series.has_values()
        values = [
            _convert(series.sum_between(bucket.start, bucket.end), metric) for bucket in buckets
        ]
        total = sum(values)
        if has_data:
            sectors_kwh += series.sum_between(range_start, range_end)
        closed_total, closed_count = series.closed_totals(range_start, range_end)
        baseline_kwh_hour = closed_total / closed_count if closed_count else 0.0
        result.append(
            ElectricitySectorStats(
                sector_id=sector.id,
                label=sector.label,
                building_id=sector.building_id,
                building_label=ELECTRICITY_BUILDINGS_BY_ID[sector.building_id].label,
                floor=sector.floor,
                total=round(total, 2),
                average=round(total / len(values) if values else 0.0, 2),
                minimum=round(min(values) if values else 0.0, 2),
                maximum=round(max(values) if values else 0.0, 2),
                share_of_building=round(total / fermin_total, 4) if fermin_total else 0.0,
                has_data=has_data,
                note=sector.note,
                series=_series_points(series, buckets, metric, baseline_kwh_hour),
            )
        )

    sectors_total = _convert(sectors_kwh, metric)
    unmetered_total = max(0.0, fermin_total - sectors_total)
    coverage = sectors_total / fermin_total if fermin_total else 0.0
    return result, fermin_total, sectors_total, unmetered_total, coverage


def _series_points(
    series: _HourlySeries,
    buckets: list[_Bucket],
    metric: ElectricityMetric,
    baseline_kwh_hour: float,
) -> list[ElectricityPoint]:
    baseline_per_hour = _convert(baseline_kwh_hour, metric)
    return [
        ElectricityPoint(
            timestamp=bucket.start,
            value=round(_convert(series.sum_between(bucket.start, bucket.end), metric), 2),
            baseline=round(baseline_per_hour * bucket.hours, 2),
        )
        for bucket in buckets
    ]


async def build_electricity(
    start: date,
    end: date,
    granularity: ElectricityGranularity,
    metric: ElectricityMetric,
    building: str | None,
    sector: str | None,
) -> ElectricityResponse:
    _validate_range(start, end)
    building_id, sector_id = _validate_scope(building, sector)
    buckets = _build_buckets(start, end, granularity)
    range_start, range_end = _range_bounds(start, end)

    cache_key = (
        "electricity",
        start.isoformat(),
        end.isoformat(),
        granularity,
        metric,
        building_id,
        sector_id,
    )

    async def _compute() -> ElectricityResponse:
        data = await _load_data(range_start, range_end)
        hourly, scope, scope_label, resolved_building_id, resolved_sector_id = _resolve_scope(
            data, building_id, sector_id
        )
        series = _HourlySeries.from_mapping(hourly)
        stats, baseline_kwh_hour = _base_stats(
            series, buckets, metric, range_start, range_end
        )
        points = _series_points(series, buckets, metric, baseline_kwh_hour)

        site_total = _convert(
            _HourlySeries.from_mapping(data.site).sum_between(range_start, range_end),
            metric,
        )
        buildings = _building_stats(data, buckets, metric, range_start, range_end)
        sectors, fermin_total, sectors_total, unmetered_total, coverage = _sector_stats(
            data, buckets, metric, range_start, range_end
        )

        return ElectricityResponse(
            start=start,
            end=end,
            granularity=granularity,
            metric=metric,
            unit=UNIT_BY_METRIC[metric],
            scope=scope,
            scope_label=scope_label,
            building_id=resolved_building_id,
            sector_id=resolved_sector_id,
            series=points,
            stats=stats,
            buildings=buildings,
            sectors=sectors,
            site_total=round(site_total, 2),
            fermin_total=round(fermin_total, 2),
            sectors_total=round(sectors_total, 2),
            unmetered_total=round(unmetered_total, 2),
            sector_coverage=round(coverage, 4),
            data_start=ELECTRICITY_DATA_START,
        )

    return await _cached(_cache, cache_key, _compute)


async def build_electricity_compare(
    start_a: date,
    end_a: date,
    start_b: date,
    end_b: date,
    granularity: ElectricityGranularity,
    metric: ElectricityMetric,
    building: str | None,
    sector: str | None,
) -> ElectricityCompareResponse:
    _validate_range(start_a, end_a)
    _validate_range(start_b, end_b)
    building_id, sector_id = _validate_scope(building, sector)
    buckets_a = _build_buckets(start_a, end_a, granularity)
    buckets_b = _build_buckets(start_b, end_b, granularity)
    if len(buckets_a) != len(buckets_b):
        raise ValueError(
            "Los dos periodos deben tener el mismo número de intervalos. "
            "Ajusta las fechas o cambia la granularidad."
        )

    range_a_start, range_a_end = _range_bounds(start_a, end_a)
    range_b_start, range_b_end = _range_bounds(start_b, end_b)
    cache_key = (
        "electricity-compare",
        start_a.isoformat(),
        end_a.isoformat(),
        start_b.isoformat(),
        end_b.isoformat(),
        granularity,
        metric,
        building_id,
        sector_id,
    )

    async def _compute() -> ElectricityCompareResponse:
        data_a, data_b = await _load_data_pair(
            range_a_start, range_a_end, range_b_start, range_b_end
        )
        hourly_a, scope, scope_label, resolved_building_id, resolved_sector_id = _resolve_scope(
            data_a, building_id, sector_id
        )
        hourly_b, _, _, _, _ = _resolve_scope(data_b, building_id, sector_id)
        series_a = _HourlySeries.from_mapping(hourly_a)
        series_b = _HourlySeries.from_mapping(hourly_b)

        stats_a, baseline_a = _base_stats(
            series_a, buckets_a, metric, range_a_start, range_a_end
        )
        stats_b, baseline_b = _base_stats(
            series_b, buckets_b, metric, range_b_start, range_b_end
        )

        closed_a, count_a = series_a.closed_totals(range_a_start, range_a_end)
        closed_b, count_b = series_b.closed_totals(range_b_start, range_b_end)
        closed_count = count_a + count_b
        baseline_kwh_hour = (closed_a + closed_b) / closed_count if closed_count else 0.0
        baseline_per_hour = _convert(baseline_kwh_hour, metric)

        points: list[ElectricityComparePoint] = []
        for index, (bucket_a, bucket_b) in enumerate(zip(buckets_a, buckets_b)):
            value_a = _convert(series_a.sum_between(bucket_a.start, bucket_a.end), metric)
            value_b = _convert(series_b.sum_between(bucket_b.start, bucket_b.end), metric)
            average_hours = (bucket_a.hours + bucket_b.hours) / 2.0
            points.append(
                ElectricityComparePoint(
                    index=index,
                    timestamp_a=bucket_a.start,
                    timestamp_b=bucket_b.start,
                    period_a=round(value_a, 2),
                    period_b=round(value_b, 2),
                    baseline=round(baseline_per_hour * average_hours, 2),
                )
            )

        total_a = stats_a.total
        total_b = stats_b.total
        delta_pct = ((total_a - total_b) / total_b * 100.0) if total_b else 0.0
        period_a_days = (end_a - start_a).days + 1
        period_b_days = (end_b - start_b).days + 1

        return ElectricityCompareResponse(
            granularity=granularity,
            metric=metric,
            unit=UNIT_BY_METRIC[metric],
            scope=scope,
            scope_label=scope_label,
            building_id=resolved_building_id,
            sector_id=resolved_sector_id,
            start_a=start_a,
            end_a=end_a,
            start_b=start_b,
            end_b=end_b,
            period_a_days=period_a_days,
            period_b_days=period_b_days,
            period_a=stats_a,
            period_b=stats_b,
            baseline_hourly=round(baseline_per_hour, 4),
            delta_pct=round(delta_pct, 1),
            series=points,
        )

    return await _cached(_cache, cache_key, _compute)


async def _load_data_pair(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
) -> tuple[_ElectricityData, _ElectricityData]:
    """Load two periods independently so a long gap is never spread across them."""
    return await asyncio.gather(
        _load_data(start_a, end_a),
        _load_data(start_b, end_b),
    )


def clear_cache() -> None:
    _cache.clear()
    _data_cache.clear()
