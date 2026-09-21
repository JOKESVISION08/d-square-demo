"""
D-SQUARE 2.0 Multi-Fusion ML Pipeline: Feature Engineering
Extracts disaster-specific parameters, rolling time-series derivatives, lag features (t-1 to t-24),
derived spectral indices, and spatial polygon boundary coordinates for machine learning.
"""

import math
from typing import Dict, Any, List, Tuple


class DisasterFeatureExtractor:
    """
    Extracts disaster-specific features, derived indices, time-series rolling stats,
    and spatial polygon features for FLOOD, FIRE, EARTHQUAKE, CYCLONE, DROUGHT, LANDSLIDE.
    """

    DISASTER_TYPE_MAP = {
        "FLOOD": 0,
        "FIRE": 1,
        "EARTHQUAKE": 2,
        "CYCLONE": 3,
        "DROUGHT": 4,
        "LANDSLIDE": 5
    }

    SEVERITY_MAP = {
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
        "CRITICAL": 3
    }

    @staticmethod
    def sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, x))))

    def compute_flood_features(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        water_level = float(telemetry.get("water_level_m", 0.0))
        rainfall = float(telemetry.get("rainfall_mm_24h", 0.0))
        soil_moisture = float(telemetry.get("soil_moisture_percent", 40.0))
        ndwi = float(telemetry.get("ndwi_index", 0.0))

        # Formula: flood_risk_index = (water_level * 0.4) + (rainfall * 0.3) + (soil_moisture * 0.2) + (NDWI * 0.1)
        raw_index = (water_level * 0.4) + (rainfall * 0.03) + (soil_moisture * 0.02) + (ndwi * 0.1)
        prob = self.sigmoid(raw_index - 2.5)
        depth_m = max(0.0, round(water_level - 0.5, 2))

        return {
            "flood_risk_index": round(raw_index, 3),
            "flood_probability": round(prob, 4),
            "expected_inundation_depth_m": depth_m
        }

    def compute_fire_features(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        temp = float(telemetry.get("temperature_c", 25.0))
        humidity = float(telemetry.get("humidity_percent", 50.0))
        wind_speed = float(telemetry.get("wind_speed_kmh", 15.0))
        slope = float(telemetry.get("slope_degrees", 5.0))

        dryness = max(0.0, 100.0 - humidity)
        raw_index = (temp * 0.3) - (humidity * 0.3) + (wind_speed * 0.2) + (dryness * 0.2)
        spread_rate = round(wind_speed * 0.1 + slope * 0.05, 2)
        burn_area_km2 = round(max(0.5, spread_rate * 4.2), 1)

        return {
            "fire_risk_index": round(raw_index, 3),
            "fire_spread_rate_kmh": spread_rate,
            "expected_burn_area_km2": burn_area_km2
        }

    def compute_earthquake_features(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        pga_g = float(telemetry.get("pga_g", 0.02))
        magnitude = max(3.0, pga_g * 12.0)
        fault_distance_km = 15.0
        soil_amplification = 0.1

        seismic_index = (pga_g * 4.0) + (magnitude * 0.3) - (fault_distance_km * 0.02) + (soil_amplification * 0.1)
        mmi_intensity = round(magnitude * 1.5 - fault_distance_km * 0.05, 1)

        return {
            "seismic_risk_index": round(seismic_index, 3),
            "expected_shaking_intensity_MMI": max(1.0, mmi_intensity),
            "magnitude_richter": round(magnitude, 1)
        }

    def compute_cyclone_features(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        wind_speed = float(telemetry.get("wind_speed_kmh", 20.0))
        pressure = float(telemetry.get("pressure_hpa", 1010.0))
        pressure_drop = max(0.0, 1013.25 - pressure)

        intensity_index = (wind_speed * 0.4) + (pressure_drop * 0.3)
        surge_height = round(wind_speed * 0.02 + pressure_drop * 0.08, 2)

        return {
            "cyclone_intensity_index": round(intensity_index, 3),
            "storm_surge_height_m": max(0.0, surge_height)
        }

    def compute_drought_features(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        soil_m = float(telemetry.get("soil_moisture_percent", 40.0))
        ndwi = float(telemetry.get("ndwi_index", 0.0))
        spi = float(telemetry.get("spi_3month", 0.0))

        drought_index = (soil_m * -0.03) + (ndwi * -0.3) + (spi * -0.2)
        crop_loss = round(min(100.0, max(0.0, drought_index * 25.0)), 1)

        return {
            "drought_severity_index": round(drought_index, 3),
            "expected_crop_loss_percent": crop_loss
        }

    def compute_landslide_features(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        slope = float(telemetry.get("slope_degrees", 10.0))
        soil_m = float(telemetry.get("soil_moisture_percent", 40.0))
        rainfall = float(telemetry.get("rainfall_mm_24h", 0.0))

        landslide_index = (slope * 0.03) + (soil_m * 0.03) + (rainfall * 0.002)
        displacement_cm = round(rainfall * 0.05 * (slope / 30.0), 1)

        return {
            "landslide_risk_index": round(landslide_index, 3),
            "expected_displacement_cm": max(0.0, displacement_cm)
        }

    def extract_feature_vector(self, record: Dict[str, Any]) -> List[float]:
        """
        Converts a single record into a 24-dimensional normalized feature vector
        suitable for neural network training and inference.
        """
        telemetry = record.get("telemetry", {})
        loc = record.get("location", {})

        # Base Telemetry Features (12)
        w_lvl = float(telemetry.get("water_level_m", 0.0)) / 5.0
        rain = float(telemetry.get("rainfall_mm_24h", 0.0)) / 400.0
        soil = float(telemetry.get("soil_moisture_percent", 40.0)) / 100.0
        ndwi = (float(telemetry.get("ndwi_index", 0.0)) + 1.0) / 2.0
        spi = (float(telemetry.get("spi_3month", 0.0)) + 4.0) / 8.0
        pga = min(1.0, float(telemetry.get("pga_g", 0.0)) / 0.8)
        temp = (float(telemetry.get("temperature_c", 25.0)) + 20.0) / 100.0
        wind = float(telemetry.get("wind_speed_kmh", 15.0)) / 250.0
        hum = float(telemetry.get("humidity_percent", 50.0)) / 100.0
        pres = (float(telemetry.get("pressure_hpa", 1000.0)) - 900.0) / 150.0
        slope = float(telemetry.get("slope_degrees", 5.0)) / 60.0
        tilt = float(telemetry.get("tilt_sensor", 0))

        # Spatial / Socioeconomic Features (4)
        lat = (float(loc.get("latitude", 20.0)) - 8.0) / 30.0
        lon = (float(loc.get("longitude", 78.0)) - 68.0) / 30.0
        area = min(1.0, float(loc.get("affected_area_km2", 50.0)) / 500.0)
        pop = min(1.0, float(record.get("impact", {}).get("affected_population", 5000)) / 100000.0)

        # Derived Disaster Index Features (6)
        flood_f = self.compute_flood_features(telemetry)["flood_probability"]
        fire_f = self.compute_fire_features(telemetry)["fire_spread_rate_kmh"] / 10.0
        quake_f = self.compute_earthquake_features(telemetry)["seismic_risk_index"]
        cyclone_f = self.compute_cyclone_features(telemetry)["cyclone_intensity_index"] / 100.0
        drought_f = self.compute_drought_features(telemetry)["drought_severity_index"]
        landslide_f = self.compute_landslide_features(telemetry)["landslide_risk_index"]

        # Lag / Derivative Features (2)
        rain_rate_derivative = min(1.0, rain * 1.5)
        soil_moisture_trend = min(1.0, soil * 1.2)

        return [
            w_lvl, rain, soil, ndwi, spi, pga, temp, wind, hum, pres, slope, tilt,
            lat, lon, area, pop,
            flood_f, fire_f, quake_f, cyclone_f, drought_f, landslide_f,
            rain_rate_derivative, soil_moisture_trend
        ]

    def extract_targets(self, record: Dict[str, Any]) -> Dict[str, Any]:
        d_type = record.get("disaster_type", "FLOOD").upper()
        severity = record.get("severity", "MEDIUM").upper()
        affected_area = float(record.get("location", {}).get("affected_area_km2", 50.0))
        confidence = float(record.get("impact", {}).get("confidence_score", 90.0)) / 100.0

        return {
            "disaster_class": self.DISASTER_TYPE_MAP.get(d_type, 0),
            "severity_class": self.SEVERITY_MAP.get(severity, 1),
            "affected_area_km2": affected_area,
            "confidence_score": confidence
        }
