import unittest
from datetime import date, datetime, time

from fastapi.testclient import TestClient

from app.core.clock import local_tz
from app.main import app
from app.services import electricity_service

client = TestClient(app)


class ElectricityEndpointsTest(unittest.TestCase):
    def setUp(self):
        electricity_service.clear_cache()

    def tearDown(self):
        electricity_service.clear_cache()

    def test_meta_lists_the_three_buildings_and_partial_sectors(self):
        response = client.get("/api/v1/energy/electricity/meta")
        self.assertEqual(response.status_code, 200)
        body = response.json()

        buildings = {building["id"]: building for building in body["buildings"]}
        self.assertEqual(set(buildings), {"ModuloA", "ModuloB", "FerminCaballero"})
        self.assertEqual(buildings["FerminCaballero"]["kind"], "residual")

        sectors = {sector["id"]: sector for sector in body["sectors"]}
        self.assertIn("CPD", sectors)
        self.assertFalse(sectors["PB_E"]["available"])
        self.assertEqual(body["price_eur_per_kwh"], 0.20)
        self.assertEqual(body["data_source"], "mock")

    def test_daily_series_and_building_totals_reconcile(self):
        response = client.get(
            "/api/v1/energy/electricity",
            params={
                "start": "2026-10-01",
                "end": "2026-10-07",
                "granularity": "day",
                "metric": "kwh",
                "building": "all",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(len(body["series"]), 7)
        self.assertEqual(len(body["buildings"]), 3)
        self.assertEqual(body["scope"], "all")
        self.assertGreater(body["site_total"], 0)
        self.assertGreater(body["stats"]["baseline_hourly"], 0)

        buildings_total = sum(building["total"] for building in body["buildings"])
        self.assertAlmostEqual(buildings_total, body["site_total"], places=1)
        self.assertAlmostEqual(body["stats"]["total"], body["site_total"], places=1)
        fermin = next(
            building
            for building in body["buildings"]
            if building["building_id"] == "FerminCaballero"
        )
        self.assertAlmostEqual(fermin["total"], body["fermin_total"], places=1)

        measured_sectors_total = sum(
            sector["total"] for sector in body["sectors"] if sector["has_data"]
        )
        self.assertAlmostEqual(measured_sectors_total, body["sectors_total"], places=1)
        self.assertAlmostEqual(
            body["sectors_total"] + body["unmetered_total"],
            body["fermin_total"],
            places=1,
        )
        self.assertGreaterEqual(body["sector_coverage"], 0.0)
        self.assertLessEqual(body["sector_coverage"], 1.0)

        for building in body["buildings"]:
            self.assertEqual(len(building["series"]), len(body["series"]))

    def test_cost_metric_uses_the_configured_price(self):
        params = {
            "start": "2026-10-01",
            "end": "2026-10-07",
            "granularity": "day",
            "building": "all",
        }
        kwh = client.get(
            "/api/v1/energy/electricity", params={**params, "metric": "kwh"}
        ).json()["stats"]["total"]
        cost = client.get(
            "/api/v1/energy/electricity", params={**params, "metric": "cost"}
        ).json()["stats"]["total"]

        self.assertAlmostEqual(cost, kwh * 0.20, places=1)

    def test_sector_scope_returns_the_sector_series(self):
        response = client.get(
            "/api/v1/energy/electricity",
            params={
                "start": "2026-10-01",
                "end": "2026-10-07",
                "granularity": "day",
                "metric": "kwh",
                "building": "FerminCaballero",
                "sector": "CPD",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        cpd = next(sector for sector in body["sectors"] if sector["sector_id"] == "CPD")

        self.assertEqual(body["scope"], "CPD")
        self.assertEqual(body["sector_id"], "CPD")
        self.assertIn("CPD", body["scope_label"])
        self.assertAlmostEqual(body["stats"]["total"], cpd["total"], places=1)

    def test_invalid_sector_for_building_returns_400(self):
        response = client.get(
            "/api/v1/energy/electricity",
            params={
                "start": "2026-10-01",
                "end": "2026-10-07",
                "granularity": "day",
                "building": "ModuloA",
                "sector": "CPD",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_comparison_overlays_equal_bucket_counts(self):
        response = client.get(
            "/api/v1/energy/electricity/compare",
            params={
                "start_a": "2026-10-01",
                "end_a": "2026-10-07",
                "start_b": "2025-10-01",
                "end_b": "2025-10-07",
                "granularity": "day",
                "metric": "kwh",
                "building": "ModuloA",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(len(body["series"]), 7)
        self.assertEqual(body["scope"], "ModuloA")
        self.assertEqual(body["period_a_days"], 7)
        self.assertEqual(body["period_b_days"], 7)
        self.assertGreater(body["period_a"]["total"], 0)
        self.assertGreater(body["period_b"]["total"], 0)
        self.assertGreater(body["baseline_hourly"], 0)
        self.assertEqual(body["series"][0]["index"], 0)

    def test_comparison_with_different_bucket_counts_returns_400(self):
        response = client.get(
            "/api/v1/energy/electricity/compare",
            params={
                "start_a": "2026-10-01",
                "end_a": "2026-10-07",
                "start_b": "2025-10-01",
                "end_b": "2025-10-06",
                "granularity": "day",
                "metric": "kwh",
                "building": "all",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("intervalos", response.json()["detail"])


class ElectricityHelpersTest(unittest.TestCase):
    def test_calendar_buckets_are_clipped_to_the_inclusive_range(self):
        day_buckets = electricity_service._build_buckets(
            date(2026, 10, 1), date(2026, 10, 7), "day"
        )
        self.assertEqual(len(day_buckets), 7)
        self.assertEqual(day_buckets[0].start.date(), date(2026, 10, 1))
        self.assertEqual(day_buckets[-1].end.date(), date(2026, 10, 8))

        # 1 Oct 2026 is a Thursday: the range touches two Monday-Sunday weeks.
        week_buckets = electricity_service._build_buckets(
            date(2026, 10, 1), date(2026, 10, 7), "week"
        )
        self.assertEqual(len(week_buckets), 2)
        self.assertEqual(week_buckets[0].start.date(), date(2026, 10, 1))
        self.assertEqual(week_buckets[-1].end.date(), date(2026, 10, 8))

        month_buckets = electricity_service._build_buckets(
            date(2026, 10, 1), date(2026, 10, 7), "month"
        )
        self.assertEqual(len(month_buckets), 1)

        year_buckets = electricity_service._build_buckets(
            date(2025, 12, 1), date(2026, 1, 31), "year"
        )
        self.assertEqual(len(year_buckets), 2)

    def test_closed_hours_are_nights_and_weekends(self):
        tz = local_tz()
        monday = date(2026, 10, 26)
        self.assertTrue(electricity_service._is_closed_hour(datetime.combine(monday, time(6, 59), tzinfo=tz)))
        self.assertFalse(electricity_service._is_closed_hour(datetime.combine(monday, time(7, 0), tzinfo=tz)))
        self.assertFalse(electricity_service._is_closed_hour(datetime.combine(monday, time(20, 59), tzinfo=tz)))
        self.assertTrue(electricity_service._is_closed_hour(datetime.combine(monday, time(21, 0), tzinfo=tz)))
        self.assertTrue(
            electricity_service._is_closed_hour(
                datetime.combine(date(2026, 10, 24), time(12, 0), tzinfo=tz)
            )
        )

    def test_fermin_is_the_non_negative_site_residual(self):
        hour = datetime(2026, 10, 1, 12, 0, tzinfo=local_tz())
        residual = electricity_service._build_fermin_residual(
            {hour: 10.0}, {hour: 2.0}, {hour: 3.0}
        )
        self.assertEqual(residual[hour], 5.0)

        clamped = electricity_service._build_fermin_residual(
            {hour: 2.0}, {hour: 3.0}, {hour: 1.0}
        )
        self.assertEqual(clamped[hour], 0.0)

    def test_scope_validation_accepts_all_with_a_sector(self):
        self.assertEqual(
            electricity_service._validate_scope("all", "CPD"),
            ("FerminCaballero", "CPD"),
        )
        with self.assertRaises(ValueError):
            electricity_service._validate_scope("ModuloA", "CPD")
        with self.assertRaises(ValueError):
            electricity_service._validate_scope("NoExiste", None)
