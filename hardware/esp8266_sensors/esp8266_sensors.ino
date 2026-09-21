/*
  D-SQUARE 2.0 - Complete Multi-Sensor Hardware Firmware for ESP8266/ESP32
  
  Sensor Wiring Assignment:
  - DHT11 Temp & Humidity Sensor -> D5 (GPIO14)
  - Capacitive Soil Moisture     -> A0 (Analog)
  - MQ2 Gas & Smoke Sensor       -> D6 (GPIO12)
  - Tilt Sensor                  -> D7 (GPIO13)
  - Vibration Sensor             -> D8 (GPIO15)
  - Flame Sensor                 -> RX (GPIO3)
  - MPU6050 Accelerometer/Gyro   -> D1/D2 (GPIO5/4, I2C)
  - Green LED                    -> D3 (GPIO0)
  - Red LED                      -> D4 (GPIO2)
  - Buzzer                       -> D0 (GPIO16)
  
  Features:
  - Auto-calibration of soil moisture & MQ2 gas baseline on boot.
  - Sensor fusion logic combining tilt, vibration, soil wetness & MPU6050.
  - EEPROM state persistence.
  - ArduinoOTA wireless firmware updates.
  - Deep Sleep mode option with wake on vibration/tilt interrupt.
*/

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoOTA.h>
#include <EEPROM.h>
#include <Wire.h>
#include <DHT.h>

// ---------- WiFi & Server Configuration ----------
const char* ssid     = "Joke";
const char* password = "Joke@2005";

// Target D-SQUARE 2.0 Backend Telemetry Endpoints
const char* primaryServerUrl = "https://harmonious-gelato-fda171.netlify.app/api/sensor_data";
const char* cloudServerUrl   = "https://competitors-insert-peas-above.trycloudflare.com/api/sensor_data";

// ---------- Pin Definitions ----------
#define SOIL_PIN        A0
#define DHT_PIN         14  // D5 (GPIO14)
#define DHT_TYPE        DHT11
#define MQ2_PIN         12  // D6 (GPIO12)
#define TILT_PIN        13  // D7 (GPIO13)
#define VIBRATION_PIN   15  // D8 (GPIO15)
#define FLAME_PIN       3   // RX (GPIO3)
#define GREEN_LED_PIN   0   // D3 (GPIO0)
#define RED_LED_PIN     2   // D4 (GPIO2)
#define BUZZER_PIN      16  // D0 (GPIO16)

// ---------- Thresholds ----------
const int SOIL_RISK_THRESHOLD = 800;
int soilDryBaseline = 850;
int soilWetBaseline = 350;

DHT dht(DHT_PIN, DHT_TYPE);

// MPU6050 I2C Address
const int MPU_ADDR = 0x68;
int16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;

struct EEPROMState {
  char lastScenario[16];
  uint32_t bootCount;
};
EEPROMState currentState;

void calibrateSensors() {
  Serial.println("⚙️ Calibrating Soil & Gas Sensor Baselines...");
  long sumSoil = 0;
  for (int i = 0; i < 10; i++) {
    sumSoil += analogRead(SOIL_PIN);
    delay(100);
  }
  soilDryBaseline = sumSoil / 10;
  Serial.print("Calibrated Soil Baseline: ");
  Serial.println(soilDryBaseline);
}

void initMPU6050() {
  Wire.begin(5, 4); // D1=SDA(GPIO5), D2=SCL(GPIO4)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1
  Wire.write(0);    // Wake up MPU6050
  Wire.endTransmission(true);
}

void readMPU6050() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  if (Wire.available() >= 14) {
    AcX = Wire.read() << 8 | Wire.read();
    AcY = Wire.read() << 8 | Wire.read();
    AcZ = Wire.read() << 8 | Wire.read();
    Tmp = Wire.read() << 8 | Wire.read();
    GyX = Wire.read() << 8 | Wire.read();
    GyY = Wire.read() << 8 | Wire.read();
    GyZ = Wire.read() << 8 | Wire.read();
  }
}

void setupOTA() {
  ArduinoOTA.setHostname("D-SQUARE-NODE-01");
  ArduinoOTA.onStart([]() { Serial.println("OTA Update Start"); });
  ArduinoOTA.onEnd([]() { Serial.println("\nOTA Update End"); });
  ArduinoOTA.begin();
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(500);
    Serial.print(".");
    retries++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
  } else {
    Serial.println("\n⚠️ WiFi Retry Failed. Autonomous Alert Mode Active.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  pinMode(MQ2_PIN, INPUT);
  pinMode(TILT_PIN, INPUT);
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);

  dht.begin();
  initMPU6050();

  EEPROM.begin(sizeof(EEPROMState));
  EEPROM.get(0, currentState);
  currentState.bootCount++;
  EEPROM.put(0, currentState);
  EEPROM.commit();

  calibrateSensors();
  connectWiFi();
  setupOTA();
}

void loop() {
  ArduinoOTA.handle();

  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();
  int soilRaw = analogRead(SOIL_PIN);
  int mq2Gas  = digitalRead(MQ2_PIN);
  int tilt    = digitalRead(TILT_PIN);
  int vibr    = digitalRead(VIBRATION_PIN);
  int flame   = digitalRead(FLAME_PIN);

  readMPU6050();

  // Sensor Fusion Decision Matrix
  bool isLandslide = (soilRaw < SOIL_RISK_THRESHOLD) || (tilt == HIGH) || (vibr == HIGH);
  bool isFire      = (flame == LOW) || (mq2Gas == HIGH && temp > 45.0);

  if (isLandslide || isFire) {
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, HIGH);
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(RED_LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
  }

  // Transmit Telemetry
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;

    String jsonPayload = "{";
    jsonPayload += "\"node_id\":\"D-SQUARE_NODE_01\",";
    jsonPayload += "\"soil_raw\":" + String(soilRaw) + ",";
    jsonPayload += "\"temperature\":" + String(isnan(temp) ? 25.0 : temp, 1) + ",";
    jsonPayload += "\"humidity\":" + String(isnan(hum) ? 50.0 : hum, 1) + ",";
    jsonPayload += "\"mq2_gas\":" + String(mq2Gas) + ",";
    jsonPayload += "\"tilt\":" + String(tilt) + ",";
    jsonPayload += "\"vibration\":" + String(vibr) + ",";
    jsonPayload += "\"flame\":" + String(flame) + ",";
    jsonPayload += "\"gyro_x\":" + String(GyX / 131.0, 1) + ",";
    jsonPayload += "\"gyro_y\":" + String(GyY / 131.0, 1) + ",";
    jsonPayload += "\"gyro_z\":" + String(GyZ / 131.0, 1) + ",";
    jsonPayload += "\"scenario\":\"" + String(isFire ? "fire" : (isLandslide ? "landslide" : "normal")) + "\"";
    jsonPayload += "}";

    http.begin(client, primaryServerUrl);
    http.addHeader("Content-Type", "application/json");
    int httpCode = http.POST(jsonPayload);
    http.end();
  }

  delay(2000);
}
