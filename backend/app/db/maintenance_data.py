"""Load the heartbeat and battery history used by the Maintenance tab.

The recorder only stores a row when the state (or its attributes) changes, which
is exactly what the tab needs:

- heartbeat entities (temperature, CO₂, meter readings...) change on every
  report, so their timestamps measure transmission cadence and silence;
- battery entities change only when the battery percentage moves, so their
  history is sparse but enough to detect replacements and trends.

The loader is read-only and adaptive: devices with no data inside the selected
period get a second, longer lookback so a legacy valve still shows its real last
contact instead of "unknown".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.core.maintenance_map import (
    BATTERY_HISTORY_DAYS,
    DEVICES,
    DEVICES_BY_ID,
    LEGACY_DEVICE_IDS,
)
from app.db import repository
from app.db.session import AsyncSessionLocal

# Small margin before the period so the first interval can be measured.
_BASELINE_LOOKBACK = timedelta(days=14)
# Devices that stopped reporting long ago (legacy valves).
_LEGACY_LOOKBACK = timedelta(days=1500)
# A device with no heartbeat in the period may still have a recent contact.
_MISSING_LOOKBACK = timedelta(days=365)


@dataclass
class MaintenanceDatabaseData:
    """Raw timestamps and battery snapshots keyed by entity id.

    ``battery_snapshots`` keeps the raw state and JSON attributes because some
    batteries live in an attribute (presence, parking, gas, weather) instead of
    the entity state.
    """

    heartbeat_times: dict[str, list[datetime]] = field(default_factory=dict)
    battery_snapshots: dict[str, list[tuple[datetime, str | None, str | None]]] = field(
        default_factory=dict
    )


def _legacy_entities(attribute: str) -> set[str]:
    entities: set[str] = set()
    for device_id in LEGACY_DEVICE_IDS:
        device = DEVICES_BY_ID.get(device_id)
        if device is None:
            continue
        value = getattr(device, attribute)
        if value:
            entities.add(value)
    return entities


async def load_maintenance_data(
    start_utc: datetime,
    end_utc: datetime,
) -> MaintenanceDatabaseData:
    """Read all heartbeat and battery history needed by the service."""
    heartbeat_entities = sorted({device.heartbeat_entity for device in DEVICES})
    battery_entities = sorted(
        {device.battery_entity for device in DEVICES if device.battery_entity}
    )
    legacy_heartbeat = _legacy_entities("heartbeat_entity")
    legacy_battery = _legacy_entities("battery_entity")

    heartbeat_times: dict[str, list[datetime]] = {}
    battery_snapshots: dict[str, list[tuple[datetime, str | None, str | None]]] = {}

    async with AsyncSessionLocal() as session:
        # 1. Heartbeat timestamps, with a small margin before the period.
        rows = await repository.fetch_state_timestamps(
            session,
            heartbeat_entities,
            start_utc - _BASELINE_LOOKBACK,
            end_utc,
        )
        for entity_id, last_updated in rows:
            heartbeat_times.setdefault(entity_id, []).append(last_updated)

        # 2. Devices with no heartbeat in the period: find their last contact.
        missing_heartbeat = [
            entity_id
            for entity_id in heartbeat_entities
            if not any(
                start_utc <= value <= end_utc
                for value in heartbeat_times.get(entity_id, [])
            )
        ]
        legacy_missing = [
            entity_id for entity_id in missing_heartbeat if entity_id in legacy_heartbeat
        ]
        regular_missing = [
            entity_id for entity_id in missing_heartbeat if entity_id not in legacy_heartbeat
        ]
        if regular_missing:
            last_regular = await repository.fetch_last_state_timestamps_before(
                session, regular_missing, end_utc, _MISSING_LOOKBACK
            )
            for entity_id, last_updated in last_regular.items():
                heartbeat_times.setdefault(entity_id, []).append(last_updated)
        if legacy_missing:
            last_legacy = await repository.fetch_last_state_timestamps_before(
                session, legacy_missing, end_utc, _LEGACY_LOOKBACK
            )
            for entity_id, last_updated in last_legacy.items():
                heartbeat_times.setdefault(entity_id, []).append(last_updated)

        # 3. Battery history: hourly snapshots keep the payload small while
        # preserving the attribute values. Always look back 90 days so the
        # trend and replacement detection do not depend on the selected period.
        battery_lookback = timedelta(days=BATTERY_HISTORY_DAYS)
        regular_battery = [
            entity_id for entity_id in battery_entities if entity_id not in legacy_battery
        ]
        if regular_battery:
            battery_rows = await repository.fetch_hourly_state_snapshots(
                session, regular_battery, end_utc - battery_lookback, end_utc
            )
            for entity_id, _bucket, state, attributes in battery_rows:
                battery_snapshots.setdefault(entity_id, []).append(
                    (
                        datetime.fromtimestamp(_bucket, tz=timezone.utc).replace(tzinfo=None),
                        state,
                        attributes,
                    )
                )
        if legacy_battery:
            legacy_rows = await repository.fetch_hourly_state_snapshots(
                session, sorted(legacy_battery), end_utc - _LEGACY_LOOKBACK, end_utc
            )
            for entity_id, _bucket, state, attributes in legacy_rows:
                battery_snapshots.setdefault(entity_id, []).append(
                    (
                        datetime.fromtimestamp(_bucket, tz=timezone.utc).replace(tzinfo=None),
                        state,
                        attributes,
                    )
                )

        # 4. Battery entities with no snapshot in the lookback: keep their last
        # known value so the UI can show how old the reading is.
        missing_battery = [
            entity_id for entity_id in battery_entities if not battery_snapshots.get(entity_id)
        ]
        missing_legacy = [
            entity_id for entity_id in missing_battery if entity_id in legacy_battery
        ]
        missing_regular = [
            entity_id for entity_id in missing_battery if entity_id not in legacy_battery
        ]
        for entity_ids, lookback in (
            (missing_regular, _MISSING_LOOKBACK),
            (missing_legacy, _LEGACY_LOOKBACK),
        ):
            if not entity_ids:
                continue
            latest = await repository.fetch_latest_state_snapshots(
                session, entity_ids, end_utc, lookback
            )
            for entity_id, (state, attributes, last_updated) in latest.items():
                battery_snapshots.setdefault(entity_id, []).append(
                    (last_updated, state, attributes)
                )

    for values in heartbeat_times.values():
        values.sort()
    for values in battery_snapshots.values():
        values.sort(key=lambda item: item[0])

    return MaintenanceDatabaseData(
        heartbeat_times=heartbeat_times,
        battery_snapshots=battery_snapshots,
    )
