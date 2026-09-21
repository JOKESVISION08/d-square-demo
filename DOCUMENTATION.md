# D-SQUARE 2.0 - Production-Ready Multi-Disaster AI System Documentation

---

## 1. System Overview

D-SQUARE 2.0 is an advanced Quadruple AI Disaster Surveillance and Emergency Rescue Platform combining:
1. **IoT Ground Telemetry Nodes**: ESP8266/ESP32 microcontrollers with 10 integrated sensors.
2. **PyTorch Deep Learning Cloud Removal AI**: Reconstructs cloud-covered Sentinel-2/Landsat-8 optical satellite imagery.
3. **ISRO Bhuvan / GPM Satellite Anomaly Pipeline**: Computes 5-year historical rainfall anomalies.
4. **Machine Learning Monsoon Engine**: Random Forest ML model forecasting 48-hour disaster risk.
5. **D-SQUARE GPT Safety Assistant**: OpenAI/Gemini LLM reasoning over ground & satellite context.
6. **Voice-Guided Rescue AI**: Turn-by-turn evacuation routing integrating Google Maps API.
7. **Mobile SOS & Emergency System**: 1-click location dispatch and safe zone navigation.
8. **Netlify-Ready Dashboard**: Responsive single-page dashboard featuring real-time cards, trends, and maps.

---

## 2. Hardware Wiring & Pin Mapping

### Component Connection Matrix (ESP8266 NodeMCU)
| Sensor / Component | ESP8266 Pin | GPIO Pin | Function / Type |
| :--- | :--- | :--- | :--- |
| **Capacitive Soil Moisture** | `A0` | `ADC0` | Analog soil wetness (0-1024) |
| **DHT11 Temp & Humidity** | `D5` | `GPIO14` | Digital Temperature & Humidity |
| **MQ2 Gas & Smoke** | `D6` | `GPIO12` | Digital/Analog Gas Leak Detection |
| **Tilt Sensor** | `D7` | `GPIO13` | Digital Slope Displacement |
| **Vibration Sensor** | `D8` | `GPIO15` | Digital Seismic / Structural Motion |
| **Flame Sensor** | `RX` | `GPIO3` | Digital Infrared Flame Signal |
| **MPU6050 (SDA)** | `D1` | `GPIO5` | I2C Serial Data (Accel/Gyro) |
| **MPU6050 (SCL)** | `D2` | `GPIO4` | I2C Serial Clock |
| **Green Status LED** | `D3` | `GPIO0` | Normal Operation Indicator |
| **Red Alert LED** | `D4` | `GPIO2` | Critical Disaster Alert Indicator |
| **Buzzer** | `D0` | `GPIO16` | Audible Alarm (1000 Hz Tone) |

---

## 3. Firmware Upload Instructions (Arduino IDE)

1. Open **Arduino IDE**.
2. Navigate to **File > Preferences** and add ESP8266 board manager URL:
   `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
3. Go to **Tools > Board > Board Manager**, search for `esp8266` and install.
4. Open [`hardware/esp8266_sensors.ino`](file:///c:/Users/WELCOME/Downloads/d-square%20demo/hardware/esp8266_sensors.ino) or [`esp8266_landslide_wireless.ino`](file:///c:/Users/WELCOME/Downloads/d-square%20demo/esp8266_landslide_wireless.ino).
5. Update your WiFi credentials:
   ```cpp
   const char* ssid     = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
6. Select **NodeMCU 1.0 (ESP-12E Module)** under **Tools > Board**.
7. Connect NodeMCU via USB and click **Upload**.

---

## 4. Backend Server Setup & API Reference

### Local Setup
1. Activate Virtual Environment:
   ```powershell
   .venv\Scripts\python.exe app.py
   ```
2. The server runs on `http://127.0.0.1:5001`.

### Key API Endpoints
- **POST `/api/sensor_data`**: Receive ESP8266 hardware telemetry.
- **GET `/api/latest_sensor_data`**: Returns latest multi-sensor readings.
- **GET `/api/historical_data?node_id=XXX&hours=24`**: Returns historical telemetry logs for charts.
- **POST `/api/auth/login`**: Authenticate rescue team members (JWT).
- **GET `/api/satellite_prediction?scenario=landslide`**: Returns rainfall anomaly percentages.
- **GET `/api/cloud_removed_image`**: Serves PyTorch U-Net cloud-removed optical imagery.
- **POST `/api/chat`**: Send natural language query to D-SQUARE GPT.
- **POST `/api/rescue_route`**: Voice-guided turn-by-turn evacuation instructions.
- **POST `/api/sos`**: Mobile 1-click emergency location dispatch.
- **GET `/api/monsoon_prediction?region=Uttarakhand`**: Random Forest ML 48-hour rainfall forecast.

---

## 5. Deployment Guide

### Deploying Frontend to Netlify
1. Log into **Netlify** (netlify.com).
2. Drag and drop the workspace root directory (containing [`index.html`](file:///c:/Users/WELCOME/Downloads/d-square%20demo/index.html) and [`mobile_sos/index.html`](file:///c:/Users/WELCOME/Downloads/d-square%20demo/mobile_sos/index.html)).
3. Netlify will deploy your responsive dashboard instantly.

### Deploying Backend to Render / Cloud
1. Connect your GitHub repository (`JOKESVISION08/d-square-demo`).
2. Create a **Web Service** on **Render.com**.
3. Environment: `Python 3`.
4. Build Command: `pip install -r requirements.txt`.
5. Start Command: `gunicorn app:app`.

---

## 6. Verification & Automated Tests
Execute the full unit test suite:
```powershell
.venv\Scripts\python.exe test_all_features.py
.venv\Scripts\python.exe test_mobile_sos.py
```
Both test suites verify 22 unit & integration endpoints with 100% pass rate.
