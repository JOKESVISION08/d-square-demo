"""
test_upload_compare.py — Test Suite for D-SQUARE 2.0 Upload & Compare Satellite Disaster Scenes
"""

import os
import sys
import json
import io
import unittest
from PIL import Image
import numpy as np

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import (
    init_db, save_satellite_scene, get_uploaded_scenes, get_scene_by_id,
    save_scene_features, get_scene_features, delete_scene
)
from satellite.upload_processor import (
    inspect_uploaded_scene, calculate_indices, compare_scene_compatibility,
    build_preview_image
)
from satellite.feature_extractor import extract_scene_features
from app import app


class TestUploadCompare(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize test database and directory setup."""
        init_db()
        cls.client = app.test_client()
        cls.client.testing = True
        os.makedirs("uploads/historical", exist_ok=True)
        os.makedirs("uploads/current", exist_ok=True)
        os.makedirs("uploads/previews", exist_ok=True)

    def create_dummy_png(self, filename="test_demo.png"):
        """Create a synthetic RGB PNG file for testing."""
        path = os.path.join("uploads/historical", filename)
        img = Image.new("RGB", (100, 100), color=(200, 50, 30))
        img.save(path)
        return path

    def test_01_rgb_image_inspection(self):
        """Rule Verification: Ordinary RGB images must be tagged as IMAGE-ONLY DEMO without fake spectral indices."""
        png_path = self.create_dummy_png("test_rgb.png")
        metadata = inspect_uploaded_scene(png_path)

        self.assertEqual(metadata["band_count"], 3)
        self.assertEqual(metadata["driver"], "PNG")
        self.assertFalse(metadata["is_geotiff"])
        self.assertEqual(metadata["capability_label"], "IMAGE-ONLY DEMO")

        features = extract_scene_features(png_path)
        indices = calculate_indices(features)
        self.assertIsNone(indices["ndvi"])
        self.assertIsNone(indices["nbr"])
        self.assertIsNone(indices["lst"])
        print("[PASS] test_01_rgb_image_inspection: RGB image correctly tagged as IMAGE-ONLY DEMO with null spectral indices.")

    def test_02_compatibility_evaluator(self):
        """Verify compatibility check returns VISUAL_ONLY when comparing RGB demo against multi-spectral scene."""
        hist_meta = {
            "satellite": "Sentinel-2",
            "product_name": "L2A Surface Reflectance",
            "is_geotiff": False,
            "quality_flag": "IMAGE_ONLY_DEMO",
            "original_filename": "demo_fire.png",
            "band_count": 3,
            "resolution_meters": 10.0,
            "spectral_indices": {"ndvi": None, "nbr": None}
        }
        curr_meta = {
            "satellite": "Sentinel-2",
            "product_name": "L2A Surface Reflectance",
            "is_geotiff": True,
            "band_count": 12,
            "resolution_meters": 10.0,
            "spectral_indices": {"ndvi": 0.65, "nbr": -0.2}
        }

        compat = compare_scene_compatibility(hist_meta, curr_meta)
        self.assertEqual(compat["compatibility_level"], "VISUAL_ONLY")
        self.assertIn("visual", compat["user_guidance"].lower())
        print("[PASS] test_02_compatibility_evaluator: Evaluator returned VISUAL_ONLY for RGB vs Multi-spectral.")

    def test_03_database_crud(self):
        """Test DB save, fetch, and delete operations for satellite scenes."""
        scene_data = {
            "scene_type": "historical",
            "event_id": "EVT_TEST_999",
            "disaster_type": "Forest_Fire",
            "satellite": "Sentinel-2",
            "product": "Sentinel-2 L2A",
            "acquisition_datetime": "2021-05-15 10:30:00",
            "latitude": 30.0668,
            "longitude": 79.0193,
            "resolution_m": 10.0,
            "cloud_cover": 1.5,
            "quality_flag": "UNVERIFIED_SOURCE",
            "verification_status": "UPLOADED_UNVERIFIED",
            "original_filename": "test_scene_999.png",
            "stored_path": "uploads/historical/test_scene_999.png",
            "preview_path": "uploads/previews/test_scene_999_preview.png"
        }

        scene_id = save_satellite_scene(scene_data)
        self.assertIsNotNone(scene_id)

        sc = get_scene_by_id(scene_id)
        self.assertIsNotNone(sc)
        self.assertEqual(sc["disaster_type"], "Forest_Fire")

        scenes = get_uploaded_scenes()
        self.assertTrue(any(s["id"] == scene_id for s in scenes))

        del_res = delete_scene(scene_id)
        self.assertTrue(del_res)
        self.assertIsNone(get_scene_by_id(scene_id))
        print("[PASS] test_03_database_crud: Scene CRUD verified in SQLite database.")

    def test_04_api_upload_and_compare(self):
        """Test Flask API upload endpoints for historical and current scenes and run comparison."""
        # 1. Upload Historical Scene
        img_bytes_hist = io.BytesIO()
        Image.new("RGB", (60, 60), color=(220, 40, 20)).save(img_bytes_hist, format="PNG")
        img_bytes_hist.seek(0)

        hist_res = self.client.post('/api/upload/historical-scene', data={
            'file': (img_bytes_hist, 'api_hist_fire.png'),
            'event_id': 'EVT_API_FIRE_01',
            'disaster_type': 'Forest_Fire',
            'satellite': 'Sentinel-2',
            'product_name': 'L2A',
            'acquisition_date': '2021-06-01 12:00:00',
            'latitude': '30.0668',
            'longitude': '79.0193',
            'verification_status': 'UPLOADED_UNVERIFIED'
        }, content_type='multipart/form-data')

        self.assertEqual(hist_res.status_code, 200)
        hist_data = json.loads(hist_res.data)
        self.assertEqual(hist_data["status"], "success")
        hist_scene_id = hist_data["scene_id"]

        # 2. Upload Current Scene
        img_bytes_curr = io.BytesIO()
        Image.new("RGB", (60, 60), color=(200, 60, 20)).save(img_bytes_curr, format="PNG")
        img_bytes_curr.seek(0)

        curr_res = self.client.post('/api/upload/current-scene', data={
            'file': (img_bytes_curr, 'api_curr_fire.png'),
            'satellite': 'Sentinel-2',
            'product_name': 'L2A',
            'acquisition_date': '2026-09-18 12:00:00',
            'latitude': '30.0668',
            'longitude': '79.0193',
            'verification_status': 'UPLOADED_UNVERIFIED'
        }, content_type='multipart/form-data')

        self.assertEqual(curr_res.status_code, 200)
        curr_data = json.loads(curr_res.data)
        self.assertEqual(curr_data["status"], "success")
        curr_scene_id = curr_data["scene_id"]

        # 3. GET /api/uploaded-scenes
        get_res = self.client.get('/api/uploaded-scenes')
        self.assertEqual(get_res.status_code, 200)
        get_data = json.loads(get_res.data)
        self.assertTrue(len(get_data["scenes"]) >= 2)

        # 4. POST /api/compare-uploaded-scenes
        comp_res = self.client.post('/api/compare-uploaded-scenes', json={
            'historical_scene_id': hist_scene_id,
            'current_scene_id': curr_scene_id,
            'patch_size': 5
        })

        self.assertEqual(comp_res.status_code, 200)
        comp_data = json.loads(comp_res.data)
        self.assertEqual(comp_data["status"], "success")
        self.assertEqual(comp_data["historical_scene"]["id"], hist_scene_id)
        self.assertEqual(comp_data["current_scene"]["id"], curr_scene_id)
        self.assertIn("evaluation", comp_data)

        # 5. Verify Preview Image Route
        prev_res = self.client.get(f'/api/scene-preview/{hist_scene_id}')
        self.assertEqual(prev_res.status_code, 200)

        # 6. Cleanup scenes
        self.client.delete(f'/api/uploaded-scenes/{hist_scene_id}')
        self.client.delete(f'/api/uploaded-scenes/{curr_scene_id}')

        print("[PASS] test_04_api_upload_and_compare: Full API pipeline (upload, preview, list, compare, delete) verified successfully.")

    def test_05_sms_safety_rule(self):
        """Rule Verification: Uploaded scene comparison MUST NOT trigger SMS alerts."""
        payload = {
            "uploaded_comparison": {
                "historical_scene_id": "MOCK_HIST",
                "current_scene_id": "MOCK_CURR",
                "leading_disaster_pattern": "Forest_Fire",
                "similarity_distance_percent": 12.0,
                "anomaly_score_percent": 88.5,
                "evaluation": {"compatibility_level": "FULL"}
            }
        }
        res = self.client.post('/api/sensor_data', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        # Verification: Twilio response should be None / omitted / not triggered by scene upload
        self.assertIsNone(data.get("twilio_sms_status"))
        print("[PASS] test_05_sms_safety_rule: SMS alerts correctly withheld during scene comparison.")


if __name__ == '__main__':
    unittest.main()
