"""
Automated Test Suite for D-SQUARE 2.0 End-to-End SOS Alert System Architecture & Geofencing Core Engine
"""

import unittest
import json
import time
import app as flask_app
import database
from services.geofencing_engine import SpatialGeofencingEngine, point_in_polygon, haversine_distance_km
from services.parallel_sos_engine import ParallelSOSAlertEngine
from services.rescue_operations_coordinator import RescueOperationsCoordinator


class TestEndToEndSOSAlertSystem(unittest.TestCase):

    def setUp(self):
        database.init_db()
        self.app = flask_app.app.test_client()
        self.app.testing = True
        self.geofence_engine = SpatialGeofencingEngine(buffer_radius_km=2.5)
        self.parallel_engine = ParallelSOSAlertEngine()
        self.rescue_coordinator = RescueOperationsCoordinator()

        # Standard Mumbai Coastal Polygon Boundary
        self.mumbai_polygon = [
            [19.0700, 72.8700],
            [19.0900, 72.8700],
            [19.0900, 72.8900],
            [19.0700, 72.8900]
        ]

    def test_geofencing_point_in_polygon_and_buffer(self):
        """1. Tests Ray-Casting Point-in-Polygon & 2.5km Haversine buffer evaluation."""
        # Point inside polygon
        inside_eval = self.geofence_engine.evaluate_location_risk(19.0800, 72.8800, self.mumbai_polygon)
        self.assertTrue(inside_eval["in_affected_zone"])
        self.assertEqual(inside_eval["zone_type"], "CRITICAL_ZONE")
        self.assertEqual(inside_eval["distance_to_boundary_km"], 0.0)

        # Point in 2.5km buffer zone
        buffer_eval = self.geofence_engine.evaluate_location_risk(19.0950, 72.8950, self.mumbai_polygon)
        self.assertTrue(buffer_eval["in_affected_zone"])
        self.assertEqual(buffer_eval["zone_type"], "WARNING_ZONE")
        self.assertLessEqual(buffer_eval["distance_to_boundary_km"], 2.5)

        # Point far outside safe zone
        safe_eval = self.geofence_engine.evaluate_location_risk(20.0000, 73.5000, self.mumbai_polygon)
        self.assertFalse(safe_eval["in_affected_zone"])
        self.assertEqual(safe_eval["zone_type"], "SAFE_ZONE")

    def test_user_channel_segmentation(self):
        """2. Tests grouping affected registered users into delivery channel queues."""
        test_users = [
            {"user_id": "U1", "name": "User 1", "latitude": 19.0800, "longitude": 72.8800, "app_installed": True, "phone": "+919000000001", "email": "u1@ex.com"},
            {"user_id": "U2", "name": "User 2", "latitude": 19.0920, "longitude": 72.8920, "app_installed": False, "phone": "+919000000002", "email": "u2@ex.com"},
            {"user_id": "U3", "name": "User 3", "latitude": 25.0000, "longitude": 80.0000, "app_installed": True, "phone": "+919000000003", "email": "u3@ex.com"}
        ]
        res = self.geofence_engine.segment_affected_users(self.mumbai_polygon, users_list=test_users)
        self.assertEqual(res["total_affected_count"], 2)
        self.assertEqual(res["critical_zone_count"], 1)
        self.assertEqual(res["warning_zone_count"], 1)
        self.assertEqual(len(res["channel_queues"]["fcm_push"]), 1)
        self.assertEqual(len(res["channel_queues"]["twilio_sms"]), 2)

    def test_parallel_sos_dispatch_sla(self):
        """3. Tests non-blocking parallel dispatch of SOS_RESCUE and SOS_PUBLIC under 30s SLA."""
        start_t = time.time()
        alert_input = {
            "disaster_type": "FLOOD",
            "severity": "CRITICAL",
            "latitude": 19.0800,
            "longitude": 72.8800,
            "area_name": "Mumbai Coastal Zone",
            "affected_population": 8500
        }
        dispatch_res = self.parallel_engine.dispatch_parallel_sos(alert_input)
        elapsed = time.time() - start_t

        self.assertLess(elapsed, 30.0)
        self.assertEqual(dispatch_res["status"], "success")
        self.assertEqual(dispatch_res["rescue_gpt_alert"]["alert_type"], "SOS_RESCUE")
        self.assertEqual(dispatch_res["dsquare_gpt_alert"]["alert_type"], "SOS_PUBLIC")

    def test_rescue_request_priority_and_assignment(self):
        """4. Tests citizen rescue request submission, priority queueing, and team assignment."""
        req_res = self.rescue_coordinator.submit_rescue_request(
            user_id="USR_TRAPPED_01",
            latitude=19.0810,
            longitude=72.8810,
            disaster_type="FLOOD",
            trapped_count=6,
            user_status="TRAPPED ON ROOFTOP",
            medical_assistance_needed=True
        )

        self.assertEqual(req_res["status"], "REGISTERED")
        self.assertEqual(req_res["priority"], "CRITICAL")
        self.assertIsNotNone(req_res["assigned_team"])

    def test_nearest_shelter_routing(self):
        """5. Tests finding nearest emergency shelter with bed capacity and evacuation routing."""
        shelter = self.geofence_engine.find_nearest_shelter(19.0850, 72.8850)
        self.assertIsNotNone(shelter)
        self.assertIn("shelter_id", shelter)
        self.assertGreater(shelter["available_beds"], 0)
        self.assertIn("google_maps_url", shelter)

    def test_flask_end_to_end_api_endpoints(self):
        """6. End-to-end Flask REST API endpoint verification."""
        # 1. Trigger SOS Alert
        sos_payload = {
            "disaster_type": "FLOOD",
            "severity": "HIGH",
            "area_name": "Mumbai Coastal Restricted Area",
            "affected_pixels": self.mumbai_polygon
        }
        resp = self.app.post("/api/v1/trigger-sos-alert", json=sos_payload)
        self.assertEqual(resp.status_code, 200)
        sos_data = json.loads(resp.data)
        self.assertEqual(sos_data["status"], "success")
        alert_id = sos_data["alert_id"]

        # 2. Check Alert Delivery Status
        status_resp = self.app.get(f"/api/v1/alert-status/{alert_id}")
        self.assertEqual(status_resp.status_code, 200)
        status_data = json.loads(status_resp.data)
        self.assertEqual(status_data["status"], "success")

        # 3. Citizen Rescue Request
        rescue_req_payload = {
            "user_id": "USR_MUMBAI_CITIZEN_5",
            "latitude": 19.0820,
            "longitude": 72.8820,
            "disaster_type": "FLOOD",
            "trapped_count": 2,
            "user_status": "I NEED HELP"
        }
        resc_resp = self.app.post("/api/v1/rescue-request", json=rescue_req_payload)
        self.assertEqual(resc_resp.status_code, 200)
        resc_data = json.loads(resc_resp.data)
        self.assertEqual(resc_data["status"], "REGISTERED")

        # 4. Query Nearest Shelter
        shelter_resp = self.app.get("/api/v1/nearest-shelter/19.0820/72.8820")
        self.assertEqual(shelter_resp.status_code, 200)
        shelter_data = json.loads(shelter_resp.data)
        self.assertEqual(shelter_data["status"], "success")

        # 5. Query Rescue Clusters
        cluster_resp = self.app.get("/api/v1/rescue-clusters")
        self.assertEqual(cluster_resp.status_code, 200)
        cluster_data = json.loads(cluster_resp.data)
        self.assertEqual(cluster_data["status"], "success")


if __name__ == "__main__":
    unittest.main()
