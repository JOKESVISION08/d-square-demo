/*
  ==============================================================================
  D-SQUARE 2.0 - ESP8266 Firebase Realtime Database Firmware
  Hardware Ground Station Telemetry & Silent Warning Ingestion Node
  ==============================================================================

  Pin Wiring Schematic:
    - DHT11 Temp & Humidity      -> D5 (GPIO14)
    - Capacitive Soil Moisture   -> A0 (Analog ADC0)
    - MQ-2 Gas & Smoke (D0)      -> D6 (GPIO12) [LOW = Smoke Detected]
    - IR Flame Sensor            -> D2 (GPIO4)  [LOW = Flame Active]
    - Green Status LED           -> D1 (GPIO5) via 220Ω
    - Red Alert LED              -> D3 (GPIO0) via 220Ω
    - Active Piezo Buzzer        -> D4 (GPIO2)

  Firebase RTDB HTTPS Endpoints (REST PUT):
    - Telemetry:      https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com/nodes/D-SQUARE_NODE_01/telemetry.json
    - Hardware Alert: https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com/nodes/D-SQUARE_NODE_01/hardware_alert.json
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

// ---------- WiFi & Firebase Configuration ----------
const char* ssid         = "Joke";
const char* password     = "Joke@2005";

// Replace YOUR_PROJECT_ID with your actual Firebase Project ID
const char* firebaseHost = "https://d-sqaure-default-rtdb.firebaseio.com";
const char* nodePath     = "/nodes/D-SQUARE_NODE_01";

// ---------- Pin Definitions ----------
#define DHT_PIN          14   // D5 / GPIO14
#define DHT_TYPE         DHT11
#define SOIL_PIN         A0   // A0 / ADC0
#define MQ2_PIN          12   // D6 / GPIO12 (MQ-2 D0)
#define FLAME_PIN        4    // D2 / GPIO4
#define GREEN_LED_PIN    5    // D1 / GPIO5
#define RED_LED_PIN      0    // D3 / GPIO0
#define BUZZER_PIN       2    // D4 / GPIO2

const int SOIL_RAW_ALERT_THRESHOLD = 800; // Alert when raw soil < 800

DHT dht(DHT_PIN, DHT_TYPE);

// Heartbeat & Anti-Spam State Tracking
bool wasInAlert = false;
unsigned long lastHeartbeatTime = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 30000; // 30s alert heartbeat

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
    Serial.println("\n✅ WiFi connected.");
    Serial.print("Node IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi connection failed.");
  }
}

void setNormalOutputs() {
  digitalWrite(GREEN_LED_PIN, HIGH);
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
}

void setAlertOutputs() {
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(MQ2_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  setNormalOutputs();
  dht.begin();

  Serial.println("\n===============================================");
  Serial.println(" D-SQUARE 2.0: ESP8266 Firebase RTDB Node");
  Serial.println(" Telemetry: " + String(firebaseHost) + nodePath + "/telemetry.json");
  Serial.println("===============================================");

  connectToWiFi();
}

void sendFirebaseHTTPS(String endpointUrl, String jsonPayload, String httpMethod = "PUT") {
  if (WiFi.status() != WL_CONNECTED) connectToWiFi();
  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClientSecure secureClient;
  secureClient.setInsecure(); // Disable SSL certificate verification for REST API

  HTTPClient https;
  if (https.begin(secureClient, endpointUrl)) {
    https.addHeader("Content-Type", "application/json");

    int httpCode = 0;
    if (httpMethod == "PUT") {
      httpCode = https.PUT(jsonPayload);
    } else if (httpMethod == "POST") {
      httpCode = https.POST(jsonPayload);
    }

    if (httpCode > 0) {
      Serial.print("✅ Firebase HTTPS ");
      Serial.print(httpMethod);
      Serial.print(" Success! Code: ");
      Serial.println(httpCode);
    } else {
      Serial.print("❌ Firebase HTTPS Error: ");
      Serial.println(https.errorToString(httpCode).c_str());
    }
    https.end();
  }
}

void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  int soilRaw = analogRead(SOIL_PIN);
  float soilMoisturePct = map(soilRaw, 1023, 0, 0, 100);
  soilMoisturePct = constrain(soilMoisturePct, 0.0, 100.0);

  int mq2Raw = digitalRead(MQ2_PIN);
  int mq2Gas = (mq2Raw == LOW) ? 1 : 0; // Inverted logic: LOW = smoke detected

  int flameRaw = digitalRead(FLAME_PIN);
  int flame = (flameRaw == LOW) ? 1 : 0; // LOW = flame detected

  bool fireHazard = (flame == 1 || mq2Gas == 1);
  bool landslideHazard = (soilRaw < SOIL_RAW_ALERT_THRESHOLD);
  bool isAlert = (fireHazard || landslideHazard);

  String disasterStr = isAlert ? (fireHazard ? "fire" : "landslide") : "none";
  String scenarioStr = isAlert ? disasterStr : "normal";

  // 1. Output Control (Local hardware buzzer/LEDs reset automatically)
  if (isAlert) {
    setAlertOutputs();
  } else {
    setNormalOutputs();
  }

  // 2. Transmit Telemetry every cycle (PUT to /nodes/D-SQUARE_NODE_01/telemetry.json)
  String telemetryUrl = String(firebaseHost) + nodePath + "/telemetry.json";
  String telemetryJson = "{";
  telemetryJson += "\"node_id\":\"D-SQUARE_NODE_01\",";
  telemetryJson += "\"temperature\":" + String(isnan(temperature) ? 25.0 : temperature, 1) + ",";
  telemetryJson += "\"humidity\":" + String(isnan(humidity) ? 50.0 : humidity, 1) + ",";
  telemetryJson += "\"soil_moisture\":" + String(soilMoisturePct, 1) + ",";
  telemetryJson += "\"soil_raw\":" + String(soilRaw) + ",";
  telemetryJson += "\"mq2_gas\":" + String(mq2Gas) + ",";
  telemetryJson += "\"flame\":" + String(flame) + ",";
  telemetryJson += "\"disaster_type\":\"" + disasterStr + "\",";
  telemetryJson += "\"scenario\":\"" + scenarioStr + "\",";
  telemetryJson += "\"updated_at\":" + String(millis());
  telemetryJson += "}";

  sendFirebaseHTTPS(telemetryUrl, telemetryJson, "PUT");

  // 3. Anti-Spam Hardware Alert Logic
  String alertUrl = String(firebaseHost) + nodePath + "/hardware_alert.json";
  unsigned long now = millis();

  if (isAlert) {
    String eventStatus = "ACTIVE";
    if (wasInAlert) {
      eventStatus = "ONGOING";
    }

    // Send ACTIVE when hazard begins OR ONGOING heartbeat every 30s
    if (!wasInAlert || (now - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS)) {
      wasInAlert = true;
      lastHeartbeatTime = now;

      String alertJson = "{";
      alertJson += "\"event_id\":\"EVT-HW-" + String(millis()) + "\",";
      alertJson += "\"node_id\":\"D-SQUARE_NODE_01\",";
      alertJson += "\"event_status\":\"" + eventStatus + "\",";
      alertJson += "\"disaster_type\":\"" + disasterStr + "\",";
      alertJson += "\"severity\":\"CRITICAL\",";
      alertJson += "\"confidence\":0.95,";
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

      sendFirebaseHTTPS(alertUrl, alertJson, "PUT");
    }
  } else if (wasInAlert) {
    // Send CLEARED event when state returns normal
    wasInAlert = false;
    String clearedJson = "null"; // Clears active hardware alert in Firebase RTDB
    sendFirebaseHTTPS(alertUrl, clearedJson, "PUT");
    Serial.println("✅ Hardware Alert CLEARED in Firebase.");
  }

  delay(2000);
}
