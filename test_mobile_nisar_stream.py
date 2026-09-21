"""
D-SQUARE 2.0 Mobile Satellite NISAR Telemetry Stream Test Suite
Tests live broadcasting of NISAR SAR radar pixels from Mobile Satellite node
to PC Dashboard API server.
"""

import unittest
import json
from app import app
from services.fusion_engine_service import fusion_engine_service


class TestMobileNisarStream(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_01_mobile_nisar_broadcast_endpoint(self):
        """Test POST /api/mobile/nisar_broadcast from Mobile Satellite Node"""
        payload = {
            "source": "MOBILE_NISAR_SATELLITE_NODE",
            "latitude": 30.0668,
            "longitude": 79.0193,
            "sar_l_band_db": -14.8,
            "sar_s_band_db": -9.5,
            "ground_deformation_mm_yr": -18.5,
            "sar_coherence": 0.91
        }
        res = self.app.post("/api/mobile/nisar_broadcast", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["nisar_pixels"]["ground_deformation_mm_yr"], -18.5)
        self.assertEqual(data["nisar_pixels"]["source"], "MOBILE_NISAR_SATELLITE_NODE")

    def test_02_pc_dashboard_receives_mobile_nisar_pixels(self):
        """Verify GET /api/satellite/nisar_pixels delivers Mobile NISAR pixels to PC Dashboard"""
        # Broadcast custom deformation velocity from mobile
        self.app.post("/api/mobile/nisar_broadcast", json={
            "source": "MOBILE_NISAR_SATELLITE_NODE",
            "ground_deformation_mm_yr": -22.4,
            "sar_l_band_db": -16.2
        })

        # PC Dashboard fetches NISAR pixels
        res = self.app.get("/api/satellite/nisar_pixels")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        np = data["nisar_pixels"]
        self.assertEqual(np["ground_deformation_mm_yr"], -22.4)
        self.assertEqual(np["sar_l_band_db"], -16.2)
        self.assertEqual(np["source"], "MOBILE_NISAR_SATELLITE_NODE")


if __name__ == "__main__":
    unittest.main()
