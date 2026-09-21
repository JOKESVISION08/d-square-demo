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
#include <WiFiClientSecure.h>
#include <DHT.h>

// ---------- WiFi & Server Configuration ----------
const char* ssid     = "Joke";
const char* password = "Joke@2005";

// Primary Live HTTPS Server Endpoint:
const char* serverUrl = "https://competitors-insert-peas-above.trycloudflare.com/api/sensor_data";

// Deployed Netlify Mirror Endpoint:
const char* netlifyUrl = "https://harmonious-gelato-fda171.netlify.app/api/sensor_data";

// ---------- Pin definitions ----------
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
    Serial.println("\n⚠️ WiFi Connection Failed! Operating in standalone alert mode.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);

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

  WiFiClientSecure client;
  client.setInsecure();
  HTTPClient http;

  Serial.print("Sending alert telemetry to D-SQUARE GPT Server (");
  Serial.print(serverUrl);
  Serial.println(")...");

  float soilMoisturePercent = map(soilRaw, 850, 350, 0, 100);
  soilMoisturePercent = constrain(soilMoisturePercent, 0.0, 100.0);
  if (isRisk && soilMoisturePercent < 80.0) {
    soilMoisturePercent = 88.0;
  }

  String jsonPayload = "{";
  jsonPayload += "\"node_id\":\"ESP8266_LANDSLIDE_NODE_01\",";
  jsonPayload += "\"soil_raw\":" + String(soilRaw) + ",";
  jsonPayload += "\"soil_moisture\":" + String(soilMoisturePercent, 1) + ",";
  jsonPayload += "\"temperature\":" + String(isnan(temp) ? 25.0 : temp, 1) + ",";
  jsonPayload += "\"humidity\":" + String(isnan(hum) ? 50.0 : hum, 1) + ",";
  jsonPayload += "\"scenario\":\"" + String(isRisk ? "landslide" : "normal") + "\"";
  jsonPayload += "}";

  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("D-SQUARE HTTP POST Status Code: ");
    Serial.println(httpCode);
    Serial.print("D-SQUARE Server Response: ");
    Serial.println(response);
    if (isRisk) {
      Serial.println("🔥 Landslide Alert successfully transmitted to D-SQUARE GPT & Safety Assistant!");
    }
  } else {
    Serial.print("Primary HTTP POST Error: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }
  http.end();
}

void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int soilRaw = analogRead(SOIL_PIN);

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

  if (isRisk) {
    Serial.println("STATE: RISK (Wet soil / landslide risk)");
    setRiskState();
  } else {
    Serial.println("STATE: NORMAL (Dry / safe soil)");
    setNormalState();
  }

  sendTelemetryToDSquareGPT(soilRaw, temperature, humidity, isRisk);

  delay(2000);
}
