"""
D-SQUARE 2.0 PC Dashboard & Backend Integration Test Suite
Verifies 10-sensor telemetry schema completeness, SOS triggering,
CORS header presence, and disaster status reporting.
"""

import unittest
import json
from app import app, latest_sensor_data

class TestDashboardBackendIntegration(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_01_latest_sensor_data_schema_completeness(self):
        """Verify /api/latest_sensor_data returns all 10 hardware sensors"""
        res = self.app.get("/api/latest_sensor_data")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        required_keys = [
            "node_id", "temperature", "humidity", "soil_moisture", "soil_raw",
            "mq2_gas", "tilt", "vibration", "flame", "gyro_x", "gyro_y", "gyro_z",
            "disaster_type", "scenario", "timestamp"
        ]
        for key in required_keys:
            self.assertIn(key, data, f"Missing required sensor telemetry key: {key}")

    def test_02_sensor_data_post_updates_telemetry(self):
        """Verify POST /api/sensor_data updates ground telemetry"""
        payload = {
            "node_id": "D-SQUARE_NODE_01",
            "temperature": 32.4,
            "humidity": 78.5,
            "soil_raw": 550.0,  # High moisture triggering landslide
            "mq2_gas": 0,
            "tilt": 1,
            "vibration": 1,
            "flame": 0,
            "gyro_x": 4.5,
            "gyro_y": -2.1,
            "gyro_z": 9.8
        }
        res = self.app.post("/api/sensor_data", json=payload)
        self.assertEqual(res.status_code, 200)
        res_data = json.loads(res.data)
        self.assertEqual(res_data["status"], "success")

        # Fetch latest sensor data and check updated fields
        res_latest = self.app.get("/api/latest_sensor_data")
        latest = json.loads(res_latest.data)
        self.assertEqual(latest["temperature"], 32.4)
        self.assertEqual(latest["humidity"], 78.5)
        self.assertEqual(latest["tilt"], 1)
        self.assertEqual(latest["vibration"], 1)
        self.assertEqual(latest["disaster_type"], "landslide")

    def test_03_trigger_sos_endpoint(self):
        """Verify POST /api/trigger_sos generates emergency dispatch response"""
        payload = {
            "user_id": "TEST_DASHBOARD_OPERATOR",
            "latitude": 30.0668,
            "longitude": 79.0193,
            "disaster_type": "Landslide",
            "consent": True
        }
        res = self.app.post("/api/trigger_sos", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("sos_id", data)

    def test_04_cors_headers_present(self):
        """Verify CORS headers are present for cross-origin Netlify frontend calls"""
        res = self.app.get("/api/latest_sensor_data", headers={"Origin": "https://d-square-demo.netlify.app"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Access-Control-Allow-Origin", res.headers)

    def test_05_index_html_rendered(self):
        """Verify GET / serves index.html dashboard"""
        res = self.app.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("D-SQUARE 2.0", html)
        self.assertIn("val-temp", html)
        self.assertIn("val-soil", html)
        self.assertIn("sosModal", html)

if __name__ == "__main__":
    unittest.main()
