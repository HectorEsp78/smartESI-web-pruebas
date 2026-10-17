import unittest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_POINTS = {"day": 24, "week": 7, "month": 30, "year": 12}
VALID_STATUS = {"ok", "fria", "valvula_abierta", "valvula_cerrada"}


class ClimateEndpointsTest(unittest.TestCase):
    def test_gas_series_and_degree_days(self):
        for range_, count in EXPECTED_POINTS.items():
            with self.subTest(range=range_):
                response = client.get("/api/v1/climate/gas", params={"range": range_})
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(len(body["series"]), count)
                self.assertGreaterEqual(body["stats"]["total_gas"], 0.0)
                self.assertGreaterEqual(body["stats"]["total_degree_days"], 0.0)
                self.assertGreaterEqual(body["stats"]["correlation_degree_days"], -1.0)
                self.assertLessEqual(body["stats"]["correlation_degree_days"], 1.0)

    def test_valves_return_every_space(self):
        body = client.get("/api/v1/climate/valves", params={"range": "month"}).json()
        self.assertGreater(len(body["spaces"]), 0)
        self.assertGreater(len(body["series"]), 0)
        for space in body["spaces"]:
            self.assertIn(space["status"], VALID_STATUS)
            self.assertGreaterEqual(space["valve_open_pct"], 0.0)
            self.assertLessEqual(space["valve_open_pct"], 100.0)

    def test_empty_spaces_annualized_is_at_least_cost(self):
        body = client.get("/api/v1/climate/empty-spaces", params={"range": "month"}).json()
        self.assertGreaterEqual(body["total_annualized_cost_eur"], body["total_cost_eur"])
        self.assertGreater(len(body["spaces"]), 0)

    def test_unknown_building_returns_404(self):
        response = client.get("/api/v1/climate/gas", params={"building": "nope"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
