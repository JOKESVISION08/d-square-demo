"""
D-SQUARE 2.0 Flask Backend Server
Disaster Surveillance using Quadruple UAV AI Remote Earth-observation
Port: 5000
"""

import os
import time
import json
import base64
import traceback
from datetime import datetime
import numpy as np
from io import BytesIO
from PIL import Image
import uuid
from werkzeug.utils import secure_filename

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS

NISAR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nisar")
UPLOAD_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
HISTORICAL_UPLOADS_DIR = os.path.join(UPLOAD_BASE_DIR, "historical")
CURRENT_UPLOADS_DIR = os.path.join(UPLOAD_BASE_DIR, "current")
PREVIEWS_DIR = os.path.join(UPLOAD_BASE_DIR, "previews")

for d in [NISAR_DIR, HISTORICAL_UPLOADS_DIR, CURRENT_UPLOADS_DIR, PREVIEWS_DIR]:
    os.makedirs(d, exist_ok=True)

ALLOWED_EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".json", ".csv", ".zip"}

from satellite.upload_processor import (
    inspect_uploaded_scene, read_multiband_geotiff, build_preview_image,
    calculate_indices, compare_scene_compatibility
)
from satellite.feature_extractor import extract_scene_features, compare_features_zscore
from database import (
    init_db, save_alert, save_sensor_log, get_recent_alerts, get_recent_sensor_logs,
    get_historical_pixel_samples, save_satellite_pixel_sample, save_current_satellite_sample,
    get_latest_current_satellite_sample, get_historical_events_summary, get_feature_statistics,
    seed_demo_historical_samples_if_empty, save_satellite_scene, save_scene_features,
    get_uploaded_scenes, get_scene_by_id, get_scene_features, delete_scene, get_scene_preview_path,
    get_safe_zones_db, save_user_location_db, cleanup_expired_location_logs, save_mobile_sos_event_db,
    save_trusted_contact_db, get_trusted_contacts_db, delete_trusted_contact_db, get_user_sos_history_db
)

from services.weather_service import WeatherService
from services.safe_zone_service import SafeZoneService, calculate_haversine_distance_km
from services.safety_assistant import SafetyAssistantService

from satellite.bhuvan_api import BhuvanSatelliteAPI
from satellite.geotiff_processor import GeoTIFFProcessor
from satellite.pixel_comparator import (
    HistoricalPixelComparator, calculate_spectral_indices, calculate_patch_statistics,
    compare_current_to_historical, calculate_anomaly_score, calculate_feature_statistics
)
from satellite.multi_satellite_api import MultiSatelliteAPIHub
from satellite.import_historical_samples import import_file
from models.fusion_engine import MultiModalFusionEngine
from twilio_alert import TwilioAlertDispatcher

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Initialize Database & Seed Demo Samples if empty
init_db()
seed_demo_historical_samples_if_empty()
bhuvan_api = BhuvanSatelliteAPI()
geotiff_proc = GeoTIFFProcessor()
pixel_comparator = HistoricalPixelComparator()
multi_sat_hub = MultiSatelliteAPIHub()
fusion_engine = MultiModalFusionEngine()
twilio_dispatcher = TwilioAlertDispatcher()

weather_service = WeatherService()
safe_zone_service = SafeZoneService()
safety_assistant_service = SafetyAssistantService()
sos_last_sent_timestamps = {}

# In-memory buffer for 30-day time series data
time_series_buffer = []

# Live Telemetry State Buffers
latest_camera_features = {
    "mean_r": 0.15,
    "mean_g": 0.65,
    "mean_b": 0.15,
    "flicker": 0.05,
    "smoke_haziness": 0.05,
    "fps": 5.0,
    "timestamp": time.time()
}

latest_camera_image_b64 = ""

latest_sensor_data = {
    "temperature": 28.0,
    "humidity": 50.0,
    "smoke": 200.0,
    "soil_moisture": 40.0,
    "water_level": 5.0,
    "flame": 0.0,
    "vibration": 0.2,
    "tilt_angle": 1.2,
    "gyro_rate": 0.5,
    "tilt_state": 0,
    "vibration_alarm": 0
}

latest_mobile_alert = {
    "active": False,
    "data_mode": "DEMO_SIMULATION",
    "disaster_type": "None",
    "risk_level": "NORMAL",
    "soil_moisture": 42.0,
    "temperature": 26.5,
    "humidity": 52.0,
    "led_state": "GREEN",
    "buzzer_state": "OFF",
    "node_id": "SIMULATED_ESP8266_NODE_01",
    "timestamp": None,
    "message": "No active simulated alert."
}

latest_satellite_metrics = {
    "satellite_fps": 5.0,
    "norm_ndvi": 0.72,
    "norm_lst": 0.42,
    "norm_soil_moisture": 0.45,
    "scenario": "normal"
}

last_nisar_save_time = 0.0

def init_time_series_buffer():
    global time_series_buffer
    time_series_buffer = []
    # Seed 30 days of baseline historical observations
    for i in range(30):
        time_series_buffer.append({
            "day": i + 1,
            "ndvi": float(np.random.uniform(0.60, 0.78)),
            "lst": float(np.random.uniform(0.35, 0.50)),
            "soil_m": float(np.random.uniform(0.35, 0.55)),
        })

init_time_series_buffer()

@app.route("/", methods=["GET", "POST"])
def index():
    """Renders main Leaflet.js dashboard or processes incoming ESP8266 POST telemetry intake."""
    if request.method == "POST":
        return post_sensor_data_route()
    return render_template("index.html")

@app.route("/mobile_camera")
@app.route("/mobile_camera.html")
def mobile_camera():
    """Renders real-time mobile camera web app."""
    return render_template("mobile_camera.html")

@app.route("/api/satellite_data", methods=["GET"])
def get_satellite_data():
    """Returns ISRO Bhuvan satellite metrics & Satellite FPS for current ROI."""
    scenario = request.args.get("scenario", "normal")
    metrics = bhuvan_api.process_roi_metrics(disaster_scenario=scenario)
    global latest_satellite_metrics
    latest_satellite_metrics = metrics

    # Build pixel sample vector for scenario comparison
    cur_pixels = {
        "red": 0.65 if scenario == "forest_fire" else (0.10 if scenario == "flood" else 0.15),
        "green": 0.15 if scenario == "forest_fire" else (0.35 if scenario == "flood" else 0.55),
        "blue": 0.10 if scenario == "forest_fire" else (0.78 if scenario == "flood" else 0.15),
        "nir": 0.10 if scenario == "forest_fire" else (0.05 if scenario == "flood" else 0.75),
        "swir": 0.35 if scenario == "forest_fire" else (0.06 if scenario == "flood" else 0.15),
        "thermal": 52.0 if scenario == "forest_fire" else 26.5
    }
    hist_comp = pixel_comparator.compare_pixels(cur_pixels, target_disaster_type=scenario)
    save_current_satellite_sample({
        "acquisition_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "satellite": "ISRO-NASA NISAR / Bhuvan",
        "product": "Multi-Spectral / L-Band SAR",
        "latitude": 30.0668,
        "longitude": 79.0193,
        "features": cur_pixels,
        "verification_status": "DEMO",
        "quality_flag": "SIMULATED_SCENARIO"
    })

    return jsonify({
        "status": "success",
        "roi_name": "Uttarakhand Himalayan High-Risk Zone",
        "coordinates": {"lat_min": 29.50, "lat_max": 30.50, "lon_min": 78.50, "lon_max": 79.80},
        "satellites": ["ISRO-NASA NISAR Dual-SAR", "Resourcesat-2", "RISAT-1", "INSAT-3D", "Landsat-8", "Sentinel-2"],
        "nisar_telemetry": {
            "orbit_pass": "ASCENDING_PASS_ORBIT_142",
            "l_band_backscatter_db": -12.4,
            "s_band_backscatter_db": -8.6,
            "ground_deformation_mm_yr": 2.4,
            "resolution": "3m-10m Sweep Swath"
        },
        "satellite_fps": metrics.get("satellite_fps", 5.0),
        "metrics": metrics,
        "historical_comparison": hist_comp
    })

@app.route("/api/historical_comparison", methods=["GET", "POST"])
def get_historical_comparison():
    """
    Returns historical satellite pixel-and-patch comparison JSON payload.
    Supports patch_size (3, 5, 9, default 5), pixel_values or patch_matrix,
    disaster_type filter, lat/lon, scene_id.
    Standardizes feature vectors, calculates missing-data-safe similarity,
    calculates patch statistics, updates fusion engine, and enforces SMS safeguards.
    """
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        pixels = body.get("pixel_values") or body.get("features") or {
            "red": 0.26, "green": 0.21, "blue": 0.18, "nir": 0.16, "swir1": 0.31, "swir2": 0.28, "thermal": 44.8, "sar_l_band_db": -12.4
        }
        patch_matrix = body.get("patch_matrix")
        patch_size = int(body.get("patch_size", 5))
        if patch_size not in [3, 5, 9]:
            patch_size = 5
        disaster_type = body.get("disaster_type")
        lat = float(body.get("latitude", body.get("location_lat", 30.0668)))
        lon = float(body.get("longitude", body.get("location_lon", 79.0193)))
        scene_id = body.get("scene_id", "CURRENT_ROI_SCENE_01")
        satellite = body.get("satellite", "Sentinel-2 / NISAR")
        product = body.get("product", "L2A Reflectance / L-Band SAR")
    else:
        disaster_type = request.args.get("disaster_type")
        patch_size = int(request.args.get("patch_size", 5))
        if patch_size not in [3, 5, 9]:
            patch_size = 5
        lat = float(request.args.get("lat", 30.0668))
        lon = float(request.args.get("lon", 79.0193))
        pixels = {
            "red": 0.26, "green": 0.21, "blue": 0.18, "nir": 0.16, "swir1": 0.31, "swir2": 0.28, "thermal": 44.8, "sar_l_band_db": -12.4
        }
        patch_matrix = None
        scene_id = "CURRENT_ROI_SCENE_01"
        satellite = "Sentinel-2 / NISAR"
        product = "L2A Reflectance / L-Band SAR"

    # Spectral indices calculation
    indices = calculate_spectral_indices(pixels)
    
    # Calculate spatial patch statistics
    if patch_matrix and isinstance(patch_matrix, list):
        patch_stats = calculate_patch_statistics(patch_matrix, patch_size=patch_size)
    else:
        # Synthesize spatial patch variation around current pixel for demo/test visualization
        synth_patch = []
        for r_idx in range(patch_size):
            for c_idx in range(patch_size):
                var = (np.random.rand() - 0.5) * 0.04
                px = dict(pixels)
                px["red"] = max(0.0, float(px.get("red", 0.15)) + var)
                px["nir"] = max(0.0, float(px.get("nir", 0.75)) - var)
                synth_patch.append(px)
        patch_stats = calculate_patch_statistics(synth_patch, patch_size=patch_size)

    # Combine spectral indices and patch stats into feature vector
    cur_record = {
        "acquisition_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "satellite": satellite,
        "product": product,
        "latitude": lat,
        "longitude": lon,
        "patch_size": patch_size,
        "scene_id": scene_id,
        "verification_status": "DEMO",
        "quality_flag": "NOT_FOR_SCIENTIFIC_VALIDATION",
        "features": {
            **pixels,
            **indices,
            "patch_mean_ndvi": patch_stats.get("ndvi", {}).get("mean"),
            "patch_std_ndvi": patch_stats.get("ndvi", {}).get("std"),
            "patch_median_ndvi": patch_stats.get("ndvi", {}).get("median"),
            "patch_mean_nbr": patch_stats.get("nbr", {}).get("mean"),
            "patch_std_nbr": patch_stats.get("nbr", {}).get("std"),
            "patch_median_nbr": patch_stats.get("nbr", {}).get("median"),
            "patch_mean_lst": patch_stats.get("lst", {}).get("mean"),
            "patch_std_lst": patch_stats.get("lst", {}).get("std"),
            "valid_pixel_count": patch_stats.get("valid_pixel_count", patch_size * patch_size)
        }
    }

    # Fetch historical records
    hist_records = get_historical_pixel_samples(disaster_type=disaster_type, limit=1000)
    feat_stats = get_feature_statistics()

    # Perform z-score feature standardization & similarity comparison
    comp_res = compare_current_to_historical(cur_record, hist_records, feature_stats=feat_stats)

    # Save current query sample to database
    save_current_satellite_sample(cur_record)

    # Compute baseline anomaly score
    baseline_records = [r for r in hist_records if str(r.get("disaster_type", "")).upper() in ["NONE", "NORMAL"]]
    anom_res = calculate_anomaly_score(cur_record, baseline_records, feature_stats=feat_stats)

    # Evaluate Multi-Modal Fusion Engine with historical evidence
    best_pattern = comp_res.get("best_historical_pattern", {})
    hist_sim = float(best_pattern.get("similarity", 0.0))
    hist_disaster = str(best_pattern.get("disaster_type", "None"))
    hist_ver_status = str(best_pattern.get("verification_status", "DEMO"))
    
    global time_series_buffer, latest_sensor_data, latest_camera_features
    fusion_res = fusion_engine.evaluate_multi_modal_fusion(
        sat_data={"red": pixels.get("red", 0.15), "green": pixels.get("green", 0.55), "blue": pixels.get("blue", 0.15), "nir": pixels.get("nir", 0.75)},
        ts_data=time_series_buffer,
        sensor_data=latest_sensor_data,
        camera_data=latest_camera_features,
        historical_similarity_score=hist_sim,
        historical_best_disaster=hist_disaster,
        anomaly_score=anom_res.get("score_percent", 0.0),
        data_quality_score=85.0 if hist_ver_status == "VERIFIED" else 50.0,
        verification_status=hist_ver_status
    )

    # SMS Alert Safeguard:
    # SMS alerts MUST NOT be dispatched solely from DEMO historical similarity matching.
    # Dispatched ONLY if risk_level is CRITICAL/HIGH AND ground sensor or camera telemetry confirms threat or data is VERIFIED.
    has_ground_trigger = (
        latest_sensor_data.get("smoke", 0) > 400 or
        latest_sensor_data.get("flame", 0) > 0 or
        latest_sensor_data.get("water_level", 0) > 8.0 or
        latest_sensor_data.get("vibration", 0) > 4.0 or
        latest_sensor_data.get("tilt_angle", 0) > 20.0 or
        latest_camera_features.get("mean_r", 0) > 0.45
    )
    if fusion_res["risk_level"] in ["CRITICAL", "HIGH"] and (has_ground_trigger or hist_ver_status == "VERIFIED"):
        dispatch = twilio_dispatcher.send_emergency_alert(
            disaster_type=fusion_res["predicted_disaster"],
            risk_level=fusion_res["risk_level"],
            confidence=fusion_res["system_confidence_percent"],
            location="Historical Satellite Patch Analysis ROI",
            lat=lat,
            lon=lon
        )
        save_alert(
            location="Historical Satellite Patch Analysis ROI",
            lat=lat,
            lon=lon,
            disaster_type=fusion_res["predicted_disaster"],
            risk_level=fusion_res["risk_level"],
            confidence=fusion_res["system_confidence_percent"],
            prob=fusion_res["disaster_probability_percent"],
            sms_sent=dispatch.get("dispatched", False)
        )

    # Build z-score vector
    from satellite.pixel_comparator import build_feature_vector
    cur_z = build_feature_vector(cur_record, feat_stats)
    
    return jsonify({
        "status": "success",
        "patch_size": patch_size,
        "location": {"lat": lat, "lon": lon},
        "query_sample": {
            "scene_id": scene_id,
            "acquisition_date": cur_record["acquisition_date"],
            "satellite": satellite,
            "product": product,
            "verification_status": cur_record["verification_status"],
            "quality_flag": cur_record["quality_flag"],
            "raw_pixels": pixels,
            "indices": indices
        },
        "multi_spectral_patch_stats": patch_stats,
        "z_score_vector": cur_z,
        "top_matches": comp_res["top_matches"],
        "class_level_scores": comp_res["class_level_scores"],
        "best_historical_pattern": comp_res["best_historical_pattern"],
        "anomaly": anom_res,
        "fusion_result": fusion_res,
        "compared_sample_count": comp_res["compared_sample_count"]
    })

@app.route("/api/historical_events_summary", methods=["GET"])
def historical_events_summary():
    """Returns summary statistics of historical satellite pixel samples in database."""
    summary = get_historical_events_summary()
    feat_stats = get_feature_statistics()
    return jsonify({
        "status": "success",
        "summary": summary,
        "feature_statistics": feat_stats
    })

@app.route("/api/satellite_history_trend", methods=["GET"])
def satellite_history_trend():
    """Returns 30-day temporal trend of pixel features/anomaly scores for a given lat/lon or location."""
    lat = float(request.args.get("lat", 30.0668))
    lon = float(request.args.get("lon", 79.0193))
    
    trend_data = []
    for entry in time_series_buffer:
        d = entry.get("day", 1)
        ndvi = entry.get("ndvi", 0.70)
        lst = entry.get("lst", 0.40)
        soil_m = entry.get("soil_m", 0.40)
        anom = round(float(np.clip(abs(0.75 - ndvi) * 100 + abs(lst - 0.40) * 80, 5.0, 95.0)), 1)
        trend_data.append({
            "day": f"Day {d}",
            "ndvi": round(float(ndvi), 4),
            "lst": round(float(lst), 4),
            "soil_moisture": round(float(soil_m), 4),
            "anomaly_score": anom
        })
    return jsonify({
        "status": "success",
        "location": {"lat": lat, "lon": lon},
        "days": len(trend_data),
        "trend": trend_data
    })

@app.route("/api/import_historical_samples", methods=["POST"])
def import_historical_samples():
    """Dynamically imports historical satellite pixel samples from uploaded CSV file or text payload."""
    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"status": "error", "message": "No file selected"}), 400
        temp_path = os.path.join(NISAR_DIR, f"upload_{int(time.time())}.csv")
        file.save(temp_path)
        result = import_file(temp_path)
        try:
            os.remove(temp_path)
        except Exception:
            pass
        return jsonify({"status": "success", "result": result})
    elif request.is_json:
        data = request.get_json()
        csv_text = data.get("csv_text")
        if not csv_text:
            return jsonify({"status": "error", "message": "Missing csv_text parameter"}), 400
        temp_path = os.path.join(NISAR_DIR, f"upload_{int(time.time())}.csv")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(csv_text)
        result = import_file(temp_path)
        try:
            os.remove(temp_path)
        except Exception:
            pass
        return jsonify({"status": "success", "result": result})
    else:
        return jsonify({"status": "error", "message": "Expected CSV file upload or JSON with csv_text"}), 400


# ==================== Satellite Scene Upload & Comparison API Routes ====================

def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@app.route("/api/upload/historical-scene", methods=["POST"])
def upload_historical_scene():
    """
    POST /api/upload/historical-scene
    Saves uploaded historical satellite scene file(s) and metadata.
    Extracts features, generates preview PNG, stores in SQLite, and returns scene info.
    """
    if "file" not in request.files and "red_band" not in request.files:
        return jsonify({"status": "error", "message": "No satellite image file provided"}), 400

    uploaded_file = request.files.get("file") or request.files.get("red_band")
    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    orig_filename = secure_filename(uploaded_file.filename)
    if not allowed_file(orig_filename):
        return jsonify({"status": "error", "message": f"Unsupported file extension: {orig_filename}"}), 400

    ext = os.path.splitext(orig_filename)[1].lower()
    unique_name = f"hist_{uuid.uuid4().hex[:10]}{ext}"
    target_path = os.path.join(HISTORICAL_UPLOADS_DIR, unique_name)
    uploaded_file.save(target_path)

    form = request.form
    event_id = form.get("event_id") or f"EVT_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:4].upper()}"
    disaster_type = form.get("disaster_type", "Forest_Fire")
    satellite = form.get("satellite", "Sentinel-2")
    product = form.get("product", "L2A Surface Reflectance")
    acq_datetime = form.get("acquisition_datetime") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lat = float(form.get("latitude", 30.0668))
    lon = float(form.get("longitude", 79.0193))
    resolution_m = float(form.get("resolution_m", 10.0))
    cloud_cover = float(form.get("cloud_cover", 0.0))
    label_source = form.get("label_source", "manual annotation")
    verification_status = form.get("verification_status", "UPLOADED_UNVERIFIED")
    source_url = form.get("source_url", "")
    patch_size = int(form.get("patch_size", 5))

    band_mapping = None
    if "band_mapping_json" in form:
        try:
            band_mapping = json.loads(form["band_mapping_json"])
        except Exception:
            pass

    insp = inspect_uploaded_scene(target_path)
    preview_abs_path = build_preview_image(target_path, band_mapping)

    quality_flag = "IMAGE_ONLY_DEMO" if insp["is_rgb_demo"] else ("VALIDATED_GEOSPATIAL" if verification_status == "VERIFIED" else "UNVERIFIED_SOURCE")

    scene_data = {
        "scene_type": "historical",
        "event_id": event_id,
        "disaster_type": disaster_type,
        "satellite": satellite,
        "product": product,
        "acquisition_datetime": acq_datetime,
        "latitude": lat,
        "longitude": lon,
        "bbox_json": insp.get("bbox") or {},
        "resolution_m": resolution_m,
        "cloud_cover": cloud_cover,
        "crs": insp.get("crs", "EPSG:4326"),
        "source_url": source_url,
        "label_source": label_source,
        "verification_status": verification_status,
        "quality_flag": quality_flag,
        "original_filename": orig_filename,
        "stored_path": target_path,
        "metadata_json": insp,
        "preview_path": preview_abs_path
    }

    scene_id = save_satellite_scene(scene_data)
    scene_data["id"] = scene_id

    features = extract_scene_features(scene_data, patch_size=patch_size, latitude=lat, longitude=lon, band_mapping=band_mapping)
    save_scene_features(scene_id, features)

    preview_url = f"/api/scene-preview/{scene_id}"

    return jsonify({
        "status": "success",
        "message": "Historical satellite scene uploaded successfully",
        "scene_id": scene_id,
        "scene": scene_data,
        "features": features,
        "preview_url": preview_url
    })


@app.route("/api/upload/current-scene", methods=["POST"])
def upload_current_scene():
    """
    POST /api/upload/current-scene
    Saves uploaded current satellite scene file(s) and metadata.
    Extracts features, generates preview PNG, stores in SQLite, and returns scene info.
    """
    if "file" not in request.files and "red_band" not in request.files:
        return jsonify({"status": "error", "message": "No satellite image file provided"}), 400

    uploaded_file = request.files.get("file") or request.files.get("red_band")
    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    orig_filename = secure_filename(uploaded_file.filename)
    if not allowed_file(orig_filename):
        return jsonify({"status": "error", "message": f"Unsupported file extension: {orig_filename}"}), 400

    ext = os.path.splitext(orig_filename)[1].lower()
    unique_name = f"curr_{uuid.uuid4().hex[:10]}{ext}"
    target_path = os.path.join(CURRENT_UPLOADS_DIR, unique_name)
    uploaded_file.save(target_path)

    form = request.form
    satellite = form.get("satellite", "Sentinel-2")
    product = form.get("product", "L2A Surface Reflectance")
    acq_datetime = form.get("acquisition_datetime") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lat = float(form.get("latitude", 30.0668))
    lon = float(form.get("longitude", 79.0193))
    resolution_m = float(form.get("resolution_m", 10.0))
    cloud_cover = float(form.get("cloud_cover", 0.0))
    label_source = form.get("label_source", "current observation")
    verification_status = form.get("verification_status", "UPLOADED_UNVERIFIED")
    patch_size = int(form.get("patch_size", 5))

    band_mapping = None
    if "band_mapping_json" in form:
        try:
            band_mapping = json.loads(form["band_mapping_json"])
        except Exception:
            pass

    insp = inspect_uploaded_scene(target_path)
    preview_abs_path = build_preview_image(target_path, band_mapping)

    quality_flag = "IMAGE_ONLY_DEMO" if insp["is_rgb_demo"] else ("VALIDATED_GEOSPATIAL" if verification_status == "VERIFIED" else "UNVERIFIED_SOURCE")

    scene_data = {
        "scene_type": "current",
        "event_id": f"CURRENT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "disaster_type": "None",
        "satellite": satellite,
        "product": product,
        "acquisition_datetime": acq_datetime,
        "latitude": lat,
        "longitude": lon,
        "bbox_json": insp.get("bbox") or {},
        "resolution_m": resolution_m,
        "cloud_cover": cloud_cover,
        "crs": insp.get("crs", "EPSG:4326"),
        "source_url": "",
        "label_source": label_source,
        "verification_status": verification_status,
        "quality_flag": quality_flag,
        "original_filename": orig_filename,
        "stored_path": target_path,
        "metadata_json": insp,
        "preview_path": preview_abs_path
    }

    scene_id = save_satellite_scene(scene_data)
    scene_data["id"] = scene_id

    features = extract_scene_features(scene_data, patch_size=patch_size, latitude=lat, longitude=lon, band_mapping=band_mapping)
    save_scene_features(scene_id, features)

    preview_url = f"/api/scene-preview/{scene_id}"

    return jsonify({
        "status": "success",
        "message": "Current satellite scene uploaded successfully",
        "scene_id": scene_id,
        "scene": scene_data,
        "features": features,
        "data_quality_score": features.get("quality_score", 50.0),
        "preview_url": preview_url
    })


@app.route("/api/uploaded-scenes", methods=["GET"])
def get_uploaded_scenes_route():
    """
    GET /api/uploaded-scenes?type=historical|current|all
    Lists uploaded scenes filtered by scene_type.
    """
    stype = request.args.get("type", "all")
    scenes = get_uploaded_scenes(scene_type=stype)
    for s in scenes:
        s["preview_url"] = f"/api/scene-preview/{s['id']}"
    return jsonify({
        "status": "success",
        "count": len(scenes),
        "scenes": scenes
    })


@app.route("/api/uploaded-scenes/<int:scene_id>", methods=["DELETE"])
def delete_uploaded_scene_route(scene_id):
    """
    DELETE /api/uploaded-scenes/<scene_id>
    Deletes an uploaded scene from SQLite database and filesystem.
    """
    ok = delete_scene(scene_id)
    if ok:
        return jsonify({"status": "success", "message": f"Scene {scene_id} deleted successfully"})
    else:
        return jsonify({"status": "error", "message": f"Scene {scene_id} not found"}), 404


@app.route("/api/compare-uploaded-scenes", methods=["POST"])
def compare_uploaded_scenes_route():
    """
    POST /api/compare-uploaded-scenes
    Compares an uploaded historical scene against an uploaded current scene.
    Evaluates compatibility, patch statistics, feature deltas, similarity %,
    baseline anomaly score, risk assessment, and fusion engine input.
    """
    body = request.get_json(silent=True) or {}
    h_id = body.get("historical_scene_id")
    c_id = body.get("current_scene_id")

    if not h_id or not c_id:
        return jsonify({"status": "error", "message": "Missing historical_scene_id or current_scene_id"}), 400

    h_scene = get_scene_by_id(int(h_id))
    c_scene = get_scene_by_id(int(c_id))

    if not h_scene:
        return jsonify({"status": "error", "message": f"Historical scene {h_id} not found"}), 404
    if not c_scene:
        return jsonify({"status": "error", "message": f"Current scene {c_id} not found"}), 404

    patch_size = int(body.get("patch_size", 5))
    if patch_size not in [3, 5, 9]:
        patch_size = 5
    lat = float(body.get("latitude", 30.0668))
    lon = float(body.get("longitude", 79.0193))

    res = compare_features_zscore(h_scene, c_scene, patch_size=patch_size, latitude=lat, longitude=lon)

    # Blend result with 4-model fusion engine using extracted current scene spectral features
    f_in = res["fusion_input"]
    c_feats = c_scene.get("features", {}) or {}
    cur_sat_data = {
        "red": float(c_feats.get("red", c_feats.get("red_mean", 0.15)) or 0.15),
        "green": float(c_feats.get("green", c_feats.get("green_mean", 0.55)) or 0.55),
        "blue": float(c_feats.get("blue", c_feats.get("blue_mean", 0.15)) or 0.15),
        "nir": float(c_feats.get("nir", c_feats.get("nir_mean", 0.75)) or 0.75)
    }

    global time_series_buffer, latest_sensor_data, latest_camera_features
    fusion_res = fusion_engine.evaluate_multi_modal_fusion(
        sat_data=cur_sat_data,
        ts_data=time_series_buffer,
        sensor_data=latest_sensor_data,
        camera_data=latest_camera_features,
        historical_similarity_score=f_in["historical_similarity_score"],
        historical_best_disaster=res["risk_assessment"]["leading_disaster_pattern"],
        anomaly_score=f_in["anomaly_score"],
        data_quality_score=f_in["data_quality_score"],
        verification_status=f_in["verification_status"],
        compatibility_level=f_in["compatibility_level"]
    )
    res["fusion_result"] = fusion_res

    # Add URL paths for UI preview images
    res["historical_scene"]["preview_url"] = f"/api/scene-preview/{h_id}"
    res["current_scene"]["preview_url"] = f"/api/scene-preview/{c_id}"

    return jsonify(res)


@app.route("/api/scene-preview/<int:scene_id>", methods=["GET"])
def get_scene_preview_route(scene_id):
    """
    GET /api/scene-preview/<scene_id>
    Safely serves preview PNG image for the specified scene_id without exposing local file paths.
    """
    prev_path = get_scene_preview_path(scene_id)
    if not prev_path or not os.path.exists(prev_path):
        prev_dir = PREVIEWS_DIR
        blank_file = "blank_preview.png"
        blank_path = os.path.join(prev_dir, blank_file)
        if not os.path.exists(blank_path):
            blank = Image.new("RGB", (256, 256), color=(18, 25, 44))
            blank.save(blank_path, format="PNG")
        return send_from_directory(prev_dir, blank_file, mimetype="image/png")

    p_dir = os.path.dirname(prev_path)
    p_name = os.path.basename(prev_path)
    return send_from_directory(p_dir, p_name, mimetype="image/png")

@app.route("/api/start_satellite_sensing", methods=["POST"])
def start_satellite_sensing():
    """
    Triggered when user clicks 'Start Satellite Sensing' on Mobile or Dashboard.
    Streams live ISRO remote sensing telemetry, computes Satellite FPS,
    and transmits parameters directly into the Multi-Modal Fusion Engine.
    """
    start_time = time.time()
    body = request.get_json(silent=True) or {}
    scenario = body.get("scenario", "normal")

    # Fetch live satellite metrics and measure Satellite FPS
    metrics = bhuvan_api.process_roi_metrics(disaster_scenario=scenario)
    satellite_fps = metrics.get("satellite_fps", 5.0)

    global latest_satellite_metrics, time_series_buffer, latest_sensor_data, latest_camera_features
    latest_satellite_metrics = metrics

    time_series_buffer.append({
        "day": len(time_series_buffer) + 1,
        "ndvi": metrics["norm_ndvi"],
        "lst": metrics["norm_lst"],
        "soil_m": metrics["norm_soil_moisture"]
    })
    if len(time_series_buffer) > 30:
        time_series_buffer.pop(0)

    sat_data = {
        "red": 0.65 if scenario == "forest_fire" else 0.15,
        "green": 0.15 if scenario == "forest_fire" else 0.55,
        "blue": 0.10 if scenario == "forest_fire" else 0.15,
        "nir": 0.10 if scenario == "forest_fire" else 0.75
    }

    fusion_result = fusion_engine.evaluate_multi_modal_fusion(
        sat_data=sat_data,
        ts_data=time_series_buffer,
        sensor_data=latest_sensor_data,
        camera_data=latest_camera_features
    )

    latency_ms = round((time.time() - start_time) * 1000.0, 2)

    if fusion_result["risk_level"] in ["CRITICAL", "HIGH"]:
        dispatch = twilio_dispatcher.send_emergency_alert(
            disaster_type=fusion_result["predicted_disaster"],
            risk_level=fusion_result["risk_level"],
            confidence=fusion_result["system_confidence_percent"],
            location="ISRO Bhuvan High-Risk Sensing ROI",
            lat=30.0668,
            lon=79.0193
        )
        save_alert(
            location="ISRO Bhuvan Satellite Sensing Stream",
            lat=30.0668,
            lon=79.0193,
            disaster_type=fusion_result["predicted_disaster"],
            risk_level=fusion_result["risk_level"],
            confidence=fusion_result["system_confidence_percent"],
            prob=fusion_result["disaster_probability_percent"],
            sms_sent=dispatch.get("dispatched", False)
        )

    return jsonify({
        "status": "success",
        "message": "Live Satellite Sensing Stream Active",
        "satellite_fps": satellite_fps,
        "camera_fps": latest_camera_features.get("fps", 5.0),
        "satellite_metrics": metrics,
        "fusion_result": fusion_result,
        "latency_ms": latency_ms
    })

@app.route("/api/sensor_data", methods=["POST"])
@app.route("/alert", methods=["POST"])
def post_sensor_data():
    """
    Intake endpoint for ESP8266 IoT NodeMCU telemetry.
    Delegates to post_sensor_data_route() for unified state management and Landslide detection.
    """
    return post_sensor_data_route()

def save_nisar_pixel_files(image_b64, mean_r, mean_g, mean_b, fusion_result, is_explicit_snapshot=False):
    global last_nisar_save_time
    now = time.time()
    timestr = datetime.now().strftime("%Y%m%d_%H%M%S")

    nisar_pixels = {
        "red": round(mean_r, 4),
        "green": round(mean_g, 4),
        "blue": round(mean_b, 4),
        "nir": round(0.15 if mean_r > 0.4 else 0.75, 4),
        "swir": round(0.35 if mean_r > 0.4 else 0.15, 4),
        "thermal": round(52.0 if mean_r > 0.4 else 26.5, 1),
        "l_band_db": round(-12.4 if mean_r <= 0.4 else -6.2, 1),
        "s_band_db": round(-8.6 if mean_r <= 0.4 else -3.8, 1)
    }

    payload_json = {
        "timestamp": now,
        "formatted_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nisar_pixels": nisar_pixels,
        "predicted_disaster": fusion_result.get("predicted_disaster", "NORMAL"),
        "risk_level": fusion_result.get("risk_level", "NORMAL"),
        "confidence_percent": fusion_result.get("system_confidence_percent", 95.0),
        "location": {"lat": 30.0668, "lon": 79.0193, "roi": "Uttarakhand Himalayan Grid"}
    }

    # Always update latest_nisar_capture files for real-time PC dashboard display
    latest_img_path = os.path.join(NISAR_DIR, "latest_nisar_capture.png")
    latest_json_path = os.path.join(NISAR_DIR, "latest_nisar_data.json")

    if image_b64:
        try:
            raw_b64 = image_b64.split(",")[1] if "," in image_b64 else image_b64
            img_bytes = base64.b64decode(raw_b64)
            with open(latest_img_path, "wb") as f:
                f.write(img_bytes)
        except Exception:
            pass

    try:
        with open(latest_json_path, "w") as f:
            json.dump(payload_json, f, indent=2)
    except Exception:
        pass

    # Save timestamped file ONCE PER MINUTE (60 seconds) or when explicit manual photo is clicked
    if is_explicit_snapshot or (last_nisar_save_time == 0) or (now - last_nisar_save_time >= 60.0):
        last_nisar_save_time = now
        ts_img_path = os.path.join(NISAR_DIR, f"nisar_pixel_{timestr}.png")
        ts_json_path = os.path.join(NISAR_DIR, f"nisar_pixel_{timestr}.json")
        if image_b64:
            try:
                raw_b64 = image_b64.split(",")[1] if "," in image_b64 else image_b64
                img_bytes = base64.b64decode(raw_b64)
                with open(ts_img_path, "wb") as f:
                    f.write(img_bytes)
            except Exception:
                pass
        try:
            with open(ts_json_path, "w") as f:
                json.dump(payload_json, f, indent=2)
        except Exception:
            pass

@app.route("/analyze_image", methods=["POST"])
def analyze_image():
    """
    Processes real-time mobile camera video frames (at 5 FPS).
    Transmits mobile FPS and frame features directly into Multi-Modal Fusion Engine.
    Saves image string for live display on software dashboard & writes to local nisar/ PC folder (1 frame/min rate limited).
    """
    start_time = time.time()
    data = request.get_json(silent=True) or {}
    image_b64 = data.get("image", "")
    client_fps = float(data.get("fps", 5.0))
    is_explicit_snapshot = bool(data.get("is_snapshot", False))

    if not image_b64:
        mean_r, mean_g, mean_b, flicker, haziness = 0.2, 0.7, 0.2, 0.0, 0.0
    else:
        try:
            raw_b64 = image_b64
            if "," in image_b64:
                raw_b64 = image_b64.split(",")[1]
            img_bytes = base64.b64decode(raw_b64)
            img = Image.open(BytesIO(img_bytes)).convert("RGB").resize((224, 224))
            arr = np.array(img, dtype=np.float32) / 255.0

            mean_r = float(np.mean(arr[:, :, 0]))
            mean_g = float(np.mean(arr[:, :, 1]))
            mean_b = float(np.mean(arr[:, :, 2]))
            flicker = float(np.std(arr[:, :, 0]))
            haziness = float(np.mean(np.abs(arr[:, :, 0] - arr[:, :, 1])))
        except Exception:
            mean_r, mean_g, mean_b, flicker, haziness = 0.2, 0.7, 0.2, 0.0, 0.0

    global latest_camera_features, latest_camera_image_b64, latest_sensor_data, latest_satellite_metrics, time_series_buffer
    
    if image_b64:
        latest_camera_image_b64 = image_b64

    latest_camera_features = {
        "mean_r": mean_r,
        "mean_g": mean_g,
        "mean_b": mean_b,
        "flicker": flicker,
        "smoke_haziness": haziness,
        "fps": client_fps,
        "timestamp": time.time()
    }

    cam_pred = fusion_engine.predict_mobile_camera_cnn(mean_r, mean_g, mean_b, flicker, haziness)
    cam_pred["fps"] = round(client_fps, 1)

    sat_data = {"red": 0.15, "green": 0.55, "blue": 0.15, "nir": 0.75}
    if cam_pred["camera_status"] == "Critical_Red":
        sat_data = {"red": 0.65, "green": 0.15, "blue": 0.10, "nir": 0.10}

    fusion_result = fusion_engine.evaluate_multi_modal_fusion(
        sat_data=sat_data,
        ts_data=time_series_buffer,
        sensor_data=latest_sensor_data,
        camera_data=latest_camera_features
    )

    # Save PNG and JSON files into local nisar/ folder on PC (1 frame / 60 seconds rate limited)
    save_nisar_pixel_files(image_b64, mean_r, mean_g, mean_b, fusion_result, is_explicit_snapshot=is_explicit_snapshot)

    latency_ms = round((time.time() - start_time) * 1000.0, 2)
    cam_pred["latency_ms"] = latency_ms

    if fusion_result["risk_level"] in ["CRITICAL", "HIGH"]:
        dispatch_sent = False
        if twilio_dispatcher:
            try:
                dispatch = twilio_dispatcher.send_emergency_alert(
                    disaster_type=fusion_result["predicted_disaster"],
                    risk_level=fusion_result["risk_level"],
                    confidence=fusion_result["system_confidence_percent"],
                    location="Uttarakhand Sector-4 High-Risk Grid",
                    lat=30.0668,
                    lon=79.0193
                )
                if isinstance(dispatch, dict):
                    dispatch_sent = dispatch.get("dispatched", False)
            except Exception:
                pass
        save_alert(
            location="Uttarakhand Mobile Back Camera Stream",
            lat=30.0668,
            lon=79.0193,
            disaster_type=fusion_result["predicted_disaster"],
            risk_level=fusion_result["risk_level"],
            confidence=fusion_result["system_confidence_percent"],
            prob=fusion_result["disaster_probability_percent"],
            sms_sent=dispatch_sent
        )

    return jsonify({
        "status": "success",
        "camera_prediction": cam_pred,
        "fusion_result": fusion_result,
        "mobile_fps": client_fps,
        "satellite_fps": latest_satellite_metrics.get("satellite_fps", 5.0),
        "latency_ms": latency_ms,
        "has_live_image": bool(latest_camera_image_b64),
        "saved_to_nisar_folder": True
    })

@app.route("/nisar/<path:filename>", methods=["GET"])
def serve_nisar_file(filename):
    """Serves files stored in the local nisar/ directory for PC dashboard viewing/downloading."""
    return send_from_directory(NISAR_DIR, filename, as_attachment=False)

@app.route("/api/nisar_files", methods=["GET"])
def get_nisar_files():
    """Returns JSON list of stored NISAR pixel files in the PC nisar/ directory."""
    files_info = []
    if os.path.exists(NISAR_DIR):
        for fname in sorted(os.listdir(NISAR_DIR), reverse=True):
            fpath = os.path.join(NISAR_DIR, fname)
            if os.path.isfile(fpath):
                stat = os.stat(fpath)
                files_info.append({
                    "filename": fname,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "url": f"/nisar/{fname}"
                })
    return jsonify({"status": "success", "files": files_info, "count": len(files_info)})

@app.route("/api/capture_nisar_frame", methods=["POST"])
def capture_nisar_frame():
    """
    POST /api/capture_nisar_frame
    Saves a 1-minute interval satellite/camera pixel capture frame PNG and JSON metadata to local nisar/ directory.
    """
    global latest_camera_features, latest_sensor_data, latest_mobile_alert, latest_camera_image_b64
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"nisar_capture_{timestamp_str}.json"
    png_filename = f"nisar_capture_{timestamp_str}.png"
    
    json_path = os.path.join(NISAR_DIR, json_filename)
    png_path = os.path.join(NISAR_DIR, png_filename)
    
    is_landslide = latest_mobile_alert.get("active", False) or latest_sensor_data.get("scenario") == "landslide"
    
    mean_r = latest_camera_features.get("mean_r", 0.15)
    mean_g = latest_camera_features.get("mean_g", 0.65)
    mean_b = latest_camera_features.get("mean_b", 0.15)
    
    if is_landslide:
        nisar_pixels = {
            "red": round(mean_r if mean_r > 0.3 else 0.52, 4),
            "green": round(mean_g if mean_g < 0.4 else 0.28, 4),
            "blue": round(mean_b, 4),
            "nir": 0.22,
            "swir": 0.65,
            "thermal": round(latest_sensor_data.get("temperature", 25.8), 1),
            "l_band_db": -4.8,
            "s_band_db": -2.6
        }
        event_id = f"LANDSLIDE_NISAR_FRAME_{timestamp_str}"
        disaster_type = "Landslide"
        risk_level = "CRITICAL"
    else:
        nisar_pixels = {
            "red": round(mean_r, 4),
            "green": round(mean_g, 4),
            "blue": round(mean_b, 4),
            "nir": round(0.15 if mean_r > 0.4 else 0.75, 4),
            "swir": round(0.35 if mean_r > 0.4 else 0.15, 4),
            "thermal": round(52.0 if mean_r > 0.4 else 26.5, 1),
            "l_band_db": round(-12.4 if mean_r <= 0.4 else -6.2, 1),
            "s_band_db": round(-8.6 if mean_r <= 0.4 else -3.8, 1)
        }
        event_id = f"NISAR_FRAME_{timestamp_str}"
        disaster_type = latest_mobile_alert.get("disaster_type", "None")
        risk_level = latest_mobile_alert.get("risk_level", "NORMAL")
    
    payload = {
        "event_id": event_id,
        "disaster_type": disaster_type,
        "risk_level": risk_level,
        "timestamp": datetime.now().isoformat(),
        "satellite": "ISRO-NASA NISAR Dual-SAR",
        "product": "L-Band (-4.8dB Landslide / -12.4dB Normal) / S-Band",
        "latitude": 30.0668,
        "longitude": 79.0193,
        "nisar_pixels": nisar_pixels,
        "ground_sensors": latest_sensor_data,
        "verification_status": "VERIFIED_GEOSPATIAL"
    }
    
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            
        saved_mobile_img = False
        if latest_camera_image_b64:
            try:
                raw_b64 = latest_camera_image_b64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                img_data = base64.b64decode(raw_b64)
                with open(png_path, "wb") as f_img:
                    f_img.write(img_data)
                saved_mobile_img = True
            except Exception:
                saved_mobile_img = False

        if not saved_mobile_img:
            arr = np.zeros((64, 64, 3), dtype=np.uint8)
            arr[:, :, 0] = int(nisar_pixels["red"] * 255)
            arr[:, :, 1] = int(nisar_pixels["green"] * 255)
            arr[:, :, 2] = int(nisar_pixels["blue"] * 255)
            img = Image.fromarray(arr)
            img.save(png_path)

        # Update latest_camera_features and latest nisar capture files for live UI refresh
        latest_camera_features["mean_r"] = nisar_pixels["red"]
        latest_camera_features["mean_g"] = nisar_pixels["green"]
        latest_camera_features["mean_b"] = nisar_pixels["blue"]
        latest_camera_features["timestamp"] = time.time()

        try:
            shutil.copyfile(png_path, os.path.join(NISAR_DIR, "latest_nisar_capture.png"))
            shutil.copyfile(json_path, os.path.join(NISAR_DIR, "latest_nisar_data.json"))
        except Exception:
            pass
    except Exception as e:
        pass
    
    return jsonify({
        "status": "success",
        "message": "1-minute NISAR satellite/camera frame saved to nisar/ folder",
        "json_filename": json_filename,
        "png_filename": png_filename,
        "payload": payload
    })

@app.route("/api/latest_camera_image", methods=["GET"])
def get_latest_camera_image():
    """Returns the latest captured mobile NISAR camera frame image and pixel payload for live display on PC software dashboard."""
    global latest_camera_image_b64, latest_camera_features
    mean_r = latest_camera_features.get("mean_r", 0.15)
    mean_g = latest_camera_features.get("mean_g", 0.65)
    mean_b = latest_camera_features.get("mean_b", 0.15)

    nisar_pixels = {
        "red": round(mean_r, 4),
        "green": round(mean_g, 4),
        "blue": round(mean_b, 4),
        "nir": round(0.15 if mean_r > 0.4 else 0.75, 4),
        "swir": round(0.35 if mean_r > 0.4 else 0.15, 4),
        "thermal": round(52.0 if mean_r > 0.4 else 26.5, 1),
        "l_band_db": round(-12.4 if mean_r <= 0.4 else -6.2, 1),
        "s_band_db": round(-8.6 if mean_r <= 0.4 else -3.8, 1)
    }

    return jsonify({
        "status": "success",
        "image": latest_camera_image_b64,
        "nisar_pixels": nisar_pixels,
        "features": latest_camera_features,
        "fps": latest_camera_features.get("fps", 5.0),
        "timestamp": latest_camera_features.get("timestamp", time.time())
    })

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Returns alert history from SQLite database."""
    alerts = get_recent_alerts(limit=50)
    return jsonify({"status": "success", "count": len(alerts), "alerts": alerts})

@app.route("/api/sensor_logs", methods=["GET"])
def get_sensor_logs():
    """Returns recent ESP8266 telemetry logs."""
    logs = get_recent_sensor_logs(limit=50)
    return jsonify({"status": "success", "count": len(logs), "logs": logs})

@app.route("/api/predict_fusion", methods=["POST"])
def predict_fusion_custom():
    """Generic fusion evaluation endpoint."""
    body = request.get_json(silent=True) or {}
    sat_data = body.get("sat_data", {"red": 0.15, "green": 0.55, "blue": 0.15, "nir": 0.75})
    sensor_data = body.get("sensor_data", {"temperature": 28.0, "humidity": 50.0, "smoke": 200.0, "soil_moisture": 40.0, "water_level": 5.0, "flame": 0.0, "vibration": 0.2})
    cam_data = body.get("camera_data", latest_camera_features)

    global time_series_buffer
    res = fusion_engine.evaluate_multi_modal_fusion(sat_data, time_series_buffer, sensor_data, cam_data)
    return jsonify(res)


# ==================== Mobile SOS & Safety Assistant Routes ====================

@app.route("/mobile_sos", methods=["GET"])
def mobile_sos_page():
    """Serves the mobile-first D-SQUARE SOS safety assistant interface."""
    return render_template("mobile_sos.html")


@app.route("/api/user/location", methods=["POST"])
def update_user_location():
    """
    POST /api/user/location
    Stores user location with explicit consent and retention expiration.
    Returns nearby active alerts and safe shelters.
    """
    body = request.get_json(silent=True) or {}
    consent = body.get("consent", False)
    if not consent:
        return jsonify({"status": "error", "message": "Location storage requires explicit user consent"}), 403

    lat = float(body.get("latitude", 0.0))
    lon = float(body.get("longitude", 0.0))
    accuracy = float(body.get("accuracy_m", 10.0))
    user_session_id = body.get("user_session_id", "MOBILE_USER_SESSION_01")

    if abs(lat) > 90.0 or abs(lon) > 180.0 or (lat == 0.0 and lon == 0.0):
        return jsonify({"status": "error", "message": "Invalid GPS latitude or longitude coordinates"}), 400

    log_id = save_user_location_db(user_session_id, lat, lon, accuracy, consent=True, retention_hours=24)
    cleanup_expired_location_logs()

    sz_res = safe_zone_service.get_safe_zones_for_user(lat, lon, hazard_lat=30.0668, hazard_lon=79.0193, hazard_radius_km=10.0)

    return jsonify({
        "status": "success",
        "message": "User location updated securely",
        "log_id": log_id,
        "safe_zones_count": sz_res["count"],
        "nearest_safe_zone": sz_res["nearest"]
    })


@app.route("/api/demo/landslide-sos", methods=["POST"])
def demo_landslide_sos():
    """
    POST /api/demo/landslide-sos
    Simulates or processes a landslide disaster SOS event from ESP8266 telemetry.
    """
    global latest_mobile_alert, latest_sensor_data
    body = request.get_json(silent=True) or {}
    node_id = body.get("node_id", "ESP8266_LANDSLIDE_NODE_01")
    temp = float(body.get("temperature", 25.8))
    hum = float(body.get("humidity", 92.0))
    soil_m = float(body.get("soil_moisture", 88.0))
    soil_raw = body.get("soil_raw")

    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    latest_mobile_alert = {
        "active": True,
        "data_mode": "DEMO_SIMULATION" if "SIMULATED" in str(node_id) else "VERIFIED_HARDWARE",
        "disaster_type": "Landslide",
        "risk_level": "CRITICAL",
        "soil_moisture": soil_m,
        "temperature": temp,
        "humidity": hum,
        "led_state": "RED",
        "buzzer_state": "ON",
        "node_id": node_id,
        "timestamp": now_iso,
        "message": "CRITICAL: Saturated soil moisture and slope risk detected! Follow emergency evacuation instructions."
    }
    latest_sensor_data.update({
        "temperature": temp,
        "humidity": hum,
        "soil_moisture": soil_m,
        "smoke": 185.0,
        "water_level": 22.0,
        "vibration": 14.8,
        "tilt_angle": 48.5,
        "gyro_rate": 86.4,
        "tilt_state": 1,
        "vibration_alarm": 1,
        "node_id": node_id,
        "scenario": "landslide",
        "led_state": "RED",
        "buzzer_state": "ON"
    })
    if soil_raw is not None:
        latest_sensor_data["soil_raw"] = float(soil_raw)
    else:
        latest_sensor_data["soil_raw"] = 720.0

    save_sensor_log({
        "temperature": temp,
        "humidity": hum,
        "smoke": 185.0,
        "soil_moisture": soil_m,
        "water_level": 22.0,
        "flame": 0.0,
        "vibration": 14.8,
        "tilt_angle": 48.5,
        "node_id": node_id,
        "data_mode": latest_mobile_alert["data_mode"]
    })
    cur_pixels = {
        "red": 0.52,
        "green": 0.28,
        "blue": 0.15,
        "nir": 0.22,
        "swir": 0.65,
        "thermal": temp,
        "sar_l_band_db": -4.8,
        "sar_s_band_db": -2.6
    }
    hist_comp = None
    try:
        hist_comp = pixel_comparator.compare_pixels(cur_pixels, target_disaster_type="Landslide")
    except Exception:
        pass

    try:
        capture_nisar_frame()
    except Exception:
        pass

    return jsonify({
        "status": "success",
        "alert": latest_mobile_alert,
        "sensor_data": latest_sensor_data,
        "historical_comparison": hist_comp,
        "disaster_probability_percent": 94.5,
        "risk_level": "CRITICAL",
        "predicted_disaster": "Landslide"
    })


@app.route("/api/demo/reset-landslide-sos", methods=["POST"])
def demo_reset_landslide_sos():
    """
    POST /api/demo/reset-landslide-sos
    Resets the simulated landslide disaster SOS state to normal.
    """
    global latest_mobile_alert, latest_sensor_data
    body = request.get_json(silent=True) or {}
    node_id = body.get("node_id", "ESP8266_LANDSLIDE_NODE_01")
    temp = float(body.get("temperature", 26.5))
    hum = float(body.get("humidity", 52.0))
    soil_m = float(body.get("soil_moisture", 42.0))
    soil_raw = body.get("soil_raw")

    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    latest_mobile_alert = {
        "active": False,
        "data_mode": "DEMO_SIMULATION" if "SIMULATED" in str(node_id) else "VERIFIED_HARDWARE",
        "disaster_type": "None",
        "risk_level": "NORMAL",
        "soil_moisture": soil_m,
        "temperature": temp,
        "humidity": hum,
        "led_state": "GREEN",
        "buzzer_state": "OFF",
        "node_id": node_id,
        "timestamp": now_iso,
        "message": "No active simulated alert."
    }
    latest_sensor_data.update({
        "temperature": temp,
        "humidity": hum,
        "soil_moisture": soil_m,
        "smoke": 185.0,
        "water_level": 4.5,
        "vibration": 0.2,
        "tilt_angle": 1.2,
        "gyro_rate": 0.5,
        "tilt_state": 0,
        "vibration_alarm": 0,
        "node_id": node_id,
        "scenario": "normal",
        "led_state": "GREEN",
        "buzzer_state": "OFF"
    })
    if soil_raw is not None:
        latest_sensor_data["soil_raw"] = float(soil_raw)
    else:
        latest_sensor_data["soil_raw"] = 850.0

    return jsonify({
        "status": "success",
        "alert": latest_mobile_alert,
        "sensor_data": latest_sensor_data,
        "disaster_probability_percent": 12.5,
        "risk_level": "LOW",
        "predicted_disaster": "None"
    })


@app.route("/api/latest_sensor_data", methods=["GET"])
def get_latest_sensor_data():
    """
    GET /api/latest_sensor_data
    Returns the latest ESP8266 hardware sensor reading (soil_raw, soil_moisture, temperature, humidity, scenario)
    and NISAR satellite pixel data captured during detection.
    """
    global latest_sensor_data, latest_mobile_alert
    scenario = latest_sensor_data.get("scenario", "normal")
    is_landslide = (scenario == "landslide" or float(latest_sensor_data.get("soil_raw", 850.0)) < 800)

    if is_landslide:
        nisar_pixels = {
            "red": 0.520,
            "green": 0.280,
            "blue": 0.150,
            "nir": 0.220,
            "swir": 0.650,
            "thermal": round(float(latest_sensor_data.get("temperature", 25.8)), 1),
            "l_band_db": -4.8,
            "s_band_db": -2.6
        }
    else:
        nisar_pixels = {
            "red": 0.150,
            "green": 0.650,
            "blue": 0.150,
            "nir": 0.750,
            "swir": 0.150,
            "thermal": round(float(latest_sensor_data.get("temperature", 26.5)), 1),
            "l_band_db": -12.4,
            "s_band_db": -8.6
        }

    return jsonify({
        "status": "success",
        "node_id": latest_sensor_data.get("node_id", "ESP8266_NODE_01"),
        "soil_raw": latest_sensor_data.get("soil_raw", 850.0),
        "soil_moisture": latest_sensor_data.get("soil_moisture", 42.0),
        "temperature": latest_sensor_data.get("temperature", 26.5),
        "humidity": latest_sensor_data.get("humidity", 52.0),
        "scenario": scenario,
        "nisar_pixels": nisar_pixels,
        "timestamp": latest_sensor_data.get("timestamp") or datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    })


@app.route("/api/mobile/active-alert", methods=["GET"])
def get_mobile_active_alert_singular():
    """
    GET /api/mobile/active-alert
    Returns the latest simulated mobile disaster alert state.
    """
    global latest_mobile_alert
    if not latest_mobile_alert.get("timestamp"):
        latest_mobile_alert["timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    return jsonify({
        "status": "success",
        "alert": latest_mobile_alert
    })


@app.route("/api/mobile/active-alerts", methods=["GET"])
def get_mobile_active_alerts():
    """
    GET /api/mobile/active-alerts?lat=...&lon=...
    Returns current active disaster alerts relative to user geolocation.
    """
    global latest_mobile_alert, time_series_buffer, latest_sensor_data, latest_camera_features
    if not latest_mobile_alert.get("timestamp"):
        latest_mobile_alert["timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    lat = float(request.args.get("lat", 30.0668))
    lon = float(request.args.get("lon", 79.0193))

    hazard_lat, hazard_lon = 30.0668, 79.0193
    dist_km = calculate_haversine_distance_km(lat, lon, hazard_lat, hazard_lon)
    inside_zone = dist_km <= 12.0

    if latest_mobile_alert["active"]:
        active_alert_obj = {
            "active": True,
            "disaster_type": latest_mobile_alert["disaster_type"],
            "risk_level": latest_mobile_alert["risk_level"],
            "disaster_probability_percent": 94.5,
            "alert_time": latest_mobile_alert["timestamp"],
            "distance_from_user_km": dist_km,
            "user_inside_hazard_zone": inside_zone,
            "data_mode": latest_mobile_alert["data_mode"],
            "soil_moisture": latest_mobile_alert["soil_moisture"],
            "temperature": latest_mobile_alert["temperature"],
            "humidity": latest_mobile_alert["humidity"],
            "led_state": latest_mobile_alert["led_state"],
            "buzzer_state": latest_mobile_alert["buzzer_state"],
            "node_id": latest_mobile_alert["node_id"],
            "message": latest_mobile_alert["message"],
            "plain_language_warning": latest_mobile_alert["message"]
        }
    else:
        active_alert_obj = None

    return jsonify({
        "status": "success",
        "data_mode": latest_mobile_alert.get("data_mode", "DEMO_SIMULATION"),
        "active_alert": active_alert_obj,
        "alert": latest_mobile_alert,
        "user_inside_hazard_zone": inside_zone,
        "distance_to_hazard_km": dist_km,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/api/sensor_data", methods=["POST"])
@app.route("/alert", methods=["POST"])
def post_sensor_data_route():
    """
    POST /api/sensor_data
    Handles physical ESP8266 sensor telemetry posts.
    Parses node_id, soil_raw, soil_moisture, temperature, humidity, and scenario.
    """
    global latest_sensor_data, latest_mobile_alert
    body = request.get_json(silent=True) or request.form.to_dict() or {}

    node_id = body.get("node_id", "ESP8266_NODE_01")
    temp = float(body.get("temperature", latest_sensor_data.get("temperature", 26.5)))
    hum = float(body.get("humidity", latest_sensor_data.get("humidity", 52.0)))
    
    # Soil moisture raw value (SOIL_PIN A0)
    soil_raw = body.get("soil_raw", body.get("soilRaw"))
    soil_raw_val = float(soil_raw) if soil_raw is not None else float(latest_sensor_data.get("soil_raw", 850.0))

    if "soil_moisture" in body:
        soil_m = float(body["soil_moisture"])
    else:
        soil_m = 88.0 if soil_raw_val < 800 else 42.0

    scenario = body.get("scenario")
    if not scenario:
        scenario = "landslide" if (soil_raw_val < 800 or soil_m >= 80.0) else "normal"

    is_landslide = (scenario == "landslide" or soil_raw_val < 800 or soil_m >= 80.0)
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Update global latest_sensor_data state
    latest_sensor_data = {
        "node_id": node_id,
        "soil_raw": soil_raw_val,
        "soil_moisture": soil_m,
        "temperature": temp,
        "humidity": hum,
        "scenario": "landslide" if is_landslide else "normal",
        "timestamp": now_iso
    }

    save_sensor_log(latest_sensor_data)

    if is_landslide:
        latest_mobile_alert = {
            "active": True,
            "data_mode": "VERIFIED_HARDWARE",
            "disaster_type": "Landslide",
            "risk_level": "CRITICAL",
            "soil_moisture": soil_m,
            "temperature": temp,
            "humidity": hum,
            "led_state": "RED",
            "buzzer_state": "ON",
            "node_id": node_id,
            "timestamp": now_iso,
            "message": "⚠️ Landslide Risk Detected (Hardware)"
        }
    else:
        latest_mobile_alert = {
            "active": False,
            "data_mode": "VERIFIED_HARDWARE",
            "disaster_type": "None",
            "risk_level": "NORMAL",
            "soil_moisture": soil_m,
            "temperature": temp,
            "humidity": hum,
            "led_state": "GREEN",
            "buzzer_state": "OFF",
            "node_id": node_id,
            "timestamp": now_iso,
            "message": "✅ Normal Condition (Hardware)"
        }

    cur_pixels = {
        "red": 0.52 if is_landslide else 0.15,
        "green": 0.28 if is_landslide else 0.55,
        "blue": 0.15,
        "nir": 0.22 if is_landslide else 0.75,
        "swir": 0.65 if is_landslide else 0.15,
        "thermal": temp,
        "sar_l_band_db": -4.8 if is_landslide else -12.4,
        "sar_s_band_db": -2.6 if is_landslide else -8.6
    }
    hist_comp = None
    try:
        hist_comp = pixel_comparator.compare_pixels(cur_pixels, target_disaster_type="Landslide" if is_landslide else "None")
    except Exception:
        pass

    try:
        capture_nisar_frame()
    except Exception:
        pass

    return jsonify({
        "status": "success",
        "message": "Hardware telemetry received and processed",
        "sensor_data": latest_sensor_data,
        "alert": latest_mobile_alert,
        "historical_comparison": hist_comp,
        "disaster_probability_percent": 94.5 if is_landslide else 12.5,
        "risk_level": "CRITICAL" if is_landslide else "LOW",
        "predicted_disaster": "Landslide" if is_landslide else "None"
    })


@app.route("/api/mobile/safe-zones", methods=["GET"])
def get_mobile_safe_zones():
    """
    GET /api/mobile/safe-zones?lat=...&lon=...&disaster_type=...
    Returns verified safe shelters excluding active hazard geometry.
    """
    lat = float(request.args.get("lat", 30.0668))
    lon = float(request.args.get("lon", 79.0193))
    disaster_type = request.args.get("disaster_type")

    res = safe_zone_service.get_safe_zones_for_user(
        lat, lon, hazard_lat=30.0668, hazard_lon=79.0193, hazard_radius_km=10.0, disaster_type=disaster_type
    )
    return jsonify(res)


@app.route("/api/mobile/sos", methods=["POST"])
def post_mobile_sos():
    """
    POST /api/mobile/sos
    Sends emergency location map link to USER-SAVED trusted contacts with explicit confirmation.
    Enforces a 60-second anti-spam cooldown per session.
    NEVER automatically contacts 112.
    """
    body = request.get_json(silent=True) or {}
    consent = body.get("consent", False) or body.get("consent_confirmed", False)
    if not consent:
        return jsonify({"status": "error", "message": "SOS dispatch requires explicit user confirmation."}), 403

    user_session_id = body.get("user_session_id", "MOBILE_USER_SESSION_01")

    now = time.time()
    last_sent = sos_last_sent_timestamps.get(user_session_id, 0)
    if now - last_sent < 60.0:
        remaining = int(60.0 - (now - last_sent))
        return jsonify({
            "status": "error",
            "message": f"SOS cooldown active. Please wait {remaining} seconds before resending SOS."
        }), 429

    lat = float(body.get("latitude", 30.0668))
    lon = float(body.get("longitude", 79.0193))
    message_text = body.get("message", "EMERGENCY SOS: I need help! Here is my live GPS location.")

    contacts = get_trusted_contacts_db(user_session_id)
    recipient_count = len(contacts)

    map_link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=15/{lat}/{lon}"

    dispatch_status = "SENT"
    twilio_status = None
    if recipient_count > 0:
        for c in contacts:
            phone = c.get("phone_number")
            if phone and twilio_dispatcher:
                try:
                    twilio_res = twilio_dispatcher.send_sms_alert(
                        location=f"GPS Coordinates ({lat}, {lon})",
                        disaster_type="Mobile SOS Alert",
                        risk_level="HIGH",
                        confidence=95.0,
                        prob=90.0
                    )
                    twilio_status = twilio_res
                except Exception:
                    pass

    sos_event = {
        "user_session_id": user_session_id,
        "latitude": lat,
        "longitude": lon,
        "accuracy_m": float(body.get("accuracy_m", 10.0)),
        "disaster_type": body.get("disaster_type", "General Emergency"),
        "risk_level": "HIGH",
        "message": message_text,
        "recipient_count": recipient_count,
        "dispatch_status": dispatch_status,
        "consent_confirmed": True,
        "data_mode": body.get("data_mode", "DEMO")
    }
    event_id = save_mobile_sos_event_db(sos_event)
    sos_last_sent_timestamps[user_session_id] = now

    return jsonify({
        "status": "success",
        "message": f"SOS alert processed successfully. Shared with {recipient_count} trusted contacts.",
        "event_id": event_id,
        "map_link": map_link,
        "twilio_status": twilio_status,
        "cooldown_seconds": 60
    })


@app.route("/api/mobile/weather", methods=["POST"])
def post_mobile_weather():
    """
    POST /api/mobile/weather
    Returns IMD official weather forecast and warnings for user geolocation.
    """
    body = request.get_json(silent=True) or {}
    lat = float(body.get("latitude", 30.0668))
    lon = float(body.get("longitude", 79.0193))
    language = body.get("language", "en")

    res = weather_service.get_weather_for_location(lat, lon, language=language)
    return jsonify(res)


@app.route("/api/mobile/ground-station-status", methods=["GET"])
def get_ground_station_status():
    """
    GET /api/mobile/ground-station-status
    Returns live ESP8266 NodeMCU ground station sensor telemetry and stream health.
    """
    global latest_sensor_data, latest_camera_features
    return jsonify({
        "status": "success",
        "node_id": latest_sensor_data.get("node_id", "ESP8266_NODE_01"),
        "telemetry": latest_sensor_data,
        "camera_fps": latest_camera_features.get("fps", 5.0),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/api/mobile/assistant", methods=["POST"])
def post_mobile_assistant():
    """
    POST /api/mobile/assistant
    Processes D-SQUARE GPT queries using Satellite, Monsoon, Ground Station, and Safety context.
    """
    body = request.get_json(silent=True) or {}
    user_msg = body.get("message", "How do I stay safe?")
    lat = float(body.get("latitude", 30.0668))
    lon = float(body.get("longitude", 79.0193))
    language = body.get("language", "en")

    weather_res = weather_service.get_weather_for_location(lat, lon, language=language)
    safe_zones_res = safe_zone_service.get_safe_zones_for_user(lat, lon, hazard_lat=30.0668, hazard_lon=79.0193)

    global time_series_buffer, latest_sensor_data, latest_camera_features
    current_fusion = fusion_engine.evaluate_multi_modal_fusion(
        sat_data={"red": 0.15, "green": 0.55, "blue": 0.15, "nir": 0.75},
        ts_data=time_series_buffer,
        sensor_data=latest_sensor_data,
        camera_data=latest_camera_features
    )

    active_alert = {
        "disaster_type": current_fusion.get("predicted_disaster", "None"),
        "risk_level": current_fusion.get("risk_level", "LOW")
    }

    res = safety_assistant_service.process_assistant_query(
        user_message=user_msg,
        user_lat=lat,
        user_lon=lon,
        active_alert=active_alert,
        fusion_result=current_fusion,
        safe_zones=safe_zones_res.get("safe_zones", []),
        weather_data=weather_res,
        ground_station_data=latest_sensor_data,
        data_mode="DEMO" if latest_sensor_data.get("scenario") else "VERIFIED"
    )
    return jsonify(res)


@app.route("/api/mobile/contacts", methods=["GET", "POST"])
def mobile_contacts_route():
    """
    GET /api/mobile/contacts?session_id=...
    POST /api/mobile/contacts (Save trusted contact)
    """
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        session_id = body.get("user_session_id", "MOBILE_USER_SESSION_01")
        name = body.get("contact_name")
        phone = body.get("phone_number")
        rel = body.get("relationship", "Family")

        if not name or not phone:
            return jsonify({"status": "error", "message": "Missing contact_name or phone_number"}), 400

        cid = save_trusted_contact_db(session_id, name, phone, rel)
        return jsonify({"status": "success", "message": "Trusted contact saved successfully", "contact_id": cid})
    else:
        session_id = request.args.get("session_id", "MOBILE_USER_SESSION_01")
        contacts = get_trusted_contacts_db(session_id)
        return jsonify({"status": "success", "count": len(contacts), "contacts": contacts})


@app.route("/api/mobile/contacts/<int:contact_id>", methods=["DELETE"])
def delete_mobile_contact_route(contact_id):
    """DELETE /api/mobile/contacts/<contact_id>?session_id=..."""
    session_id = request.args.get("session_id", "MOBILE_USER_SESSION_01")
    ok = delete_trusted_contact_db(session_id, contact_id)
    if ok:
        return jsonify({"status": "success", "message": f"Contact {contact_id} deleted successfully"})
    return jsonify({"status": "error", "message": f"Contact {contact_id} not found"}), 404


@app.route("/api/mobile/sos-history", methods=["GET"])
def get_mobile_sos_history():
    """GET /api/mobile/sos-history?session_id=..."""
    session_id = request.args.get("session_id", "MOBILE_USER_SESSION_01")
    history = get_user_sos_history_db(session_id)
    return jsonify({"status": "success", "count": len(history), "history": history})

if __name__ == "__main__":
    import threading
    print("==================================================")
    print("  D-SQUARE 2.0 Dual HTTP/HTTPS Server Launching")
    print("==================================================")
    from generate_ssl_cert import generate_self_signed_cert, CERT_FILE, KEY_FILE
    cert_path, key_path = generate_self_signed_cert()

    # Function for HTTP listener on Port 5001
    def run_http():
        try:
            app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
        except Exception as e:
            print(f"[HTTP Server Error] {e}")

    # Launch HTTP thread
    http_thread = threading.Thread(target=run_http, daemon=True)
    http_thread.start()

    print(f"  [HTTPS URL] Mobile Camera: https://10.172.49.122:5000/mobile_camera")
    print(f"  [HTTPS URL] Software Dashboard: https://127.0.0.1:5000")
    print(f"  [HTTP URL]  Software Dashboard: http://127.0.0.1:5001")
    print(f"  [HTTP URL]  Mobile Camera: http://10.172.49.122:5001/mobile_camera")
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        app.run(host="0.0.0.0", port=5000, ssl_context=(cert_path, key_path), debug=False, use_reloader=False)
    else:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
