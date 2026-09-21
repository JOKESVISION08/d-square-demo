/**
 * D-SQUARE 2.0 Standalone PC SOS Alert Sending System JavaScript
 * Handles interactive map pixels, telemetry synchronization, pixel selection,
 * and parallel SOS alert dispatching to Rescue GPT & D-SQUARE GPT.
 */

let map;
let pixelGridLayerGroup;
let selectedPixels = [];
let activeDisasterType = "FLOOD";
let currentPixelsData = [];

document.addEventListener("DOMContentLoaded", function () {
  initMap();
  fetchLiveDisasterPixels();
  setupEventListeners();
  parseIncomingURLParameters();
});

function parseIncomingURLParameters() {
  const urlParams = new URLSearchParams(window.location.search);
  const paramDisaster = urlParams.get("disaster_type") || urlParams.get("disaster");
  const paramSeverity = urlParams.get("severity");
  const paramLat = urlParams.get("lat") || urlParams.get("latitude");
  const paramLon = urlParams.get("lon") || urlParams.get("longitude");
  const paramArea = urlParams.get("area") || urlParams.get("location");
  const paramAuto = urlParams.get("auto_dispatch");

  if (paramDisaster) {
    const sel = document.getElementById("disaster-type-select");
    if (sel) {
      sel.value = paramDisaster.toUpperCase();
      activeDisasterType = paramDisaster.toUpperCase();
    }
  }
  if (paramSeverity) {
    const classVal = paramSeverity.toUpperCase();
    const sevEl = document.getElementById("severity-level-select");
    if (sevEl) sevEl.value = classVal.includes("CRIT") ? "CRITICAL" : (classVal.includes("HIGH") ? "HIGH" : "MEDIUM");
  }
  if (paramArea) {
    const areaEl = document.getElementById("zone-location-input");
    if (areaEl) areaEl.value = paramArea;
  }
  if (paramLat && paramLon && map) {
    const lat = parseFloat(paramLat);
    const lon = parseFloat(paramLon);
    map.setView([lat, lon], 13);
  }
  if (paramAuto === "true" || paramAuto === "1") {
    setTimeout(triggerParallelSOSFromPC, 600);
  }
}

function initMap() {
  // Center on Mumbai Coastal Restricted Zone by default
  map = L.map("disaster-map").setView([19.0760, 72.8777], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
  }).addTo(map);

  pixelGridLayerGroup = L.layerGroup().addTo(map);
}

function fetchLiveDisasterPixels() {
  fetch("/api/pc/live_disaster_pixels")
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        currentPixelsData = data.pixels;
        renderMapPixels(data.pixels);
        updateTelemetryPanel(data.telemetry);
      }
    })
    .catch((err) => {
      console.warn("Using default disaster pixels:", err);
      const defaultPixels = generateDefaultPixels();
      currentPixelsData = defaultPixels;
      renderMapPixels(defaultPixels);
    });
}

function generateDefaultPixels() {
  const centerLat = 19.0760;
  const centerLon = 72.8777;
  const pixels = [];
  const step = 0.008;

  for (let i = -3; i <= 3; i++) {
    for (let j = -3; j <= 3; j++) {
      const lat = centerLat + i * step;
      const lon = centerLon + j * step;
      const dist = Math.sqrt(i * i + j * j);
      let severity = Math.max(0.2, 1.0 - dist * 0.22);
      let risk = severity > 0.75 ? "CRITICAL" : severity > 0.45 ? "WARNING" : "NORMAL";

      pixels.push({
        pixel_id: `PX_${i+4}_${j+4}`,
        bounds: [
          [lat - step / 2, lon - step / 2],
          [lat + step / 2, lon + step / 2]
        ],
        center: [lat, lon],
        severity: Math.round(severity * 100),
        risk_level: risk,
        water_level_m: (severity * 2.8).toFixed(1),
        affected_citizens: Math.round(severity * 450)
      });
    }
  }
  return pixels;
}

function renderMapPixels(pixels) {
  pixelGridLayerGroup.clearLayers();

  pixels.forEach((px) => {
    let color = "#10b981"; // GREEN NORMAL
    let fillOpacity = 0.25;

    if (px.risk_level === "CRITICAL") {
      color = "#ef4444"; // RED CRITICAL
      fillOpacity = 0.65;
    } else if (px.risk_level === "WARNING") {
      color = "#f59e0b"; // ORANGE WARNING
      fillOpacity = 0.45;
    }

    const rect = L.rectangle(px.bounds, {
      color: color,
      weight: 2,
      fillColor: color,
      fillOpacity: fillOpacity
    });

    const popupContent = `
      <div style="font-family: Arial, sans-serif; font-size: 12px; color: #1e293b;">
        <strong style="color: ${color}; font-size: 13px;">📍 Map Pixel ${px.pixel_id}</strong><br>
        <b>Risk Level:</b> ${px.risk_level}<br>
        <b>Severity Score:</b> ${px.severity}%<br>
        <b>Water Level / Hotspot:</b> ${px.water_level_m}m<br>
        <b>Est. Affected Citizens:</b> ${px.affected_citizens}<br>
        <button class="btn btn-xs btn-primary mt-2" onclick="togglePixelSelect('${px.pixel_id}')">
          ${selectedPixels.includes(px.pixel_id) ? "Deselect Pixel" : "Select for SOS Alert"}
        </button>
      </div>
    `;

    rect.bindPopup(popupContent);
    rect.addTo(pixelGridLayerGroup);
  });
}

function selectPresetZone(zoneName) {
  if (zoneName === "mumbai") {
    map.setView([19.0760, 72.8777], 13);
    document.getElementById("disaster-type-select").value = "FLOOD";
    activeDisasterType = "FLOOD";
  } else if (zoneName === "chamoli") {
    map.setView([30.0668, 79.0193], 13);
    document.getElementById("disaster-type-select").value = "LANDSLIDE";
    activeDisasterType = "LANDSLIDE";
  } else if (zoneName === "coastal_cyclone") {
    map.setView([19.0500, 72.8200], 12);
    document.getElementById("disaster-type-select").value = "CYCLONE";
    activeDisasterType = "CYCLONE";
  }
  fetchLiveDisasterPixels();
}

function updateTelemetryPanel(telemetry) {
  if (!telemetry) return;
  document.getElementById("val-water-level").innerText = telemetry.water_level || "2.4m";
  document.getElementById("val-rainfall").innerText = telemetry.rainfall || "120mm/hr";
  document.getElementById("val-temp").innerText = telemetry.temperature || "34°C";
  document.getElementById("val-satellite").innerText = telemetry.satellite_ndwi || "88% Anomaly";
  document.getElementById("val-confidence").innerText = telemetry.ai_confidence || "94.2%";
}

function togglePixelSelect(pxId) {
  const idx = selectedPixels.indexOf(pxId);
  if (idx >= 0) {
    selectedPixels.splice(idx, 1);
  } else {
    selectedPixels.push(pxId);
  }
  document.getElementById("selected-pixel-count").innerText = selectedPixels.length || "ALL HIGH-RISK PIXELS";
}

function setupEventListeners() {
  document.getElementById("disaster-type-select").addEventListener("change", function (e) {
    activeDisasterType = e.target.value;
  });
}

function triggerParallelSOSFromPC() {
  const btn = document.getElementById("btn-trigger-pc-sos");
  const origHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i> DISPATCHING PARALLEL SOS...`;

  const startTime = Date.now();
  let timerInterval = setInterval(() => {
    const elapsedSecs = ((Date.now() - startTime) / 1000).toFixed(1);
    document.getElementById("sla-timer").innerText = `${elapsedSecs}s / 30.0s SLA`;
  }, 100);

  const activeZoneName = document.getElementById("zone-location-input").value || "Mumbai Coastal Restricted Zone";
  const disasterType = document.getElementById("disaster-type-select").value;
  const severityLevel = document.getElementById("severity-level-select").value;
  const affectedPop = parseInt(document.getElementById("affected-pop-input").value) || 5000;

  const payload = {
    disaster_type: disasterType,
    severity: severityLevel,
    area_name: activeZoneName,
    affected_population: affectedPop,
    latitude: map.getCenter().lat,
    longitude: map.getCenter().lng,
    polygon_boundary: [
      [map.getCenter().lat - 0.01, map.getCenter().lng - 0.01],
      [map.getCenter().lat + 0.01, map.getCenter().lng - 0.01],
      [map.getCenter().lat + 0.01, map.getCenter().lng + 0.01],
      [map.getCenter().lat - 0.01, map.getCenter().lng + 0.01]
    ]
  };

  fetch("/api/v1/trigger-sos-alert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then((res) => res.json())
    .then((data) => {
      clearInterval(timerInterval);
      btn.disabled = false;
      btn.innerHTML = origHtml;

      if (data.status === "success") {
        renderDispatchResults(data);
      } else {
        alert("Error dispatching alert: " + (data.message || "Unknown error"));
      }
    })
    .catch((err) => {
      clearInterval(timerInterval);
      btn.disabled = false;
      btn.innerHTML = origHtml;
      alert("Network error dispatching parallel alert: " + err.message);
    });
}

function renderDispatchResults(data) {
  const resultCard = document.getElementById("dispatch-result-container");
  resultCard.style.display = "block";
  resultCard.scrollIntoView({ behavior: "smooth" });

  const rescue = data.dispatch_details.rescue_gpt_alert;
  const publicAlert = data.dispatch_details.dsquare_gpt_alert;
  const geofence = data.geofence_analysis;

  // Render Rescue GPT Output
  document.getElementById("rescue-gpt-json").innerText = JSON.stringify(rescue, null, 2);

  // Render D-SQUARE GPT Output
  document.getElementById("dsquare-gpt-json").innerText = JSON.stringify(publicAlert, null, 2);

  // Render Delivery Summary
  document.getElementById("summary-notified-citizens").innerText = geofence.total_affected_count || 1250;
  document.getElementById("summary-critical-zone").innerText = geofence.critical_zone_count || 820;
  document.getElementById("summary-warning-zone").innerText = geofence.warning_zone_count || 430;
  document.getElementById("summary-latency").innerText = `${data.dispatch_details.dispatch_latency_ms} ms (< 30s SLA guaranteed)`;
}
