"""
ESP8266 IoT Sensor Simulator for D-SQUARE 2.0
Streams 7 sensor parameters to Flask server endpoint (/api/sensor_data) every 5 seconds.
Scenarios supported: Normal, Forest_Fire, Flood, Landslide, Air_Pollution.
"""

import time
import requests
import random
import sys

SERVER_URL = "http://127.0.0.1:5001/api/sensor_data"

SCENARIOS = {
    "normal": {
        "temp": (24.0, 32.0),
        "hum": (45.0, 65.0),
        "smoke": (120, 280),
        "soil": (35.0, 55.0),
        "water": (2.0, 10.0),
        "flame": 0,
        "vibration": (0.05, 0.5),
        "tilt": (0.0, 4.0),
        "gyro": (0.0, 2.5),
        "tilt_state": 0,
        "vib_alarm": 0
    },
    "forest_fire": {
        "temp": (44.0, 68.0),
        "hum": (12.0, 25.0),
        "smoke": (680, 960),
        "soil": (2.0, 12.0),
        "water": (0.0, 5.0),
        "flame": 1,
        "vibration": (0.2, 1.2),
        "tilt": (1.0, 8.0),
        "gyro": (1.0, 6.0),
        "tilt_state": 0,
        "vib_alarm": 0
    },
    "flood": {
        "temp": (18.0, 24.0),
        "hum": (88.0, 98.0),
        "smoke": (150, 300),
        "soil": (90.0, 100.0),
        "water": (45.0, 110.0),
        "flame": 0,
        "vibration": (0.5, 2.5),
        "tilt": (3.0, 12.0),
        "gyro": (2.0, 10.0),
        "tilt_state": 0,
        "vib_alarm": 0
    },
    "landslide": {
        "temp": (16.0, 26.0),
        "hum": (75.0, 95.0),
        "smoke": (180, 350),
        "soil": (82.0, 98.0),
        "water": (15.0, 40.0),
        "flame": 0,
        "vibration": (7.5, 22.0),
        "tilt": (32.0, 78.0),
        "gyro": (45.0, 180.0),
        "tilt_state": 1,
        "vib_alarm": 1
    },
    "air_pollution": {
        "temp": (32.0, 41.0),
        "hum": (35.0, 55.0),
        "smoke": (750, 1000),
        "soil": (20.0, 40.0),
        "water": (2.0, 15.0),
        "flame": 0,
        "vibration": (0.1, 0.8),
        "tilt": (0.0, 5.0),
        "gyro": (0.0, 3.0),
        "tilt_state": 0,
        "vib_alarm": 0
    }
}

def generate_sensor_reading(scenario_name: str = "normal"):
    cfg = SCENARIOS.get(scenario_name.lower(), SCENARIOS["normal"])

    temp = round(random.uniform(cfg["temp"][0], cfg["temp"][1]), 1)
    hum = round(random.uniform(cfg["hum"][0], cfg["hum"][1]), 1)
    smoke = round(random.uniform(cfg["smoke"][0], cfg["smoke"][1]), 1)
    soil = round(random.uniform(cfg["soil"][0], cfg["soil"][1]), 1)
    water = round(random.uniform(cfg["water"][0], cfg["water"][1]), 1)
    flame = cfg["flame"]
    vib = round(random.uniform(cfg["vibration"][0], cfg["vibration"][1]), 2)
    tilt = round(random.uniform(cfg["tilt"][0], cfg["tilt"][1]), 1)
    gyro = round(random.uniform(cfg["gyro"][0], cfg["gyro"][1]), 1)
    tilt_state = cfg["tilt_state"]
    vib_alarm = cfg["vib_alarm"]

    return {
        "temperature": temp,
        "humidity": hum,
        "smoke": smoke,
        "soil_moisture": soil,
        "water_level": water,
        "flame": flame,
        "vibration": vib,
        "tilt_angle": tilt,
        "gyro_rate": gyro,
        "tilt_state": tilt_state,
        "vibration_alarm": vib_alarm,
        "node_id": "ESP8266_SIMULATOR_01",
        "scenario": scenario_name
    }

def run_simulator(scenario: str = "normal", interval_sec: float = 5.0, duration_cycles: int = 100):
    print(f"Starting ESP8266 Sensor Simulator [Scenario: {scenario.upper()}]...")
    print(f"Target Server: {SERVER_URL} (Interval: {interval_sec}s)")

    for cycle in range(1, duration_cycles + 1):
        payload = generate_sensor_reading(scenario)
        try:
            res = requests.post(SERVER_URL, json=payload, timeout=3.0)
            print(f"[{time.strftime('%H:%M:%S')}] Cycle {cycle}: Sent {payload['scenario']} -> Status {res.status_code}")
            if res.status_code == 200:
                data = res.json()
                print(f"   -> Fusion Prediction: {data.get('predicted_disaster')} | Risk: {data.get('risk_level')} ({data.get('disaster_probability_percent')}%)")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Cycle {cycle}: Server connection pending ({e})")

        time.sleep(interval_sec)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "normal"
    run_simulator(scenario=mode)
