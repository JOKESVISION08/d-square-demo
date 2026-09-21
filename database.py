"""
Database Manager for D-SQUARE 2.0
SQLite persistence for multi-node sensor logs, disaster alerts, JWT users, rescue teams,
and satellite pixel observations.
"""

import sqlite3
import os
import time
import json
import tempfile
import shutil
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

SEED_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disasters.db")


def get_db_file():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        test_file = os.path.join(base_dir, ".db_write_test")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return SEED_DB_FILE
    except (OSError, PermissionError):
        tmp_db = os.path.join(tempfile.gettempdir(), "dsquare_disasters.db")
        if not os.path.exists(tmp_db) and os.path.exists(SEED_DB_FILE):
            try:
                shutil.copyfile(SEED_DB_FILE, tmp_db)
            except Exception:
                pass
        return tmp_db


DB_FILE = SEED_DB_FILE


def get_db_connection():
    target_db = get_db_file()
    conn = sqlite3.connect(target_db)
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
        data_mode TEXT NOT NULL DEFAULT 'DEMO_SIMULATION',
        message TEXT,
        soil_moisture REAL,
        temperature REAL,
        humidity REAL
    )
    """)

    # Multi-node Sensor Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        node_id TEXT NOT NULL,
        temperature REAL,
        humidity REAL,
        smoke REAL,
        soil_moisture REAL,
        soil_raw REAL,
        water_level REAL,
        flame REAL,
        vibration REAL,
        tilt_angle REAL,
        gyro_x REAL,
        gyro_y REAL,
        gyro_z REAL,
        data_mode TEXT NOT NULL DEFAULT 'DEMO_SIMULATION'
    )
    """)

    # Active Nodes Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_nodes (
        node_id TEXT PRIMARY KEY,
        location TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        last_seen TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ONLINE'
    )
    """)

    # JWT Users & Registered Citizens Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'RESCUE_TEAM',
        email TEXT,
        phone TEXT,
        latitude REAL DEFAULT 19.0760,
        longitude REAL DEFAULT 72.8777,
        app_installed INTEGER DEFAULT 1,
        sms_subscribed INTEGER DEFAULT 1,
        whatsapp_subscribed INTEGER DEFAULT 1
    )
    """)

    for col_name, col_type in [
        ("user_id", "TEXT"),
        ("latitude", "REAL DEFAULT 19.0760"),
        ("longitude", "REAL DEFAULT 72.8777"),
        ("app_installed", "INTEGER DEFAULT 1"),
        ("sms_subscribed", "INTEGER DEFAULT 1"),
        ("whatsapp_subscribed", "INTEGER DEFAULT 1")
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass

    # Rescue Teams Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rescue_teams (
        team_id TEXT PRIMARY KEY,
        team_name TEXT NOT NULL,
        team_type TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'AVAILABLE',
        assigned_alert_id INTEGER
    )
    """)

    # Rescue Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rescue_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        alert_id INTEGER,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        trapped_count INTEGER DEFAULT 1,
        priority TEXT NOT NULL DEFAULT 'MEDIUM',
        status TEXT NOT NULL DEFAULT 'PENDING',
        assigned_team_id TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Alert Delivery Channel Recipients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alert_recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        delivery_channel TEXT NOT NULL,
        delivery_status TEXT NOT NULL,
        delivered_at TEXT
    )
    """)

    # Mobile SOS Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sos_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        user_id TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        disaster_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING'
    )
    """)

    # Multi-Parameter Disaster Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disaster_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        disaster_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        confidence REAL NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        location_name TEXT NOT NULL,
        parameters_triggered TEXT NOT NULL,
        recommended_actions TEXT NOT NULL
    )
    """)

    # Parallel SOS Alerts Table (Rescue GPT + D-SQUARE GPT)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parallel_sos_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        disaster_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        area_name TEXT NOT NULL,
        affected_population INTEGER NOT NULL,
        rescue_payload TEXT NOT NULL,
        public_payload TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'DISPATCHED'
    )
    """)

    # Emergency Shelters Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shelters (
        shelter_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        capacity INTEGER NOT NULL,
        available_beds INTEGER NOT NULL,
        contact_number TEXT NOT NULL,
        facilities TEXT NOT NULL
    )
    """)

    # Rescue Resources & Fleet Allocation Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rescue_resources (
        resource_id TEXT PRIMARY KEY,
        resource_type TEXT NOT NULL,
        assigned_area TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'AVAILABLE',
        quantity INTEGER NOT NULL,
        last_updated TEXT NOT NULL
    )
    """)

    # Model Performance & Calibration Metrics Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        model_name TEXT NOT NULL,
        disaster_type TEXT NOT NULL,
        precision_score REAL NOT NULL,
        recall_score REAL NOT NULL,
        f1_score REAL NOT NULL,
        total_evaluations INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()
    seed_default_nodes_and_users()


def seed_default_nodes_and_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Default node registration
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT OR REPLACE INTO active_nodes (node_id, location, latitude, longitude, last_seen, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("D-SQUARE_NODE_01", "Uttarakhand Slope Sector 4", 30.0668, 79.0193, now_str, "ONLINE"))

    # Default rescue team user & registered citizens
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] <= 1:
        cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, username, password_hash, role, email, phone, latitude, longitude, app_installed, sms_subscribed, whatsapp_subscribed)
        VALUES ('USR_001', 'admin', 'admin123_hash', 'RESCUE_TEAM', 'rescue@dsquare.org', '+919876543210', 19.0760, 72.8777, 1, 1, 1)
        """)
        citizens = [
            ('USR_002', 'aarav_sharma', 'pass123', 'CITIZEN', 'aarav@example.com', '+919811122233', 19.0800, 72.8800, 1, 1, 1),
            ('USR_003', 'priya_patel', 'pass123', 'CITIZEN', 'priya@example.com', '+919822233344', 19.0820, 72.8850, 1, 1, 0),
            ('USR_004', 'rajesh_kumar', 'pass123', 'CITIZEN', 'rajesh@example.com', '+919833344455', 30.0680, 79.0200, 0, 1, 1),
            ('USR_005', 'sunita_verma', 'pass123', 'CITIZEN', 'sunita@example.com', '+919844455566', 30.0700, 79.0250, 1, 0, 1)
        ]
        cursor.executemany("""
        INSERT OR REPLACE INTO users (user_id, username, password_hash, role, email, phone, latitude, longitude, app_installed, sms_subscribed, whatsapp_subscribed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, citizens)

    # Seed Rescue Teams
    cursor.execute("SELECT COUNT(*) FROM rescue_teams")
    if cursor.fetchone()[0] == 0:
        teams_data = [
            ("TEAM_NDRF_01", "NDRF Alpha Squad", "NDRF_RESCUE", 19.0750, 72.8750, "AVAILABLE", None),
            ("TEAM_BOAT_02", "Coast Guard Boat Unit 2", "BOAT_RESCUE", 19.0850, 72.8900, "AVAILABLE", None),
            ("TEAM_FIRE_01", "City Fire Tenders Unit", "FIRE_ENGINE", 30.0650, 79.0180, "AVAILABLE", None)
        ]
        cursor.executemany("""
        INSERT INTO rescue_teams (team_id, team_name, team_type, latitude, longitude, status, assigned_alert_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, teams_data)

    # Seed Emergency Shelters
    cursor.execute("SELECT COUNT(*) FROM shelters")
    if cursor.fetchone()[0] == 0:
        shelters_data = [
            ("SHELTER_01", "School XYZ Community Hall & Relief Center", "124 High Ground Sector 4, Uttarakhand", 30.0820, 79.0310, 500, 320, "+91-1372-252100", "Medical Triage, Food Rations, Water, Generator"),
            ("SHELTER_02", "Gopeshwar Disaster Relief HQ", "Gopeshwar Town Center, District Chamoli", 30.0500, 79.0050, 800, 550, "+91-1372-252200", "ICU Beds, Helicopter Pad, Amphibious Fleet, Solar Power"),
            ("SHELTER_03", "Mumbai Coastal High Ground Refuge", "Marine Drive Relief Complex, Mumbai", 19.0910, 72.8920, 1000, 650, "+91-22-28491000", "NDRF Boat Docks, Triage Camp, Sanitation Kits")
        ]
        cursor.executemany("""
        INSERT INTO shelters (shelter_id, name, address, latitude, longitude, capacity, available_beds, contact_number, facilities)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, shelters_data)

    # Seed Rescue Resources Fleet
    cursor.execute("SELECT COUNT(*) FROM rescue_resources")
    if cursor.fetchone()[0] == 0:
        resources_data = [
            ("RES_BOAT_01", "Motorized Inflatable Rescue Boats", "Mumbai Coastal Zone", "DEPLOYED", 12, now_str),
            ("RES_AMB_01", "Advanced Life Support Ambulances", "Uttarakhand Slope Sector 4", "AVAILABLE", 8, now_str),
            ("RES_FIRE_01", "Heavy Foam Fire Tenders", "Chamoli Industrial Area", "STANDBY", 6, now_str),
            ("RES_NDRF_01", "NDRF Search & Rescue Personnel Teams", "Gopeshwar HQ", "DEPLOYED", 45, now_str)
        ]
        cursor.executemany("""
        INSERT INTO rescue_resources (resource_id, resource_type, assigned_area, status, quantity, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
        """, resources_data)

    # Seed Model Performance Metrics
    cursor.execute("SELECT COUNT(*) FROM model_performance")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO model_performance (timestamp, model_name, disaster_type, precision_score, recall_score, f1_score, total_evaluations)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now_str, "MultiParameterFusionModel_v2.0", "FLOOD_FIRE_LANDSLIDE", 0.925, 0.890, 0.907, 1250))

    conn.commit()
    conn.close()


def save_parallel_sos_alert(alert_res: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rescue = alert_res.get("rescue_gpt_alert", {})
    public = alert_res.get("dsquare_gpt_alert", {})

    loc = rescue.get("location", {})
    lat = float(loc.get("latitude", 19.0760))
    lon = float(loc.get("longitude", 72.8777))
    area = loc.get("area_name", "Mumbai Coastal Restricted Zone")

    cursor.execute("""
    INSERT INTO parallel_sos_alerts (
        timestamp, disaster_type, severity, latitude, longitude, area_name,
        affected_population, rescue_payload, public_payload, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'DISPATCHED')
    """, (
        now_str,
        rescue.get("disaster_type", "FLOOD"),
        rescue.get("severity", "HIGH"),
        lat,
        lon,
        area,
        int(rescue.get("affected_population", 5000)),
        json.dumps(rescue),
        json.dumps(public)
    ))

    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id


def clear_all_parallel_sos_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM parallel_sos_alerts")
    cursor.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()


def get_active_parallel_alerts(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM parallel_sos_alerts
    ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        item = dict(r)
        try:
            item["rescue_payload"] = json.loads(item["rescue_payload"])
            item["public_payload"] = json.loads(item["public_payload"])
        except Exception:
            pass
        result.append(item)
    return result


def get_shelters_list() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shelters ORDER BY available_beds DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_rescue_resources_list() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rescue_resources ORDER BY last_updated DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_sensor_log(log_dict: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    node_id = log_dict.get("node_id", "D-SQUARE_NODE_01")
    cursor.execute("""
    INSERT INTO sensor_logs (
        timestamp, node_id, temperature, humidity, smoke, soil_moisture, soil_raw,
        water_level, flame, vibration, tilt_angle, gyro_x, gyro_y, gyro_z, data_mode
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now_str,
        node_id,
        log_dict.get("temperature", 25.0),
        log_dict.get("humidity", 50.0),
        log_dict.get("smoke", 0.0),
        log_dict.get("soil_moisture", 40.0),
        log_dict.get("soil_raw", 850.0),
        log_dict.get("water_level", 0.0),
        log_dict.get("flame", 0.0),
        log_dict.get("vibration", 0.0),
        log_dict.get("tilt_angle", 0.0),
        log_dict.get("gyro_x", 0.0),
        log_dict.get("gyro_y", 0.0),
        log_dict.get("gyro_z", 0.0),
        log_dict.get("data_mode", "VERIFIED_HARDWARE")
    ))

    # Update active nodes
    cursor.execute("""
    INSERT OR REPLACE INTO active_nodes (node_id, location, latitude, longitude, last_seen, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (node_id, "Uttarakhand Himalayan Station", 30.0668, 79.0193, now_str, "ONLINE"))

    conn.commit()
    conn.close()


def get_historical_sensor_logs(node_id: str = "D-SQUARE_NODE_01", hours: int = 24) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM sensor_logs 
    WHERE node_id = ? 
    ORDER BY id DESC LIMIT 100
    """, (node_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_nodes() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM active_nodes")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_sos_request(user_id: str, lat: float, lon: float, disaster_type: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO sos_requests (timestamp, user_id, latitude, longitude, disaster_type, status)
    VALUES (?, ?, ?, ?, ?, 'PENDING')
    """, (now_str, user_id, lat, lon, disaster_type))
    sos_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sos_id


init_db()
