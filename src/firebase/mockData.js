export const DEFAULT_TELEMETRY = {
  node_id: "D-SQUARE_NODE_01",
  temperature: 26.5,
  humidity: 55.0,
  soil_moisture: 42.0,
  soil_raw: 850,
  mq2_gas: 0,
  smoke: 0,
  tilt: 0,
  vibration: 0,
  flame: 0,
  water_level: 5.0,
  scenario: "normal",
  disaster_type: "none",
  updated_at: Date.now()
};

export const SAMPLE_HARDWARE_ALERT = {
  event_id: "EVT-HW-849201",
  node_id: "D-SQUARE_NODE_01",
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
    temperature_c: 44.8,
    humidity_pct: 18.0,
    soil_moisture_pct: 12.0,
    soil_raw: 850,
    mq2_smoke: 1,
    flame: 1,
    vibration: 0.2
  },
  updated_at: Date.now()
};

export const SAMPLE_VERIFIED_INCIDENT = {
  incident_id: "DSQ-SOS-001",
  source_event_id: "EVT-HW-849201",
  source_node_id: "D-SQUARE_NODE_01",
  disaster_type: "fire",
  severity: "CRITICAL",
  confidence: 0.95,
  location_name: "Uttarakhand Slope Sector 4",
  latitude: 30.0668,
  longitude: 79.0193,
  status: "SOS_ACTIVE",
  verified_by: "operator@dsquare.gov.in",
  verification_note: "Verified active flame hotspot on mobile sentinel camera feed.",
  verified_at: Date.now() - 300000,
  dispatch: {
    dsquare_gpt: "DISPATCHED",
    rescue_gpt: "DISPATCHED"
  }
};
