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

    def test_meta_lists_buildings(self):
        response = client.get("/api/v1/meta/buildings")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(len(body["buildings"]), 2)
        for building in body["buildings"]:
            self.assertTrue(building["id"])
            self.assertTrue(building["label"])


if __name__ == "__main__":
    unittest.main()
