"""
Automated Test Suite for D-SQUARE 2.0 Standalone PC SOS Alert Sending System
"""

import unittest
import json
import app as flask_app
import database


class TestPCSOSAlertSystem(unittest.TestCase):

    def setUp(self):
        database.init_db()
        self.app = flask_app.app.test_client()
        self.app.testing = True

    def test_01_pc_sos_alert_page_loads(self):
        """Verifies /pc_sos_alert HTML page renders correctly."""
        resp = self.app.get("/pc_sos_alert")
        self.assertEqual(resp.status_code, 200)
        html_str = resp.data.decode("utf-8")
        self.assertIn("STANDALONE PC SOS ALERT CENTER", html_str)
        self.assertIn("disaster-map", html_str)
        self.assertIn("btn-trigger-pc-sos", html_str)

    def test_02_live_disaster_pixels_api(self):
        """Verifies /api/pc/live_disaster_pixels returns spatial pixel grid & telemetry."""
        resp = self.app.get("/api/pc/live_disaster_pixels")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["total_pixels"], 0)
        self.assertIn("pixels", data)
        self.assertIn("telemetry", data)

        px = data["pixels"][0]
        self.assertIn("pixel_id", px)
        self.assertIn("bounds", px)
        self.assertIn("severity", px)
        self.assertIn("risk_level", px)

    def test_03_pc_sos_alert_trigger_flow(self):
        """Verifies trigger parallel alert flow from PC alert sending system."""
        payload = {
            "disaster_type": "FLOOD",
            "severity": "CRITICAL",
            "area_name": "Mumbai Coastal Zone Sector 1",
            "affected_population": 12000,
            "latitude": 19.0760,
            "longitude": 72.8777
        }
        resp = self.app.post("/api/v1/trigger-sos-alert", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("alert_id", data)
        self.assertIn("dispatch_details", data)

        rescue_alert = data["dispatch_details"]["rescue_gpt_alert"]
        public_alert = data["dispatch_details"]["dsquare_gpt_alert"]

        self.assertEqual(rescue_alert["alert_type"], "SOS_RESCUE")
        self.assertEqual(public_alert["alert_type"], "SOS_PUBLIC")
        self.assertLess(data["dispatch_details"]["dispatch_latency_ms"], 30000)


if __name__ == "__main__":
    unittest.main()
