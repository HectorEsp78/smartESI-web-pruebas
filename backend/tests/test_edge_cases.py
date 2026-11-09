"""Regression tests for edge cases: extreme dates, DST days and broken sensors."""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.dialects import mysql

from app.core import clock
from app.core.clock import local_tz
from app.db import repository
from app.db.database_data import net_occupancy, parse_counter_value
from app.db.environment_data import _hourly_presence
from app.main import app
from app.services import electricity_service, environment_service, lighting_context

client = TestClient(app, raise_server_exceptions=False)


class ExtremeDatesTest(unittest.TestCase):
    """Dates a browser cannot send but a URL can: a client error, never a 500."""

    def test_electricity_rejects_dates_outside_the_supported_window(self):
        for start, end in (("9999-12-01", "9999-12-31"), ("0001-01-01", "0001-01-02")):
            with self.subTest(start=start):
                response = client.get(
                    "/api/v1/energy/electricity", params={"start": start, "end": end}
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("fechas", response.json()["detail"])

    def test_compare_many_rejects_dates_outside_the_supported_window(self):
        response = client.get(
            "/api/v1/energy/electricity/compare-many",
            params={
                "start": ["9999-12-30", "2025-01-01"],
                "end": ["9999-12-31", "2025-01-02"],
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_environment_rejects_dates_outside_the_supported_window(self):
        for params in ({"end": "0001-01-01"}, {"start": "0001-01-01", "end": "0001-01-02"}):
            with self.subTest(params=params):
                response = client.get("/api/v1/environment/overview", params=params)
                self.assertEqual(response.status_code, 422)

    def test_malformed_date_gets_a_message_the_user_can_read(self):
        response = client.get(
            "/api/v1/energy/electricity", params={"start": "ayer", "end": "hoy"}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("parámetros", response.json()["detail"])


class UnhandledErrorTest(unittest.TestCase):
    def test_unexpected_errors_are_logged_and_not_leaked(self):
        with (
            patch.object(
                electricity_service,
                "build_electricity",
                side_effect=RuntimeError("secreto interno"),
            ),
            self.assertLogs("app.main", level="ERROR") as logs,
        ):
            response = client.get(
                "/api/v1/energy/electricity",
                params={"start": "2026-01-01", "end": "2026-01-02"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secreto", response.text)
        self.assertIn("secreto interno", logs.output[0])


class DaylightSavingTest(unittest.TestCase):
    @staticmethod
    def _day_hours(day: date) -> float:
        start, end = electricity_service._range_bounds(day, day)
        return electricity_service._Bucket(start, end).hours

    def test_day_buckets_measure_real_hours(self):
        self.assertEqual(self._day_hours(date(2026, 3, 29)), 23.0)
        self.assertEqual(self._day_hours(date(2026, 10, 25)), 25.0)
        self.assertEqual(self._day_hours(date(2026, 6, 15)), 24.0)


class BrokenSensorsTest(unittest.TestCase):
    def test_non_finite_counters_are_not_values(self):
        for state in ("nan", "inf", "-inf", "unavailable", None):
            with self.subTest(state=state):
                self.assertIsNone(parse_counter_value(state, None))
        self.assertIsNone(net_occupancy(parse_counter_value("nan", None), 1.0, 100))

    def test_current_value_rejects_nan(self):
        latest = {"sensor.x": ("nan", None, clock.utc_now())}
        self.assertEqual(
            environment_service._current_from_raw(latest, "sensor.x", 0.0, 50.0),
            (None, None),
        )

    def test_a_drop_in_the_long_term_sum_is_not_consumption(self):
        start = datetime(2026, 1, 1, 10)
        rows = [
            (start, 50_000.0),
            (start + timedelta(hours=1), 50_010.0),
            (start + timedelta(hours=2), 49_000.0),
            (start + timedelta(hours=3), 49_005.0),
        ]
        increments = environment_service._hourly_increments(rows)
        self.assertEqual(sorted(increments.values()), [5.0, 10.0])

    def test_motion_sensor_without_changes_keeps_its_last_state(self):
        start = datetime(2026, 10, 30, 10)
        end = start + timedelta(hours=3)
        self.assertEqual(sorted(_hourly_presence([], "No", start, end).values()), [0.0] * 3)
        self.assertEqual(sorted(_hourly_presence([], "Sí", start, end).values()), [1.0] * 3)


class LightingBucketsTest(unittest.TestCase):
    def test_buckets_never_include_hours_that_have_not_happened(self):
        now = datetime(2026, 11, 9, 10, 30, tzinfo=local_tz())
        limit = now.replace(minute=0) + timedelta(hours=1)
        for range_, count in (("day", 24), ("week", 7), ("month", 30), ("year", 12)):
            with self.subTest(range=range_), patch.object(
                lighting_context, "local_now", return_value=now
            ):
                buckets = lighting_context.build_buckets(range_)
                self.assertEqual(len(buckets), count)
                self.assertEqual(buckets[-1].end, limit)


class RepositorySqlTest(unittest.TestCase):
    """The mapped models must keep producing the read-only MySQL statements."""

    def test_latest_state_subquery_compiles_for_mysql(self):
        subquery = repository._latest_state_ids(
            ["sensor.x"], datetime(2026, 1, 2), timedelta(days=1)
        )
        sql = str(subquery.compile(dialect=mysql.dialect()))
        self.assertIn("max(states.state_id)", sql)
        self.assertIn("GROUP BY states.entity_id", sql)


if __name__ == "__main__":
    unittest.main()
