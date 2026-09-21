/*
  D-SQUARE 2.0 - Complete IoT Ground Station Node Firmware (6 Sensors + Alerts)
  Matches D-SQUARE Live Telemetry Dashboard Pinout:

  Pin Mapping:
  - DHT11 Temp & Humidity      -> D5 (GPIO14)
  - Capacitive Soil Moisture   -> A0 (Analog ADC)
  - MQ-2 Gas & Smoke           -> D6 (GPIO12)
  - SW-520D Tilt Sensor        -> D7 (GPIO13)
  - 801S Vibration Sensor      -> D8 (GPIO15)
  - IR Flame Sensor            -> D2 (GPIO4)
  - Status Indicators (LED/Buzzer):
      • Green Status LED       -> D1 (GPIO5) via 220Ω
      • Red Alert LED / Buzzer -> D3 (GPIO0) via 220Ω

  Sends JSON HTTP POST telemetry payload to D-SQUARE Server (/api/sensor_data).
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

// ---------- WiFi & Backend Server Settings ----------
const char* ssid     = "Joke";                     // Replace with your WiFi SSID
const char* password = "Joke@2005";                // Replace with your WiFi Password

// Primary Backend Server URL (Cloudflare Tunnel or Local IP e.g. http://192.168.1.100:5001/api/sensor_data)
const char* serverUrl = "https://competitors-insert-peas-above.trycloudflare.com/api/sensor_data";

// ---------- Pin Definitions (Matching Telemetry Dashboard) ----------
#define DHT_PIN          14   // D5 / GPIO14 (DHT11 Temp & Humidity)
#define DHT_TYPE         DHT11

#define SOIL_PIN         A0   // A0 / ADC0 (Capacitive Soil Moisture Analog)

#define MQ2_PIN          12   // D6 / GPIO12 (MQ2 Gas/Smoke Digital Output)
#define TILT_PIN         13   // D7 / GPIO13 (SW-520D Tilt Switch Digital Output)
#define VIBRATION_PIN    15   // D8 / GPIO15 (801S Vibration Digital Output)
#define FLAME_PIN        4    // D2 / GPIO4  (IR Flame Digital Output - Active LOW/HIGH)

#define GREEN_LED_PIN    5    // D1 / GPIO5  (Normal Status LED)
#define RED_ALERT_PIN    0    // D3 / GPIO0  (Red Alert LED & Active Buzzer)

// ---------- Thresholds ----------
const int SOIL_DRY_RAW = 850;
const int SOIL_WET_RAW = 350;

DHT dht(DHT_PIN, DHT_TYPE);

void connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected Successfully!");
    Serial.print("Node IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n⚠️ WiFi Connection Timeout! Standalone Alert Mode Active.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Pin Modes
  pinMode(MQ2_PIN, INPUT);
  pinMode(TILT_PIN, INPUT_PULLUP);
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_ALERT_PIN, OUTPUT);

  // Default LED state
  digitalWrite(GREEN_LED_PIN, HIGH);
  digitalWrite(RED_ALERT_PIN, LOW);

  dht.begin();

  Serial.println();
  Serial.println("=================================================");
  Serial.println(" D-SQUARE 2.0 IoT Ground Telemetry Node Initialized");
  Serial.println(" 6 Sensor Channels Connected & Monitoring Active ");
  Serial.println("=================================================");

  connectToWiFi();
}

void sendTelemetryToServer(float temp, float hum, int soilRaw, float soilPct, int mq2Gas, int tilt, int vibration, int flame, bool isAlert) {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  WiFiClientSecure client;
  client.setInsecure(); // Bypass SSL verification for HTTPS tunnel
  HTTPClient http;

  String scenarioStr = isAlert ? "hazard_alert" : "normal";
  String disasterStr = "none";

  if (flame == 1) disasterStr = "fire";
  else if (tilt == 1 || vibration == 1) disasterStr = "landslide";
  else if (soilRaw < 450) disasterStr = "flood";
  else if (mq2Gas == 1) disasterStr = "fire";

  // Construct JSON Payload matching Flask backend app.py
  String jsonPayload = "{";
  jsonPayload += "\"node_id\":\"D-SQUARE_NODE_01\",";
  jsonPayload += "\"temperature\":" + String(isnan(temp) ? 25.0 : temp, 1) + ",";
  jsonPayload += "\"humidity\":" + String(isnan(hum) ? 50.0 : hum, 1) + ",";
  jsonPayload += "\"soil_moisture\":" + String(soilPct, 1) + ",";
  jsonPayload += "\"soil_raw\":" + String(soilRaw) + ",";
  jsonPayload += "\"mq2_gas\":" + String(mq2Gas) + ",";
  jsonPayload += "\"tilt\":" + String(tilt) + ",";
  jsonPayload += "\"vibration\":" + String(vibration) + ",";
  jsonPayload += "\"flame\":" + String(flame) + ",";
  jsonPayload += "\"disaster_type\":\"" + disasterStr + "\",";
  jsonPayload += "\"scenario\":\"" + scenarioStr + "\"";
  jsonPayload += "}";

  Serial.println("\nTransmitting Telemetry to D-SQUARE Dashboard...");
  Serial.println(jsonPayload);

  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("HTTP Response Code: ");
    Serial.println(httpCode);
    Serial.print("Server Response: ");
    Serial.println(response);
  } else {
    Serial.print("HTTP Error: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }
  http.end();
}

void loop() {
  // 1. Read DHT11 Temperature & Humidity (Pin D5 / GPIO14)
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // 2. Read Capacitive Soil Moisture (Pin A0 / ADC0)
  int soilRaw = analogRead(SOIL_PIN);
  float soilMoisturePct = map(soilRaw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100);
  soilMoisturePct = constrain(soilMoisturePct, 0.0, 100.0);

  // 3. Read MQ-2 Gas & Smoke (Pin D6 / GPIO12)
  int mq2Raw = digitalRead(MQ2_PIN);
  int mq2Gas = (mq2Raw == HIGH) ? 1 : 0; // HIGH = Gas Detected

  // 4. Read SW-520D Tilt Sensor (Pin D7 / GPIO13)
  int tiltRaw = digitalRead(TILT_PIN);
  int tilt = (tiltRaw == LOW) ? 1 : 0;   // LOW = Tilted / Unstable

  // 5. Read 801S Vibration Sensor (Pin D8 / GPIO15)
  int vibrationRaw = digitalRead(VIBRATION_PIN);
  int vibration = (vibrationRaw == HIGH) ? 1 : 0; // HIGH = Vibration Pulse

  // 6. Read IR Flame Sensor (Pin D2 / GPIO4)
  int flameRaw = digitalRead(FLAME_PIN);
  int flame = (flameRaw == LOW) ? 1 : 0; // LOW = Flame Detected on IR Sensor

  // Determine Alert Condition
  bool isAlert = (flame == 1 || tilt == 1 || vibration == 1 || mq2Gas == 1 || soilMoisturePct > 85.0);

  if (isAlert) {
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(RED_ALERT_PIN, HIGH);
    Serial.println("\n🚨 HAZARD ALERT DETECTED ON GROUND SENSORS!");
  } else {
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(RED_ALERT_PIN, LOW);
  }

  // Debug Print Telemetry
  Serial.println("\n---------- LIVE GROUND TELEMETRY READING ----------");
  Serial.print("1. Temperature: "); Serial.print(isnan(temperature) ? 25.0 : temperature, 1); Serial.println(" °C (Pin D5)");
  Serial.print("2. Humidity:    "); Serial.print(isnan(humidity) ? 50.0 : humidity, 1); Serial.println(" % (Pin D5)");
  Serial.print("3. Soil Moist:  "); Serial.print(soilMoisturePct, 1); Serial.print("% [ADC: "); Serial.print(soilRaw); Serial.println("] (Pin A0)");
  Serial.print("4. MQ2 Gas:     "); Serial.println(mq2Gas == 1 ? "⚠️ GAS DETECTED" : "NORMAL (Pin D6)");
  Serial.print("5. Tilt Sensor: "); Serial.println(tilt == 1 ? "⚠️ SLOPE TILTED" : "LEVEL (Pin D7)");
  Serial.print("6. Vibration:   "); Serial.println(vibration == 1 ? "⚠️ TREMOR DETECTED" : "STABLE (Pin D8)");
  Serial.print("7. Flame Sensor:"); Serial.println(flame == 1 ? "🔥 FLAME DETECTED" : "SAFE (Pin D2)");

  // Transmit telemetry to D-SQUARE Backend Server
  sendTelemetryToServer(temperature, humidity, soilRaw, soilMoisturePct, mq2Gas, tilt, vibration, flame, isAlert);

  delay(2000); // 2-second update interval
}
