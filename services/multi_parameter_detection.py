"""
D-SQUARE 2.0 Multi-Parameter Disaster Detection Engine
Implements disaster-specific parameters, weighted ensemble scoring,
and false positive suppression for 6 disaster types:
FLOOD, FIRE, EARTHQUAKE, CYCLONE, DROUGHT, LANDSLIDE.
"""

import math
from datetime import datetime
from typing import Dict, Any, List, Tuple


class DisasterParams:
    """Base class for disaster-specific parameter evaluation"""

    @staticmethod
    def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        return max(min_val, min(max_val, val))


class FloodParams(DisasterParams):
    """
    Flood Detection Parameters:
    - IoT: Water level > 2.0m, Rainfall > 100mm/hr, Soil Moisture > 85%, River gauge > 90%
    - Satellite: NDWI > 0.5, Water body expansion > 30%, SAR backscatter
    - Weather: 24h Rainfall > 150mm, Humidity > 90%, Wind speed < 20 km/hr
    - AI: Flood ML probability > 80%, Drainage blockage > 70%
    """

    @classmethod
    def evaluate(cls, iot: Dict[str, Any], sat: Dict[str, Any], wx: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        water_level = float(iot.get("water_level", 0.0))
        rainfall = float(iot.get("rainfall", 0.0))
        soil_moisture = float(iot.get("soil_moisture", 0.0))
        river_gauge = float(iot.get("river_gauge", 0.0))

        ndwi = float(sat.get("ndwi", 0.0))
        water_expansion = float(sat.get("water_body_expansion", 0.0))
        sar_backscatter = float(sat.get("sar_backscatter_db", 0.0))

        wx_rain_24h = float(wx.get("rain_24h", 0.0))
        wx_humidity = float(wx.get("humidity", 0.0))

        flood_prob = float(ai.get("flood_probability", 0.0))
        drainage_block = float(ai.get("drainage_blockage", 0.0))

        triggered_params = []
        confirmations = 0

        # IoT Confirmation
        iot_score = 0.0
        if water_level > 2.0:
            triggered_params.append("water_level_critical (>2.0m)")
        if rainfall > 100.0:
            triggered_params.append("intense_rainfall (>100mm/hr)")
        if soil_moisture > 85.0:
            triggered_params.append("soil_saturation (>85%)")
        if river_gauge > 90.0:
            triggered_params.append("river_gauge_capacity (>90%)")

        if (water_level > 2.0 and rainfall > 100.0) or (water_level > 2.0 and soil_moisture > 85.0) or (river_gauge > 90.0):
            confirmations += 1
            iot_score = 0.90
        elif water_level > 1.5 or rainfall > 60.0 or soil_moisture > 75.0:
            iot_score = 0.55

        # Satellite Confirmation
        sat_score = 0.0
        if ndwi > 0.5:
            triggered_params.append("ndwi_water_index (>0.5)")
        if water_expansion > 30.0:
            triggered_params.append("water_body_expansion (>30%)")

        if (ndwi > 0.5 and water_expansion > 30.0) or (ndwi > 0.6):
            confirmations += 1
            sat_score = 0.92
        elif ndwi > 0.3 or water_expansion > 15.0:
            sat_score = 0.50

        # AI ML Model Confirmation
        ai_score = 0.0
        if flood_prob > 80.0:
            triggered_params.append("ai_flood_model (>80%)")
        if drainage_block > 70.0:
            triggered_params.append("drainage_capacity_blockage (>70%)")

        if (flood_prob > 80.0 and soil_moisture > 85.0) or (flood_prob > 85.0):
            confirmations += 1
            ai_score = 0.88
        elif flood_prob > 60.0:
            ai_score = 0.50

        # Weighted Ensemble: 40% IoT + 35% Satellite + 25% AI
        confidence = (0.40 * iot_score) + (0.35 * sat_score) + (0.25 * ai_score)
        confidence_percent = round(confidence * 100.0, 1)

        # Trigger Condition & Severity Logic
        rule1 = (water_level > 2.0 and rainfall > 100.0)
        rule2 = (ndwi > 0.5 and water_expansion > 30.0)
        rule3 = (flood_prob > 80.0 and soil_moisture > 85.0)

        is_detected = False
        severity = "NONE"

        if (rule1 or rule2 or rule3) and confirmations >= 2:
            is_detected = True
            if water_level > 3.0 or rainfall > 150.0 or confidence_percent > 85.0:
                severity = "CRITICAL"
            else:
                severity = "HIGH"
        elif (rule1 or rule2 or rule3) or confidence_percent > 65.0:
            is_detected = True
            severity = "MEDIUM"

        return {
            "disaster_type": "FLOOD",
            "is_detected": is_detected,
            "severity": severity,
            "confidence": confidence_percent,
            "confirmations": confirmations,
            "triggered_parameters": triggered_params,
            "recommended_actions": [
                "Deploy NDRF boat rescue units to flooded zones",
                "Evacuate citizens to designated high-ground shelters",
                "Issue restricted access warning for low-lying roads",
                "Set up emergency medical triage and water purification camps"
            ]
        }


class FireParams(DisasterParams):
    """
    Fire Detection Parameters:
    - IoT: Ambient temp > 60°C, Surface temp > 100°C, Smoke CO2 > 500ppm, Humidity < 20%
    - Satellite: Thermal anomaly > 50°C, FIRMS active fire pixels, NBR < 0.1, AOD > 0.5
    - Weather: Ambient temp > 40°C, Humidity < 25%, Wind speed > 30 km/hr, SPI < -1.5
    - AI: Fire risk model > 75%, Vegetation dryness > 60%
    """

    @classmethod
    def evaluate(cls, iot: Dict[str, Any], sat: Dict[str, Any], wx: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        temp = float(iot.get("temperature", 0.0))
        surface_temp = float(iot.get("surface_temperature", temp))
        smoke = float(iot.get("smoke_co2", iot.get("mq2_gas", 0.0)))
        humidity = float(iot.get("humidity", wx.get("humidity", 50.0)))

        thermal_anomaly = float(sat.get("thermal_anomaly_c", 0.0))
        firms_fire = bool(sat.get("firms_active_fire", False))
        nbr = float(sat.get("nbr", 0.5))
        aod = float(sat.get("aod", 0.1))

        wx_temp = float(wx.get("temperature", temp))
        wx_humidity = float(wx.get("humidity", humidity))
        wx_wind = float(wx.get("wind_speed", 0.0))
        wx_spi = float(wx.get("spi", 0.0))

        fire_risk = float(ai.get("fire_risk", 0.0))
        veg_dryness = float(ai.get("vegetation_dryness", 0.0))

        triggered_params = []
        confirmations = 0

        # IoT Confirmation
        iot_score = 0.0
        if temp > 60.0 or surface_temp > 100.0:
            triggered_params.append("high_ambient_surface_temp (>60°C)")
        if smoke > 500.0:
            triggered_params.append("smoke_co2_spike (>500ppm)")
        if humidity < 20.0:
            triggered_params.append("dry_relative_humidity (<20%)")

        if (temp > 60.0 and smoke > 500.0) or (surface_temp > 100.0 and smoke > 300.0):
            confirmations += 1
            iot_score = 0.95
        elif temp > 45.0 or smoke > 400.0:
            iot_score = 0.50

        # Satellite Confirmation
        sat_score = 0.0
        if thermal_anomaly > 50.0:
            triggered_params.append("satellite_thermal_hotspot (>50°C delta)")
        if firms_fire:
            triggered_params.append("firms_active_fire_pixel_detected")
        if nbr < 0.1:
            triggered_params.append("normalized_burn_ratio_critical (<0.1)")

        if (thermal_anomaly > 50.0 and firms_fire) or (firms_fire and nbr < 0.1):
            confirmations += 1
            sat_score = 0.90
        elif thermal_anomaly > 30.0 or firms_fire:
            sat_score = 0.55

        # AI ML Model Confirmation
        ai_score = 0.0
        if fire_risk > 75.0:
            triggered_params.append("ai_fire_risk_model (>75%)")
        if veg_dryness > 60.0:
            triggered_params.append("vegetation_dryness_index (>60%)")

        if (fire_risk > 75.0 and wx_humidity < 25.0 and wx_wind > 30.0) or (fire_risk > 80.0):
            confirmations += 1
            ai_score = 0.85
        elif fire_risk > 60.0:
            ai_score = 0.50

        # Weighted Ensemble: 40% IoT + 35% Satellite + 25% AI
        confidence = (0.40 * iot_score) + (0.35 * sat_score) + (0.25 * ai_score)
        confidence_percent = round(confidence * 100.0, 1)

        # Trigger Condition Rules
        rule1 = (temp > 60.0 and smoke > 500.0)
        rule2 = (thermal_anomaly > 50.0 and firms_fire)
        rule3 = (fire_risk > 75.0 and wx_humidity < 25.0 and wx_wind > 30.0)

        is_detected = False
        severity = "NONE"

        if (rule1 or rule2 or rule3) and confirmations >= 2:
            is_detected = True
            severity = "CRITICAL" if (temp > 90.0 or wx_wind > 45.0) else "HIGH"
        elif (rule1 or rule2 or rule3) or confidence_percent > 65.0:
            is_detected = True
            severity = "MEDIUM"

        return {
            "disaster_type": "FIRE",
            "is_detected": is_detected,
            "severity": severity,
            "confidence": confidence_percent,
            "confirmations": confirmations,
            "triggered_parameters": triggered_params,
            "recommended_actions": [
                "Deploy fire tenders and chemical suppression trucks",
                "Evacuate residents upwind of fire plume",
                "Create firebreaks and isolate gas/power lines",
                "Issue toxic smoke health advisory and N95 mask distribution"
            ]
        }


class EarthquakeParams(DisasterParams):
    """
    Earthquake Detection Parameters:
    - IoT: Accelerometer PGA > 0.1g, Vibration 1-10 Hz, Tilt shift > 5°, Structural stress > 80%
    - Satellite: InSAR ground displacement > 10cm, Collapsed structures, Road blockage > 30%
    - AI: Richter Magnitude > 5.0, Aftershock prob > 60%, Tsunami risk (Mag > 7.0 + Coastal + Depth < 30km)
    """

    @classmethod
    def evaluate(cls, iot: Dict[str, Any], sat: Dict[str, Any], wx: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        pga = float(iot.get("pga_seismic_g", iot.get("vibration", 0.0) / 100.0))
        tilt = float(iot.get("tilt_shift_deg", iot.get("tilt", 0.0)))
        stress = float(iot.get("structural_stress_percent", 0.0))

        insar_disp = float(sat.get("insar_displacement_cm", 0.0))
        building_damage = bool(sat.get("building_collapse_detected", False))
        road_block = float(sat.get("road_blockage_percent", 0.0))

        magnitude = float(ai.get("richter_magnitude", 0.0))
        aftershock_prob = float(ai.get("aftershock_probability", 0.0))
        is_coastal = bool(ai.get("coastal_location", False))
        depth_km = float(ai.get("focal_depth_km", 20.0))

        triggered_params = []
        confirmations = 0

        # IoT Confirmation
        iot_score = 0.0
        if pga > 0.1:
            triggered_params.append(f"peak_ground_acceleration (PGA {pga:.2f}g > 0.1g)")
        if tilt > 5.0:
            triggered_params.append("sudden_structural_tilt (>5°)")
        if stress > 80.0:
            triggered_params.append("structural_capacity_stress (>80%)")

        if (pga > 0.1 and magnitude > 5.0) or (pga > 0.2) or (tilt > 5.0 and pga > 0.08):
            confirmations += 1
            iot_score = 0.95
        elif pga > 0.05 or tilt > 3.0:
            iot_score = 0.50

        # Satellite Confirmation
        sat_score = 0.0
        if insar_disp > 10.0:
            triggered_params.append(f"insar_surface_displacement ({insar_disp:.1f}cm > 10cm)")
        if building_damage:
            triggered_params.append("structural_collapse_detected_satellite")
        if road_block > 30.0:
            triggered_params.append("transportation_network_blockage (>30%)")

        if (insar_disp > 10.0 and building_damage) or (insar_disp > 15.0):
            confirmations += 1
            sat_score = 0.92
        elif insar_disp > 5.0 or building_damage:
            sat_score = 0.55

        # AI ML Model Confirmation
        ai_score = 0.0
        if magnitude > 5.0:
            triggered_params.append(f"seismic_magnitude_model (M{magnitude:.1f} > 5.0)")
        if aftershock_prob > 60.0:
            triggered_params.append("aftershock_risk_high (>60%)")
        if magnitude > 7.0 and is_coastal and depth_km < 30.0:
            triggered_params.append("tsunami_hazard_trigger (M>7.0 coastal shallow)")

        if (magnitude > 5.0) or (magnitude > 7.0 and is_coastal):
            confirmations += 1
            ai_score = 0.90

        # Weighted Ensemble: 40% IoT + 35% Satellite + 25% AI
        confidence = (0.40 * iot_score) + (0.35 * sat_score) + (0.25 * ai_score)
        confidence_percent = round(confidence * 100.0, 1)

        # Trigger Condition Rules
        rule1 = (pga > 0.1 and magnitude > 5.0)
        rule2 = (insar_disp > 10.0 and building_damage)
        rule3 = (magnitude > 7.0 and is_coastal)

        is_detected = False
        severity = "NONE"

        if (rule1 or rule2 or rule3) and confirmations >= 2:
            is_detected = True
            severity = "CRITICAL"
        elif (rule1 or rule2 or rule3) or confidence_percent > 65.0:
            is_detected = True
            severity = "HIGH"

        return {
            "disaster_type": "EARTHQUAKE",
            "is_detected": is_detected,
            "severity": severity,
            "confidence": confidence_percent,
            "confirmations": confirmations,
            "triggered_parameters": triggered_params,
            "recommended_actions": [
                "Deploy USAR (Urban Search & Rescue) heavy collapse teams",
                "Shut down gas lines and electrical substations to prevent fire",
                "Establish field trauma medical centers outside hazardous structure zones",
                "Issue Tsunami warning and coastal evacuation if M > 7.0"
            ]
        }


class CycloneParams(DisasterParams):
    """
    Cyclone Detection Parameters:
    - IoT: Wind speed > 100 km/hr, Barometric pressure < 980 hPa, 24h Rain > 200mm, Wave height > 4m
    - Satellite: Cyclone eye pattern, Cloud top temp < -70°C, Storm surge > 2m
    - Weather: SST > 28°C, Wind shear < 10 m/s, Ocean heat > 50 kJ/cm²
    - AI: Cyclone landfall prob > 70%, Storm surge > 3m
    """

    @classmethod
    def evaluate(cls, iot: Dict[str, Any], sat: Dict[str, Any], wx: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        wind = float(iot.get("wind_speed", wx.get("wind_speed", 0.0)))
        pressure = float(iot.get("barometric_pressure", wx.get("pressure", 1013.25)))
        rain_24h = float(iot.get("rain_24h", wx.get("rain_24h", 0.0)))
        wave_height = float(iot.get("wave_height_m", 0.0))

        cyclone_eye = bool(sat.get("cyclone_eye_detected", False))
        cloud_top_temp = float(sat.get("cloud_top_temp_c", 0.0))
        storm_surge = float(sat.get("storm_surge_m", ai.get("storm_surge_m", 0.0)))

        sst = float(wx.get("sea_surface_temp_c", 29.0))
        wind_shear = float(wx.get("vertical_wind_shear", 8.0))

        landfall_prob = float(ai.get("landfall_probability", 0.0))
        is_coastal = bool(ai.get("coastal_location", True))

        triggered_params = []
        confirmations = 0

        # IoT Confirmation
        iot_score = 0.0
        if wind > 100.0:
            triggered_params.append(f"severe_gale_force_wind ({wind:.1f}km/h > 100km/h)")
        if pressure < 980.0:
            triggered_params.append(f"barometric_pressure_drop ({pressure:.1f}hPa < 980hPa)")
        if rain_24h > 200.0:
            triggered_params.append("torrential_24h_rainfall (>200mm)")
        if wave_height > 4.0:
            triggered_params.append("coastal_high_wave_height (>4m)")

        if (wind > 100.0 and pressure < 980.0) or (wind > 120.0):
            confirmations += 1
            iot_score = 0.95
        elif wind > 75.0 or pressure < 995.0:
            iot_score = 0.55

        # Satellite Confirmation
        sat_score = 0.0
        if cyclone_eye:
            triggered_params.append("cyclone_eye_circular_pattern_sat")
        if cloud_top_temp < -70.0:
            triggered_params.append("deep_convective_cloud_temp (<-70°C)")
        if storm_surge > 2.0:
            triggered_params.append(f"storm_surge_inundation ({storm_surge:.1f}m > 2m)")

        if (cyclone_eye and landfall_prob > 70.0) or (cyclone_eye and cloud_top_temp < -70.0):
            confirmations += 1
            sat_score = 0.92
        elif cyclone_eye or cloud_top_temp < -60.0:
            sat_score = 0.55

        # AI ML Model Confirmation
        ai_score = 0.0
        if landfall_prob > 70.0:
            triggered_params.append(f"cyclone_landfall_model ({landfall_prob:.1f}% > 70%)")
        if storm_surge > 3.0 and is_coastal:
            triggered_params.append(f"catastrophic_storm_surge ({storm_surge:.1f}m > 3m)")

        if (landfall_prob > 70.0) or (storm_surge > 3.0 and is_coastal):
            confirmations += 1
            ai_score = 0.90

        # Weighted Ensemble: 40% IoT + 35% Satellite + 25% AI
        confidence = (0.40 * iot_score) + (0.35 * sat_score) + (0.25 * ai_score)
        confidence_percent = round(confidence * 100.0, 1)

        # Trigger Condition Rules
        rule1 = (wind > 100.0 and pressure < 980.0)
        rule2 = (cyclone_eye and landfall_prob > 70.0)
        rule3 = (storm_surge > 3.0 and is_coastal)

        is_detected = False
        severity = "NONE"

        if (rule1 or rule2 or rule3) and confirmations >= 2:
            is_detected = True
            severity = "CRITICAL"
        elif (rule1 or rule2 or rule3) or confidence_percent > 65.0:
            is_detected = True
            severity = "HIGH"

        return {
            "disaster_type": "CYCLONE",
            "is_detected": is_detected,
            "severity": severity,
            "confidence": confidence_percent,
            "confirmations": confirmations,
            "triggered_parameters": triggered_params,
            "recommended_actions": [
                "Issue immediate red alert evacuation for coastal belt within 20km",
                "Position storm-surge marine rescue and amphibious vehicles",
                "Reinforce power grid and secure port/harbor infrastructure",
                "Stock emergency shelters with 72-hour dry rations and medical supplies"
            ]
        }


class DroughtParams(DisasterParams):
    """
    Drought Detection Parameters:
    - IoT: Soil moisture < 15%, Groundwater depth > 50m, Reservoir level < 20%, Stream flow < 30%
    - Satellite: NDVI < 0.2, LST > 45°C, TCI < 30, VCI < 25, GRACE depletion > 30%
    - Weather: Precipitation deficit < 50%, SPI < -2.0, Dry days > 60
    - AI: Drought model > 80%, Crop reduction > 40%
    """

    @classmethod
    def evaluate(cls, iot: Dict[str, Any], sat: Dict[str, Any], wx: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        soil_moisture = float(iot.get("soil_moisture", 50.0))
        groundwater_depth = float(iot.get("groundwater_depth_m", 15.0))
        reservoir_pct = float(iot.get("reservoir_capacity_percent", 60.0))

        ndvi = float(sat.get("ndvi", 0.5))
        lst = float(sat.get("lst_c", 30.0))
        tci = float(sat.get("tci", 50.0))
        vci = float(sat.get("vci", 50.0))
        grace_depletion = float(sat.get("grace_depletion_percent", 0.0))

        spi = float(wx.get("spi", 0.0))
        dry_days = int(wx.get("consecutive_dry_days", 0))

        drought_prob = float(ai.get("drought_probability", 0.0))

        triggered_params = []
        confirmations = 0

        # IoT Confirmation
        iot_score = 0.0
        if soil_moisture < 15.0:
            triggered_params.append("severe_soil_moisture_depletion (<15%)")
        if groundwater_depth > 50.0:
            triggered_params.append("deep_groundwater_table_drop (>50m)")
        if reservoir_pct < 20.0:
            triggered_params.append("critical_reservoir_depletion (<20%)")

        if (soil_moisture < 15.0 and spi < -2.0) or (groundwater_depth > 50.0 and reservoir_pct < 20.0):
            confirmations += 1
            iot_score = 0.90
        elif soil_moisture < 25.0 or reservoir_pct < 35.0:
            iot_score = 0.50

        # Satellite Confirmation
        sat_score = 0.0
        if ndvi < 0.2:
            triggered_params.append("vegetation_stress_ndvi (<0.2)")
        if lst > 45.0:
            triggered_params.append("land_surface_heat_stress (>45°C)")
        if tci < 30.0:
            triggered_params.append("temperature_condition_index_critical (<30)")

        if (ndvi < 0.2 and lst > 45.0) or (vci < 25.0 and grace_depletion > 30.0):
            confirmations += 1
            sat_score = 0.88
        elif ndvi < 0.3 or lst > 40.0:
            sat_score = 0.50

        # AI ML Model Confirmation
        ai_score = 0.0
        if drought_prob > 80.0:
            triggered_params.append("ai_drought_severity_model (>80%)")
        if dry_days > 60:
            triggered_params.append(f"prolonged_dry_spells ({dry_days} days > 60)")

        if (drought_prob > 80.0 and dry_days > 60) or (drought_prob > 85.0):
            confirmations += 1
            ai_score = 0.85
        elif drought_prob > 60.0:
            ai_score = 0.50

        # Weighted Ensemble: 40% IoT + 35% Satellite + 25% AI
        confidence = (0.40 * iot_score) + (0.35 * sat_score) + (0.25 * ai_score)
        confidence_percent = round(confidence * 100.0, 1)

        # Trigger Condition Rules
        rule1 = (soil_moisture < 15.0 and spi < -2.0 and ndvi < 0.2)
        rule2 = (groundwater_depth > 50.0 and reservoir_pct < 20.0)
        rule3 = (drought_prob > 80.0 and dry_days > 60)

        is_detected = False
        severity = "NONE"

        if (rule1 or rule2 or rule3) and confirmations >= 2:
            is_detected = True
            severity = "HIGH" if (groundwater_depth > 60.0 or dry_days > 90) else "MEDIUM"
        elif (rule1 or rule2 or rule3) or confidence_percent > 65.0:
            is_detected = True
            severity = "MEDIUM"

        return {
            "disaster_type": "DROUGHT",
            "is_detected": is_detected,
            "severity": severity,
            "confidence": confidence_percent,
            "confirmations": confirmations,
            "triggered_parameters": triggered_params,
            "recommended_actions": [
                "Implement agricultural water rationing and tanker supply",
                "Deploy drought-relief fodder and cattle camps",
                "Initiate emergency groundwater recharge protocols",
                "Distribute drought financial aid and crop insurance support"
            ]
        }


class LandslideParams(DisasterParams):
    """
    Landslide Detection Parameters:
    - IoT: Tilt > 10°, Soil moisture > 90%, Strain > 5cm, Piezometer pore pressure > threshold
    - Satellite: Slope > 30°, Vegetation loss, InSAR displacement > 15cm
    - Weather: 24h Rain > 150mm, 48h Rain > 200mm, 7-day Antecedent Rain > 300mm
    - AI: Landslide prob > 75%, Slope stability index < 0.8
    """

    @classmethod
    def evaluate(cls, iot: Dict[str, Any], sat: Dict[str, Any], wx: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        tilt = float(iot.get("tilt", iot.get("tilt_shift_deg", 0.0)))
        soil_moisture = float(iot.get("soil_moisture", 50.0))
        strain_cm = float(iot.get("strain_cm", iot.get("vibration", 0.0) / 20.0))

        slope_deg = float(sat.get("slope_deg", 35.0))
        insar_disp = float(sat.get("insar_displacement_cm", 0.0))

        rain_24h = float(wx.get("rain_24h", iot.get("rainfall", 0.0)))
        antecedent_rain_7d = float(wx.get("antecedent_rain_7d", rain_24h * 2.5))

        landslide_prob = float(ai.get("landslide_probability", 0.0))
        slope_stability = float(ai.get("slope_stability_index", 1.0))

        triggered_params = []
        confirmations = 0

        # IoT Confirmation
        iot_score = 0.0
        if tilt > 10.0:
            triggered_params.append(f"slope_tilt_displacement ({tilt:.1f}° > 10°)")
        if soil_moisture > 90.0:
            triggered_params.append("soil_pore_saturation (>90%)")
        if strain_cm > 5.0:
            triggered_params.append("ground_movement_strain (>5cm)")

        if (tilt > 10.0 and soil_moisture > 90.0 and rain_24h > 150.0) or (tilt > 15.0):
            confirmations += 1
            iot_score = 0.95
        elif tilt > 5.0 or soil_moisture > 80.0:
            iot_score = 0.50

        # Satellite Confirmation
        sat_score = 0.0
        if insar_disp > 15.0:
            triggered_params.append(f"insar_slope_displacement ({insar_disp:.1f}cm > 15cm)")
        if slope_deg > 30.0:
            triggered_params.append(f"high_inclination_slope ({slope_deg:.0f}° > 30°)")

        if (insar_disp > 15.0 and slope_deg > 30.0) or (insar_disp > 20.0):
            confirmations += 1
            sat_score = 0.90
        elif insar_disp > 8.0:
            sat_score = 0.55

        # AI ML Model Confirmation
        ai_score = 0.0
        if landslide_prob > 75.0:
            triggered_params.append(f"ai_landslide_model ({landslide_prob:.1f}% > 75%)")
        if antecedent_rain_7d > 300.0:
            triggered_params.append(f"antecedent_7d_rainfall ({antecedent_rain_7d:.0f}mm > 300mm)")
        if slope_stability < 0.8:
            triggered_params.append("unstable_slope_index (<0.8)")

        if (landslide_prob > 75.0 and antecedent_rain_7d > 300.0) or (landslide_prob > 85.0):
            confirmations += 1
            ai_score = 0.88
        elif landslide_prob > 60.0:
            ai_score = 0.50

        # Weighted Ensemble: 40% IoT + 35% Satellite + 25% AI
        confidence = (0.40 * iot_score) + (0.35 * sat_score) + (0.25 * ai_score)
        confidence_percent = round(confidence * 100.0, 1)

        # Trigger Condition Rules
        rule1 = (tilt > 10.0 and soil_moisture > 90.0 and rain_24h > 150.0)
        rule2 = (insar_disp > 15.0 and slope_deg > 30.0)
        rule3 = (landslide_prob > 75.0 and antecedent_rain_7d > 300.0)

        is_detected = False
        severity = "NONE"

        if (rule1 or rule2 or rule3) and confirmations >= 2:
            is_detected = True
            severity = "CRITICAL" if (tilt > 18.0 or insar_disp > 25.0) else "HIGH"
        elif (rule1 or rule2 or rule3) or confidence_percent > 65.0:
            is_detected = True
            severity = "MEDIUM"

        return {
            "disaster_type": "LANDSLIDE",
            "is_detected": is_detected,
            "severity": severity,
            "confidence": confidence_percent,
            "confirmations": confirmations,
            "triggered_parameters": triggered_params,
            "recommended_actions": [
                "Evacuate slope-adjacent habitations immediately",
                "Deploy heavy debris-clearing equipment and earthmovers",
                "Block landslide-prone mountain highway passes",
                "Monitor slope pore-water pressure and drainage channels"
            ]
        }


class MultiParameterFusionEngine:
    """
    Core Multi-Fusion Engine evaluating all 6 disaster parameters simultaneously.
    Provides conflict resolution, false-positive suppression, and confidence scoring.
    """

    DISASTER_EVALUATORS = [
        FloodParams,
        FireParams,
        EarthquakeParams,
        CycloneParams,
        DroughtParams,
        LandslideParams
    ]

    SEVERITY_WEIGHTS = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
        "NONE": 0
    }

    @classmethod
    def analyze_all_disasters(cls, iot_data: Dict[str, Any], sat_data: Dict[str, Any], wx_data: Dict[str, Any], ai_data: Dict[str, Any]) -> Dict[str, Any]:
        evaluations = []

        for evaluator in cls.DISASTER_EVALUATORS:
            res = evaluator.evaluate(iot_data, sat_data, wx_data, ai_data)
            if res["is_detected"]:
                evaluations.append(res)

        # Sort detected disasters by severity rank and confidence
        evaluations.sort(
            key=lambda x: (cls.SEVERITY_WEIGHTS.get(x["severity"], 0), x["confidence"]),
            reverse=True
        )

        if evaluations:
            primary_disaster = evaluations[0]
        else:
            primary_disaster = {
                "disaster_type": "NONE",
                "is_detected": False,
                "severity": "NORMAL",
                "confidence": 98.0,
                "confirmations": 0,
                "triggered_parameters": ["All sensors within normal threshold parameters"],
                "recommended_actions": ["Maintain active surveillance and IoT telemetry polling"]
            }

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "primary_disaster": primary_disaster,
            "all_detected_disasters": evaluations,
            "total_detected": len(evaluations),
            "false_positive_suppression_active": True,
            "ensemble_weights": {
                "iot_sensors": 0.40,
                "satellite_remote_sensing": 0.35,
                "ai_prediction_model": 0.25
            }
        }
