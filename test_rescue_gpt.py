"""
Unit Test Suite for D-SQUARE Rescue GPT
Verifies dual-role AI disaster guidance, survival probability calculator, hazard avoidance routing, and API endpoints.
"""

import unittest
import json
from app import app

class TestRescueGPT(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_rescue_chat_victim_trapped(self):
        res = self.client.post("/api/rescue_chat", json={
            "user_type": "victim",
            "message": "I'm trapped under debris after a landslide collapse!",
            "disaster_type": "landslide",
            "location": {"lat": 30.0668, "lon": 79.0193}
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("LANDSLIDE RESCUE GUIDANCE", data["response"])
        self.assertTrue(data["call_112_recommended"])
        self.assertIn("call_112_recommended", data["actions"])

    def test_02_rescue_chat_rescue_team_route(self):
        res = self.client.post("/api/rescue_chat", json={
            "user_type": "rescue_team",
            "message": "What's the optimal route to victim at 30.0668°N, 79.0193°E?",
            "disaster_type": "landslide",
            "location": {"lat": 30.0668, "lon": 79.0193}
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("RESCUE ROUTE OPTIMIZATION", data["response"])
        self.assertIn("route", data)
        self.assertGreater(data["route"]["distance_km"], 0.0)

    def test_03_survival_probability_calculator(self):
        res = self.client.get("/api/survival_probability?time_trapped=180&injury_type=bleeding&temp=8.0&water_exposure=true")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("probability", data)
        self.assertLess(data["probability"], 0.60) # High risk decay
        self.assertIn("hypothermia", data["recommendation"].lower())

    def test_04_trigger_rescue_dispatch(self):
        res = self.client.post("/api/trigger_rescue", json={
            "victim_location": {"lat": 30.0668, "lon": 79.0193},
            "disaster_type": "landslide",
            "severity": "critical"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("NDRF_DISPATCH", data["dispatch_id"])

    def test_05_rescue_gpt_page_load(self):
        res = self.client.get("/rescue_gpt")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"D-SQUARE Rescue GPT", res.data)


if __name__ == "__main__":
    unittest.main()
