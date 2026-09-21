"""
Automated Test Suite for D-SQUARE GPT Weather Conversational AI & PC Alert Integrator
"""

import unittest
import json
import app as flask_app
import database
from services.parallel_sos_engine import ParallelSOSAlertEngine


class TestDSquareGPTWeatherAI(unittest.TestCase):

    def setUp(self):
        database.init_db()
        self.app = flask_app.app.test_client()
        self.app.testing = True

    def test_01_dsquare_gpt_portal_loads(self):
        """Verifies /dsquare_gpt HTML portal loads correctly."""
        resp = self.app.get("/dsquare_gpt")
        self.assertEqual(resp.status_code, 200)
        html_str = resp.data.decode("utf-8")
        self.assertIn("D-SQUARE GPT", html_str)
        self.assertIn("Weather Conversational AI", html_str)
        self.assertIn("chat-box", html_str)

    def test_02_weather_telemetry_api(self):
        """Verifies /api/public/weather_telemetry returns instant weather, satellite pixels, and history."""
        resp = self.app.get("/api/public/weather_telemetry")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("instant_weather", data)
        self.assertIn("satellite_pixels", data)
        self.assertIn("previous_weather", data)
        self.assertGreater(data["instant_weather"]["temperature_c"], 0)

    def test_03_instant_weather_conversational_query(self):
        """Verifies conversational AI query for instant weather updates."""
        payload = {"query": "What is the instant weather update?", "language": "en"}
        resp = self.app.post("/api/public/assistant_query", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["category"], "INSTANT_WEATHER")
        self.assertIn("Temperature", data["response"])
        self.assertIn("Rainfall Rate", data["response"])

    def test_04_satellite_pixels_conversational_query(self):
        """Verifies conversational AI query for satellite pixel telemetry."""
        payload = {"query": "Show satellite pixel information for NISAR", "language": "en"}
        resp = self.app.post("/api/public/assistant_query", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["category"], "SATELLITE_PIXELS")
        self.assertIn("NISAR Satellite Pixel Analysis", data["response"])
        self.assertIn("NDWI Inundation", data["response"])

    def test_05_previous_weather_data_query(self):
        """Verifies conversational AI query for previous 24h weather data and historical trend."""
        payload = {"query": "What was the previous 24h weather data trend?", "language": "en"}
        resp = self.app.post("/api/public/assistant_query", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["category"], "PREVIOUS_WEATHER")
        self.assertIn("Previous 24-Hour Weather", data["response"])

    def test_06_receive_alert_from_pc_sos_alert_center(self):
        """Verifies D-SQUARE GPT receives and displays active alerts sent from PC SOS Alert Center."""
        # 1. Trigger an alert from PC SOS Alert Center
        sos_engine = ParallelSOSAlertEngine()
        alert_payload = {
            "disaster_type": "FLOOD",
            "severity": "CRITICAL",
            "area_name": "Mumbai Coastal Zone Sector 1",
            "affected_population": 9500,
            "latitude": 19.0760,
            "longitude": 72.8777
        }
        dispatch_res = sos_engine.dispatch_parallel_sos(alert_payload)
        database.save_parallel_sos_alert(dispatch_res)

        # 2. Query D-SQUARE GPT for active PC alert status
        query_payload = {"query": "Check active PC SOS Alert status", "language": "en"}
        resp = self.app.post("/api/public/assistant_query", json=query_payload)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["has_active_pc_alert"])
        self.assertIn("ACTIVE PC SOS ALERT RECEIVED", data["response"])
        self.assertIn("Mumbai Coastal Zone", data["response"])


if __name__ == "__main__":
    unittest.main()
