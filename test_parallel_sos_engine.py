"""
D-SQUARE 2.0 Parallel SOS Alert Engine Test Suite
Tests parallel non-blocking alert dispatch (SOS_RESCUE + SOS_PUBLIC), multi-language localization (EN, HI, MR),
database persistence, public assistant queries, and rescue operations APIs.
"""

import unittest
import json
from app import app
from services.parallel_sos_engine import parallel_sos_engine, MultiLanguageLocalization
from database import get_active_parallel_alerts, get_shelters_list, get_rescue_resources_list


class TestParallelSOSEngine(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_01_parallel_dispatch_payload_structure(self):
        """Test parallel dispatch generates both SOS_RESCUE and SOS_PUBLIC payloads"""
        input_data = {
            "disaster_type": "FLOOD",
            "severity": "HIGH",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "area_name": "Mumbai Coastal Zone",
            "affected_population": 5000,
            "sensor_data": {"water_level": "2.5m", "rainfall": "150mm/hr"}
        }

        res = parallel_sos_engine.dispatch_parallel_sos(input_data)
        self.assertEqual(res["status"], "success")
        self.assertLess(res["dispatch_latency_ms"], 1000.0) # < 1s local latency

        rescue = res["rescue_gpt_alert"]
        public = res["dsquare_gpt_alert"]

        # Validate SOS_RESCUE Payload Contract
        self.assertEqual(rescue["alert_type"], "SOS_RESCUE")
        self.assertEqual(rescue["disaster_type"], "FLOOD")
        self.assertEqual(rescue["severity"], "HIGH")
        self.assertEqual(rescue["affected_population"], 5000)
        self.assertIn("108", rescue["emergency_contacts"]["disaster_helpline"])
        self.assertIn("112", rescue["emergency_contacts"]["national_emergency"])

        # Validate SOS_PUBLIC Payload Contract
        self.assertEqual(public["alert_type"], "SOS_PUBLIC")
        self.assertEqual(public["disaster_type"], "FLOOD")
        self.assertIn("evacuation_route", public)
        self.assertEqual(len(public["safety_instructions"]), 5)
        self.assertIn("english", public["languages"])
        self.assertIn("hindi", public["languages"])
        self.assertIn("marathi", public["languages"])

    def test_02_multilanguage_localization(self):
        """Validate multi-language safety steps for English, Hindi, Marathi"""
        en = MultiLanguageLocalization.get_localized_content("FLOOD", "en")
        hi = MultiLanguageLocalization.get_localized_content("FLOOD", "hi")
        mr = MultiLanguageLocalization.get_localized_content("FLOOD", "mr")

        self.assertIn("FLOOD ALERT", en["title"])
        self.assertIn("बाढ़ चेतावनी", hi["title"])
        self.assertIn("पूर इशारा", mr["title"])
        self.assertEqual(len(en["safety_steps"]), 5)
        self.assertEqual(len(hi["safety_steps"]), 5)
        self.assertEqual(len(mr["safety_steps"]), 5)

    def test_03_trigger_parallel_sos_api_and_db_persistence(self):
        """Test POST /api/sos/trigger_parallel and DB insertion"""
        payload = {
            "disaster_type": "FIRE",
            "severity": "CRITICAL",
            "latitude": 30.0668,
            "longitude": 79.0193,
            "area_name": "Chamoli Industrial Zone",
            "affected_population": 1200
        }

        res = self.app.post("/api/sos/trigger_parallel", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("database_alert_id", data)

        active = get_active_parallel_alerts(limit=5)
        self.assertGreater(len(active), 0)
        latest = active[0]
        self.assertEqual(latest["disaster_type"], "FIRE")

    def test_04_public_assistant_query_api(self):
        """Test POST /api/public/assistant_query handling citizen Q&A"""
        payload = {
            "query": "Where is the nearest shelter?",
            "language": "hi",
            "disaster_type": "FLOOD"
        }
        res = self.app.post("/api/public/assistant_query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("Nearest Shelter", data["response"])
        self.assertEqual(len(data["safety_instructions"]), 5)

    def test_05_rescue_dashboard_summary_and_resources_api(self):
        """Test GET /api/rescue/dashboard_summary and resource updates"""
        res = self.app.get("/api/rescue/dashboard_summary")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertGreater(len(data["shelters"]), 0)
        self.assertGreater(len(data["rescue_resources"]), 0)

        # Test updating resource allocation
        alloc_res = self.app.post("/api/rescue/resource_allocation", json={
            "resource_id": "RES_BOAT_01",
            "assigned_area": "Mumbai Coastal Zone Sector 3",
            "status": "DEPLOYED"
        })
        self.assertEqual(alloc_res.status_code, 200)
        alloc_data = json.loads(alloc_res.data)
        self.assertEqual(alloc_data["status"], "success")


if __name__ == "__main__":
    unittest.main()
