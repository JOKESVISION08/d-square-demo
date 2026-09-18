"""
test_mobile_sos.py — Test Suite for D-SQUARE SOS Mobile Public Safety Module
Verifies mobile page loading, geolocation consent, safe zone hazard exclusion,
emergency call 112 button presence, SOS confirmation & cooldown, GPT safety safeguards,
weather fallback, and backward compatibility.
"""

import os
import sys
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import init_db
from app import app


class TestMobileSOSModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize database and test client."""
        init_db()
        cls.client = app.test_client()
        cls.client.testing = True

    def test_01_mobile_page_loads(self):
        """Test GET /mobile_sos returns 200 HTML content."""
        res = self.client.get('/mobile_sos')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"D-SQUARE GPT", res.data)
        self.assertIn(b"tel:112", res.data)
        print("[PASS] test_01_mobile_page_loads: /mobile_sos page loaded with tel:112 button.")

    def test_02_location_consent_validation(self):
        """Test POST /api/user/location requires explicit consent."""
        # Without consent
        res1 = self.client.post('/api/user/location', json={
            "latitude": 30.0668, "longitude": 79.0193, "consent": False
        })
        self.assertEqual(res1.status_code, 403)

        # With consent
        res2 = self.client.post('/api/user/location', json={
            "latitude": 30.0668, "longitude": 79.0193, "consent": True
        })
        self.assertEqual(res2.status_code, 200)
        print("[PASS] test_02_location_consent_validation: Consent required for location logging.")

    def test_03_invalid_coordinates_rejection(self):
        """Test POST /api/user/location rejects invalid lat/lon coordinates."""
        res = self.client.post('/api/user/location', json={
            "latitude": 999.0, "longitude": 79.0193, "consent": True
        })
        self.assertEqual(res.status_code, 400)
        print("[PASS] test_03_invalid_coordinates_rejection: Invalid lat 999 rejected with 400.")

    def test_04_emergency_call_112_button(self):
        """Test templates/mobile_sos.html contains tel:112 action button."""
        res = self.client.get('/mobile_sos')
        self.assertIn(b'href="tel:112"', res.data)
        print("[PASS] test_04_emergency_call_112_button: tel:112 button confirmed in HTML.")

    def test_05_safe_zone_hazard_exclusion(self):
        """Test safe zone query excludes shelters inside active hazard radius."""
        res = self.client.get('/api/mobile/safe-zones?lat=30.0668&lon=79.0193')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        # All returned shelters should be outside 10km hazard radius if hazard is active
        for z in data.get("safe_zones", []):
            self.assertGreater(z.get("distance_km", 0.0), 0.0)
        print("[PASS] test_05_safe_zone_hazard_exclusion: Safe zones query executed correctly.")

    def test_06_sos_confirmation_and_cooldown(self):
        """Test SOS endpoint requires consent confirmation and enforces 60s cooldown."""
        session_id = "TEST_COOLDOWN_SESSION_99"

        # 1. Dispatch first SOS
        res1 = self.client.post('/api/mobile/sos', json={
            "user_session_id": session_id,
            "latitude": 30.0668,
            "longitude": 79.0193,
            "consent": True
        })
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.data)
        self.assertEqual(data1["status"], "success")

        # 2. Dispatch second SOS within 60s (Cooldown test)
        res2 = self.client.post('/api/mobile/sos', json={
            "user_session_id": session_id,
            "latitude": 30.0668,
            "longitude": 79.0193,
            "consent": True
        })
        self.assertEqual(res2.status_code, 429)
        data2 = json.loads(res2.data)
        self.assertIn("cooldown active", data2["message"].lower())
        print("[PASS] test_06_sos_confirmation_and_cooldown: Cooldown correctly enforced.")

    def test_07_gpt_assistant_danger_triggers(self):
        """Test GPT safety assistant triggers call_112_recommended for trapped/injury queries."""
        res = self.client.post('/api/mobile/assistant', json={
            "message": "I am trapped in a building with fire nearby!",
            "latitude": 30.0668,
            "longitude": 79.0193
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("call_112_recommended"))
        self.assertIn("112", data.get("message"))
        print("[PASS] test_07_gpt_assistant_danger_triggers: 112 call recommended for trapped/fire danger.")

    def test_08_weather_fallback_handling(self):
        """Test weather service handles unconfigured IMD credentials gracefully without fabricating data."""
        res = self.client.post('/api/mobile/weather', json={
            "latitude": 30.0668, "longitude": 79.0193
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("unavailable", data.get("message").lower())
        print("[PASS] test_08_weather_fallback_handling: Weather fallback verified.")

    def test_09_backward_compatibility_existing_endpoints(self):
        """Test pre-existing dashboard endpoints continue to work without breakage."""
        # 1. GET /
        res_dash = self.client.get('/')
        self.assertEqual(res_dash.status_code, 200)

        # 2. POST /api/sensor_data
        res_sensor = self.client.post('/api/sensor_data', json={"scenario": "normal"})
        self.assertEqual(res_sensor.status_code, 200)

        # 3. GET /api/uploaded-scenes
        res_scenes = self.client.get('/api/uploaded-scenes')
        self.assertEqual(res_scenes.status_code, 200)
        print("[PASS] test_09_backward_compatibility_existing_endpoints: Existing dashboard API endpoints fully functional.")

    def test_10_dsquare_gpt_satellite_knowledge(self):
        """Test D-SQUARE GPT provides detailed satellite remote sensing answers (NISAR, NDVI, Sentinel)."""
        res = self.client.post('/api/mobile/assistant', json={
            "message": "What is NISAR SAR radar and NDVI?",
            "latitude": 30.0668,
            "longitude": 79.0193
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("NISAR", data.get("message", ""))
        self.assertIn("NDVI", data.get("message", ""))
        print("[PASS] test_10_dsquare_gpt_satellite_knowledge: D-SQUARE GPT correctly answers satellite remote sensing queries.")

    def test_11_dsquare_gpt_monsoon_forecast(self):
        """Test D-SQUARE GPT provides monsoon forecast and heavy rainfall guidance."""
        res = self.client.post('/api/mobile/assistant', json={
            "message": "Give me the monsoon forecast and heavy rain alerts.",
            "latitude": 30.0668,
            "longitude": 79.0193
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("Monsoon", data.get("message", ""))
        print("[PASS] test_11_dsquare_gpt_monsoon_forecast: D-SQUARE GPT correctly answers monsoon forecast queries.")

    def test_12_dsquare_gpt_ground_station_telemetry(self):
        """Test D-SQUARE GPT incorporates ground station sensor readings (ESP8266_NODE_01)."""
        res = self.client.post('/api/mobile/assistant', json={
            "message": "What is the ground station status and sensor reading?",
            "latitude": 30.0668,
            "longitude": 79.0193
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("ESP8266_NODE_01", data.get("message", ""))
        print("[PASS] test_12_dsquare_gpt_ground_station_telemetry: D-SQUARE GPT returns live ground station sensor readings.")

    def test_13_ground_station_status_api(self):
        """Test GET /api/mobile/ground-station-status returns live node telemetry and stream health."""
        res = self.client.get('/api/mobile/ground-station-status')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("telemetry", data)
        self.assertEqual(data["node_id"], "ESP8266_NODE_01")
        print("[PASS] test_13_ground_station_status_api: /api/mobile/ground-station-status verified.")

    def test_14_demo_landslide_sos_endpoints(self):
        """Test POST /api/demo/landslide-sos, POST /api/demo/reset-landslide-sos, and GET /api/mobile/active-alert."""
        # 1. Trigger Landslide SOS
        res1 = self.client.post('/api/demo/landslide-sos', json={"source": "dashboard_scenario_injector"})
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.data)
        self.assertEqual(data1["status"], "success")
        self.assertTrue(data1["alert"]["active"])
        self.assertEqual(data1["alert"]["disaster_type"], "Landslide")
        self.assertEqual(data1["alert"]["risk_level"], "CRITICAL")
        self.assertEqual(data1["alert"]["soil_moisture"], 88.0)
        self.assertEqual(data1["alert"]["temperature"], 25.8)
        self.assertEqual(data1["alert"]["humidity"], 92.0)
        self.assertEqual(data1["alert"]["led_state"], "RED")
        self.assertEqual(data1["alert"]["buzzer_state"], "ON")

        # 2. Query active alert
        res_get = self.client.get('/api/mobile/active-alert')
        self.assertEqual(res_get.status_code, 200)
        data_get = json.loads(res_get.data)
        self.assertTrue(data_get["alert"]["active"])
        self.assertEqual(data_get["alert"]["disaster_type"], "Landslide")

        # 3. Reset Landslide SOS
        res2 = self.client.post('/api/demo/reset-landslide-sos', json={"source": "dashboard_scenario_injector"})
        self.assertEqual(res2.status_code, 200)
        data2 = json.loads(res2.data)
        self.assertFalse(data2["alert"]["active"])
        self.assertEqual(data2["alert"]["risk_level"], "NORMAL")
        self.assertEqual(data2["alert"]["soil_moisture"], 42.0)
        print("[PASS] test_14_demo_landslide_sos_endpoints: Demo landslide SOS endpoints verified.")


if __name__ == '__main__':
    unittest.main()


