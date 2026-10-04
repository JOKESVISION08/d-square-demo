/*
  ==============================================================================
  D-SQUARE 2.0 - ESP8266 Local Testing & Mock Telemetry Firmware Sketch
  ==============================================================================

  Configuration Flags:
    - USE_MOCK_SENSOR_VALUES: true  -> Generates realistic mock sensor data cycles
    - USE_FIREBASE_EMULATOR:  false -> Directs HTTP requests to Cloud RTDB or Local Emulator

  Simulated Telemetry Cycles (rotates every 10 seconds):
    1. Normal Telemetry (Temp: 28.5°C, Hum: 55%, Soil Raw: 920, MQ2: 0, Flame: 0)
    2. Simulated Fire Anomaly (Temp: 48.2°C, Hum: 22%, MQ2: 1, Flame: 1)
    3. Simulated Landslide Anomaly (Soil Raw: 420 [soil_moisture: 85%], Temp: 24.1°C)
    4. Recovery / Return to Normal
*/

#define USE_MOCK_SENSOR_VALUES true
#define USE_FIREBASE_EMULATOR false

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>

// WiFi Configuration
const char* ssid         = "Joke";
const char* password     = "Joke@2005";

#if USE_FIREBASE_EMULATOR
  const char* firebaseHost = "http://10.190.219.122:9000"; // Local PC IP running Firebase RTDB Emulator
#else
  const char* firebaseHost = "https://d-sqaure-default-rtdb.firebaseio.com";
#endif

const char* nodePath     = "/nodes/D-SQUARE_NODE_01";

// Pins
#define GREEN_LED_PIN    5   // D1
#define RED_LED_PIN      0   // D3
#define BUZZER_PIN       2   // D4

int mockCycleStep = 0;
unsigned long lastCycleTime = 0;
const unsigned long CYCLE_INTERVAL_MS = 10000; // 10s per test phase

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
    Serial.println("\n✅ Connected. IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n❌ WiFi connection failed.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(GREEN_LED_PIN, HIGH);
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.println("\n=======================================================");
  Serial.println(" D-SQUARE 2.0: ESP8266 Mock Test Firmware");
  Serial.println(" USE_MOCK_SENSOR_VALUES: TRUE");
  Serial.println(" Target Host: " + String(firebaseHost));
  Serial.println("=======================================================");

  connectToWiFi();
}

void sendFirebaseData(String endpointUrl, String jsonPayload) {
  if (WiFi.status() != WL_CONNECTED) connectToWiFi();
  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClientSecure secureClient;
  secureClient.setInsecure();

  HTTPClient https;
  if (https.begin(secureClient, endpointUrl)) {
    https.addHeader("Content-Type", "application/json");
    int httpCode = https.PUT(jsonPayload);
    if (httpCode > 0) {
      Serial.println("✅ Firebase PUT OK [" + String(httpCode) + "]");
    } else {
      Serial.println("❌ Firebase PUT Error: " + https.errorToString(httpCode));
    }
    https.end();
  }
}

void loop() {
  unsigned long now = millis();
  if (now - lastCycleTime >= CYCLE_INTERVAL_MS) {
    lastCycleTime = now;
    mockCycleStep = (mockCycleStep + 1) % 4;
  }

  float temperature = 26.5;
  float humidity = 52.0;
  int soilRaw = 920;
  float soilMoisturePct = 25.0;
  int mq2Gas = 0;
  int flame = 0;
  String disasterStr = "none";
  bool isAlert = false;

  if (mockCycleStep == 1) {
    // Fire Scenario Mock Data
    temperature = 51.4;
    humidity = 18.0;
    mq2Gas = 1;
    flame = 1;
    disasterStr = "fire";
    isAlert = true;
  } else if (mockCycleStep == 2) {
    // Landslide Scenario Mock Data
    temperature = 22.0;
    soilRaw = 410;
    soilMoisturePct = 86.5;
    disasterStr = "landslide";
    isAlert = true;
  }

  // Outputs on local board
  if (isAlert) {
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, HIGH);
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(RED_LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
  }

  // Telemetry PUT
  String telemetryUrl = String(firebaseHost) + nodePath + "/telemetry.json";
  String telemetryJson = "{";
  telemetryJson += "\"node_id\":\"D-SQUARE_NODE_01\",";
  telemetryJson += "\"temperature\":" + String(temperature, 1) + ",";
  telemetryJson += "\"humidity\":" + String(humidity, 1) + ",";
  telemetryJson += "\"soil_moisture\":" + String(soilMoisturePct, 1) + ",";
  telemetryJson += "\"soil_raw\":" + String(soilRaw) + ",";
  telemetryJson += "\"mq2_gas\":" + String(mq2Gas) + ",";
  telemetryJson += "\"flame\":" + String(flame) + ",";
  telemetryJson += "\"disaster_type\":\"" + disasterStr + "\",";
  telemetryJson += "\"updated_at\":" + String(millis());
  telemetryJson += "}";

  sendFirebaseData(telemetryUrl, telemetryJson);

  // Hardware Alert PUT
  String alertUrl = String(firebaseHost) + nodePath + "/hardware_alert.json";
  if (isAlert) {
    String alertJson = "{";
    alertJson += "\"event_id\":\"EVT-MOCK-" + String(millis()) + "\",";
    alertJson += "\"node_id\":\"D-SQUARE_NODE_01\",";
    alertJson += "\"event_status\":\"ACTIVE\",";
    alertJson += "\"disaster_type\":\"" + disasterStr + "\",";
    alertJson += "\"severity\":\"CRITICAL\",";
    alertJson += "\"confidence\":0.96,";
    alertJson += "\"requires_operator_verification\":true,";
    alertJson += "\"auto_sos_dispatch\":false,";
    alertJson += "\"latitude\":30.0668,";
    alertJson += "\"longitude\":79.0193,";
    alertJson += "\"location_name\":\"Uttarakhand Slope Sector 4\",";
    alertJson += "\"sensor_readings\":{";
    alertJson += "\"temperature_c\":" + String(temperature, 1) + ",";
    alertJson += "\"humidity_pct\":" + String(humidity, 1) + ",";
    alertJson += "\"soil_moisture_pct\":" + String(soilMoisturePct, 1) + ",";
    alertJson += "\"soil_raw\":" + String(soilRaw) + ",";
    alertJson += "\"mq2_smoke\":" + String(mq2Gas) + ",";
    alertJson += "\"flame\":" + String(flame);
    alertJson += "},";
    alertJson += "\"updated_at\":" + String(millis());
    alertJson += "}";

    sendFirebaseData(alertUrl, alertJson);
  } else {
    sendFirebaseData(alertUrl, "null");
  }

  delay(2500);
}
