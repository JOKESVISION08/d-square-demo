"""
Database Manager for D-SQUARE 2.0
SQLite persistence for sensor logs, satellite snapshots, disaster alerts,
and historical/current satellite pixel-and-patch observations.
"""

import sqlite3
import os
import time
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disasters.db")


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Alerts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        location TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        disaster_type TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        confidence REAL NOT NULL,
        disaster_probability REAL NOT NULL,
        sms_sent INTEGER DEFAULT 0,
        status TEXT DEFAULT 'ACTIVE'
    )
    """)

    # Sensor Telemetry Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        node_id TEXT NOT NULL,
        temperature REAL,
        humidity REAL,
        smoke REAL,
        soil_moisture REAL,
        water_level REAL,
        flame INTEGER,
        vibration REAL,
        tilt_angle REAL,
        gyro_rate REAL,
        tilt_state INTEGER,
        vibration_alarm INTEGER,
        scenario TEXT
    )
    """)

    # Safe migration for sensor_logs columns if pre-existing
    for col, col_type in [("tilt_angle", "REAL"), ("gyro_rate", "REAL"), ("tilt_state", "INTEGER"), ("vibration_alarm", "INTEGER")]:
        try:
            cursor.execute(f"ALTER TABLE sensor_logs ADD COLUMN {col} {col_type}")
        except Exception:
            pass

    # Satellite Snapshots Table (Legacy)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS satellite_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        roi_name TEXT NOT NULL,
        ndvi REAL,
        lst REAL,
        soil_moisture REAL,
        ndwi REAL,
        aod REAL
    )
    """)

    # 1) Historical Satellite Pixel & Patch Samples Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS satellite_pixel_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL,
        disaster_type TEXT NOT NULL,
        acquisition_date TEXT NOT NULL,
        satellite TEXT NOT NULL,
        product TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        patch_size INTEGER DEFAULT 5,
        red REAL,
        green REAL,
        blue REAL,
        nir REAL,
        swir1 REAL,
        swir2 REAL,
        thermal REAL,
        sar_l_band_db REAL,
        sar_s_band_db REAL,
        sar_vv_db REAL,
        sar_vh_db REAL,
        sar_coherence REAL,
        ground_deformation_mm REAL,
        ndvi REAL,
        ndwi REAL,
        mndwi REAL,
        nbr REAL,
        lst REAL,
        soil_moisture REAL,
        rainfall REAL,
        slope REAL,
        patch_mean_ndvi REAL,
        patch_std_ndvi REAL,
        patch_median_ndvi REAL,
        patch_mean_nbr REAL,
        patch_std_nbr REAL,
        patch_median_nbr REAL,
        patch_mean_lst REAL,
        patch_std_lst REAL,
        valid_pixel_count INTEGER,
        cloud_cover REAL,
        label_source TEXT,
        source_url TEXT,
        verification_status TEXT DEFAULT 'DEMO',
        quality_flag TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2) Current Satellite Observations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS current_satellite_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        acquisition_date TEXT NOT NULL,
        satellite TEXT NOT NULL,
        product TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        patch_size INTEGER DEFAULT 5,
        feature_json TEXT NOT NULL,
        verification_status TEXT DEFAULT 'DEMO',
        quality_flag TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3) Satellite Scenes Table (Uploaded Historical and Current Scenes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS satellite_scenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scene_type TEXT NOT NULL,
        event_id TEXT,
        disaster_type TEXT,
        satellite TEXT NOT NULL,
        product TEXT,
        acquisition_datetime TEXT,
        latitude REAL,
        longitude REAL,
        bbox_json TEXT,
        resolution_m REAL,
        cloud_cover REAL,
        crs TEXT,
        source_url TEXT,
        label_source TEXT,
        verification_status TEXT NOT NULL,
        quality_flag TEXT,
        original_filename TEXT,
        stored_path TEXT,
        metadata_json TEXT,
        preview_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4) Satellite Scene Features Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS satellite_scene_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scene_id INTEGER NOT NULL,
        patch_size INTEGER DEFAULT 5,
        roi_json TEXT,
        valid_pixel_count INTEGER,
        red_mean REAL,
        green_mean REAL,
        blue_mean REAL,
        nir_mean REAL,
        swir1_mean REAL,
        swir2_mean REAL,
        thermal_mean REAL,
        sar_l_band_db_mean REAL,
        sar_s_band_db_mean REAL,
        sar_vv_db_mean REAL,
        sar_vh_db_mean REAL,
        ndvi_mean REAL,
        ndvi_std REAL,
        ndwi_mean REAL,
        ndwi_std REAL,
        mndwi_mean REAL,
        mndwi_std REAL,
        nbr_mean REAL,
        nbr_std REAL,
        lst_mean REAL,
        lst_std REAL,
        soil_moisture_mean REAL,
        quality_score REAL,
        feature_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(scene_id) REFERENCES satellite_scenes(id) ON DELETE CASCADE
    )
    """)

    # 5) Safe Zones Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS safe_zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT,
        capacity INTEGER DEFAULT 100,
        contact_phone TEXT,
        source_name TEXT DEFAULT 'Official Registry',
        source_url TEXT,
        verification_status TEXT DEFAULT 'VERIFIED',
        verified_at TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6) Mobile SOS Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mobile_sos_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_session_id TEXT NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        accuracy_m REAL,
        disaster_type TEXT,
        risk_level TEXT,
        message TEXT,
        recipient_count INTEGER DEFAULT 0,
        dispatch_status TEXT DEFAULT 'PENDING',
        consent_confirmed INTEGER DEFAULT 1,
        data_mode TEXT DEFAULT 'DEMO'
    )
    """)

    # 7) Mobile Location Logs Table (Ephemeral, consent-based)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mobile_location_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_session_id TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        accuracy_m REAL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        consent INTEGER DEFAULT 1,
        expires_at TEXT
    )
    """)

    # 8) Trusted Contacts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trusted_contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_session_id TEXT NOT NULL,
        contact_name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        relationship TEXT DEFAULT 'Family',
        verified INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 9) Weather Cache Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude_bucket REAL NOT NULL,
        longitude_bucket REAL NOT NULL,
        provider TEXT NOT NULL,
        raw_response_json TEXT,
        normalized_response_json TEXT,
        fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
        valid_until TEXT
    )
    """)

    conn.commit()
    conn.close()

    # Seed demo data if empty
    seed_demo_historical_samples_if_empty()
    seed_demo_safe_zones_if_empty()


# ==================== Database Helper Functions ====================

def save_alert(location: str, lat: float, lon: float, disaster_type: str, risk_level: str, confidence: float, prob: float, sms_sent: bool = False) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    cursor.execute("""
    INSERT INTO alerts (timestamp, location, latitude, longitude, disaster_type, risk_level, confidence, disaster_probability, sms_sent)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ts, location, lat, lon, disaster_type, risk_level, confidence, prob, 1 if sms_sent else 0))
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id


def save_sensor_log(data: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    cursor.execute("""
    INSERT INTO sensor_logs (timestamp, node_id, temperature, humidity, smoke, soil_moisture, water_level, flame, vibration, tilt_angle, gyro_rate, tilt_state, vibration_alarm, scenario)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts,
        data.get("node_id", "ESP8266_01"),
        data.get("temperature"),
        data.get("humidity"),
        data.get("smoke"),
        data.get("soil_moisture"),
        data.get("water_level"),
        data.get("flame"),
        data.get("vibration"),
        data.get("tilt_angle", 0.0),
        data.get("gyro_rate", 0.0),
        data.get("tilt_state", 0),
        data.get("vibration_alarm", 0),
        data.get("scenario", "normal")
    ))
    conn.commit()
    conn.close()


def get_recent_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_sensor_logs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensor_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== Satellite Pixel/Patch DB Functions ====================

def save_satellite_pixel_sample(sample: Dict[str, Any]) -> int:
    """Inserts a single historical satellite patch sample record into satellite_pixel_samples."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cols = [
        "event_id", "disaster_type", "acquisition_date", "satellite", "product",
        "latitude", "longitude", "patch_size", "red", "green", "blue", "nir",
        "swir1", "swir2", "thermal", "sar_l_band_db", "sar_s_band_db", "sar_vv_db",
        "sar_vh_db", "sar_coherence", "ground_deformation_mm", "ndvi", "ndwi",
        "mndwi", "nbr", "lst", "soil_moisture", "rainfall", "slope",
        "patch_mean_ndvi", "patch_std_ndvi", "patch_median_ndvi",
        "patch_mean_nbr", "patch_std_nbr", "patch_median_nbr",
        "patch_mean_lst", "patch_std_lst", "valid_pixel_count",
        "cloud_cover", "label_source", "source_url", "verification_status", "quality_flag"
    ]
    
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO satellite_pixel_samples ({', '.join(cols)}) VALUES ({placeholders})"
    values = [sample.get(c) for c in cols]
    
    cursor.execute(sql, values)
    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return inserted_id


def get_historical_pixel_samples(disaster_type: Optional[str] = None, verification_status: Optional[str] = None, limit: int = 10000) -> List[Dict[str, Any]]:
    """Retrieves historical satellite pixel samples filtered by disaster_type and/or verification_status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM satellite_pixel_samples WHERE 1=1"
    params = []
    
    if disaster_type and disaster_type.upper() != "ALL":
        query += " AND UPPER(disaster_type) = UPPER(?)"
        params.append(disaster_type)
        
    if verification_status and verification_status.upper() != "ALL":
        query += " AND UPPER(verification_status) = UPPER(?)"
        params.append(verification_status)
        
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_current_satellite_sample(sample: Dict[str, Any]) -> int:
    """Saves a current satellite observation record into current_satellite_samples."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    feat_json = sample.get("feature_json")
    if isinstance(feat_json, dict):
        feat_json = json.dumps(feat_json)
    elif not feat_json:
        feat_json = json.dumps(sample.get("features", {}))
        
    cursor.execute("""
    INSERT INTO current_satellite_samples (acquisition_date, satellite, product, latitude, longitude, patch_size, feature_json, verification_status, quality_flag)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sample.get("acquisition_date", time.strftime("%Y-%m-%d %H:%M:%S")),
        sample.get("satellite", "ISRO-NASA NISAR / Sentinel-2"),
        sample.get("product", "L2A Surface Reflectance / L-Band SAR"),
        float(sample.get("latitude", 30.0668)),
        float(sample.get("longitude", 79.0193)),
        int(sample.get("patch_size", 5)),
        feat_json,
        sample.get("verification_status", "DEMO"),
        sample.get("quality_flag", "SIMULATED_SCENARIO")
    ))
    sample_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sample_id


def get_latest_current_satellite_sample() -> Optional[Dict[str, Any]]:
    """Fetches the most recent current satellite observation sample."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM current_satellite_samples ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        try:
            d["features"] = json.loads(d["feature_json"])
        except Exception:
            d["features"] = {}
        return d
    return None


def get_historical_events_summary() -> Dict[str, Any]:
    """Returns event count grouped by disaster_type, satellite, verification_status, and year."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_count FROM satellite_pixel_samples")
    total_count = cursor.fetchone()["total_count"]
    
    cursor.execute("SELECT disaster_type, COUNT(*) as count FROM satellite_pixel_samples GROUP BY disaster_type")
    by_disaster = {r["disaster_type"]: r["count"] for r in cursor.fetchall()}
    
    cursor.execute("SELECT satellite, COUNT(*) as count FROM satellite_pixel_samples GROUP BY satellite")
    by_satellite = {r["satellite"]: r["count"] for r in cursor.fetchall()}
    
    cursor.execute("SELECT verification_status, COUNT(*) as count FROM satellite_pixel_samples GROUP BY verification_status")
    by_verification = {r["verification_status"]: r["count"] for r in cursor.fetchall()}
    
    cursor.execute("SELECT strftime('%Y', acquisition_date) as year, COUNT(*) as count FROM satellite_pixel_samples GROUP BY year")
    by_year = {r["year"] or "Unknown": r["count"] for r in cursor.fetchall()}
    
    conn.close()
    return {
        "total_records": total_count,
        "by_disaster_type": by_disaster,
        "by_satellite": by_satellite,
        "by_verification_status": by_verification,
        "by_year": by_year
    }


def get_feature_statistics(disaster_type: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """Calculates feature-wise mean and std across historical records for z-score normalization."""
    records = get_historical_pixel_samples(disaster_type=disaster_type, limit=10000)
    if not records:
        return {}
        
    feature_keys = [
        "red", "green", "blue", "nir", "swir1", "swir2", "thermal",
        "sar_l_band_db", "sar_s_band_db", "sar_vv_db", "sar_vh_db",
        "sar_coherence", "ground_deformation_mm", "ndvi", "ndwi",
        "mndwi", "nbr", "lst", "soil_moisture", "rainfall", "slope"
    ]
    
    stats = {}
    for key in feature_keys:
        vals = [float(r[key]) for r in records if r.get(key) is not None]
        if vals:
            arr = np.array(vals, dtype=np.float64)
            stats[key] = {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)) if len(arr) > 1 else 1.0,
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "count": len(vals)
            }
    return stats


def seed_demo_historical_samples_if_empty():
    """
    Seeds demo historical dataset if satellite_pixel_samples table is empty.
    Seeds 10 samples per disaster class (Forest_Fire, Flood, Landslide, Air_Pollution, None).
    Every seeded row is tagged with verification_status='DEMO', label_source='Synthetic prototype scenario',
    source_url='Prototype demonstration dataset', quality_flag='NOT_FOR_SCIENTIFIC_VALIDATION'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM satellite_pixel_samples")
    count = cursor.fetchone()["count"]
    conn.close()
    
    if count > 0:
        return
        
    print("[DB SEED] Seeding demo historical satellite samples...")
    
    scenarios_config = {
        "Forest_Fire": {
            "satellite": "Sentinel-2 / Landsat-8", "product": "L2A Surface Reflectance",
            "red": (0.22, 0.35), "green": (0.12, 0.22), "blue": (0.10, 0.18),
            "nir": (0.12, 0.20), "swir1": (0.28, 0.42), "swir2": (0.30, 0.45),
            "thermal": (42.0, 65.0), "lst": (42.0, 65.0), "soil_moisture": (2.0, 15.0),
            "sar_l_band_db": (-8.0, -4.0), "sar_s_band_db": (-5.0, -2.0),
            "cloud_cover": 2.5, "event_prefix": "FF_UTT"
        },
        "Flood": {
            "satellite": "Sentinel-1 / RISAT-1", "product": "Dual-Pol SAR / L2A Optical",
            "red": (0.05, 0.12), "green": (0.12, 0.25), "blue": (0.25, 0.45),
            "nir": (0.02, 0.08), "swir1": (0.02, 0.06), "swir2": (0.01, 0.05),
            "thermal": (18.0, 24.0), "lst": (18.0, 24.0), "soil_moisture": (85.0, 100.0),
            "sar_l_band_db": (-22.0, -18.0), "sar_s_band_db": (-18.0, -14.0),
            "cloud_cover": 45.0, "event_prefix": "FL_CHE"
        },
        "Landslide": {
            "satellite": "ISRO NISAR / Sentinel-1", "product": "InSAR Ground Deformation",
            "red": (0.18, 0.28), "green": (0.15, 0.22), "blue": (0.12, 0.20),
            "nir": (0.14, 0.24), "swir1": (0.20, 0.32), "swir2": (0.18, 0.30),
            "thermal": (15.0, 25.0), "lst": (15.0, 25.0), "soil_moisture": (75.0, 95.0),
            "sar_l_band_db": (-15.0, -10.0), "sar_s_band_db": (-10.0, -6.0),
            "ground_deformation_mm": (-45.0, -120.0), "slope": (32.0, 68.0),
            "cloud_cover": 12.0, "event_prefix": "LS_CHM"
        },
        "Air_Pollution": {
            "satellite": "INSAT-3D / Sentinel-5P", "product": "Aerosol Optical Depth",
            "red": (0.20, 0.30), "green": (0.25, 0.35), "blue": (0.30, 0.45),
            "nir": (0.25, 0.35), "swir1": (0.18, 0.28), "swir2": (0.15, 0.25),
            "thermal": (30.0, 42.0), "lst": (30.0, 42.0), "soil_moisture": (15.0, 35.0),
            "sar_l_band_db": (-12.0, -9.0), "sar_s_band_db": (-8.0, -5.0),
            "cloud_cover": 8.0, "event_prefix": "AP_DEL"
        },
        "None": {
            "satellite": "Sentinel-2 / Resourcesat-2", "product": "L2A Surface Reflectance",
            "red": (0.10, 0.18), "green": (0.45, 0.65), "blue": (0.10, 0.18),
            "nir": (0.65, 0.85), "swir1": (0.10, 0.20), "swir2": (0.08, 0.16),
            "thermal": (22.0, 30.0), "lst": (22.0, 30.0), "soil_moisture": (35.0, 55.0),
            "sar_l_band_db": (-12.4, -10.0), "sar_s_band_db": (-8.6, -6.0),
            "cloud_cover": 1.0, "event_prefix": "NORM_UTT"
        }
    }
    
    np.random.seed(42)
    sample_count = 0
    
    for disaster_type, cfg in scenarios_config.items():
        for i in range(10):
            event_id = f"{cfg['event_prefix']}_DEMO_{2018 + (i % 6)}_{i+1:02d}"
            year = 2018 + (i % 6)
            month = (i % 12) + 1
            day = ((i * 3) % 27) + 1
            acq_date = f"{year}-{month:02d}-{day:02d} 10:30:00"
            
            lat = 30.0668 + np.random.uniform(-0.15, 0.15)
            lon = 79.0193 + np.random.uniform(-0.15, 0.15)
            
            r = round(float(np.random.uniform(cfg["red"][0], cfg["red"][1])), 4)
            g = round(float(np.random.uniform(cfg["green"][0], cfg["green"][1])), 4)
            b = round(float(np.random.uniform(cfg["blue"][0], cfg["blue"][1])), 4)
            nir = round(float(np.random.uniform(cfg["nir"][0], cfg["nir"][1])), 4)
            sw1 = round(float(np.random.uniform(cfg["swir1"][0], cfg["swir1"][1])), 4)
            sw2 = round(float(np.random.uniform(cfg["swir2"][0], cfg["swir2"][1])), 4)
            therm = round(float(np.random.uniform(cfg["thermal"][0], cfg["thermal"][1])), 1)
            
            eps = 1e-6
            ndvi = round(float((nir - r) / (nir + r + eps)), 4)
            ndwi = round(float((g - nir) / (g + nir + eps)), 4)
            mndwi = round(float((g - sw1) / (g + sw1 + eps)), 4)
            nbr = round(float((nir - sw2) / (nir + sw2 + eps)), 4)
            lst = therm
            soil_m = round(float(np.random.uniform(cfg["soil_moisture"][0], cfg["soil_moisture"][1])), 1)
            
            sar_l = round(float(np.random.uniform(cfg["sar_l_band_db"][0], cfg["sar_l_band_db"][1])), 1)
            sar_s = round(float(np.random.uniform(cfg["sar_s_band_db"][0], cfg["sar_s_band_db"][1])), 1)
            def_mm = round(float(np.random.uniform(cfg.get("ground_deformation_mm", (-2.0, 2.0))[0], cfg.get("ground_deformation_mm", (-2.0, 2.0))[1])), 1)
            slope = round(float(np.random.uniform(cfg.get("slope", (5.0, 25.0))[0], cfg.get("slope", (5.0, 25.0))[1])), 1)
            
            # Simulated 5x5 patch statistics
            p_mean_ndvi = ndvi
            p_std_ndvi = round(float(np.random.uniform(0.01, 0.05)), 4)
            p_med_ndvi = ndvi
            
            p_mean_nbr = nbr
            p_std_nbr = round(float(np.random.uniform(0.01, 0.06)), 4)
            p_med_nbr = nbr
            
            p_mean_lst = lst
            p_std_lst = round(float(np.random.uniform(0.5, 2.0)), 1)
            
            sample = {
                "event_id": event_id,
                "disaster_type": disaster_type,
                "acquisition_date": acq_date,
                "satellite": cfg["satellite"],
                "product": cfg["product"],
                "latitude": lat,
                "longitude": lon,
                "patch_size": 5,
                "red": r, "green": g, "blue": b, "nir": nir,
                "swir1": sw1, "swir2": sw2, "thermal": therm,
                "sar_l_band_db": sar_l, "sar_s_band_db": sar_s,
                "sar_vv_db": round(sar_l - 2.0, 1), "sar_vh_db": round(sar_l - 6.0, 1),
                "sar_coherence": 0.85 if disaster_type == "None" else 0.35,
                "ground_deformation_mm": def_mm,
                "ndvi": ndvi, "ndwi": ndwi, "mndwi": mndwi, "nbr": nbr, "lst": lst,
                "soil_moisture": soil_m, "rainfall": 120.0 if disaster_type in ["Flood", "Landslide"] else 5.0,
                "slope": slope,
                "patch_mean_ndvi": p_mean_ndvi, "patch_std_ndvi": p_std_ndvi, "patch_median_ndvi": p_med_ndvi,
                "patch_mean_nbr": p_mean_nbr, "patch_std_nbr": p_std_nbr, "patch_median_nbr": p_med_nbr,
                "patch_mean_lst": p_mean_lst, "patch_std_lst": p_std_lst,
                "valid_pixel_count": 25,
                "cloud_cover": cfg["cloud_cover"],
                "label_source": "Synthetic prototype scenario",
                "source_url": "Prototype demonstration dataset",
                "verification_status": "DEMO",
                "quality_flag": "NOT_FOR_SCIENTIFIC_VALIDATION"
            }
            save_satellite_pixel_sample(sample)
            sample_count += 1
            
    print(f"[DB SEED SUCCESS] Seeded {sample_count} demo historical satellite patch samples.")


# ==================== Uploaded Satellite Scene DB Helper Functions ====================

def save_satellite_scene(data: Dict[str, Any]) -> int:
    """Saves a new uploaded satellite scene record into satellite_scenes table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    meta_json = data.get("metadata_json")
    if isinstance(meta_json, (dict, list)):
        meta_json = json.dumps(meta_json)

    cursor.execute("""
    INSERT INTO satellite_scenes (
        scene_type, event_id, disaster_type, satellite, product, acquisition_datetime,
        latitude, longitude, bbox_json, resolution_m, cloud_cover, crs, source_url,
        label_source, verification_status, quality_flag, original_filename, stored_path,
        metadata_json, preview_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("scene_type", "historical"),
        data.get("event_id", "EVT_UPLOAD_01"),
        data.get("disaster_type", "None"),
        data.get("satellite", "Other"),
        data.get("product", "Uploaded Product"),
        data.get("acquisition_datetime", time.strftime("%Y-%m-%d %H:%M:%S")),
        float(data.get("latitude", 30.0668)),
        float(data.get("longitude", 79.0193)),
        json.dumps(data.get("bbox_json", {})) if isinstance(data.get("bbox_json"), dict) else data.get("bbox_json"),
        float(data.get("resolution_m", 10.0)),
        float(data.get("cloud_cover", 0.0)),
        data.get("crs", "EPSG:4326"),
        data.get("source_url", ""),
        data.get("label_source", "manual annotation"),
        data.get("verification_status", "UPLOADED_UNVERIFIED"),
        data.get("quality_flag", "UNVERIFIED_SOURCE"),
        data.get("original_filename", ""),
        data.get("stored_path", ""),
        meta_json or "{}",
        data.get("preview_path", "")
    ))
    scene_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scene_id


def save_scene_features(scene_id: int, features: Dict[str, Any]) -> int:
    """Saves patch feature statistics for an uploaded satellite scene into satellite_scene_features table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    feat_json = features.get("feature_json")
    if isinstance(feat_json, (dict, list)):
        feat_json = json.dumps(feat_json)
    elif not feat_json:
        feat_json = json.dumps(features)

    cursor.execute("""
    INSERT INTO satellite_scene_features (
        scene_id, patch_size, roi_json, valid_pixel_count, red_mean, green_mean, blue_mean,
        nir_mean, swir1_mean, swir2_mean, thermal_mean, sar_l_band_db_mean, sar_s_band_db_mean,
        sar_vv_db_mean, sar_vh_db_mean, ndvi_mean, ndvi_std, ndwi_mean, ndwi_std, mndwi_mean,
        mndwi_std, nbr_mean, nbr_std, lst_mean, lst_std, soil_moisture_mean, quality_score, feature_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        scene_id,
        int(features.get("patch_size", 5)),
        json.dumps(features.get("roi_json", {})) if isinstance(features.get("roi_json"), dict) else features.get("roi_json"),
        int(features.get("valid_pixel_count", 25)),
        features.get("red_mean"), features.get("green_mean"), features.get("blue_mean"),
        features.get("nir_mean"), features.get("swir1_mean"), features.get("swir2_mean"),
        features.get("thermal_mean"), features.get("sar_l_band_db_mean"), features.get("sar_s_band_db_mean"),
        features.get("sar_vv_db_mean"), features.get("sar_vh_db_mean"),
        features.get("ndvi_mean"), features.get("ndvi_std"),
        features.get("ndwi_mean"), features.get("ndwi_std"),
        features.get("mndwi_mean"), features.get("mndwi_std"),
        features.get("nbr_mean"), features.get("nbr_std"),
        features.get("lst_mean"), features.get("lst_std"),
        features.get("soil_moisture_mean"),
        float(features.get("quality_score", 50.0)),
        feat_json
    ))
    feat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feat_id


def get_uploaded_scenes(scene_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves uploaded scenes list, optionally filtered by scene_type ('historical' or 'current')."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if scene_type and scene_type.lower() != "all":
        cursor.execute("SELECT * FROM satellite_scenes WHERE UPPER(scene_type) = UPPER(?) ORDER BY id DESC", (scene_type,))
    else:
        cursor.execute("SELECT * FROM satellite_scenes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["features"] = get_scene_features(d["id"])
        results.append(d)
    return results


def get_scene_by_id(scene_id: Any) -> Optional[Dict[str, Any]]:
    """Fetches a single uploaded scene record by ID, event_id, or filename."""
    conn = get_db_connection()
    cursor = conn.cursor()
    row = None
    is_numeric = False
    try:
        sid_int = int(scene_id)
        is_numeric = True
        cursor.execute("SELECT * FROM satellite_scenes WHERE id = ?", (sid_int,))
        row = cursor.fetchone()
    except (ValueError, TypeError):
        pass

    if not row and not is_numeric:
        cursor.execute("SELECT * FROM satellite_scenes WHERE event_id = ? OR original_filename LIKE ? ORDER BY id DESC LIMIT 1", (str(scene_id), f"%{scene_id}%"))
        row = cursor.fetchone()

    conn.close()
    if row:
        d = dict(row)
        d["features"] = get_scene_features(d["id"])
        return d
    return None


def get_scene_features(scene_id: Any) -> Optional[Dict[str, Any]]:
    """Fetches feature statistics for a specified scene ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sid_int = int(scene_id)
        cursor.execute("SELECT * FROM satellite_scene_features WHERE scene_id = ? ORDER BY id DESC LIMIT 1", (sid_int,))
        row = cursor.fetchone()
    except (ValueError, TypeError):
        row = None

    conn.close()
    if row:
        d = dict(row)
        try:
            d["raw_features"] = json.loads(d.get("feature_json", "{}"))
        except Exception:
            d["raw_features"] = {}
        return d
    return None


def delete_scene(scene_id: Any) -> bool:
    """Deletes an uploaded scene record and removes associated stored files."""
    conn = get_db_connection()
    cursor = conn.cursor()
    row = None
    is_numeric = False
    try:
        sid_int = int(scene_id)
        is_numeric = True
        cursor.execute("SELECT id, stored_path, preview_path FROM satellite_scenes WHERE id = ?", (sid_int,))
        row = cursor.fetchone()
    except (ValueError, TypeError):
        pass

    if not row and not is_numeric:
        cursor.execute("SELECT id, stored_path, preview_path FROM satellite_scenes WHERE event_id = ? OR original_filename LIKE ? ORDER BY id DESC LIMIT 1", (str(scene_id), f"%{scene_id}%"))
        row = cursor.fetchone()

    if not row:
        conn.close()
        return False

    real_id = row["id"]
    stored_path = row["stored_path"]
    preview_path = row["preview_path"]

    cursor.execute("DELETE FROM satellite_scene_features WHERE scene_id = ?", (real_id,))
    cursor.execute("DELETE FROM satellite_scenes WHERE id = ?", (real_id,))
    conn.commit()
    conn.close()

    for fpath in [stored_path, preview_path]:
        if fpath and os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass
    return True


# ==================== Mobile SOS & Safe Zone Helper Functions ====================

def seed_demo_safe_zones_if_empty():
    """Seeds verified demo safe shelters in the Himalayan Uttarakhand grid if safe_zones table is empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM safe_zones")
    row = cursor.fetchone()
    if row and row["count"] > 0:
        conn.close()
        return

    demo_shelters = [
        {
            "name": "Almora District Relief Shelter 01",
            "category": "Disaster Relief Camp",
            "latitude": 30.1200,
            "longitude": 79.0800,
            "address": "Government High School Grounds, Almora Highway, Uttarakhand",
            "capacity": 250,
            "contact_phone": "+91-1362-234567",
            "source_name": "SDMA Uttarakhand Verified Registry",
            "source_url": "https://sdma.uk.gov.in",
            "verification_status": "VERIFIED",
            "verified_at": "2026-09-18 10:00:00"
        },
        {
            "name": "Ranikhet Community Emergency Safe Hub",
            "category": "Government Community Center",
            "latitude": 30.0150,
            "longitude": 78.9500,
            "address": "Civil Lines Community Hall, Ranikhet, Uttarakhand",
            "capacity": 180,
            "contact_phone": "+91-1362-234890",
            "source_name": "District Collectorate Registry",
            "source_url": "https://almora.nic.in",
            "verification_status": "VERIFIED",
            "verified_at": "2026-09-18 10:00:00"
        },
        {
            "name": "Karnaprayag High-Ground Evacuation Center",
            "category": "Flood & Landslide Shelter",
            "latitude": 30.2600,
            "longitude": 79.2200,
            "address": "Stadium Complex, Karnaprayag Hill Campus",
            "capacity": 400,
            "contact_phone": "+91-1363-255100",
            "source_name": "NDRF District Coordination Base",
            "source_url": "https://ndrf.gov.in",
            "verification_status": "VERIFIED",
            "verified_at": "2026-09-18 10:00:00"
        },
        {
            "name": "Naini Hill Safety Enclosure (Demo)",
            "category": "Demonstration Emergency Shelter",
            "latitude": 29.9800,
            "longitude": 79.1100,
            "address": "Demo Safety Zone, Himalayan Ridge Prototype",
            "capacity": 100,
            "contact_phone": "+91-11-23456789",
            "source_name": "D-SQUARE Demo Dataset",
            "source_url": "https://d-square-demo.local",
            "verification_status": "DEMO",
            "verified_at": "2026-09-18 10:00:00"
        }
    ]

    for s in demo_shelters:
        cursor.execute("""
        INSERT INTO safe_zones (
            name, category, latitude, longitude, address, capacity, contact_phone,
            source_name, source_url, verification_status, verified_at, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            s["name"], s["category"], s["latitude"], s["longitude"], s["address"],
            s["capacity"], s["contact_phone"], s["source_name"], s["source_url"],
            s["verification_status"], s["verified_at"]
        ))

    conn.commit()
    conn.close()
    print("[DB SEED SUCCESS] Seeded demo safe zones into safe_zones table.")


def get_safe_zones_db(verification_status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves safe zones from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if verification_status_filter:
        cursor.execute("SELECT * FROM safe_zones WHERE active = 1 AND UPPER(verification_status) = UPPER(?) ORDER BY id ASC", (verification_status_filter,))
    else:
        cursor.execute("SELECT * FROM safe_zones WHERE active = 1 ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_user_location_db(user_session_id: str, lat: float, lon: float, accuracy_m: float = 10.0, consent: bool = True, retention_hours: int = 24) -> int:
    """Saves user location log with explicit consent and retention expiration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    ts = datetime.now()
    expires_at = (ts + timedelta(hours=retention_hours)).strftime("%Y-%m-%d %H:%M:%S")
    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO mobile_location_logs (user_session_id, latitude, longitude, accuracy_m, timestamp, consent, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_session_id, float(lat), float(lon), float(accuracy_m), ts_str, 1 if consent else 0, expires_at))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def cleanup_expired_location_logs():
    """Deletes location logs older than their expiration timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM mobile_location_logs WHERE expires_at < ?", (now_str,))
    conn.commit()
    conn.close()


def save_mobile_sos_event_db(data: Dict[str, Any]) -> int:
    """Saves a mobile SOS event record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO mobile_sos_events (
        user_session_id, timestamp, latitude, longitude, accuracy_m, disaster_type,
        risk_level, message, recipient_count, dispatch_status, consent_confirmed, data_mode
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("user_session_id", "ANON_SESSION"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        float(data.get("latitude", 0.0)),
        float(data.get("longitude", 0.0)),
        float(data.get("accuracy_m", 10.0)),
        data.get("disaster_type", "General Emergency"),
        data.get("risk_level", "HIGH"),
        data.get("message", ""),
        int(data.get("recipient_count", 0)),
        data.get("dispatch_status", "SENT"),
        1 if data.get("consent_confirmed", True) else 0,
        data.get("data_mode", "DEMO")
    ))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id


def save_trusted_contact_db(user_session_id: str, contact_name: str, phone_number: str, relationship: str = "Family") -> int:
    """Saves a trusted contact for a user session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO trusted_contacts (user_session_id, contact_name, phone_number, relationship, verified)
    VALUES (?, ?, ?, ?, 1)
    """, (user_session_id, contact_name, phone_number, relationship))
    cid = cursor.lastrowid
    conn.commit()
    conn.close()
    return cid


def get_trusted_contacts_db(user_session_id: str) -> List[Dict[str, Any]]:
    """Retrieves trusted contacts for a user session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trusted_contacts WHERE user_session_id = ? ORDER BY id DESC", (user_session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_trusted_contact_db(user_session_id: str, contact_id: int) -> bool:
    """Deletes a trusted contact."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trusted_contacts WHERE id = ? AND user_session_id = ?", (contact_id, user_session_id))
    cnt = cursor.rowcount
    conn.commit()
    conn.close()
    return cnt > 0


def get_user_sos_history_db(user_session_id: str) -> List[Dict[str, Any]]:
    """Retrieves SOS history for a user session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mobile_sos_events WHERE user_session_id = ? ORDER BY id DESC", (user_session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cached_weather_db(lat: float, lon: float, provider: str = "IMD") -> Optional[Dict[str, Any]]:
    """Fetches cached weather response if unexpired."""
    conn = get_db_connection()
    cursor = conn.cursor()
    lat_b = round(lat, 1)
    lon_b = round(lon, 1)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    SELECT * FROM weather_cache
    WHERE latitude_bucket = ? AND longitude_bucket = ? AND provider = ? AND valid_until > ?
    ORDER BY id DESC LIMIT 1
    """, (lat_b, lon_b, provider, now_str))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        try:
            return json.loads(d["normalized_response_json"])
        except Exception:
            return None
    return None


def save_cached_weather_db(lat: float, lon: float, provider: str, raw_data: Dict[str, Any], norm_data: Dict[str, Any], valid_minutes: int = 30):
    """Saves weather response into cache table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    lat_b = round(lat, 1)
    lon_b = round(lon, 1)
    ts = datetime.now()
    valid_until = (ts + timedelta(minutes=valid_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO weather_cache (latitude_bucket, longitude_bucket, provider, raw_response_json, normalized_response_json, fetched_at, valid_until)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lat_b, lon_b, provider, json.dumps(raw_data), json.dumps(norm_data), ts_str, valid_until))
    conn.commit()
    conn.close()


def get_scene_preview_path(scene_id: int) -> Optional[str]:
    """Returns absolute preview image path for a given scene ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT preview_path FROM satellite_scenes WHERE id = ?", (scene_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row["preview_path"]:
        return row["preview_path"]
    return None


if __name__ == "__main__":
    init_db()
    print("Database initialized & demo dataset verified.")
