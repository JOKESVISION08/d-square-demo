"""
Unit tests for ML Fusion Satellite Upload & Auto-Analysis REST API Endpoints in app.py
"""

import os
import json
import io
import unittest
from app import app, UPLOAD_BASE_DIR, OUTPUT_DIR


class TestMLFusionUploadApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_upload_image_success(self):
        """Test POST /api/v1/upload-image with valid PNG satellite image."""
        img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        data = {
            "file": (io.BytesIO(img_bytes), "test_sentinel2_past.png"),
            "type": "baseline"
        }
        res = self.app.post("/api/v1/upload-image", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("image_id", json_data)
        self.assertEqual(json_data["filename"], "test_sentinel2_past.png")
        self.assertEqual(json_data["type"], "baseline")

    def test_02_upload_image_invalid_extension(self):
        """Test POST /api/v1/upload-image with unsupported file extension."""
        data = {
            "file": (io.BytesIO(b"dummy content"), "test_file.txt"),
            "type": "baseline"
        }
        res = self.app.post("/api/v1/upload-image", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "error")
        self.assertIn("Allowed", json_data["message"])

    def test_03_analyze_change(self):
        """Test POST /api/v1/analyze-change executing U-Net change analysis."""
        payload = {
            "past_image_id": "img_test_past",
            "current_image_id": "img_test_curr",
            "disaster_type": "FLOOD",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "resolution_m": 20.0
        }
        res = self.app.post("/api/v1/analyze-change", json=payload)
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("analysis_id", json_data)
        self.assertIn("result", json_data)

        result = json_data["result"]
        self.assertIn("affected_pixels_count", result)
        self.assertIn("affected_area_km2", result)
        self.assertIn("polygon_boundary", result)
        has_confidence = ("confidence" in result) or ("confidence_score" in result)
        self.assertTrue(has_confidence)

    def test_04_analysis_progress(self):
        """Test GET /api/v1/analysis-progress/<analysis_id>."""
        # First trigger analysis
        res_trig = self.app.post("/api/v1/analyze-change", json={"disaster_type": "LANDSLIDE"})
        analysis_id = res_trig.get_json()["analysis_id"]

        res = self.app.get(f"/api/v1/analysis-progress/{analysis_id}")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["progress"], 100)

    def test_05_download_geojson(self):
        """Test GET /api/v1/download-geojson/<analysis_id>."""
        res_trig = self.app.post("/api/v1/analyze-change", json={"disaster_type": "FIRE"})
        analysis_id = res_trig.get_json()["analysis_id"]

        res = self.app.get(f"/api/v1/download-geojson/{analysis_id}")
        self.assertEqual(res.status_code, 200)

    def test_06_download_change_mask(self):
        """Test GET /api/v1/download-change-mask/<analysis_id>."""
        res_trig = self.app.post("/api/v1/analyze-change", json={"disaster_type": "EARTHQUAKE"})
        analysis_id = res_trig.get_json()["analysis_id"]

        res = self.app.get(f"/api/v1/download-change-mask/{analysis_id}")
        self.assertEqual(res.status_code, 200)

    def test_07_send_to_sos(self):
        """Test POST /api/v1/send-to-sos forwarding to D-SQUARE SOS Engine."""
        payload = {
            "disaster_type": "FLOOD",
            "severity": "CRITICAL",
            "affected_pixels_count": 84,
            "affected_area_km2": 0.0336,
            "confidence": 94.8,
            "latitude": 19.0760,
            "longitude": 72.8777
        }
        res = self.app.post("/api/v1/send-to-sos", json=payload)
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("sos_alert_id", json_data)


if __name__ == "__main__":
    unittest.main()
