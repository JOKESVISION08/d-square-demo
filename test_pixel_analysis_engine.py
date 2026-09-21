"""
D-SQUARE 2.0 Pixel-Level Satellite Image Analysis Engine Test Suite
Validates PAST vs CURRENT satellite pixel change detection, spectral index differencing (delta_NDWI, delta_MNDWI, delta_NDVI, delta_NBR),
PyTorch U-Net change detector model, GeoJSON polygon boundary generation, GPS coordinate extraction, and Flask REST endpoints.
"""

import json
import time
import unittest

try:
    import torch
    HAS_PYTORCH = True
except ImportError:
    HAS_PYTORCH = False

from app import app
from ml_pipeline.pixel_analysis_engine import (
    SpectralDifferencingEngine,
    PixelAnalysisEngine,
    PixelUNetChangeDetector
)


class TestSpectralDifferencing(unittest.TestCase):
    """Tests spectral index differencing formulas for satellite imagery."""

    def setUp(self):
        self.engine = SpectralDifferencingEngine()

    def test_ndwi_and_mndwi_differencing(self):
        past_p = {"green": 0.3, "nir": 0.7, "swir": 0.4, "red": 0.2}
        curr_p = {"green": 0.65, "nir": 0.15, "swir": 0.1, "red": 0.3}

        deltas = self.engine.compute_pixel_deltas(past_p, curr_p)
        self.assertIn("delta_ndwi", deltas)
        self.assertIn("delta_mndwi", deltas)
        self.assertIn("cva_magnitude", deltas)
        self.assertGreater(deltas["delta_ndwi"], 0.3)
        self.assertGreater(deltas["delta_mndwi"], 0.4)

    def test_nbr_fire_differencing(self):
        past_p = {"green": 0.3, "nir": 0.7, "swir": 0.2, "red": 0.2}
        curr_p = {"green": 0.2, "nir": 0.1, "swir": 0.7, "red": 0.6}

        deltas = self.engine.compute_pixel_deltas(past_p, curr_p)
        self.assertGreater(deltas["delta_nbr"], 0.2)
        self.assertLess(deltas["delta_ndvi"], -0.3)


class TestPixelAnalysisEngine(unittest.TestCase):
    """Tests pixel-level change detection, polygon generation, and GPS coordinates list."""

    def setUp(self):
        self.engine = PixelAnalysisEngine()

    def test_flood_pixel_analysis_and_polygon(self):
        res = self.engine.analyze_pixel_changes(
            past_scene={},
            curr_scene={},
            disaster_type="FLOOD",
            center_lat=19.0760,
            center_lon=72.8777,
            resolution_m=20.0
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["disaster_type"], "FLOOD")
        self.assertIn("affected_pixels_count", res)
        self.assertGreater(res["affected_pixels_count"], 0)
        self.assertIn("polygon_boundary", res)
        self.assertGreaterEqual(len(res["polygon_boundary"]), 4)

        # Verify GeoJSON centroid and bounding box
        centroid = res["centroid"]
        self.assertAlmostEqual(centroid["lat"], 19.0760, places=3)
        self.assertAlmostEqual(centroid["lon"], 72.8777, places=3)

        bbox = res["bounding_box"]
        self.assertIn("min_lat", bbox)
        self.assertIn("max_lat", bbox)
        self.assertIn("min_lon", bbox)
        self.assertIn("max_lon", bbox)

    def test_affected_pixels_gps_coordinates(self):
        res = self.engine.analyze_pixel_changes(
            past_scene={},
            curr_scene={},
            disaster_type="LANDSLIDE",
            center_lat=30.0668,
            center_lon=79.0193
        )
        pixels = res["affected_pixels"]
        self.assertIsInstance(pixels, list)
        self.assertGreater(len(pixels), 0)
        p = pixels[0]
        self.assertIn("lat", p)
        self.assertIn("lon", p)
        self.assertIn("pixel_id", p)

    def test_latency_under_30_seconds(self):
        start_t = time.time()
        res = self.engine.analyze_pixel_changes(
            past_scene={},
            curr_scene={},
            disaster_type="FIRE",
            center_lat=21.8000,
            center_lon=86.3000
        )
        elapsed_sec = time.time() - start_t
        self.assertLess(elapsed_sec, 30.0)
        self.assertLess(res["inference_latency_ms"], 30000.0)


@unittest.skipUnless(HAS_PYTORCH, "PyTorch environment required for U-Net forward pass")
class TestPixelUNetArchitecture(unittest.TestCase):
    """Tests PyTorch U-Net neural change detector model forward pass."""

    def test_unet_forward_pass(self):
        model = PixelUNetChangeDetector(in_channels=10, num_classes=6)
        model.eval()
        batch_size = 2
        # Input tensor: batch_size, 10 bands (5 PAST + 5 CURRENT), 64x64 spatial resolution
        x = torch.randn(batch_size, 10, 64, 64)

        with torch.no_grad():
            out = model(x)

        self.assertEqual(out.shape, (batch_size, 6, 64, 64))


class TestFlaskPixelAnalysisEndpoints(unittest.TestCase):
    """Tests Flask API endpoints for pixel change detection and scene upload comparison."""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_api_ml_pixel_change_detect(self):
        payload = {
            "disaster_type": "FLOOD",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "resolution_m": 20.0
        }
        res = self.client.post("/api/ml/pixel_change_detect", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("polygon_boundary", data)
        self.assertIn("affected_pixels", data)

    def test_api_fusion_upload_compare(self):
        payload = {
            "lat": 30.0668,
            "lon": 79.0193,
            "prev_filename": "landsat_2020.tif",
            "curr_filename": "sentinel_2026.tif"
        }
        res = self.client.post("/api/fusion/upload_compare", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("pixel_analysis", data)
        self.assertIn("polygon_boundary", data)
        self.assertIn("affected_pixels", data)


if __name__ == "__main__":
    unittest.main()
