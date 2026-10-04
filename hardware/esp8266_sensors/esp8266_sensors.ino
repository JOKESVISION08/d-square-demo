/*
  D-SQUARE 2.0 - IoT Ground Station Node Firmware
  Auto-Reset Alert Logic (Flame + Smoke + Soil Moisture Only)

  MQ-2 logic FIXED for modules where:
    - No smoke (clean air) => D0 = HIGH
    - Smoke detected       => D0 = LOW

  Behavior:
    - If flame OR smoke OR soil_raw < 800:
        • Green LED OFF
        • Red LED ON
        • Buzzer ON continuously
    - When all sensors return to normal:
        • Green LED ON
        • Red LED OFF
        • Buzzer OFF

  Pin Mapping:
    - DHT11 Temp & Humidity      -> D5 (GPIO14)
    - Capacitive Soil Moisture   -> A0 (Analog ADC)
    - MQ-2 Gas & Smoke (D0)      -> D6 (GPIO12)
    - IR Flame Sensor            -> D2 (GPIO4)
    - Green Status LED           -> D1 (GPIO5) via 220Ω
    - Red Alert LED              -> D3 (GPIO0) via 220Ω
    - Buzzer                     -> D4 (GPIO2)
        • Buzzer+: D4, Buzzer-: GND
        • Red LED+: 220Ω -> D3, Red LED-: GND
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

// ---------- WiFi & Server Configuration ----------
const char* ssid     = "Joke";
const char* password = "Joke@2005";

const char* localServerUrl   = "http://10.172.49.122:5001/api/sensor_data";
const char* hardwareAlertUrl = "http://10.172.49.122:5001/api/v1/hardware-alert";
const char* cloudflareUrl    = "https://competitors-insert-peas-above.trycloudflare.com/api/sensor_data";

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

  // Start in normal display mode
  setNormalOutputs();

  dht.begin();

  Serial.println();
  Serial.println("===============================================");
  Serial.println("D-SQUARE 2.0: Auto-Reset Alert System");
  Serial.println("MQ-2: HIGH = no smoke, LOW = smoke detected");
  Serial.println("Alert: Flame OR Smoke OR Soil Raw < 800");
  Serial.println("Normal: Green ON | Alert: Red + Buzzer ON");
  Serial.println("===============================================");

  connectToWiFi();
}

// ---------- Telemetry Send Function ----------
void sendTelemetryToServer(float temp, float hum, int soilRaw, float soilPct,
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

  String jsonPayload = "{";
  jsonPayload += "\"node_id\":\"D-SQUARE_NODE_01\",";
  jsonPayload += "\"temperature\":" + String(isnan(temp) ? 25.0 : temp, 1) + ",";
  jsonPayload += "\"humidity\":" + String(isnan(hum) ? 50.0 : hum, 1) + ",";
  jsonPayload += "\"soil_moisture\":" + String(soilPct, 1) + ",";
  jsonPayload += "\"soil_raw\":" + String(soilRaw) + ",";
  jsonPayload += "\"mq2_gas\":" + String(mq2Gas) + ",";
  jsonPayload += "\"flame\":" + String(flame) + ",";
  jsonPayload += "\"disaster_type\":\"" + disasterStr + "\",";
  jsonPayload += "\"scenario\":\"" + scenarioStr + "\"";
  jsonPayload += "}";

  Serial.println("\nTelemetry:");
  Serial.println(jsonPayload);

  // Step 1: Local HTTP telemetry
  WiFiClient client;
  HTTPClient http;
  http.begin(client, localServerUrl);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(jsonPayload);
  if (httpCode > 0) {
    Serial.print("Telemetry HTTP code: ");
    Serial.println(httpCode);
  } else {
    Serial.print("Local HTTP error: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }
  http.end();

  // Step 2: Hardware alert endpoint only while a hazard exists
  if (isAlert) {
    String hwPayload = "{";
    hwPayload += "\"event_id\":\"EVT-HW-" + String(millis()) + "\",";
    hwPayload += "\"node_id\":\"D-SQUARE_NODE_01\",";
    hwPayload += "\"disaster_type\":\"" + disasterStr + "\",";
    hwPayload += "\"severity\":\"CRITICAL\",";
    hwPayload += "\"confidence\":0.95,";
    hwPayload += "\"latitude\":30.0668,";
    hwPayload += "\"longitude\":79.0193,";
    hwPayload += "\"location_name\":\"Uttarakhand Slope Sector 4\",";
    hwPayload += "\"sensor_readings\":{\"temp\":" + String(temp, 1);
    hwPayload += ",\"hum\":" + String(hum, 1);
    hwPayload += ",\"soil\":" + String(soilPct, 1);
    hwPayload += ",\"soil_raw\":" + String(soilRaw);
    hwPayload += ",\"mq2\":" + String(mq2Gas);
    hwPayload += ",\"flame\":" + String(flame) + "}";
    hwPayload += "}";

    HTTPClient httpAlert;
    httpAlert.begin(client, hardwareAlertUrl);
    httpAlert.addHeader("Content-Type", "application/json");
    int alertCode = httpAlert.POST(hwPayload);
    if (alertCode > 0) {
      Serial.print("Hardware alert HTTP code: ");
      Serial.println(alertCode);
    }
    httpAlert.end();
  }

  // Step 3: HTTPS fallback telemetry
  WiFiClientSecure secureClient;
  secureClient.setInsecure();

  HTTPClient https;
  https.begin(secureClient, cloudflareUrl);
  https.addHeader("Content-Type", "application/json");
  int httpsCode = https.POST(jsonPayload);

  if (httpsCode > 0) {
    Serial.print("Cloudflare HTTPS code: ");
    Serial.println(httpsCode);
  } else {
    Serial.print("Cloudflare HTTPS error: ");
    Serial.println(https.errorToString(httpsCode).c_str());
  }
  https.end();
}

// ---------- Main Loop ----------
void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  int soilRaw = analogRead(SOIL_PIN);
  float soilMoisturePct = map(soilRaw, 1023, 0, 0, 100);
  soilMoisturePct = constrain(soilMoisturePct, 0.0, 100.0);

  // Read MQ-2 digital output
  int mq2Raw = digitalRead(MQ2_PIN);
  // INVERTED logic for your module:
  //   LOW  => smoke detected
  //   HIGH => no smoke
  int mq2Gas = (mq2Raw == LOW) ? 1 : 0;

  // Flame module logic: LOW = flame detected
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

  // Auto-reset state: evaluated on every loop.
  if (isAlert) {
    setAlertOutputs();
    Serial.println("OUTPUT: Red ON | Buzzer ON");
  } else {
    setNormalOutputs();
    Serial.println("OUTPUT: Green ON | Buzzer OFF");
  }

  sendTelemetryToServer(
    temperature, humidity, soilRaw, soilMoisturePct,
    mq2Gas, flame, isAlert
  );

  delay(2000);
}
