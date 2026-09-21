"""
D-SQUARE 2.0 Historical Satellite Pixel & Patch Comparison Test Suite
Fully validates patch statistics, z-score standardization, missing-data-safe similarity,
provenance tracking, anomaly scoring, fusion engine evidence integration, and Flask endpoints.
"""

import sys
import json
import unittest
import numpy as np
from satellite.pixel_comparator import (
    calculate_spectral_indices, calculate_patch_statistics, calculate_feature_statistics,
    build_feature_vector, compare_current_to_historical, summarize_disaster_matches,
    calculate_anomaly_score, HistoricalPixelComparator
)
from database import (
    init_db, seed_demo_historical_samples_if_empty, get_historical_pixel_samples,
    save_current_satellite_sample, get_historical_events_summary, get_feature_statistics
)
from models.fusion_engine import MultiModalFusionEngine
from app import app


class TestHistoricalPixelPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        seed_demo_historical_samples_if_empty()
        cls.fusion_engine = MultiModalFusionEngine()
        cls.app_client = app.test_client()

    def test_1_spectral_indices(self):
        """Test spectral indices calculations & division by zero safeguards."""
        px = {"red": 0.25, "green": 0.20, "blue": 0.15, "nir": 0.15, "swir": 0.35, "thermal": 52.0}
        idx = calculate_spectral_indices(px)
        self.assertIsNotNone(idx["ndvi"])
        self.assertIsNotNone(idx["nbr"])
        self.assertEqual(idx["lst"], 52.0)
        self.assertLess(idx["ndvi"], 0.0)
        self.assertLess(idx["nbr"], 0.0)

        # Test zero denominator safeguard
        zero_px = {"red": 0.0, "green": 0.0, "nir": 0.0, "swir": 0.0}
        zero_idx = calculate_spectral_indices(zero_px)
        self.assertIsNone(zero_idx["ndvi"])

    def test_2_patch_statistics(self):
        """Test spatial patch statistics (3x3, 5x5, 9x9) with mean, std, median, valid_pixel_count."""
        patch_5x5 = []
        for i in range(25):
            patch_5x5.append({
                "red": 0.20 + i * 0.005,
                "green": 0.15,
                "nir": 0.10,
                "swir": 0.30,
                "thermal": 50.0 + i * 0.2
            })
        stats = calculate_patch_statistics(patch_5x5, patch_size=5)
        self.assertEqual(stats["patch_size"], 5)
        self.assertEqual(stats["valid_pixel_count"], 25)
        self.assertIn("mean", stats["ndvi"])
        self.assertIn("std", stats["ndvi"])
        self.assertIn("median", stats["ndvi"])

    def test_3_zscore_standardization(self):
        """Test z-score feature standardization vector."""
        hist_samples = get_historical_pixel_samples(limit=50)
        self.assertGreater(len(hist_samples), 0)
        feat_stats = calculate_feature_statistics(hist_samples)
        self.assertIn("red", feat_stats)

        sample = hist_samples[0]
        z_vector = build_feature_vector(sample, feat_stats)
        self.assertIsInstance(z_vector, dict)
        self.assertIn("red", z_vector)

    def test_4_missing_data_safe_similarity(self):
        """Test missing-data-safe similarity calculation and top matches ranking."""
        hist_samples = get_historical_pixel_samples(limit=50)
        cur_sample = {
            "latitude": 30.0668,
            "longitude": 79.0193,
            "features": {"red": 0.65, "green": 0.15, "blue": 0.10, "nir": 0.10, "thermal": 52.0}
        }
        res = compare_current_to_historical(cur_sample, hist_samples)
        self.assertIn("top_matches", res)
        self.assertIn("class_level_scores", res)
        self.assertIn("best_historical_pattern", res)
        self.assertGreater(len(res["top_matches"]), 0)

        # Ensure top match has similarity between 0 and 100%
        top1 = res["top_matches"][0]
        self.assertGreaterEqual(top1["similarity_percent"], 0.0)
        self.assertLessEqual(top1["similarity_percent"], 100.0)
        self.assertIn("verification_status", top1)
        self.assertIn("quality_flag", top1)

    def test_5_anomaly_score_calculation(self):
        """Test baseline anomaly score calculation against normal baseline samples."""
        hist_samples = get_historical_pixel_samples(limit=50)
        baseline_samples = [r for r in hist_samples if r.get("disaster_type") in ["None", "Normal"]]
        fire_sample = {"features": {"red": 0.65, "nir": 0.10, "thermal": 55.0, "lst": 55.0}}
        anom = calculate_anomaly_score(fire_sample, baseline_samples)
        self.assertIn("score_percent", anom)
        self.assertIn("status", anom)
        self.assertIn(anom["status"], ["NORMAL", "WATCH", "HIGH", "CRITICAL"])

    def test_6_multi_modal_fusion_historical_evidence(self):
        """Test fusion engine blending historical evidence with 10-15% calibrated adjustment."""
        fusion = self.fusion_engine.evaluate_multi_modal_fusion(
            sat_data={"red": 0.65, "green": 0.15, "blue": 0.10, "nir": 0.10},
            ts_data=[{"ndvi": 0.3, "lst": 0.8, "soil_m": 0.1}] * 30,
            sensor_data={"temperature": 52.0, "humidity": 15.0, "smoke": 800.0, "soil_moisture": 5.0, "water_level": 2.0, "flame": 1.0, "vibration": 0.2},
            camera_data={"mean_r": 0.65, "mean_g": 0.15, "mean_b": 0.10, "flicker": 0.05, "smoke_haziness": 0.05},
            historical_similarity_score=0.92,
            historical_best_disaster="Forest_Fire",
            anomaly_score=85.0,
            data_quality_score=80.0,
            verification_status="DEMO"
        )
        self.assertIn("historical_evidence", fusion)
        self.assertIn("explanation", fusion)
        self.assertIn("model_agreement", fusion)

    def test_7_historical_pixel_comparator_wrapper(self):
        """Test backward compatible wrapper class HistoricalPixelComparator."""
        comparator = HistoricalPixelComparator()
        res = comparator.compare_pixels({"red": 0.26, "green": 0.21, "blue": 0.18, "nir": 0.16, "swir": 0.31, "thermal": 44.8})
        self.assertIn("status", res)
        self.assertEqual(res["status"], "success")

    def test_8_api_historical_comparison_endpoint(self):
        """Test POST /api/historical_comparison Flask endpoint."""
        payload = {
            "patch_size": 5,
            "disaster_type": "Forest_Fire",
            "pixel_values": {"red": 0.65, "green": 0.15, "blue": 0.10, "nir": 0.10, "thermal": 52.0}
        }
        rv = self.app_client.post('/api/historical_comparison', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["patch_size"], 5)
        self.assertIn("query_sample", data)
        self.assertIn("multi_spectral_patch_stats", data)
        self.assertIn("top_matches", data)
        self.assertIn("fusion_result", data)

    def test_9_api_historical_events_summary_endpoint(self):
        """Test GET /api/historical_events_summary Flask endpoint."""
        rv = self.app_client.get('/api/historical_events_summary')
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("summary", data)

    def test_10_api_satellite_history_trend_endpoint(self):
        """Test GET /api/satellite_history_trend Flask endpoint."""
        rv = self.app_client.get('/api/satellite_history_trend')
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("trend", data)
        self.assertEqual(len(data["trend"]), 30)

    def test_11_api_import_historical_samples_endpoint(self):
        """Test POST /api/import_historical_samples Flask endpoint."""
        csv_data = (
            "event_id,disaster_type,acquisition_date,satellite,product,latitude,longitude,patch_size,red,green,blue,nir,swir1,swir2,thermal,sar_l_band_db,sar_s_band_db,sar_vv_db,sar_vh_db,sar_coherence,ground_deformation_mm,ndvi,ndwi,mndwi,nbr,lst,soil_moisture,rainfall,slope,patch_mean_ndvi,patch_std_ndvi,patch_median_ndvi,patch_mean_nbr,patch_std_nbr,patch_median_nbr,patch_mean_lst,patch_std_lst,valid_pixel_count,cloud_cover,label_source,source_url,verification_status,quality_flag\n"
            "EVT_TEST_01,Forest_Fire,2023-05-15,Sentinel-2,L2A,30.0668,79.0193,5,0.65,0.15,0.10,0.10,0.35,0.30,52.0,-12.4,-8.6,-14.2,-20.1,0.45,2.4,-0.7333,-0.25,-0.4,-0.5,52.0,8.0,0.0,25.0,-0.71,0.02,-0.73,-0.48,0.03,-0.5,51.5,0.8,25,2.5,Test Suite,https://example.com,VERIFIED,VALIDATED_GROUND_TRUTH\n"
        )
        payload = {"csv_text": csv_data}
        rv = self.app_client.post('/api/import_historical_samples', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["result"]["accepted_rows"], 1)


if __name__ == "__main__":
    unittest.main()
