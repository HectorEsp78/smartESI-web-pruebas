import unittest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class EnergyDecisionEndpointsTest(unittest.TestCase):
    def test_breakdown_base_and_activity_add_up_to_total(self):
        body = client.get("/api/v1/energy/breakdown", params={"range": "month"}).json()
        self.assertAlmostEqual(body["base_total"] + body["activity_total"], body["total"], places=0)
        self.assertAlmostEqual(
            body["lighting_total"] + body["other_total"], body["total"], places=0
        )
        self.assertGreaterEqual(body["base_share"], 0.0)
        self.assertLessEqual(body["base_share"], 1.0)

    def test_compare_has_previous_period(self):
        body = client.get("/api/v1/energy/compare", params={"range": "month"}).json()
        self.assertGreaterEqual(body["current_total"], 0.0)
        self.assertGreaterEqual(body["previous_total"], 0.0)
        self.assertEqual(len(body["series"]), 30)

    def test_efficiency_normalizes_by_area(self):
        body = client.get("/api/v1/energy/efficiency", params={"range": "month"}).json()
        self.assertGreater(body["avg_kwh_per_m2"], 0.0)
        for space in body["spaces"]:
            self.assertGreater(space["area_m2"], 0.0)
            self.assertGreaterEqual(space["kwh_per_m2"], 0.0)

    def test_decisions_rank_opportunities(self):
        body = client.get("/api/v1/decisions/opportunities", params={"range": "month"}).json()
        self.assertGreater(len(body["items"]), 0)
        savings = [item["savings_eur_year"] for item in body["items"]]
        self.assertEqual(savings, sorted(savings, reverse=True))
        expected = sum(
            item["savings_eur_year"] for item in body["items"] if item["category"] != "tendencia"
        )
        self.assertAlmostEqual(body["total_savings_eur_year"], expected, places=1)


if __name__ == "__main__":
    unittest.main()
