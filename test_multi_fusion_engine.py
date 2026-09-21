"""
D-SQUARE 2.0 Multi-Parameter Fusion Engine Test Suite
Tests detection logic for all 6 disaster types (FLOOD, FIRE, EARTHQUAKE, CYCLONE, DROUGHT, LANDSLIDE),
weighted ensemble scoring, and false positive suppression.
"""

import unittest
import json
from app import app
from services.multi_parameter_detection import (
    MultiParameterFusionEngine, FloodParams, FireParams, EarthquakeParams,
    CycloneParams, DroughtParams, LandslideParams
)


class TestMultiFusionEngine(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_01_flood_detection_parameters(self):
        """Test Flood parameters: Water level > 2m, Rainfall > 100mm/hr, NDWI > 0.5"""
        iot = {"water_level": 2.5, "rainfall": 120.0, "soil_moisture": 90.0, "river_gauge": 92.0}
        sat = {"ndwi": 0.65, "water_body_expansion": 40.0}
        wx = {"rain_24h": 180.0, "humidity": 95.0}
        ai = {"flood_probability": 88.0}

        res = FloodParams.evaluate(iot, sat, wx, ai)
        self.assertTrue(res["is_detected"])
        self.assertEqual(res["disaster_type"], "FLOOD")
        self.assertIn(res["severity"], ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(res["confidence"], 80.0)
        self.assertGreaterEqual(res["confirmations"], 2)

    def test_02_fire_detection_parameters(self):
        """Test Fire parameters: Temp > 60°C, Smoke > 500ppm, Thermal Anomaly > 50°C, FIRMS pixel"""
        iot = {"temperature": 75.0, "surface_temperature": 115.0, "smoke_co2": 650.0, "humidity": 15.0}
        sat = {"thermal_anomaly_c": 62.0, "firms_active_fire": True, "nbr": 0.05}
        wx = {"humidity": 18.0, "wind_speed": 35.0}
        ai = {"fire_risk": 82.0}

        res = FireParams.evaluate(iot, sat, wx, ai)
        self.assertTrue(res["is_detected"])
        self.assertEqual(res["disaster_type"], "FIRE")
        self.assertIn(res["severity"], ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(res["confidence"], 75.0)

    def test_03_earthquake_detection_parameters(self):
        """Test Earthquake parameters: PGA > 0.1g, InSAR > 10cm, Magnitude > 5.0"""
        iot = {"pga_seismic_g": 0.25, "tilt_shift_deg": 6.5, "structural_stress_percent": 85.0}
        sat = {"insar_displacement_cm": 14.2, "building_collapse_detected": True}
        wx = {}
        ai = {"richter_magnitude": 6.2, "aftershock_probability": 70.0}

        res = EarthquakeParams.evaluate(iot, sat, wx, ai)
        self.assertTrue(res["is_detected"])
        self.assertEqual(res["disaster_type"], "EARTHQUAKE")
        self.assertEqual(res["severity"], "CRITICAL")
        self.assertGreaterEqual(res["confidence"], 80.0)

    def test_04_cyclone_detection_parameters(self):
        """Test Cyclone parameters: Wind > 100km/h, Pressure < 980hPa, Cyclone eye pattern"""
        iot = {"wind_speed": 130.0, "barometric_pressure": 965.0, "rain_24h": 220.0}
        sat = {"cyclone_eye_detected": True, "cloud_top_temp_c": -75.0, "storm_surge_m": 3.5}
        wx = {"sea_surface_temp_c": 30.0, "vertical_wind_shear": 6.0}
        ai = {"landfall_probability": 85.0, "coastal_location": True}

        res = CycloneParams.evaluate(iot, sat, wx, ai)
        self.assertTrue(res["is_detected"])
        self.assertEqual(res["disaster_type"], "CYCLONE")
        self.assertEqual(res["severity"], "CRITICAL")

    def test_05_drought_detection_parameters(self):
        """Test Drought parameters: Soil moisture < 15%, Groundwater > 50m, NDVI < 0.2, SPI < -2.0"""
        iot = {"soil_moisture": 11.0, "groundwater_depth_m": 58.0, "reservoir_capacity_percent": 14.0}
        sat = {"ndvi": 0.15, "lst_c": 47.5, "tci": 22.0, "vci": 18.0}
        wx = {"spi": -2.4, "consecutive_dry_days": 75}
        ai = {"drought_probability": 86.0}

        res = DroughtParams.evaluate(iot, sat, wx, ai)
        self.assertTrue(res["is_detected"])
        self.assertEqual(res["disaster_type"], "DROUGHT")
        self.assertIn(res["severity"], ["MEDIUM", "HIGH"])

    def test_06_landslide_detection_parameters(self):
        """Test Landslide parameters: Tilt > 10°, Soil Moisture > 90%, InSAR > 15cm, Slope > 30°"""
        iot = {"tilt_shift_deg": 14.5, "soil_moisture": 94.0, "vibration": 120.0}
        sat = {"insar_displacement_cm": 18.5, "slope_deg": 38.0}
        wx = {"rain_24h": 175.0, "antecedent_rain_7d": 340.0}
        ai = {"landslide_probability": 82.0}

        res = LandslideParams.evaluate(iot, sat, wx, ai)
        self.assertTrue(res["is_detected"])
        self.assertEqual(res["disaster_type"], "LANDSLIDE")
        self.assertIn(res["severity"], ["HIGH", "CRITICAL"])

    def test_07_false_positive_suppression(self):
        """Test False Positive Suppression: Requires 2+ independent confirmations"""
        # Single isolated unconfirmed high sensor spike without satellite or AI backing
        iot = {"temperature": 65.0, "smoke_co2": 100.0} # Temp high but no smoke
        sat = {"thermal_anomaly_c": 5.0, "firms_active_fire": False}
        wx = {"humidity": 60.0, "wind_speed": 10.0}
        ai = {"fire_risk": 20.0}

        res = FireParams.evaluate(iot, sat, wx, ai)
        self.assertFalse(res["is_detected"])
        self.assertEqual(res["severity"], "NONE")

    def test_08_api_v1_detect_disaster_endpoint(self):
        """Test POST /api/v1/detect-disaster API contract"""
        payload = {
            "location": {"latitude": 19.0760, "longitude": 72.8777, "area_name": "Mumbai Coastal Area"},
            "sensor_data": {"water_level": 2.6, "rainfall": 140.0, "soil_moisture": 89.0},
            "satellite_data": {"ndwi": 0.62, "water_body_expansion": 35.0},
            "weather_data": {"rain_24h": 190.0},
            "ai_prediction": {"flood_probability": 86.0}
        }

        res = self.app.post("/api/v1/detect-disaster", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["disaster_type"], "FLOOD")
        self.assertIn(data["severity"], ["HIGH", "CRITICAL"])
        self.assertIn("parallel_sos_dispatch", data["full_fusion_analysis"])


if __name__ == "__main__":
    unittest.main()
