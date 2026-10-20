import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.entity_map import SITE_ENERGY_KEY
from app.main import app
from app.services.energy_service import (
    _EnergyProvider,
    build_buckets,
    build_by_building,
    build_consumption,
    clear_cache,
)

client = TestClient(app)


class EnergyEndpointsTest(unittest.TestCase):
    def test_consumption_returns_expected_number_of_points(self):
        expected_points = {"day": 24, "week": 7, "month": 30, "year": 12}

        for range_, count in expected_points.items():
            with self.subTest(range=range_):
                response = client.get(
                    "/api/v1/energy/consumption", params={"range": range_}
                )
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(len(body["series"]), count)
                self.assertGreater(body["total"], 0)
                self.assertIsNotNone(body["peak"])

    def test_metric_conversion_uses_configured_factors(self):
        kwh = client.get(
            "/api/v1/energy/consumption", params={"range": "week", "metric": "kwh"}
        ).json()["total"]
        cost = client.get(
            "/api/v1/energy/consumption", params={"range": "week", "metric": "cost"}
        ).json()["total"]
        co2 = client.get(
            "/api/v1/energy/consumption", params={"range": "week", "metric": "co2"}
        ).json()["total"]

        self.assertAlmostEqual(cost, kwh * 0.20, places=1)
        self.assertAlmostEqual(co2, kwh * 0.15, places=1)

    def test_unknown_building_returns_404(self):
        response = client.get(
            "/api/v1/energy/consumption", params={"building": "does-not-exist"}
        )
        self.assertEqual(response.status_code, 404)

    def test_by_building_shares_add_up_to_one(self):
        response = client.get("/api/v1/energy/by-building", params={"range": "month"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        total_share = sum(building["share"] for building in body["buildings"])
        self.assertAlmostEqual(total_share, 1.0, places=2)
        self.assertAlmostEqual(body["coverage"], 1.0, places=4)
        self.assertAlmostEqual(body["unmetered_total"], 0.0, places=2)
        self.assertGreater(len(body["spaces"]), 0)


class SiteMeterAggregationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        clear_cache()

    async def asyncTearDown(self):
        clear_cache()

    async def test_all_buildings_uses_the_site_meter_and_reports_coverage(self):
        buckets = build_buckets("day")
        provider = _EnergyProvider(
            {
                SITE_ENERGY_KEY: {bucket.start: 100.0 for bucket in buckets},
                "FerminCaballero": {bucket.start: 10.0 for bucket in buckets},
                "ModuloB": {bucket.start: 5.0 for bucket in buckets},
            }
        )

        with patch(
            "app.services.energy_service._load_provider",
            new=AsyncMock(return_value=provider),
        ):
            all_buildings = await build_consumption("day", "all", "kwh")
            fermin = await build_consumption("day", "FerminCaballero", "kwh")
            by_building = await build_by_building("day", "kwh")

        self.assertAlmostEqual(all_buildings.total, 2400.0, places=2)
        self.assertAlmostEqual(fermin.total, 240.0, places=2)

        self.assertAlmostEqual(by_building.total, 2400.0, places=2)
        self.assertAlmostEqual(by_building.submetered_total, 360.0, places=2)
        self.assertAlmostEqual(by_building.unmetered_total, 2040.0, places=2)
        self.assertAlmostEqual(by_building.coverage, 0.15, places=4)
        self.assertAlmostEqual(
            sum(building.share for building in by_building.buildings), 0.15, places=4
        )


if __name__ == "__main__":
    unittest.main()
