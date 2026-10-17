import unittest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class HealthEndpointsTest(unittest.TestCase):
    def test_root(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_live_reports_data_source(self):
        response = client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data_source"], "mock")

    def test_ready(self):
        response = client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_meta_lists_buildings_and_spaces(self):
        response = client.get("/api/v1/meta/buildings")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(len(body["buildings"]), 2)
        self.assertGreater(len(body["spaces"]), 0)
        for building in body["buildings"]:
            self.assertGreater(building["area_m2"], 0)
            self.assertGreater(building["lighting_kw"], 0)
            self.assertGreater(building["setpoint_c"], 0)
        for space in body["spaces"]:
            self.assertGreater(space["area_m2"], 0)
            self.assertIn("has_valve", space)


if __name__ == "__main__":
    unittest.main()
