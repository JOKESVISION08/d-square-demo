"""
D-SQUARE 2.0 Multi-Modal Fusion Engine
Combines predictions from 4 AI models:
- Satellite Imagery CNN (25% Weight)
- Time-Series LSTM (25% Weight)
- ESP8266 Ground Sensor RF (25% Weight)
- Mobile Camera Real-Time CV (25% Weight)
Computes final disaster probability (0-100%) and risk tier (CRITICAL, HIGH, MEDIUM, LOW).
"""

import os
import pickle
import numpy as np
from typing import Dict, Any, List

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(MODELS_DIR, "dsquare_trained_models.pkl")


class MultiModalFusionEngine:
    """
    Ensemble Fusion Engine combining Satellite, Time-Series, IoT Sensors, and Camera CV predictions.
    Weight Distribution:
    - Satellite CNN: 0.25
    - LSTM Time-Series: 0.25
    - Ground Sensor RF: 0.25
    - Mobile Camera CV: 0.25
    """

    LAND_COVER_CLASSES = ["Forest", "Water", "Urban", "Agricultural", "Burnt_Scar", "Flood"]
    TIME_SERIES_RISK_CLASSES = ["Low", "Medium", "High"]
    DISASTER_TYPES = ["Forest_Fire", "Flood", "Landslide", "Air_Pollution", "None"]
    CAMERA_STATUS_CLASSES = ["Normal_Green", "Warning_Orange", "Critical_Red"]

    def __init__(self):
        self.models_loaded = False
        self._load_models()

    def _load_models(self):
        if not os.path.exists(MODEL_FILE):
            # Train if missing
            from models.train_models import train_and_save_all_models
            artifacts = train_and_save_all_models()
        else:
            with open(MODEL_FILE, "rb") as f:
                artifacts = pickle.load(f)

        self.sat_model = artifacts["satellite_model"]
        self.sat_scaler = artifacts["satellite_scaler"]
        self.ts_model = artifacts["timeseries_model"]
        self.ts_scaler = artifacts["timeseries_scaler"]
        self.sensor_model = artifacts["sensor_model"]
        self.sensor_scaler = artifacts["sensor_scaler"]
        self.cam_model = artifacts["camera_model"]
        self.cam_scaler = artifacts["camera_scaler"]
        self.models_loaded = True

    def predict_satellite_cnn(self, red: float, green: float, blue: float, nir: float) -> Dict[str, Any]:
        """
        Runs Satellite CNN Classifier.
        """
        eps = 1e-6
        ndvi = (nir - red) / (nir + red + eps)
        ndwi = (green - nir) / (green + nir + eps)
        brightness = (red + green + blue + nir) / 4.0
        variance = 0.03

        feat = np.array([[red, green, blue, nir, ndvi, ndwi, brightness, variance]], dtype=np.float32)
        scaled = self.sat_scaler.transform(feat)
        probs = self.sat_model.predict_proba(scaled)[0]
        pred_idx = np.argmax(probs)
        pred_class = self.LAND_COVER_CLASSES[pred_idx]
        confidence = float(probs[pred_idx])

        # Disaster risk score from land cover
        risk_score = 0.95 if pred_class in ["Burnt_Scar", "Flood"] else (0.4 if pred_class == "Agricultural" else 0.1)

        return {
            "predicted_class": pred_class,
            "confidence": round(confidence, 4),
            "risk_score": round(risk_score, 4),
            "probabilities": {cls: round(float(p), 4) for cls, p in zip(self.LAND_COVER_CLASSES, probs)}
        }

    def predict_timeseries_lstm(self, last_30_days_data: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Runs LSTM Time-Series Classifier (30-day sequence of [NDVI, LST_norm, Soil_M_norm]).
        """
        if len(last_30_days_data) < 30:
            # Fill or repeat if needed
            last_entry = last_30_days_data[-1] if last_30_days_data else {"ndvi": 0.7, "lst": 0.4, "soil_m": 0.4}
            while len(last_30_days_data) < 30:
                last_30_days_data.insert(0, last_entry)

        ndvi_arr = [d.get("ndvi", 0.7) for d in last_30_days_data[:30]]
        lst_arr = [d.get("lst", 0.4) for d in last_30_days_data[:30]]
        soil_arr = [d.get("soil_m", 0.4) for d in last_30_days_data[:30]]

        seq_feat = np.concatenate([ndvi_arr, lst_arr, soil_arr]).reshape(1, -1)
        scaled = self.ts_scaler.transform(seq_feat)
        probs = self.ts_model.predict_proba(scaled)[0]
        pred_idx = np.argmax(probs)
        pred_class = self.TIME_SERIES_RISK_CLASSES[pred_idx]
        confidence = float(probs[pred_idx])

        risk_score = 0.90 if pred_class == "High" else (0.50 if pred_class == "Medium" else 0.15)

        return {
            "predicted_risk_level": pred_class,
            "confidence": round(confidence, 4),
            "risk_score": round(risk_score, 4),
            "prediction_horizon": "3-7 Days",
            "probabilities": {cls: round(float(p), 4) for cls, p in zip(self.TIME_SERIES_RISK_CLASSES, probs)}
        }

    def predict_ground_sensor_rf(self, temp: float, humidity: float, smoke: float, soil_m: float, water_level: float, flame: float, vibration: float, tilt_angle: float = 0.0, gyro_rate: float = 0.0, tilt_state: int = 0) -> Dict[str, Any]:
        """
        Runs Random Forest Ground Sensor Classifier with MPU6050 Tilt & Gyroscope Fusion.
        """
        feat = np.array([[temp, humidity, smoke, soil_m, water_level, flame, vibration]], dtype=np.float32)
        scaled = self.sensor_scaler.transform(feat)
        probs = self.sensor_model.predict_proba(scaled)[0]

        # MPU6050 Gyro & Tilt Sensor Fusion Override for Landslide Detection
        if tilt_angle > 25.0 or tilt_state == 1 or gyro_rate > 30.0 or vibration > 6.0:
            landslide_idx = self.DISASTER_TYPES.index("Landslide")
            probs[landslide_idx] = max(probs[landslide_idx], 0.85)
            # Re-normalize probabilities
            probs = probs / np.sum(probs)

        pred_idx = np.argmax(probs)
        pred_disaster = self.DISASTER_TYPES[pred_idx]
        confidence = float(probs[pred_idx])

        risk_score = 0.05 if pred_disaster == "None" else 0.95

        return {
            "predicted_disaster": pred_disaster,
            "confidence": round(confidence, 4),
            "risk_score": round(risk_score, 4),
            "probabilities": {dis: round(float(p), 4) for dis, p in zip(self.DISASTER_TYPES, probs)}
        }

    def predict_mobile_camera_cnn(self, mean_r: float, mean_g: float, mean_b: float, flicker: float, smoke_haziness: float) -> Dict[str, Any]:
        """
        Runs Real-Time Mobile Camera CV Classifier (<100ms latency).
        """
        feat = np.array([[mean_r, mean_g, mean_b, flicker, smoke_haziness]], dtype=np.float32)
        scaled = self.cam_scaler.transform(feat)
        probs = self.cam_model.predict_proba(scaled)[0]
        pred_idx = np.argmax(probs)
        pred_status = self.CAMERA_STATUS_CLASSES[pred_idx]
        confidence = float(probs[pred_idx])

        risk_score = 0.95 if pred_status == "Critical_Red" else (0.60 if pred_status == "Warning_Orange" else 0.10)
        led_color = "RED" if pred_status == "Critical_Red" else ("ORANGE" if pred_status == "Warning_Orange" else "GREEN")
        buzzer_active = True if pred_status in ["Critical_Red", "Warning_Orange"] else False

        return {
            "camera_status": pred_status,
            "led_indicator": led_color,
            "buzzer_active": buzzer_active,
            "confidence": round(confidence, 4),
            "risk_score": round(risk_score, 4),
            "probabilities": {st: round(float(p), 4) for st, p in zip(self.CAMERA_STATUS_CLASSES, probs)}
        }

    def evaluate_multi_modal_fusion(
        self,
        sat_data: Dict[str, float],
        ts_data: List[Dict[str, float]],
        sensor_data: Dict[str, float],
        camera_data: Dict[str, float],
        historical_similarity_score: float = 0.0,
        historical_best_disaster: str = "None",
        anomaly_score: float = 0.0,
        data_quality_score: float = 80.0,
        verification_status: str = "DEMO",
        compatibility_level: str = "FULL"
    ) -> Dict[str, Any]:
        """
        Combines 4 core model predictions (25% each) with historical pattern evidence
        contributing a calibrated 10-15% maximum risk score adjustment.
        Returns final disaster probability %, risk tier, model agreement, and scientific explanation.
        """
        # 1. Satellite Prediction
        sat_res = self.predict_satellite_cnn(
            sat_data.get("red", 0.15),
            sat_data.get("green", 0.45),
            sat_data.get("blue", 0.15),
            sat_data.get("nir", 0.75)
        )

        # 2. Time-Series Prediction
        ts_res = self.predict_timeseries_lstm(ts_data)

        # 3. Ground Sensor Prediction (with MPU6050 Tilt/Gyro & SW-420/520D sensors)
        sns_res = self.predict_ground_sensor_rf(
            sensor_data.get("temperature", 28.0),
            sensor_data.get("humidity", 50.0),
            sensor_data.get("smoke", 200.0),
            sensor_data.get("soil_moisture", 40.0),
            sensor_data.get("water_level", 5.0),
            sensor_data.get("flame", 0.0),
            sensor_data.get("vibration", 0.2),
            tilt_angle=sensor_data.get("tilt_angle", 0.0),
            gyro_rate=sensor_data.get("gyro_rate", 0.0),
            tilt_state=sensor_data.get("tilt_state", 0)
        )

        # 4. Camera CV Prediction
        cam_res = self.predict_mobile_camera_cnn(
            camera_data.get("mean_r", 0.15),
            camera_data.get("mean_g", 0.65),
            camera_data.get("mean_b", 0.15),
            camera_data.get("flicker", 0.05),
            camera_data.get("smoke_haziness", 0.05)
        )

        # Core 4-model weighted base score (25% each)
        w_sat = 0.25
        w_ts = 0.25
        w_sns = 0.25
        w_cam = 0.25

        base_fusion_score = (
            sat_res["risk_score"] * w_sat +
            ts_res["risk_score"] * w_ts +
            sns_res["risk_score"] * w_sns +
            cam_res["risk_score"] * w_cam
        )

        # Historical Evidence Calibrated Adjustment (max 10-15%)
        # Scale down historical influence if DEMO or low quality data or VISUAL_ONLY
        qual_weight = max(min(data_quality_score / 100.0, 1.0), 0.2)
        demo_penalty = 0.5 if verification_status.upper() in ["DEMO", "UPLOADED_UNVERIFIED"] else 1.0
        
        # If VISUAL_ONLY, do not use it for physical spectral-risk calculations
        if compatibility_level.upper() == "VISUAL_ONLY":
            hist_weight = 0.0
        else:
            hist_weight = 0.12 * qual_weight * demo_penalty

        hist_risk_val = float(historical_similarity_score) if historical_best_disaster != "None" else 0.0
        
        # Blend base score (88-100%) and historical evidence (0-12%)
        fusion_score = base_fusion_score * (1.0 - hist_weight) + (hist_risk_val * hist_weight)
        disaster_probability = round(float(np.clip(fusion_score * 100.0, 0.0, 100.0)), 2)

        # Determine Risk Level Tier
        if disaster_probability > 80.0:
            risk_level = "CRITICAL"
        elif disaster_probability >= 60.0:
            risk_level = "HIGH"
        elif disaster_probability >= 40.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Primary Disaster Type Determination
        predicted_disaster = sns_res["predicted_disaster"]
        if predicted_disaster == "None":
            if sat_res["predicted_class"] == "Burnt_Scar":
                predicted_disaster = "Forest_Fire"
            elif sat_res["predicted_class"] == "Flood":
                predicted_disaster = "Flood"
            elif ts_res["predicted_risk_level"] == "High":
                predicted_disaster = "Landslide"
            elif historical_best_disaster != "None" and historical_similarity_score > 0.75:
                predicted_disaster = historical_best_disaster
            else:
                predicted_disaster = "None"

        # Model Agreement Evaluation
        preds = [
            sat_res["predicted_class"] if sat_res["predicted_class"] in ["Burnt_Scar", "Flood"] else "None",
            sns_res["predicted_disaster"],
            cam_res["camera_status"] if cam_res["camera_status"] == "Critical_Red" else "None",
            historical_best_disaster if historical_similarity_score > 0.6 else "None"
        ]
        
        # Check conflict between ground sensors and historical/sat
        if sns_res["predicted_disaster"] != "None" and historical_best_disaster != "None" and sns_res["predicted_disaster"] != historical_best_disaster:
            model_agreement = "CONFLICTING EVIDENCE"
        else:
            matching_preds = [p for p in preds if p != "None" and p == predicted_disaster]
            if len(matching_preds) >= 3:
                model_agreement = "STRONG"
            elif len(matching_preds) >= 2:
                model_agreement = "PARTIAL"
            else:
                model_agreement = "PARTIAL" if predicted_disaster != "None" else "STRONG"

        system_confidence = round(
            (sat_res["confidence"] + ts_res["confidence"] + sns_res["confidence"] + cam_res["confidence"]) / 4.0 * 100.0, 2
        )

        # Human-Readable Scientific Explanation
        demo_note = " (Historical contribution reduced due to DEMO satellite data mode)." if verification_status.upper() == "DEMO" else ""
        if predicted_disaster != "None":
            explanation = (
                f"{predicted_disaster.replace('_', ' ')} is the primary prediction because current ground telemetry and satellite analysis "
                f"indicate elevated risk with {disaster_probability}% probability. "
                f"Historical pattern matching shows {round(historical_similarity_score * 100, 1)}% similarity to past {historical_best_disaster.replace('_', ' ')} records.{demo_note}"
            )
        else:
            explanation = (
                "Normal environmental conditions detected across satellite remote sensing, ESP8266 IoT ground sensors, and mobile CV camera stream. "
                f"Baseline anomaly score is low at {round(anomaly_score, 1)}%."
            )

        return {
            "disaster_probability_percent": disaster_probability,
            "risk_level": risk_level,
            "predicted_disaster": predicted_disaster,
            "system_confidence_percent": system_confidence,
            "model_agreement": model_agreement,
            "explanation": explanation,
            "historical_evidence": {
                "similarity_score": round(historical_similarity_score, 4),
                "similarity_percent": round(historical_similarity_score * 100.0, 2),
                "best_matched_disaster": historical_best_disaster,
                "anomaly_score_percent": round(anomaly_score, 2),
                "verification_status": verification_status
            },
            "data_quality": {
                "score_percent": round(data_quality_score, 2),
                "verification_status": verification_status
            },
            "model_breakdown": {
                "satellite_cnn": sat_res,
                "timeseries_lstm": ts_res,
                "ground_sensors_rf": sns_res,
                "mobile_camera_cnn": cam_res,
            },
            "weights": {
                "satellite_cnn": w_sat,
                "timeseries_lstm": w_ts,
                "ground_sensors_rf": w_sns,
                "mobile_camera_cnn": w_cam,
                "historical_evidence_adj": round(hist_weight, 4)
            }
        }
