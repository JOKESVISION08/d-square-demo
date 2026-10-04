"""
Comprehensive Integration & Unit Test Suite for Three-Stage Alert Workflow
Testing:
1. Stage 1 (MONITORING): Normal background sensor state.
2. Stage 2 (HARDWARE_WARNING / PENDING_VERIFICATION): Silent ingest of raw hardware alert via /api/v1/hardware-alert.
3. Stage 3 (Human Verification Gate): Authorized operator inputs operator_id & notes via /api/v1/verify-and-trigger-sos, generating signed token.
4. Stage 4 (SOS_CONFIRMED & SOS_ACTIVE): Standalone SOS Center activation via /api/v1/standalone-sos/activate, siren enabled, live map loaded.
5. Stage 5 (Parallel GPT Dispatch): Concurrent dispatch to D-SQUARE GPT (/api/v1/dsquare-gpt/incident) & Rescue GPT (/api/v1/rescue-gpt/incident) within 10s SLA.
6. Stage 6 (DISPATCHED & Mute Siren): Alert delivery acknowledgement via /api/v1/incident/{id}/acknowledge and local siren mute via /api/v1/incident/{id}/mute-siren.
7. Stage 7 (RESOLVED): Operator incident resolution via /api/v1/incident/{id}/resolve and SQLite audit log verification.
8. Citizen Rescue Request: Submission via /api/v1/rescue-request and queueing for Rescue GPT.
"""

import unittest
import json
import time
from app import app
from database import get_incident_audit_logs, get_verified_incident, get_citizen_rescue_requests


class TestThreeStageAlertWorkflow(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_complete_three_stage_alert_workflow(self):
        # Step 1: Silent Hardware Alert Ingestion (Stage 2: HARDWARE_WARNING / PENDING_VERIFICATION)
        hardware_payload = {
            "event_id": "EVT-TEST-2026-001",
            "node_id": "D-SQUARE_NODE_01",
            "disaster_type": "LANDSLIDE",
            "severity": "CRITICAL",
            "confidence": 0.96,
            "latitude": 30.0668,
            "longitude": 79.0193,
            "location_name": "Uttarakhand Slope Sector 4",
            "sensor_readings": {
                "tilt_angle": 14.8,
                "vibration": 0.85,
                "soil_moisture": 94.2
            },
            "affected_pixels": [{"x": 105, "y": 204, "delta": 0.91}],
            "polygon_boundary": [
                {"lat": 30.0668, "lng": 79.0193},
                {"lat": 30.0700, "lng": 79.0250},
                {"lat": 30.0650, "lng": 79.0280}
            ]
        }

        resp_hw = self.app.post("/api/v1/hardware-alert", json=hardware_payload)
        self.assertEqual(resp_hw.status_code, 200)
        data_hw = json.loads(resp_hw.data)
        
        self.assertEqual(data_hw["status"], "HARDWARE_WARNING")
        self.assertTrue(data_hw["silent"])
        incident_id = data_hw["incident_id"]
        self.assertIsNotNone(incident_id)

        # Check DB State: HARDWARE_WARNING
        inc_db = get_verified_incident(incident_id)
        self.assertEqual(inc_db["status"], "HARDWARE_WARNING")
        self.assertEqual(inc_db["siren_muted"], 0)

        # Step 2: Human Operator Verification & Gate (Stage 3 -> Stage 4: SOS_CONFIRMED)
        verify_payload = {
            "incident_id": incident_id,
            "operator_id": "OP_OPERATOR_007",
            "verification_note": "Confirmed slope displacement on webcam stream and radar anomaly.",
            "action": "CONFIRM"
        }

        resp_verify = self.app.post("/api/v1/verify-and-trigger-sos", json=verify_payload)
        self.assertEqual(resp_verify.status_code, 200)
        data_verify = json.loads(resp_verify.data)

        self.assertEqual(data_verify["status"], "SOS_CONFIRMED")
        self.assertIn("VTK-", data_verify["verification_token"])
        self.assertEqual(data_verify["operator_id"], "OP_OPERATOR_007")

        # Step 3: Standalone SOS Center Activation (Stage 5: SOS_ACTIVE)
        activate_payload = {"incident_id": incident_id}
        start_time = time.time()
        resp_act = self.app.post("/api/v1/standalone-sos/activate", json=activate_payload)
        elapsed_sla = time.time() - start_time

        self.assertEqual(resp_act.status_code, 200)
        data_act = json.loads(resp_act.data)

        self.assertEqual(data_act["status"], "SOS_ACTIVE")
        self.assertTrue(data_act["siren_active"])
        self.assertTrue(data_act["map_enabled"])
        self.assertLess(elapsed_sla, 10.0, "Parallel dispatch must satisfy < 10s SLA")
        self.assertIn("parallel_dispatch", data_act)

        # Step 4: Verify D-SQUARE GPT & Rescue GPT Endpoints
        resp_dsquare = self.app.get("/api/v1/dsquare-gpt/incident")
        self.assertEqual(resp_dsquare.status_code, 200)
        data_dsquare = json.loads(resp_dsquare.data)
        self.assertIn("public_alert", data_dsquare)

        resp_rescue = self.app.get("/api/v1/rescue-gpt/incident")
        self.assertEqual(resp_rescue.status_code, 200)
        data_rescue = json.loads(resp_rescue.data)
        self.assertIn("rescue_alert", data_rescue)

        # Step 5: Citizen Rescue Request Submission
        rescue_req_payload = {
            "incident_id": incident_id,
            "user_id": "CITIZEN_99",
            "citizen_name": "Anil Sharma",
            "phone": "+919876500000",
            "latitude": 30.0670,
            "longitude": 79.0200,
            "location_name": "Sector 4 Slope Bridge",
            "trapped_count": 3,
            "medical_emergency": 1,
            "description": "Trapped under debris near bridge.",
            "priority": "CRITICAL"
        }
        resp_req = self.app.post("/api/v1/rescue-request", json=rescue_req_payload)
        self.assertEqual(resp_req.status_code, 200)

        data_req = json.loads(resp_req.data)
        self.assertIn("request_id", data_req)

        # Step 6: SOS Center / Responder Acknowledgement (Stage 6: DISPATCHED) & Mute Siren
        resp_ack = self.app.post(f"/api/v1/incident/{incident_id}/acknowledge", json={"operator_id": "HQ_DISPATCHER_1"})
        self.assertEqual(resp_ack.status_code, 200)
        data_ack = json.loads(resp_ack.data)
        self.assertEqual(data_ack["status"], "DISPATCHED")

        resp_mute = self.app.post(f"/api/v1/incident/{incident_id}/mute-siren", json={"operator_id": "OP_OPERATOR_007"})
        self.assertEqual(resp_mute.status_code, 200)
        data_mute = json.loads(resp_mute.data)
        self.assertEqual(data_mute["siren_muted"], 1)

        # Step 7: Incident Resolution (Stage 7: RESOLVED)
        resolve_payload = {
            "operator_id": "OP_OPERATOR_007",
            "resolution_note": "Debris cleared, all citizens rescued safely."
        }
        resp_res = self.app.post(f"/api/v1/incident/{incident_id}/resolve", json=resolve_payload)
        self.assertEqual(resp_res.status_code, 200)
        data_res = json.loads(resp_res.data)
        self.assertEqual(data_res["status"], "RESOLVED")

        # Step 8: Audit Log Verification
        audits = get_incident_audit_logs(incident_id)
        self.assertGreater(len(audits), 3)
        states_logged = [a["new_state"] for a in audits]
        self.assertIn("HARDWARE_WARNING", states_logged)
        self.assertIn("SOS_CONFIRMED", states_logged)
        self.assertIn("SOS_ACTIVE", states_logged)
        self.assertIn("DISPATCHED", states_logged)
        self.assertIn("RESOLVED", states_logged)

    def test_operator_dismiss_flow(self):
        # Test dismissing an alert at operator gate
        hardware_payload = {
            "event_id": "EVT-FALSE-ALARM",
            "disaster_type": "FIRE",
            "severity": "MEDIUM",
            "confidence": 0.55
        }
        resp_hw = self.app.post("/api/v1/hardware-alert", json=hardware_payload)
        data_hw = json.loads(resp_hw.data)
        inc_id = data_hw["incident_id"]

        dismiss_payload = {
            "incident_id": inc_id,
            "operator_id": "OP_OPERATOR_007",
            "verification_note": "Inspected webcam - dust cloud mistaken for smoke.",
            "action": "DISMISS"
        }
        resp_dismiss = self.app.post("/api/v1/verify-and-trigger-sos", json=dismiss_payload)
        self.assertEqual(resp_dismiss.status_code, 200)
        data_dismiss = json.loads(resp_dismiss.data)
        self.assertEqual(data_dismiss["status"], "DISMISSED")

        inc_db = get_verified_incident(inc_id)
        self.assertEqual(inc_db["status"], "RESOLVED")


if __name__ == "__main__":
    unittest.main()
