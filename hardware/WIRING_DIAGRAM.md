# D-SQUARE 2.0 Hardware Wiring Diagram & Connection Guide

## D-SQUARE IoT Ground Telemetry Station (ESP8266 NodeMCU)

This wiring layout matches the **Live Ground Telemetry Dashboard** sensors and pin assignments.

```
 +-------------------------------------------------------------------------+
 |             ESP8266 NodeMCU Hardware Pin Connection Schematic           |
 |                                                                         |
 |  [D5 / GPIO14] <---> DHT11 Temperature & Humidity Sensor Data           |
 |  [A0 / Analog] <---> Capacitive Soil Moisture Sensor Analog Output (ADC)|
 |  [D6 / GPIO12] <---> MQ-2 Smoke & Gas Detector Digital Output           |
 |  [D7 / GPIO13] <---> SW-520D Tilt Sensor Switch Digital Output          |
 |  [D8 / GPIO15] <---> 801S Vibration Sensor Digital Output               |
 |  [D2 / GPIO4]  <---> IR Flame Sensor Digital Output                     |
 |  [D1 / GPIO5]  <---> Green Status LED (Normal Operation)                |
 |  [D3 / GPIO0]  <---> Red Alert LED & Active Piezo Buzzer                |
 |  [3V3 / 5V]    <---> VCC Power Rails (3.3V for Sensors / 5V for MQ2)    |
 |  [GND]         <---> Common Ground (GND) Rail                           |
 +-------------------------------------------------------------------------+
```

---

## Complete Sensor Connection Table

| Sensor Card in Dashboard | Physical Sensor Model | Sensor Pin | ESP8266 NodeMCU Pin | Power Rail | Notes / Logic |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Temperature** | DHT11 | VCC, Data, GND | **3.3V, D5 (GPIO14), GND** | 3.3V DC | Temperature (°C) Range: 0–50°C |
| **Humidity** | DHT11 | VCC, Data, GND | **3.3V, D5 (GPIO14), GND** | 3.3V DC | Relative Humidity (40–70% Optimal) |
| **Soil Moisture** | Capacitive Probe v1.2 | VCC, AO, GND | **3.3V, A0 (ADC0), GND** | 3.3V DC | Raw ADC: 850 (Dry) to 350 (Wet) |
| **MQ2 Gas/Smoke** | MQ-2 Module | VCC, DO, GND | **5V, D6 (GPIO12), GND** | 5V DC | HIGH = Smoke/LPG Gas Detected |
| **Tilt Sensor** | SW-520D Ball Switch | VCC, DO, GND | **3.3V, D7 (GPIO13), GND** | 3.3V DC | LOW = Slope Tilt / Unstable |
| **Vibration** | 801S Shock Sensor | VCC, DO, GND | **3.3V, D8 (GPIO15), GND** | 3.3V DC | HIGH = Seismic Tremor / Vibration |
| **Flame Sensor** | IR Flame Detector | VCC, DO, GND | **3.3V, D2 (GPIO4), GND** | 3.3V DC | LOW = Infrared Flame Detected |
| **Green Status LED** | 5mm Green LED | Anode (+), Cathode (-) | **D1 (GPIO5)**, GND via 220Ω | 3.3V DC | ON = System Normal |
| **Red Alert LED & Buzzer**| 5mm Red LED + Buzzer| Anode (+), Cathode (-) | **D3 (GPIO0)**, GND via 220Ω | 3.3V DC | ON = Hazard Alert Activated |

---

## Arduino IDE Flashing Instructions

1. Open Arduino IDE and install the **ESP8266 Board Package** (`http://arduino.esp8266.com/stable/package_esp8266com_index.json`).
2. Go to **Sketch** -> **Include Library** -> **Manage Libraries** and install the **DHT sensor library** by Adafruit.
3. Open [`esp8266_landslide_wireless.ino`](file:///c:/Users/WELCOME/Downloads/d-square%20demo/esp8266_landslide_wireless.ino).
4. Enter your WiFi credentials:
   ```cpp
   const char* ssid     = "YOUR_WIFI_NAME";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
5. Select Board: **NodeMCU 1.0 (ESP-12E Module)** and Port.
6. Click **Upload**.
