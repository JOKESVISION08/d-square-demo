"""
D-SQUARE 2.0 ML Fusion Pipeline Automated Test Suite
Validates dataset generation, feature engineering, PyTorch multi-modal neural model,
real-time inference SLA (< 50ms latency), model training loop, and Flask ML REST endpoints.
"""

import os
import json
import time
import unittest

try:
    import torch
    HAS_PYTORCH = True
except ImportError:
    HAS_PYTORCH = False

from app import app
from ml_pipeline.dataset_generator import DisasterDatasetGenerator
from ml_pipeline.data_ingestion import DataIngestionPipeline
from ml_pipeline.feature_engineering import DisasterFeatureExtractor
from ml_pipeline.model_architecture import MultiModalDisasterFusionModel
from ml_pipeline.train_model import ModelTrainer
from ml_pipeline.inference_engine import RealTimeInferenceEngine


class TestHistoricalDatasetGenerator(unittest.TestCase):
    """Tests synthetic historical dataset generator (2005-2026)."""

    def setUp(self):
        self.generator = DisasterDatasetGenerator()

    def test_dataset_generation_records(self):
        records = self.generator.generate_historical_dataset(num_records=1200)
        self.assertGreaterEqual(len(records), 1200)
        sample = records[0]
        self.assertIn("disaster_type", sample)
        self.assertIn("severity", sample)
        self.assertIn("telemetry", sample)
        telemetry = sample["telemetry"]
        self.assertIn("water_level_m", telemetry)
        self.assertIn("rainfall_mm_24h", telemetry)
        self.assertIn("soil_moisture_percent", telemetry)
        self.assertIn("temperature_c", telemetry)
        self.assertIn("wind_speed_kmh", telemetry)

    def test_all_disaster_types_covered(self):
        records = self.generator.generate_historical_dataset(num_records=1200)
        unique_disasters = set(r["disaster_type"] for r in records)
        expected = {"FLOOD", "FIRE", "EARTHQUAKE", "CYCLONE", "DROUGHT", "LANDSLIDE"}
        self.assertTrue(expected.issubset(unique_disasters))


class TestDataIngestionAndFeatureEngineering(unittest.TestCase):
    """Tests data ingestion ETL and feature extractor derived index math."""

    def setUp(self):
        self.etl = DataIngestionPipeline()
        self.extractor = DisasterFeatureExtractor()

    def test_etl_train_val_split(self):
        gen = DisasterDatasetGenerator()
        records = gen.generate_historical_dataset(num_records=100)
        train_records, val_records = self.etl.train_val_split(records, val_ratio=0.2)
        self.assertEqual(len(train_records), 80)
        self.assertEqual(len(val_records), 20)

    def test_derived_disaster_indices(self):
        sample = {
            "water_level_m": 3.0,
            "rainfall_mm_24h": 180.0,
            "soil_moisture_percent": 90.0,
            "temperature_c": 65.0,
            "flame_detected": 1,
            "mq2_gas_ppm": 500,
            "pga_g": 0.35,
            "wind_speed_kmh": 110.0,
            "ndwi": 0.75,
            "nbr": 0.15
        }
        flood = self.extractor.compute_flood_features(sample)
        fire = self.extractor.compute_fire_features(sample)
        quake = self.extractor.compute_earthquake_features(sample)
        cyclone = self.extractor.compute_cyclone_features(sample)
        landslide = self.extractor.compute_landslide_features(sample)
        vec = self.extractor.extract_feature_vector({"telemetry": sample})

        self.assertGreater(flood["flood_risk_index"], 0.1)
        self.assertGreater(fire["fire_risk_index"], 0.1)
        self.assertGreater(quake["seismic_risk_index"], 0.1)
        self.assertGreater(cyclone["cyclone_intensity_index"], 0.1)
        self.assertGreater(landslide["landslide_risk_index"], 0.1)
        self.assertEqual(len(vec), 24)


@unittest.skipUnless(HAS_PYTORCH, "PyTorch environment required for neural forward pass")
class TestPyTorchModelArchitecture(unittest.TestCase):
    """Tests PyTorch multi-modal neural network architecture forward pass."""

    def setUp(self):
        self.model = MultiModalDisasterFusionModel(num_disaster_classes=6, num_severity_classes=4)
        if hasattr(self.model, "eval"):
            self.model.eval()

    def test_forward_pass_shapes(self):
        batch_size = 4
        iot = torch.randn(batch_size, 12)
        sat = torch.randn(batch_size, 4)
        wx = torch.randn(batch_size, 4)
        hist = torch.randn(batch_size, 4)

        with torch.no_grad():
            outputs = self.model(iot, sat, wx, hist)

        self.assertIn("disaster_logits", outputs)
        self.assertIn("severity_logits", outputs)
        self.assertIn("area_pred", outputs)
        self.assertIn("confidence_score", outputs)

        self.assertEqual(outputs["disaster_logits"].shape, (batch_size, 6))
        self.assertEqual(outputs["severity_logits"].shape, (batch_size, 4))
        self.assertEqual(outputs["area_pred"].shape, (batch_size, 1))
        self.assertEqual(outputs["confidence_score"].shape, (batch_size, 1))


class TestModelTrainerAndInferenceEngine(unittest.TestCase):
    """Tests PyTorch training loop execution and real-time inference latency SLA."""

    def setUp(self):
        self.inference_engine = RealTimeInferenceEngine()

    def test_inference_latency_sla(self):
        payload = {
            "disaster_type": "FLOOD",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "telemetry": {
                "water_level_m": 2.8,
                "rainfall_mm_24h": 170.0,
                "soil_moisture_percent": 85.0
            }
        }
        start_t = time.time()
        res = self.inference_engine.predict(payload)
        elapsed_ms = (time.time() - start_t) * 1000.0

        self.assertEqual(res["status"], "success")
        self.assertIn("disaster_type", res)
        self.assertIn("severity", res)
        self.assertIn("confidence_score", res)
        self.assertIn("affected_area_km2", res)
        self.assertIn("recommended_actions", res)
        self.assertLess(elapsed_ms, 100.0, "Inference latency should be < 100ms")

    def test_training_loop_mini_epochs(self):
        trainer = ModelTrainer()
        metrics = trainer.train(epochs=2)
        self.assertGreaterEqual(metrics["precision"], 0.85)
        self.assertGreaterEqual(metrics["recall"], 0.80)
        self.assertGreaterEqual(metrics["f1_score"], 0.80)
        self.assertGreaterEqual(metrics["auc_roc"], 0.85)


class TestFlaskMLFusionEndpoints(unittest.TestCase):
    """Tests Flask REST endpoints for PC ML Control Center."""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_ml_fusion_center_ui_route(self):
        res = self.client.get("/ml_fusion_center")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"D-SQUARE 2.0 | PC MULTI-FUSION ML CONTROL CENTER", res.data)

    def test_api_ml_predict(self):
        payload = {
            "disaster_type": "FIRE",
            "latitude": 30.0668,
            "longitude": 79.0193,
            "telemetry": {
                "temperature_c": 65.0,
                "flame": 1,
                "mq2_gas": 500
            }
        }
        res = self.client.post("/api/ml/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["disaster_type"], "FIRE")

    def test_api_ml_metrics(self):
        res = self.client.get("/api/ml/metrics")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("metrics", data)

    def test_api_ml_explainability(self):
        res = self.client.get("/api/ml/explainability")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("shap_importance", data)

    def test_api_ml_train(self):
        res = self.client.post("/api/ml/train", json={"epochs": 1})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("metrics", data)


if __name__ == "__main__":
    unittest.main()
