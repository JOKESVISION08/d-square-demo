/*
 * D-SQUARE 2.0 (Disaster Surveillance using Quadruple UAV AI Remote Earth-observation)
 * ESP8266 NodeMCU Firmware (10 Sensors + Alert Controls)
 * 
 * FINAL CORRECTED Pin Configuration - ALL CONFLICTS RESOLVED
 * 
 * Hardware Connections:
 * - DHT11 (Temp/Humidity): GPIO 14 (D5)
 * - Soil Moisture Sensor: Analog A0 + Power Control GPIO 16 (D0)
 * - MQ-2 Smoke Sensor: Digital Output GPIO 10 (RX) - ALREADY CONNECTED
 * - SW-420 Vibration Sensor: GPIO 12 (D6)
 * - SW-520D Tilt Sensor: GPIO 13 (D7)
 * - HC-SR04 Ultrasonic (Water Level): TRIG GPIO 15 (D8), ECHO GPIO 3 (RX)
 * - MPU6050 (Vibration/Accel): I2C SDA GPIO 4 (D2), SCL GPIO 5 (D1)
 * - RGB Alert LED: Red GPIO 1 (TX), Green GPIO 2 (D4)
 * - Piezo Buzzer: GPIO 0 (D3)
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ==================== WiFi Configuration ====================
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// ==================== Server Endpoint ====================
const char* serverUrl = "http://192.168.1.100:5000/api/sensor_data";

// ==================== FINAL CORRECTED Pin Definitions ====================
#define DHTPIN 14              // D5 - DHT11 Temperature/Humidity
#define DHTTYPE DHT11

#define SOIL_MOISTURE_PIN A0   // A0 - Soil Moisture Analog Output
#define SOIL_POWER_PIN 16      // D0 - Soil Sensor Power Control (prevents electrolysis)

#define MQ2_SMOKE_DO_PIN 10    // RX - MQ-2 Gas/Smoke Digital Output (ALREADY CONNECTED)

#define VIB_SW420_PIN 12       // D6 - SW-420 Digital Vibration Sensor
#define TILT_SW520_PIN 13      // D7 - SW-520D Tilt Ball Switch Sensor

#define TRIG_PIN 15            // D8 - HC-SR04 Ultrasonic Trigger
#define ECHO_PIN 3             // RX - HC-SR04 Ultrasonic Echo

#define RED_LED_PIN 1          // TX - Red Alert LED (Active LOW)
#define GREEN_LED_PIN 2        // D4 - Green Status LED (Active LOW)
#define BUZZER_PIN 0           // D3 - Piezo Buzzer (Active LOW)

// ==================== Global Objects ====================
DHT dht(DHTPIN, DHTTYPE);
Adafruit_MPU6050 mpu;

// ==================== Setup Function ====================
void setup() {
  Serial.begin(115200);
  delay(1000);

  // Initialize all pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(VIB_SW420_PIN, INPUT);
  pinMode(TILT_SW520_PIN, INPUT_PULLUP);
  pinMode(MQ2_SMOKE_DO_PIN, INPUT);
  pinMode(SOIL_POWER_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Initialize DHT11 sensor
  dht.begin();
  
  // Initialize I2C for MPU6050 (SDA=GPIO 4, SCL=GPIO 5)
  Wire.begin(4, 5);

  // Initialize MPU6050
  if (!mpu.begin()) {
    Serial.println("Warning: MPU6050 Gyro/Accelerometer not detected!");
  } else {
    Serial.println("MPU6050 initialized successfully!");
  }

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("\nConnecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Set default LED state (GREEN = Normal, RED = OFF)
  digitalWrite(GREEN_LED_PIN, LOW);    // GREEN ON (Active LOW)
  digitalWrite(RED_LED_PIN, HIGH);     // RED OFF (Active HIGH)
  digitalWrite(BUZZER_PIN, LOW);       // Buzzer OFF

  Serial.println("\n=== D-SQUARE 2.0 Node Initialized ===");
  Serial.println("Sensors: DHT11, Soil Moisture, MQ-2, Vibration, Tilt, HC-SR04, MPU6050");
  Serial.println("======================================\n");
}

// ==================== Main Loop Function ====================
void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    
    // ========== 1. Read DHT11 Temperature & Humidity ==========
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();
    
    // Handle sensor read errors
    if (isnan(temp)) {
      Serial.println("DHT11 Temperature read error, using default");
      temp = 25.0;
    }
    if (isnan(hum)) {
      Serial.println("DHT11 Humidity read error, using default");
      hum = 50.0;
    }

    // ========== 2. Read Capacitive Soil Moisture Sensor (with Power Control) ==========
    digitalWrite(SOIL_POWER_PIN, HIGH);  // Power ON soil probe
    delay(10);                            // Wait for sensor to stabilize
    int soilRaw = analogRead(SOIL_MOISTURE_PIN);
    digitalWrite(SOIL_POWER_PIN, LOW);   // Power OFF to prevent electrolysis/corrosion
    
    // Map raw ADC value (350-850) to percentage (0-100%)
    float soilMoisturePercent = map(soilRaw, 850, 350, 0, 100);
    soilMoisturePercent = constrain(soilMoisturePercent, 0, 100);  // Clamp to 0-100%

    // ========== 3. Read MQ-2 Smoke & Gas Detector (Digital Output) ==========
    float smokePpm = digitalRead(MQ2_SMOKE_DO_PIN) == HIGH ? 850.0 : 185.0;

    // ========== 4. Read SW-520D Tilt Switch & SW-420 Vibration Switch ==========
    int tiltState = digitalRead(TILT_SW520_PIN) == LOW ? 1 : 0;  // LOW = Tilted
    int vibAlarmState = digitalRead(VIB_SW420_PIN) == HIGH ? 1 : 0;  // HIGH = Vibration detected

    // ========== 5. Read HC-SR04 Ultrasonic Water Level ==========
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
    
    // Calculate distance in cm (speed of sound = 0.0343 cm/µs)
    float waterLevelCm = (duration * 0.0343) / 2.0;
    
    // Validate reading (0-400cm range)
    if (waterLevelCm < 0 || waterLevelCm > 400) {
      waterLevelCm = 0;  // Invalid reading
    }

    // ========== 6. Read MPU6050 6-Axis Gyro & Accelerometer ==========
    sensors_event_t a, g, temp_mpu;
    float vibration = 0.1;
    float tiltAngleDeg = 0.0;
    float gyroRotationDegS = 0.0;

    if (mpu.getEvent(&a, &g, &temp_mpu)) {
      // Calculate acceleration magnitude minus gravity (9.81 m/s²)
      float accelMag = sqrt(
        a.acceleration.x * a.acceleration.x +
        a.acceleration.y * a.acceleration.y +
        a.acceleration.z * a.acceleration.z
      );
      vibration = abs(accelMag - 9.81);

      // Calculate Pitch & Roll tilt angles in degrees
      float pitch = atan2(a.acceleration.y, a.acceleration.z) * 180.0 / M_PI;
      float roll = atan2(-a.acceleration.x, 
                sqrt(a.acceleration.y * a.acceleration.y + a.acceleration.z * a.acceleration.z)) * 180.0 / M_PI;
      tiltAngleDeg = sqrt(pitch * pitch + roll * roll);

      // Calculate gyroscope angular rate magnitude (deg/s)
      gyroRotationDegS = sqrt(
        g.gyro.x * g.gyro.x +
        g.gyro.y * g.gyro.y +
        g.gyro.z * g.gyro.z
      ) * 57.2958;  // Convert rad/s to deg/s
    }

    // ========== 7. Prepare JSON Payload ==========
    WiFiClient client;
    HTTPClient http;
    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{";
    jsonPayload += "\"temperature\":" + String(temp, 1) + ",";
    jsonPayload += "\"humidity\":" + String(hum, 1) + ",";
    jsonPayload += "\"smoke\":" + String(smokePpm, 1) + ",";
    jsonPayload += "\"soil_moisture\":" + String(soilMoisturePercent, 1) + ",";
    jsonPayload += "\"water_level\":" + String(waterLevelCm, 1) + ",";
    jsonPayload += "\"flame\":" + String(0) + ",";
    jsonPayload += "\"vibration\":" + String(vibration, 2) + ",";
    jsonPayload += "\"tilt_angle\":" + String(tiltAngleDeg, 1) + ",";
    jsonPayload += "\"gyro_rate\":" + String(gyroRotationDegS, 1) + ",";
    jsonPayload += "\"tilt_state\":" + String(tiltState) + ",";
    jsonPayload += "\"vibration_alarm\":" + String(vibAlarmState) + ",";
    jsonPayload += "\"node_id\":\"ESP8266_NODE_01\"";
    jsonPayload += "}";

    // ========== 8. Send Data to Server ==========
    Serial.println("\n--- Sending Sensor Data ---");
    Serial.println("Payload: " + jsonPayload);
    
    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("HTTP Response Code: " + String(httpResponseCode));
      Serial.println("Server Response: " + response);

      // ========== 9. Trigger Local Alarm if CRITICAL ==========
      bool isCritical = response.indexOf("CRITICAL") > 0;
      bool isHighTemp = temp > 45.0;
      bool isHighSmoke = smokePpm > 700;
      bool isHighVibration = vibration > 2.0;
      bool isTilted = tiltState == 1;

      if (isCritical || isHighTemp || isHighSmoke || isHighVibration || isTilted) {
        // Trigger RED LED + Buzzer alarm
        digitalWrite(RED_LED_PIN, LOW);     // RED ON (Active LOW)
        digitalWrite(GREEN_LED_PIN, HIGH);  // GREEN OFF
        tone(BUZZER_PIN, 1000);             // 1 kHz alarm sound
        
        Serial.println("⚠️ ALERT TRIGGERED! RED LED + BUZZER ON");
      } else {
        // Normal state - GREEN LED ON
        digitalWrite(RED_LED_PIN, HIGH);    // RED OFF
        digitalWrite(GREEN_LED_PIN, LOW);   // GREEN ON (Active LOW)
        noTone(BUZZER_PIN);                 // Buzzer OFF
        
        Serial.println("✅ Normal State - GREEN LED ON");
      }
    } else {
      Serial.println("Error on HTTP POST: " + String(httpResponseCode));
      
      // Connection error - blink RED LED
      digitalWrite(RED_LED_PIN, LOW);
      delay(200);
      digitalWrite(RED_LED_PIN, HIGH);
    }
    
    http.end();
    
  } else {
    // WiFi disconnected - blink RED LED
    Serial.println("WiFi Disconnected!");
    digitalWrite(RED_LED_PIN, LOW);
    delay(500);
    digitalWrite(RED_LED_PIN, HIGH);
    delay(500);
  }

  // ========== 10. Wait 5 Seconds Before Next Reading ==========
  delay(5000);
}
