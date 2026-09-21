/*
  D-SQUARE 2.0 - IoT Ground Station Node Firmware (Fixed Dual HTTP/HTTPS Endpoint)
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
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

// ---------- WiFi & Server Configuration ----------
const char* ssid     = "Joke";                     // Your WiFi Network Name
const char* password = "Joke@2005";                // Your WiFi Network Password

// 1. Primary Direct Local IP Endpoint (Fastest & SSL-Free for ESP8266):
const char* localServerUrl = "http://10.172.49.122:5001/api/sensor_data";

// 2. Cloudflare HTTPS Tunnel Endpoint (Fallback):
const char* cloudflareUrl  = "https://competitors-insert-peas-above.trycloudflare.com/api/sensor_data";

// ---------- Pin Definitions ----------
#define DHT_PIN          14   // D5 / GPIO14 (DHT11 Temp & Humidity)
#define DHT_TYPE         DHT11

#define SOIL_PIN         A0   // A0 / ADC0 (Capacitive Soil Moisture Analog)

#define MQ2_PIN          12   // D6 / GPIO12 (MQ2 Gas/Smoke Digital Output)
#define TILT_PIN         13   // D7 / GPIO13 (SW-520D Tilt Switch Digital Output)
#define VIBRATION_PIN    15   // D8 / GPIO15 (801S Vibration Digital Output)
#define FLAME_PIN        4    // D2 / GPIO4  (IR Flame Digital Output)

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
  while (WiFi.status() != WL_CONNECTED && attempts < 25) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected Successfully!");
    Serial.print("ESP8266 Node IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n⚠️ WiFi Connection Failed! Check SSID/Password.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(MQ2_PIN, INPUT);
  pinMode(TILT_PIN, INPUT_PULLUP);
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_ALERT_PIN, OUTPUT);

  digitalWrite(GREEN_LED_PIN, HIGH);
  digitalWrite(RED_ALERT_PIN, LOW);

  dht.begin();

  Serial.println();
  Serial.println("=================================================");
  Serial.println(" D-SQUARE 2.0 IoT Ground Telemetry Node Initialized");
  Serial.println(" Primary Endpoint: http://10.172.49.122:5001/api/sensor_data");
  Serial.println("=================================================");

  connectToWiFi();
}

void sendTelemetryToServer(float temp, float hum, int soilRaw, float soilPct, int mq2Gas, int tilt, int vibration, int flame, bool isAlert) {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  String scenarioStr = isAlert ? "hazard_alert" : "normal";
  String disasterStr = "none";

  if (flame == 1) disasterStr = "fire";
  else if (mq2Gas == 1) disasterStr = "fire";
  else if (tilt == 1 || vibration == 1) disasterStr = "landslide";
  else if (soilRaw < 450) disasterStr = "flood";

  // Build JSON payload
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

  Serial.println("\nTransmitting Telemetry to D-SQUARE Server...");
  Serial.println(jsonPayload);

  // --- Step 1: Try Local HTTP Direct Endpoint ---
  WiFiClient client;
  HTTPClient http;

  http.begin(client, localServerUrl);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("✅ HTTP Success! Code: ");
    Serial.println(httpCode);
    Serial.print("Server Response: ");
    Serial.println(response);
    http.end();
    return;
  } else {
    Serial.print("Local HTTP Connection Error: ");
    Serial.println(http.errorToString(httpCode).c_str());
    http.end();
  }

  // --- Step 2: Fallback to HTTPS Cloudflare Tunnel ---
  Serial.println("Attempting Fallback HTTPS Cloudflare Tunnel...");
  WiFiClientSecure secureClient;
  secureClient.setInsecure();

  HTTPClient https;
  https.begin(secureClient, cloudflareUrl);
  https.addHeader("Content-Type", "application/json");

  int httpsCode = https.POST(jsonPayload);
  if (httpsCode > 0) {
    String response = https.getString();
    Serial.print("✅ HTTPS Cloudflare Success! Code: ");
    Serial.println(httpsCode);
    Serial.print("Server Response: ");
    Serial.println(response);
  } else {
    Serial.print("❌ HTTPS Tunnel Error: ");
    Serial.println(https.errorToString(httpsCode).c_str());
  }
  https.end();
}

void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  int soilRaw = analogRead(SOIL_PIN);
  float soilMoisturePct = map(soilRaw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100);
  soilMoisturePct = constrain(soilMoisturePct, 0.0, 100.0);

  int mq2Raw = digitalRead(MQ2_PIN);
  int mq2Gas = (mq2Raw == HIGH) ? 1 : 0;

  int tiltRaw = digitalRead(TILT_PIN);
  int tilt = (tiltRaw == LOW) ? 1 : 0;

  int vibrationRaw = digitalRead(VIBRATION_PIN);
  int vibration = (vibrationRaw == HIGH) ? 1 : 0;

  int flameRaw = digitalRead(FLAME_PIN);
  int flame = (flameRaw == LOW) ? 1 : 0;

  bool isAlert = (flame == 1 || tilt == 1 || vibration == 1 || mq2Gas == 1 || soilMoisturePct > 85.0);

  if (isAlert) {
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(RED_ALERT_PIN, HIGH);
    Serial.println("\n🚨 HAZARD ALERT DETECTED ON GROUND SENSORS!");
  } else {
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(RED_ALERT_PIN, LOW);
  }

  sendTelemetryToServer(temperature, humidity, soilRaw, soilMoisturePct, mq2Gas, tilt, vibration, flame, isAlert);

  delay(2000);
}
