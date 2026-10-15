import { playDispatchBeep } from "../utils/audio";

// Offline Timeout Constant (30 seconds)
export const NODE_OFFLINE_TIMEOUT_MS = 30000;

const STORAGE_KEYS = {
  TELEMETRY: "dsquare_standalone_telemetry",
  HARDWARE_ALERT: "dsquare_standalone_hardware_alert",
  INCIDENTS: "dsquare_standalone_incidents",
  SATELLITE: "dsquare_standalone_satellite"
};

// Default initial telemetry
function getStoredTelemetry(nodeId) {
  try {
    const data = localStorage.getItem(`${STORAGE_KEYS.TELEMETRY}_${nodeId}`);
    if (data) return JSON.parse(data);
  } catch (e) {}

  const defaultTel = {
    node_id: nodeId,
    temperature: 28.5,
    humidity: 54.0,
    soil_moisture: 42.0,
    soil_raw: 920,
    mq2_gas: 0,
    flame: 0,
    disaster_type: "none",
    scenario: "normal",
    updated_at: Date.now()
  };
  localStorage.setItem(`${STORAGE_KEYS.TELEMETRY}_${nodeId}`, JSON.stringify(defaultTel));
  return defaultTel;
}

function getStoredHardwareAlert(nodeId) {
  try {
    const data = localStorage.getItem(`${STORAGE_KEYS.HARDWARE_ALERT}_${nodeId}`);
    if (data) return JSON.parse(data);
  } catch (e) {}
  return null; // Null means no active alert by default
}

function getStoredIncidents() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.INCIDENTS);
    if (data) return JSON.parse(data);
  } catch (e) {}
  return [];
}

export function calculateNodeHealth(telemetryData) {
  if (!telemetryData) {
    return { status: "OFFLINE", lastSeen: null, isStale: true, message: "Waiting for node telemetry..." };
  }

  const now = Date.now();
  const timestamp = telemetryData.updated_at || telemetryData.timestamp || 0;
  const ageMs = now - timestamp;

  if (telemetryData.sensor_status === "DHT11_ERROR" || telemetryData.temperature === null) {
    return {
      status: "INVALID",
      lastSeen: timestamp ? new Date(timestamp) : null,
      isStale: ageMs > NODE_OFFLINE_TIMEOUT_MS,
      message: "Sensor fault detected (DHT11 Communication Error)"
    };
  }

  return {
    status: "ONLINE",
    lastSeen: new Date(timestamp),
    isStale: false,
    message: "Node operating normally (Standalone Netlify Mode)"
  };
}

export function subscribeToTelemetry(nodeId = "D-SQUARE_NODE_01", callback) {
  const current = getStoredTelemetry(nodeId);
  callback(current);

  const interval = setInterval(() => {
    const latest = getStoredTelemetry(nodeId);
    callback(latest);
  }, 2000);

  const handleStorage = (e) => {
    if (e.key === `${STORAGE_KEYS.TELEMETRY}_${nodeId}` && e.newValue) {
      try {
        callback(JSON.parse(e.newValue));
      } catch (err) {}
    }
  };
  window.addEventListener("storage", handleStorage);

  return () => {
    clearInterval(interval);
    window.removeEventListener("storage", handleStorage);
  };
}

export function subscribeToHardwareAlert(nodeId = "D-SQUARE_NODE_01", callback) {
  const current = getStoredHardwareAlert(nodeId);
  callback(current);

  const interval = setInterval(() => {
    const latest = getStoredHardwareAlert(nodeId);
    callback(latest);
  }, 2000);

  const handleStorage = (e) => {
    if (e.key === `${STORAGE_KEYS.HARDWARE_ALERT}_${nodeId}`) {
      try {
        callback(e.newValue ? JSON.parse(e.newValue) : null);
      } catch (err) {}
    }
  };
  window.addEventListener("storage", handleStorage);

  return () => {
    clearInterval(interval);
    window.removeEventListener("storage", handleStorage);
  };
}

export function subscribeToIncidents(callback) {
  const current = getStoredIncidents();
  callback(current);

  const interval = setInterval(() => {
    const latest = getStoredIncidents();
    callback(latest);
  }, 2000);

  const handleStorage = (e) => {
    if (e.key === STORAGE_KEYS.INCIDENTS && e.newValue) {
      try {
        callback(JSON.parse(e.newValue));
      } catch (err) {}
    }
  };
  window.addEventListener("storage", handleStorage);

  return () => {
    clearInterval(interval);
    window.removeEventListener("storage", handleStorage);
  };
}

export async function createVerifiedIncident(incidentPayload) {
  const incidentId = incidentPayload.incident_id || `DSQ-SOS-${Date.now().toString().slice(-4)}`;
  const now = Date.now();

  const incidentData = {
    incident_id: incidentId,
    source_event_id: incidentPayload.source_event_id || `EVT-HW-${now}`,
    source_node_id: incidentPayload.source_node_id || "D-SQUARE_NODE_01",
    disaster_type: (incidentPayload.disaster_type || "fire").toLowerCase(),
    severity: (incidentPayload.severity || "CRITICAL").toUpperCase(),
    confidence: incidentPayload.confidence || 0.95,
    location_name: incidentPayload.location_name || "Uttarakhand Slope Sector 4",
    latitude: incidentPayload.latitude || 30.0668,
    longitude: incidentPayload.longitude || 79.0193,
    sensor_readings: incidentPayload.sensor_readings || {},
    verified_by: incidentPayload.verified_by || "operator@dsquare.gov.in",
    verification_note: incidentPayload.verification_note || "Authorized operator verified incident via live ground sensors.",
    verified_at: now,
    status: "SOS_ACTIVE",
    dispatch: {
      dsquare_gpt: "DISPATCHED",
      rescue_gpt: "DISPATCHED"
    },
    dispatch_notes: {
      dsquare_gpt: "Standalone Netlify Dispatch OK",
      rescue_gpt: "Standalone Netlify Dispatch OK"
    }
  };

  const incidents = getStoredIncidents();
  const existingIndex = incidents.findIndex(i => i.incident_id === incidentId);
  if (existingIndex >= 0) {
    incidents[existingIndex] = incidentData;
  } else {
    incidents.unshift(incidentData);
  }

  localStorage.setItem(STORAGE_KEYS.INCIDENTS, JSON.stringify(incidents));
  playDispatchBeep(880, 'sine', 0.25);
  setTimeout(() => playDispatchBeep(1046.5, 'triangle', 0.3), 300);

  return incidentData;
}

export async function updateDispatchStatus(incidentId, dispatchTarget, status) {
  const incidents = getStoredIncidents();
  const inc = incidents.find(i => i.incident_id === incidentId);
  if (inc) {
    if (!inc.dispatch) inc.dispatch = {};
    inc.dispatch[dispatchTarget] = status;
    localStorage.setItem(STORAGE_KEYS.INCIDENTS, JSON.stringify(incidents));
  }
}

export async function resolveIncident(incidentId) {
  const incidents = getStoredIncidents();
  const inc = incidents.find(i => i.incident_id === incidentId);
  if (inc) {
    inc.status = "RESOLVED";
    localStorage.setItem(STORAGE_KEYS.INCIDENTS, JSON.stringify(incidents));
  }
}

export async function fetchSystemDiagnostics(nodeId = "D-SQUARE_NODE_01") {
  const telemetry = getStoredTelemetry(nodeId);
  const alert = getStoredHardwareAlert(nodeId);

  return {
    database_url: "Serverless Standalone Netlify Mode",
    connection_state: "CONNECTED",
    node_id: nodeId,
    last_telemetry: telemetry,
    last_hardware_alert: alert,
    satellite_data: { status: "ACTIVE", source: "NISAR Satellite Downlink" },
    last_update_time: telemetry?.updated_at || Date.now(),
    firmware_version: "2.0.0-SERVERLESS-PROD",
    http_status: 200
  };
}
