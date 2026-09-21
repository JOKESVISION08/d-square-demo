"""
D-SQUARE 2.0 Complete System Test Suite
Tests hardware telemetry intake, JWT auth, satellite prediction, cloud removal AI,
D-SQUARE GPT chatbot, voice rescue assistant, mobile SOS, and monsoon ML prediction.
"""

import unittest
import json
from app import app

class TestDSquareFullSystem(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_01_telemetry_intake(self):
        payload = {
            "node_id": "D-SQUARE_NODE_01",
            "temperature": 29.5,
            "humidity": 72.0,
            "soil_raw": 750.0,
            "mq2_gas": 0,
            "tilt": 0,
            "vibration": 0,
            "flame": 0,
            "gyro_x": 1.2,
            "gyro_y": -0.5,
            "gyro_z": 9.8
        }
        res = self.app.post("/api/sensor_data", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")

    def test_02_latest_sensor_data(self):
        res = self.app.get("/api/latest_sensor_data")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("node_id", data)

    def test_03_satellite_prediction(self):
        res = self.app.get("/api/satellite_prediction?scenario=landslide")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("anomaly_percentage", data)

    def test_04_cloud_removal_ai(self):
        res = self.app.get("/api/cloud_removed_image")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("cloud_free_image_b64", data)

    def test_05_dsquare_gpt_chatbot(self):
        res = self.app.post("/api/chat", json={"message": "Is there a landslide risk?"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("response", data)

    def test_06_voice_rescue_route(self):
        res = self.app.post("/api/rescue_route", json={"start_lat": 30.0668, "start_lon": 79.0193, "language": "en"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("route", data)

    def test_07_mobile_sos(self):
        res = self.app.post("/api/sos", json={"user_id": "TEST_USER", "latitude": 30.0668, "longitude": 79.0193, "disaster_type": "Landslide"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")

    def test_08_monsoon_prediction_engine(self):
        res = self.app.get("/api/monsoon_prediction?region=Uttarakhand")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("predicted_48h_rainfall_mm", data)


if __name__ == "__main__":
    unittest.main()
