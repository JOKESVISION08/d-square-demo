# D-SQUARE 2.0 — Landslide SOS Software-Only Demo Mode Guide

## Hackathon Software-Only Demonstration Overview

This module provides a **Software-Only Demo Mode** for simulating a landslide emergency SOS alert using simulated ESP8266 sensor telemetry, without needing Arduino firmware compilation or hardware uploads.

---

## 1. Simulated ESP8266 Sensor Telemetry

When **Landslide** scenario is triggered, the system simulates the following ESP8266 telemetry state:
- **Node ID**: `SIMULATED_ESP8266_LANDSLIDE_01`
- **Capacitive Soil Moisture**: `88.0%` (High slope saturation)
- **DHT11 Temperature**: `25.8°C`
- **DHT11 Humidity**: `92.0%`
- **RGB Alert LED**: `RED` (Active alert)
- **Piezo Buzzer**: `ON` (Active audible alarm)
- **SW-420 Vibration**: `14.8 m/s²`
- **MPU6050 Tilt Angle**: `48.5°` (Slope tilt detected)

When **Normal** scenario is triggered, the telemetry resets to baseline:
- **Node ID**: `SIMULATED_ESP8266_NODE_01`
- **Soil Moisture**: `42.0%`
- **Temperature**: `26.5°C`
- **Humidity**: `52.0%`
- **RGB Alert LED**: `GREEN`
- **Piezo Buzzer**: `OFF`

---

## 2. Software Backend Endpoints

### 1. Trigger Landslide SOS Demo
```http
POST /api/demo/landslide-sos
Content-Type: application/json

{ "source": "dashboard_scenario_injector" }
```
**Response:**
```json
{
  "status": "success",
  "alert": {
    "active": true,
    "data_mode": "DEMO_SIMULATION",
    "disaster_type": "Landslide",
    "risk_level": "CRITICAL",
    "soil_moisture": 88.0,
    "temperature": 25.8,
    "humidity": 92.0,
    "led_state": "RED",
    "buzzer_state": "ON",
    "node_id": "SIMULATED_ESP8266_LANDSLIDE_01",
    "timestamp": "2026-09-18T23:00:00Z",
    "message": "DEMO: High soil moisture and humidity indicate simulated slope-instability risk. Follow official authority guidance in a real event."
  }
}
```

### 2. Reset Landslide SOS Demo
```http
POST /api/demo/reset-landslide-sos
Content-Type: application/json

{ "source": "dashboard_scenario_injector" }
```

### 3. Mobile Active Alert Status Polling
```http
GET /api/mobile/active-alert
```

---

## 3. Demonstration Workflow & Verification

1. **Launch Server**: Start Flask backend on port 5001:
   ```powershell
   .venv\Scripts\python.exe app.py
   ```
2. **Open Desktop Dashboard**: `http://127.0.0.1:5001/`
3. **Open Mobile SOS Application**: `http://127.0.0.1:5001/mobile_sos`
4. **Trigger Landslide**:
   - On the Desktop Dashboard, click the **Landslide** button in the *Live Scenario Test Injector* toolbar.
   - On the Mobile SOS page, verify the UI updates within 2 seconds:
     - Header displays `DEMO_SIMULATION` badge and `🚨 CRITICAL LANDSLIDE RISK (DEMO)`.
     - ESP8266 Telemetry card updates to Soil 88.0%, Temp 25.8°C, Hum 92.0%, LED RED, Buzzer ON, Node SIMULATED_ESP8266_LANDSLIDE_01.
     - Landslide escape rules card displays.
5. **Reset Alert**:
   - On the Desktop Dashboard, click the **Normal** button in the toolbar.
   - Mobile SOS page reverts to `🟢 AWAITING SIMULATED ALERT` within 2 seconds.

---

## 5. PC Ground Station Operator SOS Dispatch & D-SQUARE GPT Auto Guidance

1. **PC Dashboard Operator Dispatch Button**:
   - In `http://127.0.0.1:5001/`, click the red **🚨 DISPATCH SOS ALERT TO D-SQUARE GPT** button in the Live Scenario toolbar.
   - This dispatches an immediate Landslide emergency SOS alert wirelessly to D-SQUARE GPT (`/mobile_sos`).

2. **D-SQUARE GPT Auto Escape Guidance**:
   - As soon as D-SQUARE GPT receives an active alert from the ground station, an automated AI chat bubble appears in the conversation window providing:
     - Clear step-by-step escape steps perpendicular to the landslide path.
     - Evacuation route pointing to **Almora Evacuation Shelter** (3.4 km East).
     - Recommended 112 emergency calls and safety checks.

3. **1-Minute NISAR Frame Auto-Capture**:
   - The PC Dashboard automatically captures multi-modal satellite/camera pixel frames every 60 seconds via `POST /api/capture_nisar_frame` and stores them in `nisar/` (`c:\Users\WELCOME\Downloads\d-square demo\nisar`).

4. **ESP8266 C++ Hardware Code Modal**:
   - Open the **ESP8266 Firmware Modal** on `http://127.0.0.1:5001/` to copy either the **Hardware-Only C++ Landslide Detection Sketch** (`DHT11 D5/14, Soil A0 < 800, Green LED D1/5, Red LED D2/4, Buzzer D6/12`) or the complete 10-Sensor NodeMCU Firmware.

---

## 4. Safety & Hackathon Demonstration Rules

- **Persistent Warning Banner**: Displays `DEMO / SIMULATION MODE — NO REAL EMERGENCY ALERT HAS BEEN ISSUED` at all times on `/mobile_sos`.
- **No External SMS / Twilio Calls**: Dispatches zero SMS/WhatsApp messages during demo mode. Clicking *SIMULATE SOS TO TRUSTED CONTACTS* shows a local demo confirmation modal.
- **Desktop 112 Confirmation Modal**: Clicking *CALL 112 NOW* displays an informational notice confirming the test before opening native `tel:112`.
