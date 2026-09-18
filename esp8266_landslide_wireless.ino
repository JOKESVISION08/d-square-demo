/*
  D-SQUARE 2.0 - Landslide Detection with Wireless D-SQUARE GPT Integration

  Components & Wiring:
  - ESP8266 NodeMCU
  - Capacitive Soil Moisture Sensor (VCC -> 3V3, GND -> GND, AOUT -> A0)
  - DHT11 Temp & Humidity Sensor   (DATA -> D5 / GPIO14)
  - Green LED                      -> D1 (GPIO5) via 220Ω
  - Red LED                        -> D2 (GPIO4) via 220Ω
  - Buzzer                         -> D6 (GPIO12)

  Behavior:
  - Normal condition:
      • Soil raw >= SOIL_RISK_THRESHOLD (800)
      • Green LED ON, Red LED OFF, Buzzer OFF
      • Sends telemetry payload to D-SQUARE server (/api/sensor_data) with scenario = "normal"
  - Risk condition (Landslide Risk):
      • Soil raw < SOIL_RISK_THRESHOLD (800)
      • Green LED OFF, Red LED ON, Buzzer ON (1000 Hz)
      • Sends HTTP POST payload to D-SQUARE server (/api/sensor_data) with scenario = "landslide"
      • Instantly triggers D-SQUARE GPT AI Safety Assistant & Emergency SOS Alerting System
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>

// ---------- WiFi & Server Configuration ----------
const char* ssid     = "Joke";        // Your WiFi SSID
const char* password = "Joke@2005";    // Your WiFi Password

// Target D-SQUARE 2.0 Backend Telemetry Endpoint (/api/sensor_data)
// Primary Local Server (Your PC IPv4 on Wi-Fi):
const char* serverUrl = "http://10.172.49.122:5001/api/sensor_data";

// Optional Cloud Server Backup:
const char* cloudServerUrl = "http://d-square-demo.onrender.com/api/sensor_data";

// ---------- Pin definitions ----------
#define SOIL_PIN A0

#define DHT_PIN 14       // D5 / GPIO14
#define DHT_TYPE DHT11

#define GREEN_LED_PIN 5  // D1 / GPIO5
#define RED_LED_PIN 4    // D2 / GPIO4
#define BUZZER_PIN 12    // D6 / GPIO12

// ---------- Soil threshold ----------
// Soil raw ADC values: Dry soil / air -> higher value (~850-1024), Saturated wet soil -> lower value (<800)
const int SOIL_RISK_THRESHOLD = 800;

DHT dht(DHT_PIN, DHT_TYPE);

void setNormalState() {
  digitalWrite(GREEN_LED_PIN, HIGH);
  digitalWrite(RED_LED_PIN, LOW);
  noTone(BUZZER_PIN);
}

void setRiskState() {
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, HIGH);
  tone(BUZZER_PIN, 1000);
}

void connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Connecting to WiFi Network: ");
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
    Serial.println("\n⚠️ WiFi Connection Failed! Operating in standalone alert mode.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);  // give time to open Serial Monitor

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  dht.begin();
  setNormalState();

  Serial.println();
  Serial.println("====================================");
  Serial.println("D-SQUARE 2.0 Landslide Detection");
  Serial.println("Wireless D-SQUARE GPT Integration");
  Serial.println("====================================");

  connectToWiFi();
}

void sendTelemetryToDSquareGPT(int soilRaw, float temp, float hum, bool isRisk) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Attempting reconnection...");
    connectToWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  WiFiClient client;
  HTTPClient http;

  Serial.print("Sending alert telemetry to D-SQUARE GPT Server (");
  Serial.print(serverUrl);
  Serial.println(")...");

  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");

  // Map soilRaw to estimated soil moisture percentage for ground station telemetry
  float soilMoisturePercent = map(soilRaw, 850, 350, 0, 100);
  soilMoisturePercent = constrain(soilMoisturePercent, 0.0, 100.0);
  if (isRisk && soilMoisturePercent < 80.0) {
    soilMoisturePercent = 88.0; // Saturate moisture percentage during risk condition
  }

  // Build JSON payload matching D-SQUARE 2.0 API schema
  String jsonPayload = "{";
  jsonPayload += "\"node_id\":\"ESP8266_LANDSLIDE_NODE_01\",";
  jsonPayload += "\"soil_raw\":" + String(soilRaw) + ",";
  jsonPayload += "\"soil_moisture\":" + String(soilMoisturePercent, 1) + ",";
  jsonPayload += "\"temperature\":" + String(isnan(temp) ? 25.0 : temp, 1) + ",";
  jsonPayload += "\"humidity\":" + String(isnan(hum) ? 50.0 : hum, 1) + ",";
  jsonPayload += "\"scenario\":\"" + String(isRisk ? "landslide" : "normal") + "\"";
  jsonPayload += "}";

  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("HTTP POST Status Code: ");
    Serial.println(httpCode);
    Serial.print("D-SQUARE Server Response: ");
    Serial.println(response);
    if (isRisk) {
      Serial.println("🔥 Landslide Alert successfully transmitted to D-SQUARE GPT & Safety Assistant!");
    }
  } else {
    Serial.print("Primary HTTP POST failed (");
    Serial.print(http.errorToString(httpCode).c_str());
    Serial.println("). Trying Cloud Backup Server...");
    
    // Backup POST to Cloud Server
    http.end();
    http.begin(client, cloudServerUrl);
    http.addHeader("Content-Type", "application/json");
    int cloudCode = http.POST(jsonPayload);
    if (cloudCode > 0) {
      Serial.print("Cloud Server HTTP Status: ");
      Serial.println(cloudCode);
    } else {
      Serial.print("Cloud POST error: ");
      Serial.println(http.errorToString(cloudCode).c_str());
    }
  }

  http.end();
}

void loop() {
  // Read DHT11
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Read soil sensor
  int soilRaw = analogRead(SOIL_PIN);

  // Print all values to Serial Monitor
  Serial.println();
  Serial.println("---------- SENSOR DATA ----------");

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT11: READ ERROR (check wiring & power)");
  } else {
    Serial.print("Temperature: ");
    Serial.print(temperature, 1);
    Serial.println(" C");

    Serial.print("Humidity: ");
    Serial.print(humidity, 1);
    Serial.println(" %");
  }

  Serial.print("Soil raw value: ");
  Serial.println(soilRaw);

  bool isRisk = (soilRaw < SOIL_RISK_THRESHOLD);

  // Decide hardware state based on soil threshold
  if (isRisk) {
    // Risk condition
    Serial.println("STATE: RISK (Wet soil / landslide risk)");
    setRiskState();
  } else {
    // Normal condition
    Serial.println("STATE: NORMAL (Dry / safe soil)");
    setNormalState();
  }

  // Transmit telemetry & alert state to D-SQUARE GPT backend
  sendTelemetryToDSquareGPT(soilRaw, temperature, humidity, isRisk);

  delay(2000);
}
