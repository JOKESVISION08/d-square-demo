/*
  ==============================================================================
  D-SQUARE 2.0 - Production ESP8266 HTTPS Ground Station Firmware
  Real Sensor Telemetry & Silent Hardware Warning Ingestion Node
  ==============================================================================

  Real Hardware Sensor Pin Mapping:
    - DHT11 Temp & Humidity      -> D5 (GPIO14)
    - Capacitive Soil Moisture   -> A0 (Analog ADC0)
    - MQ-2 Gas & Smoke (D0)      -> D6 (GPIO12) [LOW = Smoke Detected]
    - IR Flame Sensor            -> D2 (GPIO4)  [LOW = Flame Active]
    - Tilt Ball Switch           -> D7 (GPIO13) [HIGH = Tilted]
    - Piezo Vibration Sensor     -> D8 (GPIO15) [HIGH = Motion/Shock]
    - Green Status LED           -> D1 (GPIO5) via 220Ω
    - Red Alert LED              -> D3 (GPIO0) via 220Ω
    - Local Buzzer               -> D4 (GPIO2)

  Firebase Production HTTPS REST Endpoints:
    - Telemetry:      https://YOUR_PROJECT.firebaseio.com/nodes/D-SQUARE_NODE_01/telemetry.json
    - Hardware Alert: https://YOUR_PROJECT.firebaseio.com/nodes/D-SQUARE_NODE_01/hardware_alert.json
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

// ---------- Production Network & Device Configuration ----------
const char* wifiSsid     = "Joke";
const char* wifiPassword = "Joke@2005";

// Production Firebase HTTPS Realtime Database Endpoint
const char* firebaseDatabaseUrl = "https://d-sqaure-default-rtdb.firebaseio.com";
const char* deviceToken         = "PROD_NODE_SECRET_TOKEN_2026";

const char* nodeId        = "D-SQUARE_NODE_01";
const float nodeLatitude  = 30.0668;
const float nodeLongitude = 79.0193;

// ---------- Pin Definitions ----------
#define DHT_PIN          14   // D5 / GPIO14
#define DHT_TYPE         DHT11
#define SOIL_PIN         A0   // A0 / ADC0
#define MQ2_PIN          12   // D6 / GPIO12
#define FLAME_PIN        4    // D2 / GPIO4
#define TILT_PIN         13   // D7 / GPIO13
#define VIBRA_PIN        15   // D8 / GPIO15

#define GREEN_LED_PIN    5    // D1 / GPIO5
#define RED_LED_PIN      0    // D3 / GPIO0
#define BUZZER_PIN       2    // D4 / GPIO2

const int SOIL_RAW_ALERT_THRESHOLD = 800; // Alert when soil raw < 800 (wet/waterlogged)

DHT dht(DHT_PIN, DHT_TYPE);

// Offline Queue & Anti-Spam State Tracking
bool wasInAlert = false;
String pendingQueuedAlertJson = "";
bool hasQueuedAlert = false;
unsigned long lastHeartbeatTime = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 30000; // 30s alert heartbeat

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

void connectWiFiNonBlocking() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Connecting Wi-Fi to: ");
  Serial.println(wifiSsid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSsid, wifiPassword);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 15) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ Wi-Fi Connected. Node IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n⚠️ Wi-Fi Unavailable. Telemetry queued offline.");
  }
}

bool sendFirebaseHTTPS(String endpointUrl, String jsonPayload) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFiNonBlocking();
  }
  if (WiFi.status() != WL_CONNECTED) return false;

  WiFiClientSecure secureClient;
  secureClient.setInsecure(); // Disable SSL cert check for REST API endpoint

  HTTPClient https;
  if (https.begin(secureClient, endpointUrl)) {
    https.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
    https.addHeader("Content-Type", "application/json");
    https.addHeader("X-Firebase-Auth", deviceToken);

    int httpCode = https.PUT(jsonPayload);
    if (httpCode >= 200 && httpCode < 300) {
      Serial.println("✅ Production HTTPS PUT Success [HTTP " + String(httpCode) + "]");
      https.end();
      return true;
    } else {
      Serial.println("❌ HTTPS PUT Failed [HTTP " + String(httpCode) + "]: " + https.errorToString(httpCode));
      if (httpCode == 404) {
        Serial.println("💡 TIP: HTTP 404 means the Firebase Database URL in line 27 is incorrect or database not created in Firebase Console.");
      }
    }
    https.end();
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(MQ2_PIN, INPUT_PULLUP);
  pinMode(FLAME_PIN, INPUT_PULLUP);
  pinMode(TILT_PIN, INPUT_PULLUP);
  pinMode(VIBRA_PIN, INPUT_PULLUP);

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  setNormalOutputs();
  dht.begin();

  Serial.println("\n=======================================================");
  Serial.println(" D-SQUARE 2.0 - Production ESP8266 HTTPS Firmware");
  Serial.println(" Target Endpoint: " + String(firebaseDatabaseUrl));
  Serial.println(" Node ID: " + String(nodeId));
  Serial.println("=======================================================");

  connectWiFiNonBlocking();
}

void loop() {
  // 1. Read Actual Physical Sensors
  float tempReading = dht.readTemperature();
  float humReading = dht.readHumidity();
  bool dhtFailed = isnan(tempReading) || isnan(humReading);

  int soilRaw = analogRead(SOIL_PIN);
  float soilMoisturePercent = map(soilRaw, 1023, 0, 0, 100);
  soilMoisturePercent = constrain(soilMoisturePercent, 0.0, 100.0);

  int mq2Raw = digitalRead(MQ2_PIN);
  int mq2Smoke = (mq2Raw == LOW) ? 1 : 0; // LOW = Smoke detected

  int flameRaw = digitalRead(FLAME_PIN);
  int flame = (flameRaw == LOW) ? 1 : 0; // LOW = Flame active

  int tiltRaw = digitalRead(TILT_PIN);
  int tiltStatus = (tiltRaw == HIGH) ? 1 : 0;

  int vibraRaw = digitalRead(VIBRA_PIN);
  int vibrationStatus = (vibraRaw == HIGH) ? 1 : 0;

  // 2. Real Alert Determination Logic
  bool fireHazard = (flame == 1 || mq2Smoke == 1);
  bool landslideHazard = (soilRaw < SOIL_RAW_ALERT_THRESHOLD);
  bool isAlert = (fireHazard || landslideHazard);

  String disasterType = isAlert ? (fireHazard ? "fire" : "landslide") : "none";
  String severity = isAlert ? "CRITICAL" : "NORMAL";

  // Local Output Pins
  if (isAlert) setAlertOutputs(); else setNormalOutputs();

  // 3. Build Production Telemetry JSON Payload
  String telemetryUrl = String(firebaseDatabaseUrl) + "/nodes/" + String(nodeId) + "/telemetry.json";
  String telemetryJson = "{";
  telemetryJson += "\"node_id\":\"" + String(nodeId) + "\",";

  if (dhtFailed) {
    telemetryJson += "\"temperature\":null,";
    telemetryJson += "\"humidity\":null,";
    telemetryJson += "\"sensor_status\":\"DHT11_ERROR\",";
  } else {
    telemetryJson += "\"temperature\":" + String(tempReading, 1) + ",";
    telemetryJson += "\"humidity\":" + String(humReading, 1) + ",";
    telemetryJson += "\"sensor_status\":\"OK\",";
  }

  telemetryJson += "\"soil_raw\":" + String(soilRaw) + ",";
  telemetryJson += "\"soil_moisture_percent\":" + String(soilMoisturePercent, 1) + ",";
  telemetryJson += "\"mq2_raw\":" + String(mq2Raw) + ",";
  telemetryJson += "\"mq2_smoke\":" + String(mq2Smoke) + ",";
  telemetryJson += "\"flame_raw\":" + String(flameRaw) + ",";
  telemetryJson += "\"flame\":" + String(flame) + ",";
  telemetryJson += "\"tilt_status\":" + String(tiltStatus) + ",";
  telemetryJson += "\"vibration_status\":" + String(vibrationStatus) + ",";
  telemetryJson += "\"disaster_type\":\"" + disasterType + "\",";
  telemetryJson += "\"latitude\":" + String(nodeLatitude, 4) + ",";
  telemetryJson += "\"longitude\":" + String(nodeLongitude, 4) + ",";
  telemetryJson += "\"updated_at\":" + String(millis());
  telemetryJson += "}";

  sendFirebaseHTTPS(telemetryUrl, telemetryJson);

  // 4. Build Hardware Alert Payload with Wi-Fi Reconnect Queueing
  String alertUrl = String(firebaseDatabaseUrl) + "/nodes/" + String(nodeId) + "/hardware_alert.json";
  unsigned long now = millis();

  if (isAlert) {
    String eventStatus = wasInAlert ? "ONGOING" : "ACTIVE";

    if (!wasInAlert || (now - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS)) {
      wasInAlert = true;
      lastHeartbeatTime = now;

      String alertJson = "{";
      alertJson += "\"event_id\":\"EVT-HW-" + String(now) + "\",";
      alertJson += "\"node_id\":\"" + String(nodeId) + "\",";
      alertJson += "\"event_status\":\"" + eventStatus + "\",";
      alertJson += "\"disaster_type\":\"" + disasterType + "\",";
      alertJson += "\"severity\":\"" + severity + "\",";
      alertJson += "\"confidence\":0.95,";
      alertJson += "\"requires_operator_verification\":true,";
      alertJson += "\"auto_sos_dispatch\":false,";
      alertJson += "\"latitude\":" + String(nodeLatitude, 4) + ",";
      alertJson += "\"longitude\":" + String(nodeLongitude, 4) + ",";
      alertJson += "\"location_name\":\"Uttarakhand Slope Sector 4\",";
      alertJson += "\"sensor_readings\":{";
      alertJson += "\"temperature_c\":" + (dhtFailed ? "null" : String(tempReading, 1)) + ",";
      alertJson += "\"humidity_pct\":" + (dhtFailed ? "null" : String(humReading, 1)) + ",";
      alertJson += "\"soil_moisture_pct\":" + String(soilMoisturePercent, 1) + ",";
      alertJson += "\"soil_raw\":" + String(soilRaw) + ",";
      alertJson += "\"mq2_smoke\":" + String(mq2Smoke) + ",";
      alertJson += "\"flame\":" + String(flame) + ",";
      alertJson += "\"tilt\":" + String(tiltStatus) + ",";
      alertJson += "\"vibration\":" + String(vibrationStatus);
      alertJson += "},";
      alertJson += "\"updated_at\":" + String(now);
      alertJson += "}";

      bool success = sendFirebaseHTTPS(alertUrl, alertJson);
      if (!success) {
        pendingQueuedAlertJson = alertJson;
        hasQueuedAlert = true;
        Serial.println("⚠️ Alert upload failed. Alert queued for Wi-Fi reconnect.");
      } else {
        hasQueuedAlert = false;
      }
    }
  } else if (wasInAlert) {
    wasInAlert = false;
    sendFirebaseHTTPS(alertUrl, "null"); // Clear hardware alert in RTDB
    Serial.println("✅ Hardware Alert cleared on server.");
  }

  // 5. Retry Queued Offline Alert if Wi-Fi Restored
  if (hasQueuedAlert && WiFi.status() == WL_CONNECTED) {
    Serial.println("🔄 Retrying queued offline alert upload...");
    if (sendFirebaseHTTPS(alertUrl, pendingQueuedAlertJson)) {
      hasQueuedAlert = false;
      pendingQueuedAlertJson = "";
      Serial.println("✅ Queued alert uploaded successfully!");
    }
  }

  delay(2500);
}
