"""
D-SQUARE 2.0 NISAR Mobile Camera & PC Dashboard Integration Test Suite
Tests frame streaming from mobile camera to backend and retrieval on PC Dashboard.
"""

import unittest
import json
import time
from app import app, latest_nisar_camera_frame


class TestNisarCameraStream(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_01_camera_stream_post_endpoint(self):
        """Test POST /analyze_image and /api/camera/stream from mobile NISAR camera"""
        sample_b64_img = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP..."
        payload = {
            "image": sample_b64_img,
            "fps": 5.0,
            "nisar_mode": True
        }
        res = self.app.post("/analyze_image", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["satellite_fps"], 5.0)

    def test_02_pc_dashboard_fetches_latest_camera_frame(self):
        """Verify GET /api/camera/latest_frame delivers live NISAR camera image to PC Dashboard"""
        sample_b64_img = "data:image/jpeg;base64,LIVE_NISAR_CAM_FRAME_DATA"
        self.app.post("/api/camera/stream", json={
            "image": sample_b64_img,
            "fps": 4.5,
            "nisar_mode": True
        })

        res = self.app.get("/api/camera/latest_frame")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        cam = data["camera"]
        self.assertEqual(cam["image"], sample_b64_img)
        self.assertEqual(cam["fps"], 4.5)
        self.assertEqual(cam["status"], "LIVE")

    def test_03_start_satellite_sensing_endpoint(self):
        """Test POST /api/start_satellite_sensing compatibility"""
        res = self.app.post("/api/start_satellite_sensing", json={"scenario": "normal"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["satellite_fps"], 5.0)


if __name__ == "__main__":
    unittest.main()
