/*
  D-SQUARE 2.0 - ESP8266 Landslide Detection & PC Application Integration

  Components & Wiring:
  - ESP8266 NodeMCU
  - Capacitive Soil Moisture Sensor (VCC -> 3V3, GND -> GND, AOUT -> A0)
  - DHT11 Temp & Humidity Sensor   (DATA -> D5 / GPIO14)
  - Green LED                      -> D1 (GPIO5) via 220Ω
  - Red LED                        -> D2 (GPIO4) via 220Ω
  - Buzzer                         -> D6 (GPIO12)

  WiFi Credentials:
  - SSID: Joke
  - Password: Joke@2005

  Behavior:
  - Normal condition:
      • Soil raw >= SOIL_RISK_THRESHOLD (800)
      • Green LED ON, Red LED OFF, Buzzer OFF
      • Sends telemetry POST to PC App (/api/sensor_data) with scenario = "normal"
  - Risk condition (Landslide Risk Detected by Hardware):
      • Soil raw < SOIL_RISK_THRESHOLD (800)
      • Green LED OFF, Red LED ON, Buzzer ON (1000 Hz)
      • Sends HTTP POST payload to PC App (/api/sensor_data) with scenario = "landslide"
      • Instantly triggers Landslide Detection in PC App UI & feeds D-SQUARE GPT
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>

// ---------- WiFi & Server Configuration ----------
const char* ssid     = "Joke";          // WiFi Network Name
const char* password = "Joke@2005";     // WiFi Password

// IP Address of host PC running D-SQUARE 2.0 Flask Server (Port 5001 HTTP)
// Update 192.168.1.100 to your host PC's local IP address on the "Joke" network
const char* serverUrl = "http://192.168.1.100:5001/api/sensor_data";

// ---------- Pin definitions (as per your wiring) ----------
#define SOIL_PIN A0

#define DHT_PIN 14       // D5 / GPIO14
#define DHT_TYPE DHT11

#define GREEN_LED_PIN 5  // D1 / GPIO5
#define RED_LED_PIN 4    // D2 / GPIO4
#define BUZZER_PIN 12    // D6 / GPIO12

// ---------- Soil threshold ----------
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
    Serial.println("\n⚠️ WiFi Connection Failed! Operating in local alert mode.");
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
  Serial.println("Wireless PC App & D-SQUARE GPT Integration");
  Serial.println("====================================");

  connectToWiFi();
}

void sendTelemetryToPCLandslideDetection(int soilRaw, float temp, float hum, bool isRisk) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    connectToWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  WiFiClient client;
  HTTPClient http;

  Serial.print("Sending telemetry to PC Landslide Detection Server (");
  Serial.print(serverUrl);
  Serial.println(")...");

  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");

  // Construct JSON payload for PC Landslide Detection & D-SQUARE GPT
  String jsonPayload = "{";
  jsonPayload += "\"node_id\":\"ESP8266_LANDSLIDE_NODE_01\",";
  jsonPayload += "\"soil_raw\":" + String(soilRaw) + ",";
  jsonPayload += "\"temperature\":" + String(isnan(temp) ? 25.8 : temp, 1) + ",";
  jsonPayload += "\"humidity\":" + String(isnan(hum) ? 92.0 : hum, 1) + ",";
  jsonPayload += "\"scenario\":\"" + String(isRisk ? "landslide" : "normal") + "\"";
  jsonPayload += "}";

  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("HTTP Response Code: ");
    Serial.println(httpCode);
    Serial.print("PC Server Response: ");
    Serial.println(response);
    if (isRisk) {
      Serial.println("🔥 Landslide Alert detected by Hardware -> Transmitted to PC Landslide Detection & D-SQUARE GPT!");
    }
  } else {
    Serial.print("Error on HTTP POST: ");
    Serial.println(http.errorToString(httpCode).c_str());
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

  // Decide local hardware state based on soil threshold
  if (isRisk) {
    // Risk condition
    Serial.println("STATE: RISK (Wet soil / landslide risk)");
    setRiskState();
  } else {
    // Normal condition
    Serial.println("STATE: NORMAL (Dry / safe soil)");
    setNormalState();
  }

  // Transmit telemetry to PC Landslide Detection App & D-SQUARE GPT
  sendTelemetryToPCLandslideDetection(soilRaw, temperature, humidity, isRisk);

  delay(2000);
}
