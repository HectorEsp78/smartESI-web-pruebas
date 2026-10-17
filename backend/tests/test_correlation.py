import unittest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class CorrelationEndpointTest(unittest.TestCase):
    def test_points_and_stats_are_returned(self):
        response = client.get(
            "/api/v1/correlation/occupancy-air-quality", params={"range": "week"}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertGreater(len(body["points"]), 0)
        for point in body["points"]:
            self.assertGreaterEqual(point["occupancy"], 0)
            self.assertGreaterEqual(point["co2"], 0)

        r = body["stats"]["pearson_r"]
        self.assertGreaterEqual(r, -1.0)
        self.assertLessEqual(r, 1.0)

    def test_air_quality_breakdown_covers_all_samples(self):
        response = client.get(
            "/api/v1/correlation/occupancy-air-quality", params={"range": "day"}
        )
        stats = response.json()["stats"]
        breakdown = stats["good_pct"] + stats["moderate_pct"] + stats["poor_pct"]
        self.assertAlmostEqual(breakdown, 100.0, delta=0.5)

    def test_per_building_scope(self):
        response = client.get(
            "/api/v1/correlation/occupancy-air-quality",
            params={"range": "day", "building": "ModuloB"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["building_id"], "ModuloB")
        for point in body["points"]:
            self.assertEqual(point["capacity"], 160)


if __name__ == "__main__":
    unittest.main()
