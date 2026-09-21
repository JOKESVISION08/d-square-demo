"""
D-SQUARE 2.0 Multi-Modal Fusion Engine Test Suite
Tests satellite spectral indices, pixel anomaly formulas, decision-level ensemble fusion,
GeoJSON risk map generation, and all 8 API endpoints.
"""

import unittest
import json
from app import app
from services.fusion_engine_service import SpectralIndexCalculator, fusion_engine_service


class TestMultiModalFusionEngine(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_01_spectral_index_formulas(self):
        """Test NDVI, NDWI, NDBI and pixel anomaly z-score formulas"""
        ndvi = SpectralIndexCalculator.compute_ndvi(nir=0.8, red=0.2)
        self.assertAlmostEqual(ndvi, 0.6, places=2)

        ndwi = SpectralIndexCalculator.compute_ndwi(green=0.7, nir=0.3)
        self.assertAlmostEqual(ndwi, 0.4, places=2)

        ndbi = SpectralIndexCalculator.compute_ndbi(swir=0.2, nir=0.6)
        self.assertAlmostEqual(ndbi, -0.5, places=2)

        # Anomaly score: (0.52 - 0.65) / 0.045 = -2.88
        z_score = SpectralIndexCalculator.compute_pixel_anomaly(0.52, 0.65, 0.045)
        self.assertAlmostEqual(z_score, -2.8888, places=2)

    def test_02_fusion_engine_service_analysis(self):
        """Test decision-level ensemble fusion formula and risk level output"""
        res = fusion_engine_service.analyze_fusion(lat=30.0668, lon=79.0193)
        self.assertEqual(res["status"], "success")
        self.assertIn("risk_score", res)
        self.assertIn("confidence", res)
        self.assertIn("fusion_weights", res)
        self.assertEqual(res["fusion_weights"]["satellite_model"], 0.40)
        self.assertEqual(res["fusion_weights"]["iot_sensor_model"], 0.40)
        self.assertEqual(res["fusion_weights"]["historical_model"], 0.20)

    def test_03_geojson_risk_map_generation(self):
        """Test 5x5 GeoJSON Grid generation for Leaflet map overlay"""
        geojson = fusion_engine_service.generate_risk_map("Uttarakhand", 30.0668, 79.0193)
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(geojson["total_cells"], 25)
        self.assertEqual(len(geojson["features"]), 25)
        self.assertIn("fill_color", geojson["features"][0]["properties"])

    def test_04_api_satellite_historical(self):
        """Test GET /api/satellite/historical"""
        res = self.app.get("/api/satellite/historical?lat=30.0668&lon=79.0193&years=5")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["images"]), 5)

    def test_05_api_satellite_current(self):
        """Test GET /api/satellite/current"""
        res = self.app.get("/api/satellite/current?lat=30.0668&lon=79.0193")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("ndvi", data["satellite_data"])

    def test_06_api_satellite_compare(self):
        """Test GET /api/satellite/compare"""
        res = self.app.get("/api/satellite/compare?lat=30.0668&lon=79.0193")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("ndvi_anomaly", data)

    def test_07_api_fusion_analyze_post(self):
        """Test POST /api/fusion/analyze"""
        payload = {
            "lat": 30.0668,
            "lon": 79.0193,
            "iot_data": {
                "soil_moisture": 92.0,
                "temperature": 26.0,
                "humidity": 88.0,
                "tilt": 1,
                "vibration": 1,
                "flame": 0
            }
        }
        res = self.app.post("/api/fusion/analyze", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["risk_score"], 60.0)

    def test_08_api_fusion_risk_map(self):
        """Test GET /api/fusion/risk_map"""
        res = self.app.get("/api/fusion/risk_map?region=Uttarakhand")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["type"], "FeatureCollection")

    def test_09_api_prediction_next_24h(self):
        """Test GET /api/prediction/next_24h"""
        res = self.app.get("/api/prediction/next_24h?lat=30.0668&lon=79.0193")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("landslide_risk", data)

    def test_10_api_prediction_monsoon_outlook(self):
        """Test GET /api/prediction/monsoon_outlook"""
        res = self.app.get("/api/prediction/monsoon_outlook?region=Uttarakhand")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("outlook", data)


if __name__ == "__main__":
    unittest.main()
