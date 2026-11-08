import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.core.maintenance_map import DEVICES_BY_ID, EVENT_OFFLINE_HOURS
from app.main import app
from app.services import maintenance_service
from app.services.maintenance_service import (
    _Period,
    _analyze_heartbeat,
    estimate_pct_from_mv,
)

client = TestClient(app)

MATRIX_CATEGORIES = {
    "correcto",
    "revisar_dispositivo",
    "cambiar_bateria",
    "bateria_y_dispositivo",
    "sin_lectura_bateria",
    "revisar_sin_datos",
}


class MaintenanceEndpointsTest(unittest.TestCase):
    def setUp(self):
        maintenance_service.clear_cache()

    def tearDown(self):
        maintenance_service.clear_cache()

    def test_overview_has_the_full_device_catalogue(self):
        response = client.get("/api/v1/maintenance/overview", params={"days": 30})
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["data_source"], "mock")
        self.assertEqual(body["days"], 30)
        self.assertEqual(len(body["devices"]), 52)
        self.assertEqual(body["summary"]["devices_total"], 52)
        self.assertEqual(body["summary"]["with_battery"], 38)
        self.assertGreater(len(body["heatmap"]), 0)
        self.assertTrue(body["notes"])

        for device in body["devices"]:
            self.assertIn("battery", device)
            self.assertIn("heartbeat", device)
            self.assertIn("availability", device)
            self.assertIn(device["matrix_category"], MATRIX_CATEGORIES)
            self.assertTrue(device["decision"])
            self.assertNotIn("battery_history", device)

    def test_allowed_periods_and_invalid_period(self):
        for days in (7, 30, 90):
            with self.subTest(days=days):
                response = client.get(
                    "/api/v1/maintenance/overview", params={"days": days}
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["days"], days)

        response = client.get("/api/v1/maintenance/overview", params={"days": 14})
        self.assertEqual(response.status_code, 422)
        self.assertIn("7, 30 o 90", response.json()["detail"])

    def test_device_detail_contains_battery_history_and_daily_coverage(self):
        response = client.get(
            "/api/v1/maintenance/devices/shelly1", params={"days": 30}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["device"]["id"], "shelly1")
        self.assertEqual(body["device"]["mode"], "periodic")
        self.assertGreater(len(body["battery_history"]), 0)
        self.assertEqual(len(body["daily"]), 31)
        for point in body["battery_history"]:
            self.assertIn(point["unit"], {"percent", "millivolt"})

    def test_unknown_device_returns_404(self):
        response = client.get("/api/v1/maintenance/devices/NO-EXISTE")
        self.assertEqual(response.status_code, 404)

    def test_decisions_cover_low_battery_and_missing_data(self):
        body = client.get(
            "/api/v1/maintenance/overview", params={"days": 30}
        ).json()

        self.assertGreater(body["summary"]["low_battery"], 0)
        self.assertGreater(body["summary"]["no_data"], 0)
        self.assertGreater(body["summary"]["replacements_detected"], 0)

        categories = {device["matrix_category"] for device in body["devices"]}
        self.assertTrue(categories <= MATRIX_CATEGORIES)
        self.assertIn("cambiar_bateria", categories)

    def test_global_outage_is_detected_and_not_split_into_device_failures(self):
        body = client.get(
            "/api/v1/maintenance/overview", params={"days": 30}
        ).json()

        self.assertGreaterEqual(body["summary"]["global_outages"], 1)
        global_outages = [
            outage for outage in body["outages"] if outage["scope"] == "global"
        ]
        self.assertTrue(global_outages)
        self.assertGreaterEqual(global_outages[0]["device_count"], 3)
        self.assertGreater(global_outages[0]["duration_hours"], 24)

    def test_forecast_horizons_are_monotonic(self):
        summary = client.get(
            "/api/v1/maintenance/overview", params={"days": 30}
        ).json()["summary"]

        self.assertLessEqual(
            summary["forecast_replace_30d"], summary["forecast_replace_60d"]
        )
        self.assertLessEqual(
            summary["forecast_replace_60d"], summary["forecast_replace_90d"]
        )

    def test_event_devices_are_not_flagged_for_short_silence(self):
        body = client.get(
            "/api/v1/maintenance/overview", params={"days": 30}
        ).json()

        for device in body["devices"]:
            if device["mode"] != "event":
                continue
            silence = device["heartbeat"]["silence_hours"]
            if silence is not None and silence <= EVENT_OFFLINE_HOURS:
                self.assertTrue(device["data_ok"], device["id"])


class MaintenanceHelpersTest(unittest.TestCase):
    def test_millivolt_curve(self):
        self.assertEqual(estimate_pct_from_mv(3600), 100)
        self.assertEqual(estimate_pct_from_mv(2900), 0)
        self.assertAlmostEqual(estimate_pct_from_mv(3200), 20)
        self.assertAlmostEqual(estimate_pct_from_mv(3400), 60)
        self.assertAlmostEqual(estimate_pct_from_mv(3300), 40)

    def test_heartbeat_gap_detection(self):
        device = DEVICES_BY_ID["shelly1"]
        start = datetime(2026, 10, 1, 0, 0)
        end = start + timedelta(days=7)
        times = []
        cursor = start - timedelta(hours=2)
        while cursor <= end:
            # Three-day silence in the middle of the period.
            if not (datetime(2026, 10, 3) <= cursor < datetime(2026, 10, 6)):
                times.append(cursor)
            cursor += timedelta(hours=2)

        analysis = _analyze_heartbeat(device, times, _Period(start, end, 7))

        self.assertTrue(analysis.gaps)
        longest = max(gap.duration_hours for gap in analysis.gaps)
        self.assertGreater(longest, 48)

    def test_default_period_is_thirty_days(self):
        period = maintenance_service.resolve_period()
        self.assertEqual(period.days, 30)
        self.assertAlmostEqual(
            (period.end - period.start).total_seconds() / 86400.0, 30.0, places=3
        )

    def test_invalid_period_raises(self):
        with self.assertRaises(ValueError):
            maintenance_service.resolve_period(14)


if __name__ == "__main__":
    unittest.main()
