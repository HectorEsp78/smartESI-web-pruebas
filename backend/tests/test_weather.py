import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.services import weather_service

client = TestClient(app)


class WeatherEndpointsTest(unittest.TestCase):
    def setUp(self):
        weather_service.clear_cache()

    def tearDown(self):
        weather_service.clear_cache()

    def test_overview_has_current_summary_series_and_crosses(self):
        response = client.get("/api/v1/weather/overview", params={"days": 30})
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["data_source"], "mock")
        self.assertEqual(body["days"], 30)
        self.assertEqual(body["granularity"], "day")
        self.assertEqual(body["current"]["status"], "ok")
        self.assertIsNotNone(body["current"]["temperature_c"])
        self.assertIsNotNone(body["current"]["humidity_pct"])
        self.assertIsNotNone(body["current"]["pressure_hpa"])
        self.assertIsNotNone(body["current"]["dew_point_c"])
        self.assertIsNotNone(body["current"]["absolute_humidity_g_m3"])

        self.assertGreater(body["summary"]["samples"], 0)
        self.assertGreater(body["summary"]["coverage_pct"], 0)
        self.assertLessEqual(body["summary"]["coverage_pct"], 100)
        self.assertIsNotNone(body["summary"]["temperature_avg_c"])
        self.assertIsNotNone(body["summary"]["heating_degree_days"])

        self.assertEqual(len(body["daily"]), 31)
        self.assertGreater(len(body["series"]), 0)
        start = datetime.fromisoformat(body["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(body["end"].replace("Z", "+00:00"))
        for point in body["series"]:
            timestamp = datetime.fromisoformat(point["timestamp"].replace("Z", "+00:00"))
            # Daily buckets are stamped at local midnight, which can fall just
            # before the exact start instant of the first partial day.
            self.assertGreaterEqual(timestamp, start - timedelta(days=1))
            self.assertLessEqual(timestamp, end + timedelta(days=1))

        self.assertTrue(body["indoor_cross"]["available"])
        self.assertTrue(body["aemet_cross"]["available"])
        self.assertTrue(body["energy_cross"]["available"])
        self.assertTrue(body["pm_cross"]["available"])
        self.assertEqual(len(body["aemet_cross"]["hourly_bias"]), 24)
        self.assertTrue(body["pm_cross"]["caveat"])
        self.assertTrue(body["notes"])

    def test_allowed_periods_and_granularity(self):
        for days, granularity in ((7, "hour"), (30, "day"), (90, "day")):
            with self.subTest(days=days):
                response = client.get(
                    "/api/v1/weather/overview", params={"days": days}
                )
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["days"], days)
                self.assertEqual(body["granularity"], granularity)
                self.assertEqual(len(body["daily"]), days + 1)
                if days == 7:
                    self.assertGreaterEqual(len(body["series"]), 160)

        response = client.get("/api/v1/weather/overview", params={"days": 14})
        self.assertEqual(response.status_code, 422)
        self.assertIn("7, 30, 90", response.json()["detail"])

    def test_mock_energy_cross_does_not_exclude_normal_days(self):
        response = client.get("/api/v1/weather/overview", params={"days": 30})
        self.assertEqual(response.status_code, 200)
        energy = response.json()["energy_cross"]
        self.assertGreater(energy["days"], 0)
        self.assertEqual(energy["excluded_days"], 0)
        self.assertIsNotNone(energy["gas_m3"])
        self.assertIsNotNone(energy["electricity_kwh"])
        self.assertIsNotNone(energy["temperature_gas_correlation"])

    def test_mock_aemet_cross_has_day_and_night_bias(self):
        response = client.get("/api/v1/weather/overview", params={"days": 30})
        self.assertEqual(response.status_code, 200)
        cross = response.json()["aemet_cross"]
        self.assertIsNotNone(cross["daytime_temperature_bias_c"])
        self.assertIsNotNone(cross["nighttime_temperature_bias_c"])
        self.assertIsNotNone(cross["temperature_correlation"])
        self.assertIsNotNone(cross["pressure_bias_hpa"])

    def test_overview_is_deterministic_for_the_same_window(self):
        first = client.get("/api/v1/weather/overview", params={"days": 30}).json()
        second = client.get("/api/v1/weather/overview", params={"days": 30}).json()
        self.assertEqual(first["summary"], second["summary"])
        self.assertEqual(first["series"], second["series"])
        self.assertEqual(first["daily"], second["daily"])
        self.assertEqual(first["energy_cross"], second["energy_cross"])
