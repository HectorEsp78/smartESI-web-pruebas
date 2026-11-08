import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.db.environment_data import _hourly_presence
from app.main import app
from app.services import environment_service
from app.services.environment_service import _series_timestamp

client = TestClient(app)

EXPECTED_ROOMS = {"A11", "A12", "A21", "A22", "F0.2", "ALU", "AnitaBorg"}


class EnvironmentEndpointsTest(unittest.TestCase):
    def setUp(self):
        environment_service.clear_cache()

    def tearDown(self):
        environment_service.clear_cache()

    def test_overview_has_confirmed_rooms_and_custom_period(self):
        response = client.get(
            "/api/v1/environment/overview",
            params={"start": "2026-10-01", "end": "2026-10-07"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data_source"], "mock")
        self.assertEqual(body["granularity"], "hour")
        self.assertEqual(body["summary"]["rooms_total"], 7)
        self.assertEqual({room["room_id"] for room in body["rooms"]}, EXPECTED_ROOMS)
        for room in body["rooms"]:
            self.assertNotIn("series", room)

    def test_granularity_adapts_to_period_length(self):
        cases = [
            ("2026-10-01", "2026-10-07", "hour"),
            ("2026-01-01", "2026-04-30", "day"),
            ("2025-01-01", "2025-12-31", "week"),
        ]
        for start, end, expected in cases:
            with self.subTest(start=start, end=end):
                response = client.get(
                    "/api/v1/environment/overview",
                    params={"start": start, "end": end},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["granularity"], expected)

    def test_only_a11_to_a22_have_climate_and_co2(self):
        body = client.get(
            "/api/v1/environment/overview",
            params={"start": "2026-10-01", "end": "2026-10-07"},
        ).json()
        rooms = {room["room_id"]: room for room in body["rooms"]}

        for room_id in ("A11", "A12", "A21", "A22"):
            room = rooms[room_id]
            self.assertTrue(room["has_temperature"])
            self.assertTrue(room["has_humidity"])
            self.assertTrue(room["has_co2"])
            self.assertTrue(room["has_presence"])
            self.assertIsNotNone(room["current_temperature_c"])
            self.assertIsNotNone(room["current_co2_ppm"])

        for room_id in ("F0.2", "ALU", "AnitaBorg"):
            room = rooms[room_id]
            self.assertFalse(room["has_temperature"])
            self.assertFalse(room["has_humidity"])
            self.assertFalse(room["has_co2"])
            self.assertTrue(room["has_presence"])

    def test_room_detail_contains_charts_and_cross_statistics(self):
        response = client.get(
            "/api/v1/environment/rooms/A11",
            params={"start": "2026-10-01", "end": "2026-10-07"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["room"]["room_id"], "A11")
        self.assertEqual(len(body["series"]), 7 * 24)
        self.assertEqual(len(body["heatmap"]), 7 * 24)
        self.assertEqual(body["benchmark"]["rooms_temperature"], 3)
        self.assertEqual(body["benchmark"]["rooms_presence"], 6)
        self.assertIsNotNone(body["co2_occupancy"]["occupied_co2_ppm"])
        self.assertIsNotNone(body["thermal_recovery"]["baseline_temperature_c"])
        self.assertTrue(body["context"]["has_gas"])
        self.assertIsNotNone(body["context"]["gas_cost_eur"])
        self.assertIsNotNone(body["series"][0]["ambient_temperature_c"])

    def test_presence_only_room_has_no_climate_crosses(self):
        body = client.get(
            "/api/v1/environment/rooms/F0.2",
            params={"start": "2026-10-01", "end": "2026-10-07"},
        ).json()

        self.assertFalse(body["room"]["has_temperature"])
        self.assertFalse(body["room"]["has_co2"])
        self.assertTrue(body["room"]["has_presence"])
        self.assertEqual(body["thermal_recovery"]["transitions"], 0)
        self.assertIsNone(body["co2_occupancy"]["occupied_co2_ppm"])
        self.assertIsNotNone(body["heatmap"][0]["presence_pct"])
        self.assertIsNone(body["heatmap"][0]["co2_ppm"])

    def test_invalid_period_is_rejected(self):
        for params in (
            {"start": "2026-10-10", "end": "2026-10-01"},
            {"start": "2025-01-01", "end": "2026-12-31"},
            {"start": "2099-01-01", "end": "2099-01-02"},
        ):
            with self.subTest(params=params):
                response = client.get("/api/v1/environment/overview", params=params)
                self.assertEqual(response.status_code, 422)

    def test_unknown_room_returns_404(self):
        response = client.get("/api/v1/environment/rooms/NO-EXISTE")
        self.assertEqual(response.status_code, 404)

    def test_default_period_is_last_seven_days(self):
        period = environment_service.resolve_period()
        self.assertEqual(period.days, 7)
        self.assertEqual((period.end_date - period.start_date).days, 6)


class EnvironmentPresenceTest(unittest.TestCase):
    def test_motion_transitions_are_weighted_by_time(self):
        start = datetime(2026, 10, 30, 10, 0)
        end = start + timedelta(hours=2)
        rows = [
            ("sensor.movimiento_a11", start + timedelta(minutes=15), "Sí"),
            ("sensor.movimiento_a11", start + timedelta(minutes=45), "No"),
        ]

        series = _hourly_presence(rows, "No", start, end)

        self.assertEqual(sorted(series.values()), [0.0, 0.5])

    def test_unknown_baseline_is_treated_as_empty(self):
        start = datetime(2026, 10, 30, 10, 0)
        end = start + timedelta(hours=1)
        rows = [("sensor.movimiento_a11", start + timedelta(minutes=15), "Sí")]

        series = _hourly_presence(rows, "unavailable", start, end)

        self.assertEqual(list(series.values()), [0.75])

    def test_current_hour_timestamp_never_looks_into_the_future(self):
        key = datetime(2026, 10, 30, 10, 0)
        now = key + timedelta(minutes=15)

        self.assertEqual(_series_timestamp(key, now), now)
        self.assertEqual(
            _series_timestamp(key - timedelta(hours=1), now),
            key,
        )


if __name__ == "__main__":
    unittest.main()
