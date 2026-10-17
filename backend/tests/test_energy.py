import unittest

from fastapi.testclient import TestClient

from app.main import app

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
        self.assertGreater(len(body["spaces"]), 0)


if __name__ == "__main__":
    unittest.main()
