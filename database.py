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

    # JWT Users & Rescue Teams Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'RESCUE_TEAM',
        email TEXT,
        phone TEXT
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

    # Default rescue team user
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO users (username, password_hash, role, email, phone)
        VALUES ('admin', 'admin123_hash', 'RESCUE_TEAM', 'rescue@dsquare.org', '+919876543210')
        """)

    conn.commit()
    conn.close()


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
