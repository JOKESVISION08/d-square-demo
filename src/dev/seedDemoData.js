import { ref, set, serverTimestamp } from "firebase/database";
import { database, isUsingEmulator } from "../firebase/config";
import { simulateHardwareAlert, clearHardwareAlert } from "../firebase/realtime";

const NODE_ID = "D-SQUARE_NODE_01";

export async function seedNormalTelemetry() {
  const payload = {
    node_id: NODE_ID,
    temperature: 25.0,
    humidity: 50.0,
    soil_moisture: 42.0,
    soil_raw: 850,
    mq2_gas: 0,
    flame: 0,
    tilt: "LEVEL",
    vibration: "STABLE",
    scenario: "normal",
    updated_at: Date.now()
  };

  try {
    const telemetryRef = ref(database, `nodes/${NODE_ID}/telemetry`);
    await set(telemetryRef, payload);
    console.log("🌱 [DEMO SEED] Normal telemetry loaded into Firebase.");
  } catch (err) {
    console.warn("Firebase seed fallback:", err);
  }
}

export async function seedFireHardwareWarning() {
  const payload = {
    event_id: "EVT-HW-DEMO-FIRE-001",
    node_id: NODE_ID,
    event_status: "ACTIVE",
    disaster_type: "fire",
    severity: "CRITICAL",
    confidence: 0.95,
    requires_operator_verification: true,
    auto_sos_dispatch: false,
    latitude: 30.0668,
    longitude: 79.0193,
    location_name: "Uttarakhand Slope Sector 4",
    sensor_readings: {
      temperature_c: 31.2,
      humidity_pct: 47.0,
      soil_moisture_pct: 42.0,
      soil_raw: 850,
      mq2_smoke: 1,
      flame: 0
    },
    updated_at: Date.now()
  };

  simulateHardwareAlert("fire", NODE_ID);
  try {
    const alertRef = ref(database, `nodes/${NODE_ID}/hardware_alert`);
    await set(alertRef, payload);
    console.log("🔥 [DEMO SEED] Silent fire warning loaded into Firebase.");
  } catch (err) {
    console.warn("Firebase seed fallback:", err);
  }
}

export async function seedLandslideHardwareWarning() {
  const payload = {
    event_id: "EVT-HW-DEMO-LANDSLIDE-001",
    node_id: NODE_ID,
    event_status: "ACTIVE",
    disaster_type: "landslide",
    severity: "HIGH",
    confidence: 0.88,
    requires_operator_verification: true,
    auto_sos_dispatch: false,
    latitude: 30.0668,
    longitude: 79.0193,
    location_name: "Uttarakhand Slope Sector 4",
    sensor_readings: {
      soil_moisture_pct: 90.0,
      soil_raw: 650,
      tilt: "SLOPE DISPLACEMENT WARNING",
      vibration: "STABLE"
    },
    updated_at: Date.now()
  };

  simulateHardwareAlert("landslide", NODE_ID);
  try {
    const alertRef = ref(database, `nodes/${NODE_ID}/hardware_alert`);
    await set(alertRef, payload);
    console.log("⛰️ [DEMO SEED] Silent landslide warning loaded into Firebase.");
  } catch (err) {
    console.warn("Firebase seed fallback:", err);
  }
}

export async function clearHardwareWarning() {
  clearHardwareAlert(NODE_ID);
  try {
    const alertRef = ref(database, `nodes/${NODE_ID}/hardware_alert`);
    await set(alertRef, null);
    console.log("🧹 [DEMO SEED] Hardware warning cleared.");
  } catch (err) {
    console.warn("Firebase seed fallback:", err);
  }
}

export async function resetAllDemoData() {
  await seedNormalTelemetry();
  await clearHardwareWarning();
  try {
    const incidentsRef = ref(database, `incidents`);
    await set(incidentsRef, null);
    console.log("🔄 [DEMO SEED] Reset all demo data and cleared incidents.");
  } catch (err) {
    console.warn("Firebase seed fallback:", err);
  }
}
