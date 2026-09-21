# Hardware Wiring Diagram & Itemized Bill of Materials (BOM)

## D-SQUARE 2.0 IoT Ground Node Architecture (10 Sensors + Controls)

The D-SQUARE 2.0 ground node uses an ESP8266 NodeMCU microcontroller connected to 10 environmental/structural sensors and 2 local alert indicators (Red/Green LED and Piezo Buzzer).

```
 +-------------------------------------------------------------------------+
 |                   ESP8266 NodeMCU Pin Schematic                         |
 |                                                                         |
 |  [D5 / GPIO14] <---> DHT11 Temperature & Humidity Sensor                |
 |  [A0 / Analog] <---> Capacitive Soil Moisture Sensor Analog Output      |
 |  [D0 / GPIO16] <---> Soil Sensor Power Control (Corrosion Prevention)   |
 |  [RX / GPIO10] <---> MQ-2 Smoke & Gas Digital Output                    |
 |  [D6 / GPIO12] <---> SW-420 Digital Vibration Sensor                    |
 |  [D7 / GPIO13] <---> SW-520D Ball Tilt Sensor Switch                    |
 |  [D8 / GPIO15] <---> HC-SR04 Ultrasonic Trigger Pin                     |
 |  [RX / GPIO3]  <---> HC-SR04 Ultrasonic Echo Pin                        |
 |  [D2 / GPIO4]  <---> MPU6050 I2C SDA (Tilt Angle & Gyro Rate)           |
 |  [D1 / GPIO5]  <---> MPU6050 I2C SCL (3-Axis Acceleration)             |
 |  [TX / GPIO1]  <---> Red Alert LED (Active LOW)                         |
 |  [D4 / GPIO2]  <---> Green Status LED (Active LOW)                      |
 |  [D3 / GPIO0]  <---> Active Piezo Buzzer (Active LOW Alarm)             |
 |  [3V3 / 5V]    <---> Common VCC Rail                                    |
 |  [GND]         <---> Common Ground Rail                                 |
 +-------------------------------------------------------------------------+
```

---

## Detailed Pin Connection Table

| Sensor / Module | Sensor Pin | ESP8266 NodeMCU Pin | Voltage | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **ESP8266 NodeMCU** | USB / Vin | 5V / USB Power | 5V DC | Micro-USB or 5V Adapter |
| **DHT11** | VCC, Data, GND | 3.3V, D5 (GPIO14), GND | 3.3V | Temperature & Humidity |
| **Capacitive Soil Moisture Probe** | VCC, AO, GND | D0 (GPIO16 Power), A0 (Analog), GND | 3.3V | Volumetric Water Content (0-100%) |
| **MQ-2 Smoke & Gas** | VCC, DO, GND | 5V, RX (GPIO10 Digital), GND | 5V | Gas/LPG/Smoke Detection |
| **SW-420 Vibration** | VCC, DO, GND | 3.3V/5V, D6 (GPIO12), GND | 3.3V | Piezo Vibration Shock Pulse |
| **SW-520D Tilt Switch** | VCC, DO, GND | 3.3V, D7 (GPIO13), GND | 3.3V | Mechanical Roll/Tilt Contact Switch |
| **HC-SR04 Water Level** | VCC, Trig, Echo, GND | 5V, D8 (Trig GPIO15), RX (Echo GPIO3), GND | 5V | Ultrasonic Water Level Measurement |
| **MPU6050 Gyro/Accel** | VCC, SDA, SCL, GND | 3.3V, D2 (SDA GPIO4), D1 (SCL GPIO5), GND | 3.3V | 6-DOF Tilt Angle & Gyro Angular Rates |
| **Red Alert LED** | Anode (+), Cathode | TX (GPIO1), GND (via 220Ω) | 3.3V | Alert Indicator (Active LOW) |
| **Green Status LED** | Anode (+), Cathode | D4 (GPIO2), GND (via 220Ω) | 3.3V | Normal Status (Active LOW) |
| **Piezo Buzzer** | Signal (+), Ground | D3 (GPIO0), GND | 3.3V | 1kHz Audible Alarm (Active LOW) |

---

## Itemized Bill of Materials (BOM) & Budget Breakdown

| Item No. | Component Description | Quantity | Unit Price (INR) | Total Cost (INR) |
| :---: | :--- | :---: | :---: | :---: |
| 1 | ESP8266 NodeMCU V3 WiFi Board | 1 | ₹350 | ₹350 |
| 2 | DHT11 Temperature & Humidity Sensor | 1 | ₹120 | ₹120 |
| 3 | Capacitive Soil Moisture Sensor Probe v1.2 | 1 | ₹80 | ₹80 |
| 4 | MQ-2 Gas & Smoke Detector Module | 1 | ₹180 | ₹180 |
| 5 | MPU6050 6-Axis Gyro/Accelerometer Module | 1 | ₹190 | ₹190 |
| 6 | SW-420 Vibration Sensor Module | 1 | ₹70 | ₹70 |
| 7 | SW-520D Tilt Sensor Ball Switch Module | 1 | ₹50 | ₹50 |
| 8 | HC-SR04 Ultrasonic Sensor Module | 1 | ₹110 | ₹110 |
| 9 | Active Piezo Buzzer (5V) | 1 | ₹30 | ₹30 |
| 10 | RGB LED Pack + 220Ω Resistors | 2 | ₹20 | ₹40 |
| 11 | MB-102 Breadboard & Jumper Wires | 1 | ₹160 | ₹160 |
| 12 | 5V 2A USB Power Cable | 1 | ₹200 | ₹200 |
| **TOTAL** | **Hardware Prototype Cost** | **13 Items** | -- | **₹1580** |
