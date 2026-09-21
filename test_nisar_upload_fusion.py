"""
D-SQUARE 2.0 NISAR Radar Pixels & Satellite Upload AI Predictor Test Suite
Tests NISAR SAR pixel calculations, previous vs current satellite scene upload comparison,
and automatic AI disaster prediction.
"""

import unittest
import json
from app import app
from services.fusion_engine_service import fusion_engine_service


class TestNisarUploadFusion(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_01_nisar_radar_pixel_calculation(self):
        """Test NISAR SAR radar backscatter & deformation rate formulas"""
        data = fusion_engine_service.sat_fetcher.get_nisar_radar_pixels(30.0668, 79.0193)
        self.assertEqual(data["satellite"], "NASA-ISRO SAR (NISAR)")
        self.assertIn("sar_l_band_db", data)
        self.assertIn("ground_deformation_mm_yr", data)
        self.assertLessEqual(data["ground_deformation_mm_yr"], 0.0)

    def test_02_api_satellite_nisar_pixels(self):
        """Test GET /api/satellite/nisar_pixels"""
        res = self.app.get("/api/satellite/nisar_pixels?lat=30.0668&lon=79.0193")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("nisar_pixels", data)
        self.assertIn("ground_deformation_mm_yr", data["nisar_pixels"])

    def test_03_api_fusion_upload_compare(self):
        """Test POST /api/fusion/upload_compare automatic AI prediction"""
        payload = {
            "lat": 30.0668,
            "lon": 79.0193,
            "prev_filename": "historical_landsat_2020.tif",
            "curr_filename": "realtime_sentinel_2026.tif"
        }
        res = self.app.post("/api/fusion/upload_compare", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("uploaded_comparison", data)
        self.assertEqual(data["uploaded_comparison"]["scene_status"], "UPLOAD_COMPARE_ANALYZED")
        self.assertIn("nisar_radar_pixels", data["uploaded_comparison"])
        self.assertGreaterEqual(data["risk_score"], 50.0)


if __name__ == "__main__":
    unittest.main()
