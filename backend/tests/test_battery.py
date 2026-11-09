import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.battery_map import BATTERY_GROUPS, MILLIVOLT_RANGE, PERCENT_RANGE
from app.core.clock import local_now, utc_now
from app.db.battery_data import LatestBatteryRows, load_latest_readings, parse_reading
from app.main import app
from app.services import battery_service
from app.services.battery_service import (
    build_history_points,
    build_sensor_status,
    classify_level,
    resolve_history_period,
)

client = TestClient(app)
URL = "/api/v1/maintenance/batteries"
SHELLYS = BATTERY_GROUPS["shellys"]
VALVES = BATTERY_GROUPS["valvulas"]
CLASSROOMS = BATTERY_GROUPS["aulas"]
NOW = datetime(2026, 11, 9, 12, 0)


class BatteryMapTest(unittest.TestCase):
    def test_groups_contain_the_requested_entities(self):
        self.assertEqual(
            [sensor.entity_id for sensor in SHELLYS.sensors],
            [f"sensor.bateria_shelly{index}" for index in range(1, 19)],
        )
        self.assertEqual(
            [sensor.entity_id for sensor in VALVES.sensors],
            [
                "sensor.bateria_valvula_f1_1",
                "sensor.bateria_valvula_ld1",
                "sensor.bateria_valvula_ld2",
                "sensor.bateria_valvula_ld3",
                "sensor.bateria_valvula_ld4",
            ],
        )
        self.assertEqual(
            [sensor.entity_id for sensor in CLASSROOMS.sensors],
            [f"sensor.sensor_bateria_a{room}" for room in (11, 12, 21, 22)],
        )


class ParseReadingTest(unittest.TestCase):
    def test_rejects_non_numeric_states(self):
        for state in (None, "", "unknown", "unavailable"):
            self.assertIsNone(parse_reading(state, PERCENT_RANGE))

    def test_rejects_impossible_classroom_voltages(self):
        self.assertIsNone(parse_reading("0.0", MILLIVOLT_RANGE))
        self.assertIsNone(parse_reading("65373.0", MILLIVOLT_RANGE))
        self.assertEqual(parse_reading("3641.0", MILLIVOLT_RANGE), 3641.0)

    def test_accepts_the_limits_of_a_percentage(self):
        self.assertEqual(parse_reading("0", PERCENT_RANGE), 0.0)
        self.assertEqual(parse_reading("100", PERCENT_RANGE), 100.0)
        self.assertIsNone(parse_reading("101", PERCENT_RANGE))


class SensorStatusTest(unittest.TestCase):
    def test_levels_use_the_unit_of_the_group(self):
        self.assertEqual(classify_level(SHELLYS, 19), "critical")
        self.assertEqual(classify_level(SHELLYS, 40), "low")
        self.assertEqual(classify_level(SHELLYS, 60), "medium")
        self.assertEqual(classify_level(SHELLYS, 61), "ok")
        self.assertEqual(classify_level(CLASSROOMS, 3190), "critical")
        self.assertEqual(classify_level(CLASSROOMS, 3640), "ok")

    def test_recent_valid_reading_is_current(self):
        status = build_sensor_status(
            SHELLYS, SHELLYS.sensors[0], 51.0, NOW - timedelta(hours=6), True, NOW
        )
        self.assertTrue(status.is_current)
        self.assertEqual(status.level, "medium")
        self.assertEqual(status.value, 51)
        self.assertIsNone(status.estimated_pct)

    def test_unknown_last_row_keeps_the_old_value_without_a_level(self):
        status = build_sensor_status(
            VALVES, VALVES.sensors[0], 84.0, NOW - timedelta(days=200), False, NOW
        )
        self.assertFalse(status.is_current)
        self.assertEqual(status.value, 84)
        self.assertEqual(status.level, "unknown")

    def test_old_reading_is_not_current_even_if_it_is_the_last_row(self):
        status = build_sensor_status(
            VALVES, VALVES.sensors[1], 79.0, NOW - timedelta(days=8), True, NOW
        )
        self.assertFalse(status.is_current)
        self.assertEqual(status.level, "unknown")

    def test_sensor_without_readings(self):
        status = build_sensor_status(VALVES, VALVES.sensors[1], None, None, False, NOW)
        self.assertIsNone(status.value)
        self.assertIsNone(status.age_hours)
        self.assertFalse(status.is_current)

    def test_classroom_percentage_is_an_estimate(self):
        status = build_sensor_status(
            CLASSROOMS, CLASSROOMS.sensors[0], 3450.0, NOW - timedelta(hours=1), True, NOW
        )
        self.assertEqual(status.value, 3450)
        self.assertEqual(status.estimated_pct, 70)
        self.assertEqual(status.level, "medium")


class LoadLatestReadingsTest(unittest.IsolatedAsyncioTestCase):
    async def _load(self, latest, fallback):
        session = AsyncMock()
        session.__aenter__.return_value = session
        with (
            patch("app.db.battery_data.AsyncSessionLocal", return_value=session),
            patch(
                "app.db.battery_data.repository.fetch_latest_state_snapshots",
                AsyncMock(return_value=latest),
            ),
            patch(
                "app.db.battery_data.repository.fetch_latest_numeric_states",
                AsyncMock(return_value=fallback),
            ) as numeric,
        ):
            return await load_latest_readings(VALVES, NOW), numeric

    async def test_looks_for_a_valid_reading_only_when_the_last_row_is_not(self):
        valid = "sensor.bateria_valvula_ld1"
        unknown = "sensor.bateria_valvula_ld3"
        old = datetime(2026, 7, 1)
        rows, numeric = await self._load(
            {valid: ("79", None, NOW), unknown: ("unknown", None, NOW)},
            {unknown: (94.0, old)},
        )
        self.assertEqual(numeric.await_args.args[1], [unknown])
        self.assertEqual(rows[valid], LatestBatteryRows("79", NOW, 79.0, NOW))
        self.assertEqual(rows[unknown], LatestBatteryRows("unknown", NOW, 94.0, old))
        self.assertEqual(
            rows["sensor.bateria_valvula_f1_1"], LatestBatteryRows(None, None, None, None)
        )

    async def test_unknown_sensor_without_any_valid_reading(self):
        unknown = "sensor.bateria_valvula_ld2"
        rows, _numeric = await self._load({unknown: ("unknown", None, NOW)}, {})
        self.assertEqual(rows[unknown], LatestBatteryRows("unknown", NOW, None, None))


class HistoryPeriodTest(unittest.TestCase):
    def test_default_period_is_90_days_ending_today(self):
        start, end, granularity = resolve_history_period()
        today = local_now().date()
        self.assertEqual(start.date(), today - timedelta(days=89))
        self.assertEqual(end.date(), today)
        self.assertEqual(granularity, "day")

    def test_granularity_depends_on_the_length(self):
        self.assertEqual(
            resolve_history_period(date(2026, 1, 1), date(2026, 1, 31))[2], "hour"
        )
        self.assertEqual(
            resolve_history_period(date(2026, 1, 1), date(2026, 2, 1))[2], "day"
        )

    def test_full_history_has_no_maximum_length(self):
        start, _end, granularity = resolve_history_period(date(2023, 1, 1), date(2026, 11, 1))
        self.assertEqual(start.date(), date(2023, 1, 1))
        self.assertEqual(granularity, "day")

    def test_rejects_invalid_dates(self):
        with self.assertRaises(ValueError):
            resolve_history_period(date(2026, 2, 1), date(2026, 1, 1))
        with self.assertRaises(ValueError):
            resolve_history_period(None, local_now().date() + timedelta(days=1))


class HistoryPointsTest(unittest.TestCase):
    @staticmethod
    def _epoch(*args):
        return int(datetime(*args, tzinfo=timezone.utc).timestamp())

    def test_hourly_points_keep_their_value(self):
        points = build_history_points(
            SHELLYS, [(self._epoch(2026, 10, 1, 8), 50.0), (self._epoch(2026, 10, 1, 9), 49.0)], "hour"
        )
        self.assertEqual([point.value for point in points], [50.0, 49.0])

    def test_daily_points_average_each_local_day(self):
        points = build_history_points(
            SHELLYS,
            [
                (self._epoch(2026, 10, 1, 8), 50.0),
                (self._epoch(2026, 10, 1, 9), 40.0),
                (self._epoch(2026, 10, 2, 9), 30.0),
            ],
            "day",
        )
        self.assertEqual([point.value for point in points], [45.0, 30.0])

    def test_long_silence_becomes_a_gap(self):
        points = build_history_points(
            SHELLYS,
            [
                (self._epoch(2026, 10, 1, 8), 50.0),
                (self._epoch(2026, 10, 8, 8), 49.0),
                (self._epoch(2026, 10, 15, 9), 48.0),
            ],
            "hour",
        )
        self.assertEqual([point.value for point in points], [50.0, 49.0, None, 48.0])

    def test_classroom_points_include_the_estimate(self):
        points = build_history_points(CLASSROOMS, [(self._epoch(2026, 10, 1, 8), 3450.0)], "hour")
        self.assertEqual(points[0].estimated_pct, 70)


class BatteryEndpointTest(unittest.TestCase):
    def setUp(self):
        battery_service.clear_cache()

    def tearDown(self):
        battery_service.clear_cache()

    def test_each_group_returns_all_its_sensors(self):
        for group_id, total in (("shellys", 18), ("valvulas", 5), ("aulas", 4)):
            response = client.get(f"{URL}/{group_id}")
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["summary"]["total"], total)
            self.assertEqual(len(body["sensors"]), total)
            self.assertEqual(body["data_source"], "mock")

    def test_mock_valves_have_no_current_reading(self):
        body = client.get(f"{URL}/valvulas").json()
        self.assertEqual(body["summary"]["without_current_reading"], 5)
        self.assertTrue(all(sensor["level"] == "unknown" for sensor in body["sensors"]))
        self.assertTrue(all(sensor["value"] is not None for sensor in body["sensors"]))

    def test_unknown_group_or_sensor_is_404(self):
        self.assertEqual(client.get(f"{URL}/otros").status_code, 404)
        self.assertEqual(client.get(f"{URL}/otros/shelly1/history").status_code, 404)
        self.assertEqual(client.get(f"{URL}/aulas/shelly1/history").status_code, 404)

    def test_history_returns_points_and_thresholds(self):
        body = client.get(f"{URL}/aulas/a11/history").json()
        self.assertEqual(body["unit"], "millivolt")
        self.assertEqual(body["granularity"], "day")
        self.assertEqual(body["low_threshold"], 3400.0)
        self.assertEqual(body["critical_threshold"], 3200.0)
        self.assertTrue(body["points"])
        self.assertIsNotNone(body["min_value"])

    def test_history_rejects_a_future_end(self):
        tomorrow = (utc_now() + timedelta(days=2)).date().isoformat()
        response = client.get(f"{URL}/shellys/shelly1/history", params={"end": tomorrow})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
