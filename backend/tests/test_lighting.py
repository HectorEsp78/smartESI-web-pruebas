import unittest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_POINTS = {"day": 24, "week": 7, "month": 30, "year": 12}


class LightingEndpointsTest(unittest.TestCase):
    def test_consumption_splits_lighting_and_other(self):
        for range_, count in EXPECTED_POINTS.items():
            with self.subTest(range=range_):
                response = client.get("/api/v1/lighting/consumption", params={"range": range_})
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(len(body["series"]), count)
                self.assertAlmostEqual(
                    body["lighting_total"] + body["other_total"], body["total"], places=1
                )
                self.assertGreater(body["lighting_share"], 0.0)
                self.assertLess(body["lighting_share"], 1.0)

    def test_by_space_shares_add_up_to_one(self):
        body = client.get(
            "/api/v1/lighting/by-space", params={"range": "month"}
        ).json()
        total = sum(space["share_of_lighting"] for space in body["spaces"])
        self.assertAlmostEqual(total, 1.0, places=2)
        self.assertGreater(len(body["spaces"]), 0)

    def test_waste_is_a_subset_of_total_lighting(self):
        body = client.get("/api/v1/lighting/waste", params={"range": "month"}).json()
        self.assertLessEqual(body["waste_lighting"], body["total_lighting"])
        self.assertGreater(body["annualized_cost_eur"], body["waste_cost_eur"])

    def test_unknown_building_returns_404(self):
        response = client.get(
            "/api/v1/lighting/consumption", params={"building": "nope"}
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
