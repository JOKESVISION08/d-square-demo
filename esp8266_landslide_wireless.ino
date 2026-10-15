/*
  D-SQUARE 2.0 - IoT Ground Station Node Firmware (Direct Firebase Cloud Integration)
  Auto-Reset Alert Logic (Flame + Smoke + Soil Moisture Only)

  Fixes "connection failed" errors by pushing sensor telemetry and hardware alerts
  directly to Firebase Realtime Database REST API over secure HTTPS (port 443).

  Pin Mapping:
    - DHT11 Temp & Humidity      -> D5 (GPIO14)
    - Capacitive Soil Moisture   -> A0 (Analog ADC)
    - MQ-2 Gas & Smoke (D0)      -> D6 (GPIO12)
    - IR Flame Sensor            -> D2 (GPIO4)
    - Green Status LED           -> D1 (GPIO5) via 220Ω
    - Red Alert LED              -> D3 (GPIO0) via 220Ω
    - Buzzer                     -> D4 (GPIO2)
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

// ---------- WiFi & Firebase Configuration ----------
const char* ssid     = "Joke";
const char* password = "Joke@2005";

// Direct Firebase Realtime Database REST Endpoints (No local server or tunnel required)
const char* firebaseHost = "https://d-sqaure-default-rtdb.firebaseio.com";
const char* telemetryEndpoint = "https://d-sqaure-default-rtdb.firebaseio.com/nodes/D-SQUARE_NODE_01/telemetry.json";
const char* hardwareAlertEndpoint = "https://d-sqaure-default-rtdb.firebaseio.com/nodes/D-SQUARE_NODE_01/hardware_alert.json";

// ---------- Pin Definitions ----------
#define DHT_PIN          14   // D5 / GPIO14
#define DHT_TYPE         DHT11
#define SOIL_PIN         A0   // A0 / ADC0
#define MQ2_PIN          12   // D6 / GPIO12 (MQ-2 D0)
#define FLAME_PIN        4    // D2 / GPIO4
#define GREEN_LED_PIN    5    // D1 / GPIO5
#define RED_LED_PIN      0    // D3 / GPIO0
#define BUZZER_PIN       2    // D4 / GPIO2

// ---------- Threshold ----------
const int SOIL_RAW_ALERT_THRESHOLD = 800;  // Alert when soil raw < 800

DHT dht(DHT_PIN, DHT_TYPE);

// ---------- WiFi Connection ----------
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
    Serial.println("\nWiFi connected successfully.");
    Serial.print("ESP8266 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed.");
  }
}

// ---------- Output Control ----------
void setNormalOutputs() {
  digitalWrite(GREEN_LED_PIN, HIGH);  // Green ON
  digitalWrite(RED_LED_PIN, LOW);     // Red OFF
  digitalWrite(BUZZER_PIN, LOW);      // Buzzer OFF
}

void setAlertOutputs() {
  digitalWrite(GREEN_LED_PIN, LOW);   // Green OFF
  digitalWrite(RED_LED_PIN, HIGH);    // Red ON
  digitalWrite(BUZZER_PIN, HIGH);     // Buzzer ON continuously
}

// ---------- Setup ----------
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

  Serial.println();
  Serial.println("===============================================");
  Serial.println("D-SQUARE 2.0: Direct Firebase IoT Node Firmware");
  Serial.println("Target: https://d-sqaure-default-rtdb.firebaseio.com");
  Serial.println("===============================================");

  connectToWiFi();
}

// ---------- Telemetry Send Function (Direct Firebase HTTPS REST API) ----------
void sendTelemetryToFirebase(float temp, float hum, int soilRaw, float soilPct,
                             int mq2Gas, int flame, bool isAlert) {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  String scenarioStr = isAlert ? "hazard_alert" : "normal";
  String disasterStr = "none";

  if (flame == 1 || mq2Gas == 1) {
    disasterStr = "fire";
  } else if (soilRaw < SOIL_RAW_ALERT_THRESHOLD) {
    disasterStr = "landslide";
  }

  unsigned long currentMillis = millis();

  // Build Telemetry JSON Payload
  String jsonPayload = "{";
  jsonPayload += "\"node_id\":\"D-SQUARE_NODE_01\",";
  jsonPayload += "\"temperature\":" + String(isnan(temp) ? 25.0 : temp, 1) + ",";
  jsonPayload += "\"humidity\":" + String(isnan(hum) ? 50.0 : hum, 1) + ",";
  jsonPayload += "\"soil_moisture\":" + String(soilPct, 1) + ",";
  jsonPayload += "\"soil_raw\":" + String(soilRaw) + ",";
  jsonPayload += "\"mq2_gas\":" + String(mq2Gas) + ",";
  jsonPayload += "\"flame\":" + String(flame) + ",";
  jsonPayload += "\"disaster_type\":\"" + disasterStr + "\",";
  jsonPayload += "\"scenario\":\"" + scenarioStr + "\",";
  jsonPayload += "\"updated_at\":" + String(currentMillis);
  jsonPayload += "}";

  Serial.println("\nPushing Telemetry to Firebase RTDB...");

  WiFiClientSecure secureClient;
  secureClient.setInsecure(); // Bypass cert validation for ESP8266 HTTPS
  HTTPClient https;

  // 1. Send Telemetry via HTTPS PUT
  https.begin(secureClient, telemetryEndpoint);
  https.addHeader("Content-Type", "application/json");
  int httpCode = https.PUT(jsonPayload);

  if (httpCode > 0) {
    Serial.print("Firebase Telemetry Success, HTTP code: ");
    Serial.println(httpCode);
  } else {
    Serial.print("Firebase Telemetry Error: ");
    Serial.println(https.errorToString(httpCode).c_str());
  }
  https.end();

  // 2. If Hazard Alert exists, push hardware alert to Firebase RTDB
  if (isAlert) {
    String hwPayload = "{";
    hwPayload += "\"event_id\":\"EVT-HW-" + String(currentMillis) + "\",";
    hwPayload += "\"node_id\":\"D-SQUARE_NODE_01\",";
    hwPayload += "\"disaster_type\":\"" + disasterStr + "\",";
    hwPayload += "\"event_status\":\"ACTIVE\",";
    hwPayload += "\"severity\":\"CRITICAL\",";
    hwPayload += "\"confidence\":0.95,";
    hwPayload += "\"latitude\":30.0668,";
    hwPayload += "\"longitude\":79.0193,";
    hwPayload += "\"location_name\":\"Uttarakhand Slope Sector 4\",";
    hwPayload += "\"sensor_readings\":{\"temperature_c\":" + String(temp, 1);
    hwPayload += ",\"humidity_pct\":" + String(hum, 1);
    hwPayload += ",\"soil_moisture_pct\":" + String(soilPct, 1);
    hwPayload += ",\"soil_raw\":" + String(soilRaw);
    hwPayload += ",\"mq2_smoke\":" + String(mq2Gas);
    hwPayload += ",\"flame\":" + String(flame) + "},";
    hwPayload += "\"updated_at\":" + String(currentMillis);
    hwPayload += "}";

    Serial.println("Pushing Active Hardware Alert to Firebase RTDB...");
    https.begin(secureClient, hardwareAlertEndpoint);
    https.addHeader("Content-Type", "application/json");
    int alertCode = https.PUT(hwPayload);

    if (alertCode > 0) {
      Serial.print("Firebase Hardware Alert Success, HTTP code: ");
      Serial.println(alertCode);
    } else {
      Serial.print("Firebase Hardware Alert Error: ");
      Serial.println(https.errorToString(alertCode).c_str());
    }
    https.end();
  } else {
    // If normal, clear or set hardware alert status to INACTIVE so warning banner clears automatically
    String clearAlertPayload = "{\"event_status\":\"INACTIVE\",\"updated_at\":" + String(currentMillis) + "}";
    https.begin(secureClient, hardwareAlertEndpoint);
    https.addHeader("Content-Type", "application/json");
    https.PUT(clearAlertPayload);
    https.end();
  }
}

// ---------- Main Loop ----------
void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  int soilRaw = analogRead(SOIL_PIN);
  float soilMoisturePct = map(soilRaw, 1023, 0, 0, 100);
  soilMoisturePct = constrain(soilMoisturePct, 0.0, 100.0);

  // Read MQ-2 digital output (LOW = smoke detected)
  int mq2Raw = digitalRead(MQ2_PIN);
  int mq2Gas = (mq2Raw == LOW) ? 1 : 0;

  // Flame module logic (LOW = flame detected)
  int flameRaw = digitalRead(FLAME_PIN);
  int flame = (flameRaw == LOW) ? 1 : 0;

  bool fireHazard = (flame == 1 || mq2Gas == 1);
  bool landslideHazard = (soilRaw < SOIL_RAW_ALERT_THRESHOLD);
  bool isAlert = (fireHazard || landslideHazard);

  // Debug output
  Serial.print("MQ2_PIN raw: ");
  Serial.print(mq2Raw);
  Serial.print(" | mq2Gas: ");
  Serial.print(mq2Gas);
  Serial.print(" | Soil Raw: ");
  Serial.print(soilRaw);
  Serial.print(" | Flame: ");
  Serial.print(flame);
  Serial.print(" | Alert: ");
  Serial.println(isAlert ? "YES" : "NO");

  if (isAlert) {
    setAlertOutputs();
    Serial.println("OUTPUT: Red ON | Buzzer ON");
  } else {
    setNormalOutputs();
    Serial.println("OUTPUT: Green ON | Buzzer OFF");
  }

  sendTelemetryToFirebase(
    temperature, humidity, soilRaw, soilMoisturePct,
    mq2Gas, flame, isAlert
  );

  delay(3000);
}
