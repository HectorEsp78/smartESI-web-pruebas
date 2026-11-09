"""Business logic for the Maintenance tab.

The tab answers three practical questions with the recorder's own data:

1. **Is the battery healthy?** The last reading, its age, the 30-day trend and a
   30/60/90-day forecast. Millivolt sensors are also shown as an approximate
   percentage, but the raw mV remain authoritative.
2. **Is the device transmitting?** Heartbeat cadence is measured separately from
   the battery, because the Shelly battery entity only changes when the
   percentage moves. Silence is compared with a per-device threshold.
3. **Is the problem the battery, the device or the recorder?** Silence gaps are
   correlated across devices so a global/group outage is not reported as dozens
   of individual failures. The final 3×2 matrix (battery OK/low/unknown × data
   OK/no data) produces the maintenance decision.

Everything is read-only and cached per period. Event-driven devices (presence,
parking, people counters) are not flagged as silent unless they have been
unavailable for several days.
"""

from __future__ import annotations

import json
import statistics
import zlib
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from itertools import pairwise
from typing import Literal

from app.core.cache import TTLCache
from app.core.clock import ensure_utc, local_now, local_tz, utc_now
from app.core.config import settings
from app.core.maintenance_map import (
    ALLOWED_MAINTENANCE_DAYS,
    BATTERY_CRITICAL_MV,
    BATTERY_CRITICAL_PCT,
    BATTERY_LOW_MV,
    BATTERY_LOW_PCT,
    BATTERY_MEDIUM_MV,
    BATTERY_MEDIUM_PCT,
    BATTERY_REPLACEMENT_HIGH_PCT,
    BATTERY_REPLACEMENT_JUMP_PCT,
    BATTERY_REPLACEMENT_LOW_PCT,
    BATTERY_STALE_HOURS,
    BATTERY_TREND_DAYS,
    BATTERY_UNKNOWN_OFFLINE_HOURS,
    DEFAULT_MAINTENANCE_DAYS,
    DEVICES,
    DEVICES_BY_ID,
    EVENT_OFFLINE_HOURS,
    GLOBAL_OUTAGE_MIN_DEVICES,
    GLOBAL_OUTAGE_MIN_SHARE,
    GROUP_OUTAGE_MIN_DEVICES,
    GROUP_OUTAGE_MIN_SHARE,
    MV_PERCENT_CURVE,
    NOTES,
    OUTAGE_CLUSTER_TOLERANCE_HOURS,
    OVER_REPORTING_FACTOR,
    MaintenanceDevice,
    expected_per_day,
    silence_threshold_hours,
)
from app.schemas.maintenance import (
    BatteryBucket,
    BatteryStatus,
    BatteryUnit,
    DataStatus,
    HeartbeatStatus,
    MaintenanceAvailabilityInfo,
    MaintenanceBatteryInfo,
    MaintenanceBatteryPoint,
    MaintenanceDailyPoint,
    MaintenanceDeviceDetailResponse,
    MaintenanceDeviceSummary,
    MaintenanceHeartbeatInfo,
    MaintenanceHeatmapCell,
    MaintenanceOutage,
    MaintenanceOverviewResponse,
    MaintenanceSummary,
    MatrixCategory,
    OutageScope,
    PriorityLabel,
)

_cache = TTLCache(ttl_seconds=settings.STATS_CACHE_TTL_SECONDS, max_entries=32)
_MATRIX_TOLERANCE = timedelta(hours=OUTAGE_CLUSTER_TOLERANCE_HOURS)

_MATRIX_CATEGORY: dict[tuple[str, str], MatrixCategory] = {
    ("ok", "ok"): "correcto",
    ("ok", "no_data"): "revisar_dispositivo",
    ("low", "ok"): "cambiar_bateria",
    ("low", "no_data"): "bateria_y_dispositivo",
    ("unknown", "ok"): "sin_lectura_bateria",
    ("unknown", "no_data"): "revisar_sin_datos",
}

_MATRIX_DECISION: dict[MatrixCategory, str] = {
    "correcto": "Correcto: batería y transmisión dentro de lo esperado.",
    "revisar_dispositivo": "Batería OK pero sin datos: revisar el dispositivo o su red.",
    "cambiar_bateria": "Batería baja con datos OK: programar el cambio de batería.",
    "bateria_y_dispositivo": "Batería baja y sin datos: cambiar la batería y revisar el dispositivo.",
    "sin_lectura_bateria": "Sin lectura de batería; el dispositivo transmite con normalidad.",
    "revisar_sin_datos": "Sin datos ni lectura de batería: revisión urgente.",
}


# --- Small helpers ------------------------------------------------------------


def _hours(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600.0


def _round(value: float | None, digits: int = 1) -> float | None:
    return round(value, digits) if value is not None else None


def _fmt(value: float, digits: int = 1) -> str:
    """Spanish number formatting for the prebuilt decision reasons."""
    text = f"{value:,.{digits}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_hours(value: float | None) -> str:
    if value is None:
        return "—"
    if value < 48:
        return f"{_fmt(value, 1)} h"
    return f"{_fmt(value / 24.0, 1)} d"


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def estimate_pct_from_mv(millivolts: float) -> float:
    """Approximate Li-SOCl2 percentage from the documented cell curve.

    The curve is deliberately conservative and only used for comparisons and
    forecasts. The raw mV are always returned alongside it.
    """
    if millivolts >= MV_PERCENT_CURVE[0][0]:
        return 100.0
    if millivolts <= MV_PERCENT_CURVE[-1][0]:
        return 0.0
    for (high_mv, high_pct), (low_mv, low_pct) in pairwise(MV_PERCENT_CURVE):
        if low_mv <= millivolts <= high_mv:
            ratio = (millivolts - low_mv) / (high_mv - low_mv)
            return low_pct + ratio * (high_pct - low_pct)
    return 0.0


# --- Internal dataset ---------------------------------------------------------


@dataclass(frozen=True)
class _Period:
    start: datetime  # naive UTC, comparable with recorder columns
    end: datetime
    days: int


@dataclass
class _BatteryPoint:
    at: datetime
    value: float
    unit: BatteryUnit


@dataclass
class _DeviceData:
    heartbeat_times: list[datetime] = field(default_factory=list)
    battery_points: list[_BatteryPoint] = field(default_factory=list)


@dataclass
class _Dataset:
    data_source: Literal["mock", "database"]
    devices: dict[str, _DeviceData]


@dataclass
class _Gap:
    device_id: str
    start: datetime
    end: datetime
    ongoing: bool
    scope: OutageScope = "individual"

    @property
    def duration_hours(self) -> float:
        return _hours(self.start, self.end)


@dataclass
class _HeartbeatAnalysis:
    info: MaintenanceHeartbeatInfo
    gaps: list[_Gap]
    period_times: list[datetime]
    latest: datetime | None
    silence_hours: float | None
    threshold_hours: float | None


# --- Battery parsing and status ----------------------------------------------


def _parse_battery_value(
    device: MaintenanceDevice,
    state: str | None,
    attributes: str | None,
) -> float | None:
    if device.battery_attribute:
        if not attributes:
            return None
        try:
            payload = json.loads(attributes)
        except (TypeError, ValueError):
            return None
        if not isinstance(payload, dict):
            return None
        raw = payload.get(device.battery_attribute)
    else:
        raw = state
    if raw is None or isinstance(raw, bool):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _normalise_battery_value(
    device: MaintenanceDevice, value: float | None
) -> float | None:
    if value is None:
        return None
    if device.battery_unit == "millivolt":
        # Some integrations publish volts instead of millivolts. Normalise
        # without inventing a value: only values in a plausible cell range pass.
        millivolts = value * 1000.0 if 0 < value < 10 else value
        if 2000.0 <= millivolts <= 4000.0:
            return millivolts
        return None
    if 0.0 <= value <= 100.0:
        return value
    return None


def _battery_pct(device: MaintenanceDevice, value: float) -> float | None:
    if device.battery_unit == "millivolt":
        return estimate_pct_from_mv(value)
    return value


def _battery_status(device: MaintenanceDevice, value: float) -> BatteryStatus:
    if device.battery_unit == "millivolt":
        if value <= BATTERY_CRITICAL_MV:
            return "critical"
        if value <= BATTERY_LOW_MV:
            return "low"
        if value <= BATTERY_MEDIUM_MV:
            return "medium"
        return "ok"
    if value <= BATTERY_CRITICAL_PCT:
        return "critical"
    if value <= BATTERY_LOW_PCT:
        return "low"
    if value <= BATTERY_MEDIUM_PCT:
        return "medium"
    return "ok"


def _battery_trend(
    points: list[tuple[datetime, float, float]], now: datetime
) -> tuple[float | None, float | None]:
    """Least-squares slope (percentage points per day) over the last 30 days."""
    window_start = now - timedelta(days=BATTERY_TREND_DAYS)
    window = [(at, pct) for at, _value, pct in points if at >= window_start]
    if len(window) < 2:
        return None, None
    first_at = window[0][0]
    xs = [(at - first_at).total_seconds() / 86400.0 for at, _pct in window]
    ys = [pct for _at, pct in window]
    if xs[-1] - xs[0] < 0.5:
        return None, None
    count = len(xs)
    mean_x = sum(xs) / count
    mean_y = sum(ys) / count
    variance = sum((x - mean_x) ** 2 for x in xs)
    if variance <= 0:
        return None, None
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    slope = covariance / variance
    return slope * BATTERY_TREND_DAYS, slope


def _analyze_battery(
    device: MaintenanceDevice,
    points: list[_BatteryPoint],
    period: _Period,
    silence_hours: float | None,
) -> MaintenanceBatteryInfo | None:
    if not device.has_battery:
        return None

    valid: list[tuple[datetime, float, float]] = []
    for point in points:
        value = _normalise_battery_value(device, point.value)
        if value is None:
            continue
        pct = _battery_pct(device, value)
        if pct is None:
            continue
        valid.append((point.at, value, pct))
    valid.sort(key=lambda item: item[0])

    if not valid:
        return MaintenanceBatteryInfo(
            unit=device.battery_unit,
            status="unknown",
        )

    last_at, last_value, last_pct = valid[-1]
    age_hours = max(0.0, _hours(last_at, period.end))
    status = _battery_status(device, last_value)
    if (
        age_hours > BATTERY_UNKNOWN_OFFLINE_HOURS
        and (silence_hours or 0.0) > BATTERY_UNKNOWN_OFFLINE_HOURS
    ):
        status = "unknown"

    replacement_at: datetime | None = None
    for (_prev_at, _prev_value, prev_pct), (current_at, _current_value, current_pct) in pairwise(
        valid
    ):
        jump = current_pct - prev_pct
        if jump >= BATTERY_REPLACEMENT_JUMP_PCT and (
            prev_pct <= BATTERY_REPLACEMENT_LOW_PCT
            or current_pct >= BATTERY_REPLACEMENT_HIGH_PCT
        ):
            replacement_at = current_at

    # After a replacement, the old discharge history is irrelevant: measure the
    # trend of the new cell only.
    trend_points = [
        point for point in valid if replacement_at is None or point[0] >= replacement_at
    ]
    trend_30d, slope = _battery_trend(trend_points, period.end)

    days_to_critical: float | None = None
    forecast_30d: float | None = None
    forecast_60d: float | None = None
    forecast_90d: float | None = None
    forecast_replacement_at: datetime | None = None

    if status != "unknown":
        if last_pct <= BATTERY_CRITICAL_PCT:
            days_to_critical = 0.0
        elif slope is not None and slope < -0.02:
            days_to_critical = (last_pct - BATTERY_CRITICAL_PCT) / (-slope)

        if slope is not None and slope < -0.02:
            forecast_30d = _clamp_pct(last_pct + slope * 30.0)
            forecast_60d = _clamp_pct(last_pct + slope * 60.0)
            forecast_90d = _clamp_pct(last_pct + slope * 90.0)
        else:
            forecast_30d = last_pct
            forecast_60d = last_pct
            forecast_90d = last_pct

        if days_to_critical is not None and days_to_critical <= 365.0 * 3.0:
            forecast_replacement_at = ensure_utc(
                period.end + timedelta(days=days_to_critical)
            )

    return MaintenanceBatteryInfo(
        value=_round(last_value, 0),
        unit=device.battery_unit,
        estimated_pct=_round(last_pct, 0),
        status=status,
        reading_at=ensure_utc(last_at),
        age_hours=_round(age_hours, 1),
        stale=age_hours > BATTERY_STALE_HOURS,
        trend_30d_pct=_round(trend_30d, 1),
        replacement_detected=replacement_at is not None,
        replacement_at=ensure_utc(replacement_at) if replacement_at else None,
        replacement_in_period=(
            replacement_at is not None
            and period.start <= replacement_at <= period.end
        ),
        days_to_critical=_round(days_to_critical, 0),
        forecast_30d_pct=_round(forecast_30d, 0),
        forecast_60d_pct=_round(forecast_60d, 0),
        forecast_90d_pct=_round(forecast_90d, 0),
        forecast_replacement_at=forecast_replacement_at,
    )


def _clamp_pct(value: float) -> float:
    return max(0.0, min(100.0, value))


# --- Heartbeat and outages ----------------------------------------------------


def _heartbeat_gaps(
    device: MaintenanceDevice,
    times: list[datetime],
    period: _Period,
    threshold: float,
) -> list[_Gap]:
    period_times = [value for value in times if period.start <= value <= period.end]
    previous = [value for value in times if value < period.start]
    baseline = max(previous) if previous else None
    anchors = ([baseline] if baseline else []) + period_times
    gaps: list[_Gap] = []

    if not anchors:
        if _hours(period.start, period.end) > threshold:
            gaps.append(_Gap(device.id, period.start, period.end, True))
        return gaps

    first = anchors[0]
    gap_start = period.start if baseline is None else max(period.start, baseline)
    if first > gap_start and _hours(gap_start, first) > threshold:
        gaps.append(_Gap(device.id, gap_start, first, False))

    for previous_anchor, current_anchor in pairwise(anchors):
        start = max(previous_anchor, period.start)
        if current_anchor > start and _hours(start, current_anchor) > threshold:
            gaps.append(_Gap(device.id, start, current_anchor, False))

    last = anchors[-1]
    if last < period.end and _hours(last, period.end) > threshold:
        gaps.append(_Gap(device.id, max(last, period.start), period.end, True))

    return gaps


def _analyze_heartbeat(
    device: MaintenanceDevice,
    times: list[datetime],
    period: _Period,
) -> _HeartbeatAnalysis:
    ordered = sorted(times)
    period_times = [value for value in ordered if period.start <= value <= period.end]
    intervals = [
        _hours(previous, current)
        for previous, current in pairwise(period_times)
    ]
    median_interval = statistics.median(intervals) if intervals else None
    p95_interval = _percentile(intervals, 95) if intervals else None

    if device.is_periodic:
        threshold = silence_threshold_hours(device, p95_interval)
    else:
        threshold = EVENT_OFFLINE_HOURS

    latest = max(ordered) if ordered else None
    silence_hours = (
        max(0.0, _hours(latest, period.end)) if latest is not None else None
    )

    period_days = max(_hours(period.start, period.end) / 24.0, 1e-9)
    observed_per_day = len(period_times) / period_days
    expected = expected_per_day(device)
    ratio = observed_per_day / expected if expected else None

    if not device.is_periodic:
        status: HeartbeatStatus = "event" if latest is not None else "unknown"
    elif latest is None or threshold is None:
        status = "unknown"
    elif silence_hours is not None and silence_hours <= threshold:
        status = "ok"
    elif silence_hours is not None and silence_hours <= threshold * 2.0:
        status = "late"
    else:
        status = "silent"

    gaps = _heartbeat_gaps(device, ordered, period, threshold) if threshold else []

    return _HeartbeatAnalysis(
        info=MaintenanceHeartbeatInfo(
            last_at=ensure_utc(latest) if latest is not None else None,
            silence_hours=_round(silence_hours, 1),
            updates_per_day=_round(observed_per_day, 1),
            expected_per_day=_round(expected, 1),
            ratio=_round(ratio, 2),
            median_interval_hours=_round(median_interval, 2),
            p95_interval_hours=_round(p95_interval, 2),
            threshold_hours=_round(threshold, 1),
            status=status,
        ),
        gaps=gaps,
        period_times=period_times,
        latest=latest,
        silence_hours=silence_hours,
        threshold_hours=threshold,
    )


def _cluster_gaps(gaps: list[_Gap]) -> list[list[_Gap]]:
    """Group gaps whose start times are close (one outage affecting many devices)."""
    clusters: list[list[_Gap]] = []
    current: list[_Gap] = []
    for gap in sorted(gaps, key=lambda item: item.start):
        if not current:
            current = [gap]
            continue
        if gap.start <= current[0].start + _MATRIX_TOLERANCE:
            current.append(gap)
        else:
            clusters.append(current)
            current = [gap]
    if current:
        clusters.append(current)
    return clusters


def _correlate_outages(
    analyses: dict[str, _HeartbeatAnalysis], period: _Period
) -> list[MaintenanceOutage]:
    active_ids = [
        device.id
        for device in DEVICES
        if device.is_periodic and analyses[device.id].period_times
    ]
    active_count = len(active_ids)
    gaps = [
        gap
        for device_id in active_ids
        for gap in analyses[device_id].gaps
    ]

    outages: list[MaintenanceOutage] = []
    for cluster in _cluster_gaps(gaps):
        device_ids = sorted({gap.device_id for gap in cluster})
        share = len(device_ids) / active_count if active_count else 0.0
        if (
            len(device_ids) >= GLOBAL_OUTAGE_MIN_DEVICES
            and share >= GLOBAL_OUTAGE_MIN_SHARE
        ):
            scope: OutageScope = "global"
        elif (
            len(device_ids) >= GROUP_OUTAGE_MIN_DEVICES
            and share >= GROUP_OUTAGE_MIN_SHARE
        ):
            scope = "group"
        else:
            scope = "individual"

        for gap in cluster:
            gap.scope = scope

        if scope == "individual":
            continue

        start = min(gap.start for gap in cluster)
        end = max(gap.end for gap in cluster)
        ongoing = any(gap.ongoing for gap in cluster) and end >= period.end - timedelta(
            hours=1
        )
        outages.append(
            MaintenanceOutage(
                scope=scope,
                start=ensure_utc(start),
                end=ensure_utc(end),
                duration_hours=_round(_hours(start, end), 1) or 0.0,
                device_count=len(device_ids),
                device_ids=device_ids,
                ongoing=ongoing,
            )
        )

    return sorted(outages, key=lambda outage: outage.start, reverse=True)


def _classify_data(
    device: MaintenanceDevice,
    analysis: _HeartbeatAnalysis,
) -> tuple[DataStatus, bool]:
    if not device.is_periodic:
        if analysis.silence_hours is None:
            return "unknown", False
        ok = analysis.silence_hours <= EVENT_OFFLINE_HOURS
        return ("ok" if ok else "device_silent"), ok

    if analysis.silence_hours is None:
        # A device with no heartbeat at all is a device issue, not a correlated
        # outage: whole-period gaps are excluded from the correlation.
        return "device_silent", False

    if (
        analysis.threshold_hours is not None
        and analysis.silence_hours <= analysis.threshold_hours
    ):
        return "ok", True

    ongoing = [gap for gap in analysis.gaps if gap.ongoing]
    if ongoing:
        scope = ongoing[-1].scope
        if scope == "global":
            return "global_outage", False
        if scope == "group":
            return "group_outage", False
    return "device_silent", False


def _build_availability(
    analysis: _HeartbeatAnalysis, period: _Period
) -> MaintenanceAvailabilityInfo:
    period_hours = _hours(period.start, period.end)
    individual = [gap for gap in analysis.gaps if gap.scope == "individual"]
    global_gaps = [gap for gap in analysis.gaps if gap.scope == "global"]
    group_gaps = [gap for gap in analysis.gaps if gap.scope == "group"]
    downtime = sum(gap.duration_hours for gap in individual)

    availability: float | None = None
    if analysis.period_times and period_hours > 0:
        availability = _clamp_pct((period_hours - downtime) / period_hours * 100.0)

    mtbf: float | None = None
    mttr: float | None = None
    if individual:
        mttr = downtime / len(individual)
        if availability is not None:
            mtbf = max(0.0, period_hours - downtime) / len(individual)

    return MaintenanceAvailabilityInfo(
        availability_pct=_round(availability, 0),
        outages_total=len(analysis.gaps),
        outages_individual=len(individual),
        outages_global=len(global_gaps),
        outages_group=len(group_gaps),
        downtime_hours=_round(downtime, 1) if analysis.period_times else None,
        mtbf_hours=_round(mtbf, 1),
        mttr_hours=_round(mttr, 1),
    )


# --- Decision, priority and reasons ------------------------------------------


def _battery_bucket(battery: MaintenanceBatteryInfo | None) -> BatteryBucket:
    if battery is None or battery.status == "unknown":
        return "unknown"
    if battery.status in ("critical", "low"):
        return "low"
    return "ok"


def _decision(
    device: MaintenanceDevice,
    category: MatrixCategory,
    data_status: DataStatus,
    battery: MaintenanceBatteryInfo | None,
) -> str:
    if data_status == "global_outage":
        return "Sin datos por un corte global del recorder; no es una avería del dispositivo."
    if data_status == "group_outage":
        return "Sin datos por un corte de grupo; revisar la red o el gateway."

    if not device.has_battery:
        if category == "correcto":
            return "Dispositivo alimentado por red: transmisión correcta."
        return "Dispositivo alimentado por red sin datos: revisar la conexión."

    if battery is not None and battery.status == "critical":
        if category == "bateria_y_dispositivo":
            return "Batería crítica y sin datos: cambiar la batería y revisar el dispositivo."
        if category == "cambiar_bateria":
            return "Batería crítica con datos OK: cambiar la batería cuanto antes."
    return _MATRIX_DECISION[category]


def _priority(
    device: MaintenanceDevice,
    battery: MaintenanceBatteryInfo | None,
    heartbeat: MaintenanceHeartbeatInfo,
    availability: MaintenanceAvailabilityInfo,
    data_status: DataStatus,
    data_ok: bool,
    bucket: BatteryBucket,
) -> tuple[int, PriorityLabel]:
    score = 0
    if battery is not None:
        if battery.status == "critical":
            score += 45
        elif battery.status == "low":
            score += 30
        elif battery.status == "medium":
            score += 10
        elif battery.status == "unknown":
            score += 5

    if data_status == "device_silent":
        score += 35
    elif data_status == "group_outage":
        score += 10
    elif data_status == "unknown":
        score += 15

    score += min(15, availability.outages_individual * 5)

    if battery is not None and battery.days_to_critical is not None:
        if battery.days_to_critical <= 30:
            score += 15
        elif battery.days_to_critical <= 60:
            score += 8
        elif battery.days_to_critical <= 90:
            score += 4

    if heartbeat.status == "silent":
        score += 10
    elif heartbeat.status == "late":
        score += 5

    if device.is_periodic and device.has_battery and not data_ok and bucket == "ok":
        score += 5

    score = min(100, score)
    if score >= 70:
        label: PriorityLabel = "urgent"
    elif score >= 45:
        label = "high"
    elif score >= 25:
        label = "medium"
    else:
        label = "low"
    return score, label


def _reasons(
    device: MaintenanceDevice,
    battery: MaintenanceBatteryInfo | None,
    heartbeat: MaintenanceHeartbeatInfo,
    availability: MaintenanceAvailabilityInfo,
) -> list[str]:
    reasons: list[str] = []

    if battery is not None:
        if battery.status == "unknown":
            reasons.append("Sin lectura de batería.")
        else:
            if battery.unit == "millivolt" and battery.value is not None:
                reasons.append(
                    f"Batería a {_fmt(battery.value, 0)} mV "
                    f"(~{_fmt(battery.estimated_pct or 0.0, 0)} %)."
                )
            elif battery.value is not None:
                reasons.append(f"Batería al {_fmt(battery.value, 0)} %.")
            if battery.stale and battery.age_hours is not None:
                reasons.append(
                    f"Última lectura de batería hace {_fmt_hours(battery.age_hours)}."
                )
            if battery.replacement_detected and battery.replacement_at is not None:
                when = ensure_utc(battery.replacement_at).astimezone(local_tz())
                reasons.append(
                    f"Cambio de batería detectado el {when.strftime('%d/%m/%Y')}."
                )
            if battery.trend_30d_pct is not None and battery.trend_30d_pct < -0.5:
                reasons.append(f"Tendencia {_fmt(battery.trend_30d_pct, 1)} pp/30 d.")
            if battery.days_to_critical is not None:
                if battery.days_to_critical <= 0:
                    reasons.append("Batería en nivel crítico.")
                else:
                    reasons.append(
                        "Batería crítica estimada en "
                        f"{_fmt(battery.days_to_critical, 0)} días."
                    )

    if heartbeat.last_at is None:
        reasons.append("Sin datos en el periodo.")
    else:
        reasons.append(f"Último dato hace {_fmt_hours(heartbeat.silence_hours or 0.0)}.")
        if heartbeat.status in ("late", "silent") and heartbeat.threshold_hours is not None:
            reasons.append(
                f"Silencio superior al umbral de {_fmt_hours(heartbeat.threshold_hours)}."
            )
        if (
            heartbeat.ratio is not None
            and heartbeat.expected_per_day is not None
            and heartbeat.updates_per_day is not None
        ):
            if heartbeat.ratio > OVER_REPORTING_FACTOR:
                reasons.append(
                    "Frecuencia alta: "
                    f"{_fmt(heartbeat.updates_per_day, 1)} datos/día "
                    f"(esperado {_fmt(heartbeat.expected_per_day, 1)})."
                )
            elif heartbeat.ratio < 0.5:
                reasons.append(
                    "Frecuencia baja: "
                    f"{_fmt(heartbeat.updates_per_day, 1)} datos/día "
                    f"(esperado {_fmt(heartbeat.expected_per_day, 1)})."
                )

    if availability.outages_individual:
        count = availability.outages_individual
        noun = "corte individual" if count == 1 else "cortes individuales"
        reasons.append(f"{count} {noun}; MTTR {_fmt_hours(availability.mttr_hours)}.")
    if availability.outages_global:
        reasons.append("Afectado por un corte global del recorder.")
    if availability.outages_group:
        reasons.append("Afectado por un corte de grupo.")
    if device.notes:
        reasons.append(device.notes)

    return reasons


# --- Mock dataset -------------------------------------------------------------


def _rand(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return zlib.crc32(payload) / 0x100000000


def _mock_battery_points(device: MaintenanceDevice, period: _Period) -> list[_BatteryPoint]:
    if not device.has_battery:
        return []

    now = period.end
    base = _rand("battery", device.id)
    has_replacement = _rand("replacement", device.id) < 0.18
    points: list[_BatteryPoint] = []

    if device.battery_unit == "millivolt":
        if has_replacement:
            current = 3550.0 + base * 100.0
        else:
            current = 3050.0 + base * 550.0
        for days_ago in range(90, -1, -3):
            if has_replacement and days_ago > 25:
                value = 3100.0 + base * 60.0
            elif has_replacement:
                value = 3700.0 - (25.0 - days_ago) / 25.0 * (3700.0 - current)
            else:
                value = current + 180.0 * (days_ago / 90.0)
            value += (_rand(device.id, days_ago, "mv") - 0.5) * 10.0
            points.append(
                _BatteryPoint(
                    at=now - timedelta(days=days_ago),
                    value=max(2900.0, min(3700.0, value)),
                    unit="millivolt",
                )
            )
    else:
        if has_replacement:
            current = 70.0 + base * 25.0
        else:
            current = 12.0 + base * 83.0
        for days_ago in range(90, -1, -3):
            if has_replacement and days_ago > 25:
                value = 12.0 + base * 18.0
            elif has_replacement:
                value = 100.0 - (25.0 - days_ago) / 25.0 * (100.0 - current)
            else:
                value = current + 35.0 * (days_ago / 90.0)
            value += (_rand(device.id, days_ago, "pct") - 0.5) * 4.0
            points.append(
                _BatteryPoint(
                    at=now - timedelta(days=days_ago),
                    value=max(0.0, min(100.0, value)),
                    unit="percent",
                )
            )

    return points


def _mock_heartbeat_times(
    device: MaintenanceDevice, period: _Period
) -> list[datetime]:
    now = period.end
    base = _rand("heartbeat", device.id)
    if _rand("nodata", device.id) < 0.03:
        return []

    if not device.is_periodic:
        interval_days = 2.0 + base * 6.0
        times: list[datetime] = []
        cursor = period.start - timedelta(days=interval_days)
        while cursor <= now:
            if _rand(device.id, cursor.isoformat()) < 0.55:
                times.append(cursor)
            cursor += timedelta(days=interval_days)
        return times

    interval = timedelta(minutes=device.expected_interval_min or 60.0)
    silent = _rand("silent", device.id) < 0.08
    silent_start = now - timedelta(days=5)
    global_start = now - timedelta(days=10)
    global_end = now - timedelta(days=8)

    times = []
    cursor = period.start - interval * 2
    while cursor <= now:
        in_global = global_start <= cursor < global_end
        in_device_silence = silent and cursor >= silent_start
        if not in_global and not in_device_silence:
            times.append(cursor)
        cursor += interval
    return times


def _mock_dataset(period: _Period) -> _Dataset:
    return _Dataset(
        data_source="mock",
        devices={
            device.id: _DeviceData(
                heartbeat_times=_mock_heartbeat_times(device, period),
                battery_points=_mock_battery_points(device, period),
            )
            for device in DEVICES
        },
    )


async def _database_dataset(period: _Period) -> _Dataset:
    # Imported lazily so mock mode never needs SQLAlchemy / a DB driver.
    from app.db import maintenance_data

    raw = await maintenance_data.load_maintenance_data(period.start, period.end)
    devices: dict[str, _DeviceData] = {}
    for device in DEVICES:
        times = raw.heartbeat_times.get(device.heartbeat_entity, [])
        battery_points: list[_BatteryPoint] = []
        if device.has_battery and device.battery_entity:
            for at, state, attributes in raw.battery_snapshots.get(
                device.battery_entity, []
            ):
                value = _parse_battery_value(device, state, attributes)
                if value is None:
                    continue
                battery_points.append(
                    _BatteryPoint(
                        at=at,
                        value=value,
                        unit=device.battery_unit or "percent",
                    )
                )
        devices[device.id] = _DeviceData(
            heartbeat_times=times,
            battery_points=battery_points,
        )
    return _Dataset(data_source="database", devices=devices)


async def _load_dataset(period: _Period) -> _Dataset:
    cache_end = period.end.replace(minute=0, second=0, microsecond=0)
    key = ("maintenance-dataset", period.days, cache_end.isoformat())
    hit = _cache.get(key)
    if hit is not None:
        return hit
    if settings.DATA_SOURCE == "database":
        value = await _database_dataset(period)
    else:
        value = _mock_dataset(period)
    _cache.set(key, value)
    return value


# --- Period, summaries and heatmap -------------------------------------------


def resolve_period(days: int | None = None) -> _Period:
    value = DEFAULT_MAINTENANCE_DAYS if days is None else int(days)
    if value not in ALLOWED_MAINTENANCE_DAYS:
        raise ValueError("El periodo debe ser de 7, 30 o 90 días.")
    end = utc_now()
    return _Period(start=end - timedelta(days=value), end=end, days=value)


def _build_summary(
    device: MaintenanceDevice,
    data: _DeviceData,
    analysis: _HeartbeatAnalysis,
    period: _Period,
) -> MaintenanceDeviceSummary:
    battery = _analyze_battery(
        device, data.battery_points, period, analysis.silence_hours
    )
    availability = _build_availability(analysis, period)
    data_status, data_ok = _classify_data(device, analysis)
    bucket = _battery_bucket(battery)

    if device.has_battery:
        data_key = "ok" if data_ok else "no_data"
        category = _MATRIX_CATEGORY[(bucket, data_key)]
    else:
        category = "correcto" if data_ok else "revisar_dispositivo"

    priority, priority_label = _priority(
        device,
        battery,
        analysis.info,
        availability,
        data_status,
        data_ok,
        bucket,
    )

    return MaintenanceDeviceSummary(
        id=device.id,
        label=device.label,
        type=device.type,
        location=device.location,
        mode=device.mode,
        has_battery=device.has_battery,
        notes=device.notes,
        battery=battery,
        heartbeat=analysis.info,
        availability=availability,
        battery_bucket=bucket,
        data_status=data_status,
        data_ok=data_ok,
        matrix_category=category,
        priority=priority,
        priority_label=priority_label,
        decision=_decision(device, category, data_status, battery),
        reasons=_reasons(device, battery, analysis.info, availability),
    )


def _summary_counts(
    summaries: list[MaintenanceDeviceSummary],
    outages: list[MaintenanceOutage],
) -> MaintenanceSummary:
    availability_values = [
        summary.availability.availability_pct
        for summary in summaries
        if summary.availability.availability_pct is not None
    ]
    forecast_30 = [
        summary
        for summary in summaries
        if summary.battery is not None
        and summary.battery.days_to_critical is not None
        and summary.battery.days_to_critical <= 30
    ]
    forecast_60 = [
        summary
        for summary in summaries
        if summary.battery is not None
        and summary.battery.days_to_critical is not None
        and summary.battery.days_to_critical <= 60
    ]
    forecast_90 = [
        summary
        for summary in summaries
        if summary.battery is not None
        and summary.battery.days_to_critical is not None
        and summary.battery.days_to_critical <= 90
    ]

    return MaintenanceSummary(
        devices_total=len(summaries),
        devices_periodic=sum(1 for summary in summaries if summary.mode == "periodic"),
        devices_event=sum(1 for summary in summaries if summary.mode == "event"),
        with_battery=sum(1 for summary in summaries if summary.has_battery),
        low_battery=sum(
            1
            for summary in summaries
            if summary.has_battery and summary.battery_bucket == "low"
        ),
        critical_battery=sum(
            1
            for summary in summaries
            if summary.battery is not None and summary.battery.status == "critical"
        ),
        unknown_battery=sum(
            1
            for summary in summaries
            if summary.has_battery and summary.battery_bucket == "unknown"
        ),
        no_data=sum(1 for summary in summaries if not summary.data_ok),
        global_outages=sum(1 for outage in outages if outage.scope == "global"),
        group_outages=sum(1 for outage in outages if outage.scope == "group"),
        individual_outages=sum(
            summary.availability.outages_individual for summary in summaries
        ),
        avg_availability_pct=_round(_mean(availability_values), 0),
        replacements_detected=sum(
            1
            for summary in summaries
            if summary.battery is not None
            and summary.battery.replacement_in_period
        ),
        forecast_replace_30d=len(forecast_30),
        forecast_replace_60d=len(forecast_60),
        forecast_replace_90d=len(forecast_90),
    )


def _local_dates(period: _Period) -> list[date]:
    start = ensure_utc(period.start).astimezone(local_tz()).date()
    end = ensure_utc(period.end).astimezone(local_tz()).date()
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _day_bounds_utc(day: date, period: _Period) -> tuple[datetime, datetime] | None:
    start_local = datetime.combine(day, time.min, tzinfo=local_tz())
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    start = max(start_utc, period.start)
    end = min(end_utc, period.end)
    if end <= start:
        return None
    return start, end


def _daily_points(
    device: MaintenanceDevice,
    analysis: _HeartbeatAnalysis,
    period: _Period,
) -> list[MaintenanceDailyPoint]:
    expected = expected_per_day(device)
    points: list[MaintenanceDailyPoint] = []
    for day in _local_dates(period):
        bounds = _day_bounds_utc(day, period)
        if bounds is None:
            continue
        start, end = bounds
        updates = sum(1 for value in analysis.period_times if start <= value < end)
        day_hours = _hours(start, end)
        expected_day = expected * day_hours / 24.0 if expected else None
        availability = None
        if expected_day is not None and expected_day > 0:
            availability = _clamp_pct(updates / expected_day * 100.0)
        points.append(
            MaintenanceDailyPoint(
                date=day.isoformat(),
                updates=updates,
                expected=_round(expected_day, 1),
                availability_pct=_round(availability, 0),
            )
        )
    return points


def _build_heatmap(
    analyses: dict[str, _HeartbeatAnalysis],
    period: _Period,
) -> list[MaintenanceHeatmapCell]:
    cells: list[MaintenanceHeatmapCell] = []
    for device in DEVICES:
        if not device.is_periodic:
            continue
        analysis = analyses[device.id]
        for point in _daily_points(device, analysis, period):
            cells.append(
                MaintenanceHeatmapCell(
                    device_id=device.id,
                    date=point.date,
                    updates=point.updates,
                    expected=point.expected,
                    availability_pct=point.availability_pct,
                )
            )
    return cells


def _notes(data_source: Literal["mock", "database"]) -> list[str]:
    notes = list(NOTES)
    if data_source == "mock":
        notes.insert(0, "Datos simulados: el backend está en modo mock.")
    else:
        notes.insert(0, "Datos reales del recorder de Home Assistant (solo lectura).")
    return notes


# --- Public builders ----------------------------------------------------------


async def build_overview(days: int | None = None) -> MaintenanceOverviewResponse:
    period = resolve_period(days)
    dataset = await _load_dataset(period)
    analyses = {
        device.id: _analyze_heartbeat(
            device, dataset.devices[device.id].heartbeat_times, period
        )
        for device in DEVICES
    }
    outages = _correlate_outages(analyses, period)
    summaries = [
        _build_summary(device, dataset.devices[device.id], analyses[device.id], period)
        for device in DEVICES
    ]
    summaries.sort(key=lambda summary: (-summary.priority, summary.label))

    return MaintenanceOverviewResponse(
        start=ensure_utc(period.start),
        end=ensure_utc(period.end),
        days=period.days,
        generated_at=ensure_utc(local_now()),
        summary=_summary_counts(summaries, outages),
        devices=summaries,
        outages=outages,
        heatmap=_build_heatmap(analyses, period),
        data_source=dataset.data_source,
        notes=_notes(dataset.data_source),
    )


def _battery_history(
    device: MaintenanceDevice, data: _DeviceData
) -> list[MaintenanceBatteryPoint]:
    if not device.has_battery:
        return []
    history: list[MaintenanceBatteryPoint] = []
    for point in data.battery_points:
        value = _normalise_battery_value(device, point.value)
        if value is None:
            continue
        pct = _battery_pct(device, value)
        if pct is None:
            continue
        history.append(
            MaintenanceBatteryPoint(
                timestamp=ensure_utc(point.at),
                value=_round(value, 0),
                unit=point.unit,
                estimated_pct=_round(pct, 0),
            )
        )
    history.sort(key=lambda item: item.timestamp)
    return history


def _device_outages(
    device: MaintenanceDevice,
    analysis: _HeartbeatAnalysis,
    outages: list[MaintenanceOutage],
) -> list[MaintenanceOutage]:
    selected = [
        outage
        for outage in outages
        if outage.scope in ("global", "group") and device.id in outage.device_ids
    ]
    for gap in analysis.gaps:
        if gap.scope != "individual":
            continue
        selected.append(
            MaintenanceOutage(
                scope="individual",
                start=ensure_utc(gap.start),
                end=ensure_utc(gap.end),
                duration_hours=_round(gap.duration_hours, 1) or 0.0,
                device_count=1,
                device_ids=[device.id],
                ongoing=gap.ongoing,
            )
        )
    return sorted(selected, key=lambda outage: outage.start, reverse=True)


async def build_device_detail(
    device_id: str, days: int | None = None
) -> MaintenanceDeviceDetailResponse:
    device = DEVICES_BY_ID.get(device_id)
    if device is None:
        raise KeyError(device_id)

    period = resolve_period(days)
    dataset = await _load_dataset(period)
    analyses = {
        candidate.id: _analyze_heartbeat(
            candidate, dataset.devices[candidate.id].heartbeat_times, period
        )
        for candidate in DEVICES
    }
    outages = _correlate_outages(analyses, period)
    data = dataset.devices[device.id]
    summary = _build_summary(device, data, analyses[device.id], period)

    return MaintenanceDeviceDetailResponse(
        start=ensure_utc(period.start),
        end=ensure_utc(period.end),
        days=period.days,
        generated_at=ensure_utc(local_now()),
        device=summary,
        battery_history=_battery_history(device, data),
        daily=_daily_points(device, analyses[device.id], period),
        outages=_device_outages(device, analyses[device.id], outages),
        data_source=dataset.data_source,
        notes=_notes(dataset.data_source),
    )


def clear_cache() -> None:
    _cache.clear()
