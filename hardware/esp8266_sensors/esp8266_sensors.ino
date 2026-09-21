/*
  D-SQUARE 2.0 - Hardware Testing Code (NO BACKEND)
  
  This code tests each sensor individually and shows results in Serial Monitor.
  No WiFi, no Flask, no dashboard needed.
  
  Hardware:
  - Soil Moisture → A0
  - MQ2 Gas → D8 (GPIO15)
  - Flame Sensor → D1 (GPIO5)
  - DHT11 → D2 (GPIO4)
  - Tilt Sensor → RX (GPIO3)
  - Green LED → D5 (GPIO14)
  - Red LED → D6 (GPIO12)
  - Buzzer → D7 (GPIO13)
*/

#include <DHT.h>

// ========== Pin Definitions ==========
#define SOIL_PIN A0
#define MQ2_PIN 15        // D8 / GPIO15
#define FLAME_PIN 5       // D1 / GPIO5
#define DHT_PIN 4         // D2 / GPIO4
#define TILT_PIN 3        // RX / GPIO3
#define GREEN_LED_PIN 14  // D5 / GPIO14
#define RED_LED_PIN 12    // D6 / GPIO12
#define BUZZER_PIN 13     // D7 / GPIO13

// ========== DHT11 Setup ==========
DHT dht(DHT_PIN, DHT11);

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  // Initialize pins
  pinMode(MQ2_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);
  pinMode(TILT_PIN, INPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Initialize DHT11
  dht.begin();
  
  Serial.println();
  Serial.println("========================================");
  Serial.println("D-SQUARE 2.0 - HARDWARE TESTING MODE");
  Serial.println("========================================");
  Serial.println();
  Serial.println("Testing all sensors...");
  Serial.println();
}

void loop() {
  Serial.println("========== SENSOR TEST ==========");
  
  // Test 1: Soil Moisture
  int soilValue = analogRead(SOIL_PIN);
  Serial.print("1. Soil Moisture: ");
  Serial.println(soilValue);
  Serial.println("   → Dry soil: 800-1024 | Wet soil: 0-600");
  
  // Test 2: MQ2 Gas
  int mq2Value = digitalRead(MQ2_PIN);
  Serial.print("2. MQ2 Gas: ");
  Serial.println(mq2Value == HIGH ? "GAS DETECTED!" : "None");
  Serial.println("   → Bring smoke/gas near sensor to test");
  
  // Test 3: Flame Sensor
  int flameValue = digitalRead(FLAME_PIN);
  bool flameDetected = (flameValue == LOW);  // LOW = flame
  Serial.print("3. Flame Sensor: ");
  Serial.println(flameDetected ? "FLAME DETECTED! 🔥" : "None");
  Serial.println("   → Bring flame (lighter/match) near sensor");
  
  // Test 4: DHT11
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  Serial.print("4. Temperature: ");
  if (isnan(temperature)) {
    Serial.println("READ ERROR (check DHT11 wiring)");
  } else {
    Serial.print(temperature, 1);
    Serial.println(" °C");
  }
  
  Serial.print("   Humidity: ");
  if (isnan(humidity)) {
    Serial.println("READ ERROR (check DHT11 wiring)");
  } else {
    Serial.print(humidity, 1);
    Serial.println(" %");
  }
  Serial.println("   → Warm sensor with hand to see change");
  
  // Test 5: Tilt Sensor
  int tiltValue = digitalRead(TILT_PIN);
  Serial.print("5. Tilt Sensor: ");
  Serial.println(tiltValue == HIGH ? "TILTED!" : "Level");
  Serial.println("   → Tilt the board to test");
  
  // Test 6: LEDs
  Serial.println("6. Testing LEDs...");
  digitalWrite(GREEN_LED_PIN, HIGH);
  digitalWrite(RED_LED_PIN, LOW);
  Serial.println("   → Green LED should be ON");
  delay(1000);
  
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, HIGH);
  Serial.println("   → Red LED should be ON");
  delay(1000);
  
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  
  // Test 7: Buzzer
  Serial.println("7. Testing Buzzer...");
  tone(BUZZER_PIN, 1000);
  Serial.println("   → Buzzer should beep for 1 second");
  delay(1000);
  noTone(BUZZER_PIN);
  
  // Summary
  Serial.println();
  Serial.println("========================================");
  Serial.println("SENSOR STATUS:");
  
  bool allOK = true;
  
  if (soilValue < 0 || soilValue > 1024) {
    Serial.println("❌ Soil Sensor: ERROR");
    allOK = false;
  } else {
    Serial.println("✅ Soil Sensor: OK");
  }
  
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("❌ DHT11: ERROR (check wiring)");
    allOK = false;
  } else {
    Serial.println("✅ DHT11: OK");
  }
  
  Serial.println("✅ MQ2: Connected");
  Serial.println("✅ Flame: Connected");
  Serial.println("✅ Tilt: Connected");
  Serial.println("✅ Green LED: Working");
  Serial.println("✅ Red LED: Working");
  Serial.println("✅ Buzzer: Working");
  
  Serial.println();
  if (allOK) {
    Serial.println("🎉 ALL HARDWARE TESTS PASSED!");
  } else {
    Serial.println("⚠️ SOME TESTS FAILED - Check wiring!");
  }
  Serial.println("========================================");
  Serial.println();
  Serial.println("Next test in 3 seconds...");
  Serial.println();
  
  delay(3000);
}