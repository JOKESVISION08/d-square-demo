import { ref, onValue, set, get } from "firebase/database";
import { database, isConfigured } from "./config";
import { playDispatchBeep } from "../utils/audio";

// Offline Timeout Constant (30 seconds)
export const NODE_OFFLINE_TIMEOUT_MS = 30000;

/**
 * Calculates real-time connection status for ESP8266 node based on telemetry timestamp.
 * Returns: { status: 'ONLINE'|'OFFLINE'|'STALE'|'INVALID', lastSeen: Date|null, isStale: boolean }
 */
export function calculateNodeHealth(telemetryData) {
  if (!telemetryData) {
    return { status: "OFFLINE", lastSeen: null, isStale: true, message: "Waiting for real ESP8266 telemetry..." };
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

  if (!timestamp || ageMs > NODE_OFFLINE_TIMEOUT_MS) {
    return {
      status: "OFFLINE",
      lastSeen: timestamp ? new Date(timestamp) : null,
      isStale: true,
      message: "NODE OFFLINE (No telemetry received in last 30s)"
    };
  }

  if (ageMs > 15000) {
    return {
      status: "STALE",
      lastSeen: new Date(timestamp),
      isStale: true,
      message: "Telemetry signal delayed (>15s)"
    };
  }

  return {
    status: "ONLINE",
    lastSeen: new Date(timestamp),
    isStale: false,
    message: "Node operating normally"
  };
}

// Subscribes to real production ESP8266 telemetry path `/nodes/{node_id}/telemetry`
export function subscribeToTelemetry(nodeId = "D-SQUARE_NODE_01", callback) {
  if (!database) {
    callback(null);
    return () => {};
  }

  const telemetryRef = ref(database, `nodes/${nodeId}/telemetry`);
  return onValue(telemetryRef, (snapshot) => {
    const val = snapshot.val();
    callback(val);
  }, (err) => {
    console.warn("Firebase telemetry listener error:", err.message);
    callback(null);
  });
}

// Subscribes to real production hardware alert path `/nodes/{node_id}/hardware_alert`
export function subscribeToHardwareAlert(nodeId = "D-SQUARE_NODE_01", callback) {
  if (!database) {
    callback(null);
    return () => {};
  }

  const alertRef = ref(database, `nodes/${nodeId}/hardware_alert`);
  return onValue(alertRef, (snapshot) => {
    const val = snapshot.val();
    callback(val);
  }, (err) => {
    console.warn("Firebase hardware alert listener error:", err.message);
    callback(null);
  });
}

// Subscribes to real incidents list `/incidents`
export function subscribeToIncidents(callback) {
  if (!database) {
    callback([]);
    return () => {};
  }

  const incidentsRef = ref(database, `incidents`);
  return onValue(incidentsRef, (snapshot) => {
    const val = snapshot.val();
    if (val) {
      const list = Object.values(val).sort((a, b) => (b.verified_at || 0) - (a.verified_at || 0));
      callback(list);
    } else {
      callback([]);
    }
  }, (err) => {
    console.warn("Firebase incidents listener error:", err.message);
    callback([]);
  });
}

/**
 * Creates a verified SOS incident in production Firebase upon human operator confirmation.
 */
export async function createVerifiedIncident(incidentPayload) {
  const incidentId = incidentPayload.incident_id || `DSQ-SOS-${Date.now().toString().slice(-4)}`;
  const now = Date.now();

  const dsquareEndpoint = import.meta.env.VITE_DSQUARE_GPT_ENDPOINT || import.meta.env.VITE_DSQUARE_GPT_WEBHOOK_URL;
  const rescueEndpoint = import.meta.env.VITE_RESCUE_GPT_ENDPOINT || import.meta.env.VITE_RESCUE_GPT_WEBHOOK_URL;

  const initialDsquareStatus = dsquareEndpoint ? "PENDING" : "FAILED";
  const initialRescueStatus = rescueEndpoint ? "PENDING" : "FAILED";

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
      dsquare_gpt: initialDsquareStatus,
      rescue_gpt: initialRescueStatus
    },
    dispatch_notes: {
      dsquare_gpt: dsquareEndpoint ? "Endpoint configured, dispatching..." : "External dispatch endpoint not configured.",
      rescue_gpt: rescueEndpoint ? "Endpoint configured, dispatching..." : "External dispatch endpoint not configured."
    }
  };

  const incidentRef = ref(database, `incidents/${incidentId}`);
  await set(incidentRef, incidentData);

  // Execute Parallel Dispatch to configured external endpoints
  executeParallelDispatch(incidentId, incidentData, dsquareEndpoint, rescueEndpoint);
  return incidentData;
}

/**
 * Parallel Multi-Agent GPT Dispatch Execution.
 * Updates dispatch status and triggers Web Audio API audio beeps ONLY after confirmation.
 */
async function executeParallelDispatch(incidentId, incidentData, dsquareEndpoint, rescueEndpoint) {
  const dsquarePromise = (async () => {
    if (dsquareEndpoint) {
      try {
        await fetch(dsquareEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: "DSQUARE_GPT", incident: incidentData })
        });
        await updateDispatchStatus(incidentId, "dsquare_gpt", "DISPATCHED");
        playDispatchBeep(880, 'sine', 0.25);
      } catch (err) {
        console.error("D-SQUARE GPT Dispatch Error:", err);
        await updateDispatchStatus(incidentId, "dsquare_gpt", "FAILED");
      }
    } else {
      await updateDispatchStatus(incidentId, "dsquare_gpt", "FAILED");
    }
  })();

  const rescuePromise = (async () => {
    if (rescueEndpoint) {
      try {
        await fetch(rescueEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: "RESCUE_GPT", incident: incidentData })
        });
        await updateDispatchStatus(incidentId, "rescue_gpt", "DISPATCHED");
        setTimeout(() => playDispatchBeep(1046.5, 'triangle', 0.3), 300);
      } catch (err) {
        console.error("Rescue GPT Dispatch Error:", err);
        await updateDispatchStatus(incidentId, "rescue_gpt", "FAILED");
      }
    } else {
      await updateDispatchStatus(incidentId, "rescue_gpt", "FAILED");
    }
  })();

  await Promise.all([dsquarePromise, rescuePromise]);
}

export async function updateDispatchStatus(incidentId, dispatchTarget, status) {
  if (!database) return;
  const dispatchRef = ref(database, `incidents/${incidentId}/dispatch/${dispatchTarget}`);
  await set(dispatchRef, status);
}

export async function resolveIncident(incidentId) {
  if (!database || !incidentId) return;
  const statusRef = ref(database, `incidents/${incidentId}/status`);
  await set(statusRef, "RESOLVED");
}

/**
 * Fetches current system diagnostics details for /diagnostics page.
 */
export async function fetchSystemDiagnostics(nodeId = "D-SQUARE_NODE_01") {
  if (!database) {
    return {
      database_url: "Not Configured",
      connection_state: "DISCONNECTED",
      node_id: nodeId,
      last_telemetry: null,
      last_hardware_alert: null,
      last_error: "Firebase Realtime Database instance unavailable."
    };
  }

  try {
    const telemetrySnap = await get(ref(database, `nodes/${nodeId}/telemetry`));
    const alertSnap = await get(ref(database, `nodes/${nodeId}/hardware_alert`));
    const satSnap = await get(ref(database, `satellite`));

    const telemetry = telemetrySnap.val();
    const alert = alertSnap.val();
    const sat = satSnap.val();

    return {
      database_url: import.meta.env.VITE_FIREBASE_DATABASE_URL || "https://d-sqaure-default-rtdb.firebaseio.com",
      connection_state: "CONNECTED",
      node_id: nodeId,
      last_telemetry: telemetry,
      last_hardware_alert: alert,
      satellite_data: sat,
      last_update_time: telemetry?.updated_at || Date.now(),
      firmware_version: "2.0.0-PROD-HTTPS",
      http_status: 200
    };
  } catch (err) {
    return {
      database_url: import.meta.env.VITE_FIREBASE_DATABASE_URL || "https://d-sqaure-default-rtdb.firebaseio.com",
      connection_state: "AUTHENTICATION_ERROR",
      node_id: nodeId,
      last_error: err.message,
      http_status: 403
    };
  }
}
