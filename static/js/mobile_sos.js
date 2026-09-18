/* D-SQUARE SOS — Mobile Public Safety Module Script */

let userLat = 30.0668;
let userLon = 79.0193;
let userSessionId = "MOBILE_USER_SESSION_01";
let hasLocationConsent = false;
let mobileMap = null;
let userMarker = null;
let hazardCircle = null;
let safeZonesGroup = null;
let lastAutoGuidanceTimestamp = null;

document.addEventListener("DOMContentLoaded", () => {
  initMobileMap();
  requestLocationPermission();
  refreshMobileAlerts();
  fetchActiveAlert();
  loadTrustedContacts();
  fetchGroundStationStatus();
  setInterval(fetchActiveAlert, 2000);
  setInterval(refreshMobileAlerts, 4000);
  setInterval(fetchGroundStationStatus, 3000);
});

function initMobileMap() {
  const mapEl = document.getElementById("mobile-map");
  if (!mapEl) return;

  mobileMap = L.map("mobile-map", { zoomControl: false }).setView([userLat, userLon], 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap / ISRO Bhuvan",
    maxZoom: 18
  }).addTo(mobileMap);

  safeZonesGroup = L.layerGroup().addTo(mobileMap);

  // User Marker
  userMarker = L.circleMarker([userLat, userLon], {
    radius: 8,
    fillColor: "#38bdf8",
    color: "#ffffff",
    weight: 2,
    fillOpacity: 0.9
  }).addTo(mobileMap).bindPopup("<b>Your Geolocation</b><br>Permission granted");

  // Hazard Radius Overlay (Default 12km)
  hazardCircle = L.circle([30.0668, 79.0193], {
    color: "#ef4444",
    fillColor: "#ef4444",
    fillOpacity: 0.15,
    radius: 12000
  }).addTo(mobileMap).bindPopup("<b>D-SQUARE High-Risk Surveillance Area</b>");

  // Simulated ESP8266 Ground Node Marker
  L.circleMarker([30.0668, 79.0193], {
    radius: 9,
    fillColor: "#f97316",
    color: "#ffffff",
    weight: 2,
    fillOpacity: 0.9
  }).addTo(mobileMap).bindPopup("<b>SIMULATED_ESP8266_LANDSLIDE_01</b><br>Simulated ESP8266 Telemetry");

  // DEMO SAFE ZONE Marker
  L.circleMarker([30.095, 79.055], {
    radius: 9,
    fillColor: "#22c55e",
    color: "#ffffff",
    weight: 2,
    fillOpacity: 0.9
  }).addTo(mobileMap).bindPopup("<b>DEMO SAFE ZONE</b><br>Almora Evacuation Shelter (Simulated)");
}

function requestLocationPermission() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        userLat = pos.coords.latitude;
        userLon = pos.coords.longitude;
        hasLocationConsent = true;

        if (userMarker) userMarker.setLatLng([userLat, userLon]);
        if (mobileMap) mobileMap.setView([userLat, userLon], 11);

        const statusEl = document.getElementById("location-status-badge");
        if (statusEl) {
          statusEl.className = "badge bg-success";
          statusEl.innerText = `GPS Active (${userLat.toFixed(4)}, ${userLon.toFixed(4)})`;
        }

        sendLocationToServer(userLat, userLon, pos.coords.accuracy || 10.0);
        loadSafeZones(userLat, userLon);
      },
      (err) => {
        console.warn("Geolocation permission denied or unavailable:", err.message);
        const statusEl = document.getElementById("location-status-badge");
        if (statusEl) {
          statusEl.className = "badge bg-secondary";
          statusEl.innerText = "GPS Permission Required (Using Default Coordinates)";
        }
        loadSafeZones(userLat, userLon);
      },
      { timeout: 8000 }
    );
  }
}

function sendLocationToServer(lat, lon, accuracy) {
  fetch("/api/user/location", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_session_id: userSessionId,
      latitude: lat,
      longitude: lon,
      accuracy_m: accuracy,
      consent: true
    })
  }).catch((err) => {});
}

function refreshMobileAlerts() {
  fetch(`/api/mobile/active-alerts?lat=${userLat}&lon=${userLon}`)
    .then((res) => res.json())
    .then((data) => {
      const modeBadge = document.getElementById("data-mode-badge");
      if (modeBadge) {
        modeBadge.innerText = data.data_mode || "DEMO";
        modeBadge.className = `badge ${data.data_mode === "VERIFIED" ? "bg-success" : "bg-secondary"}`;
      }

      const alertCard = document.getElementById("active-alert-card");
      const noAlertCard = document.getElementById("no-alert-card");
      const systemStatusBadge = document.getElementById("system-status-badge");

      if (data.active_alert && data.active_alert.active) {
        const a = data.active_alert;
        if (alertCard) alertCard.style.display = "block";
        if (noAlertCard) noAlertCard.style.display = "none";
        if (systemStatusBadge) {
          systemStatusBadge.className = "badge bg-danger fs-6";
          systemStatusBadge.innerText = "🚨 CRITICAL LANDSLIDE RISK (DEMO)";
        }

        const titleEl = document.getElementById("alert-disaster-title");
        if (titleEl) {
          titleEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-danger me-1"></i> ${a.risk_level || "CRITICAL"} ${(a.disaster_type || "LANDSLIDE").toUpperCase()} RISK`;
        }
        const badgeEl = document.getElementById("alert-severity-badge");
        if (badgeEl) {
          badgeEl.innerText = `${a.risk_level || "CRITICAL"} RISK`;
          badgeEl.className = `badge ${a.risk_level === "CRITICAL" ? "bg-danger" : "bg-warning text-dark"}`;
        }
        const distEl = document.getElementById("alert-distance-text");
        if (distEl) {
          const distVal = typeof a.distance_from_user_km === 'number' ? a.distance_from_user_km.toFixed(1) : a.distance_from_user_km;
          distEl.innerText = `Distance to Hazard Zone: ${distVal} km`;
        }
        const msgEl = document.getElementById("alert-warning-body");
        if (msgEl) {
          msgEl.innerText = a.plain_language_warning || a.message;
        }

        updateEscapeGuidance(a.disaster_type || "Landslide");

        const ts = a.alert_time || a.timestamp;
        if (ts && lastAutoGuidanceTimestamp !== ts) {
          lastAutoGuidanceTimestamp = ts;
          triggerAutoEscapeGuidance({
            disaster_type: a.disaster_type,
            risk_level: a.risk_level,
            timestamp: ts
          });
        }
      } else {
        if (alertCard) alertCard.style.display = "none";
        if (noAlertCard) noAlertCard.style.display = "block";
        if (systemStatusBadge) {
          systemStatusBadge.className = "badge bg-success fs-6";
          systemStatusBadge.innerText = "🟢 AWAITING SIMULATED ALERT";
        }
        updateEscapeGuidance("General");
      }
    })
    .catch((err) => {});
}

function fetchActiveAlert() {
  fetch("/api/mobile/active-alert")
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success" && data.alert) {
        const a = data.alert;
        const alertCard = document.getElementById("active-alert-card");
        const noAlertCard = document.getElementById("no-alert-card");
        const systemStatusBadge = document.getElementById("system-status-badge");
        const dataModeBadge = document.getElementById("data-mode-badge");

        if (dataModeBadge) {
          dataModeBadge.innerText = a.data_mode || "DEMO_SIMULATION";
          dataModeBadge.className = "badge bg-warning text-dark fw-bold";
        }

        if (a.active || a.risk_level === "CRITICAL") {
          if (alertCard) alertCard.style.display = "block";
          if (noAlertCard) noAlertCard.style.display = "none";
          if (systemStatusBadge) {
            systemStatusBadge.className = "badge bg-danger fs-6";
            systemStatusBadge.innerText = "🚨 CRITICAL LANDSLIDE RISK (DEMO)";
          }

          const titleEl = document.getElementById("alert-disaster-title");
          if (titleEl) {
            titleEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-danger me-1"></i> ${a.risk_level || "CRITICAL"} ${(a.disaster_type || "LANDSLIDE").toUpperCase()} RISK`;
          }

          const badgeEl = document.getElementById("alert-severity-badge");
          if (badgeEl) {
            badgeEl.innerText = `${a.risk_level || "CRITICAL"} RISK`;
            badgeEl.className = "badge bg-danger fs-6";
          }

          const msgEl = document.getElementById("alert-warning-body");
          if (msgEl) {
            msgEl.innerText = a.message || "DEMO: High soil moisture and humidity indicate simulated slope-instability risk. Follow official authority guidance in a real event.";
          }

          // Update Simulated Telemetry Card elements
          if (document.getElementById("sim-soil")) document.getElementById("sim-soil").innerText = `${a.soil_moisture !== undefined ? a.soil_moisture : 88.0}%`;
          if (document.getElementById("sim-temp")) document.getElementById("sim-temp").innerText = `${a.temperature !== undefined ? a.temperature : 25.8}°C`;
          if (document.getElementById("sim-hum")) document.getElementById("sim-hum").innerText = `${a.humidity !== undefined ? a.humidity : 92.0}%`;
          if (document.getElementById("sim-led")) {
            const ledEl = document.getElementById("sim-led");
            ledEl.innerText = a.led_state || "RED";
            ledEl.className = a.led_state === "RED" ? "text-danger fw-bold" : "text-success";
          }
          if (document.getElementById("sim-buzzer")) {
            const buzEl = document.getElementById("sim-buzzer");
            buzEl.innerText = a.buzzer_state || "ON";
            buzEl.className = a.buzzer_state === "ON" ? "text-danger fw-bold" : "text-success";
          }
          if (document.getElementById("telemetry-node-title")) document.getElementById("telemetry-node-title").innerText = a.node_id || "SIMULATED_ESP8266_LANDSLIDE_01";
          if (document.getElementById("sim-node-label")) document.getElementById("sim-node-label").innerText = a.node_id || "SIMULATED_ESP8266_LANDSLIDE_01";
          if (document.getElementById("sim-timestamp")) document.getElementById("sim-timestamp").innerText = a.timestamp ? `Timestamp: ${a.timestamp}` : "Updated Just Now";

          updateEscapeGuidance("Landslide");

          if (lastAutoGuidanceTimestamp !== a.timestamp) {
            lastAutoGuidanceTimestamp = a.timestamp;
            triggerAutoEscapeGuidance(a);
          }
        } else {
          if (alertCard) alertCard.style.display = "none";
          if (noAlertCard) noAlertCard.style.display = "block";
          if (systemStatusBadge) {
            systemStatusBadge.className = "badge bg-success fs-6";
            systemStatusBadge.innerText = "🟢 AWAITING SIMULATED ALERT";
          }
          if (document.getElementById("no-alert-status-text")) {
            document.getElementById("no-alert-status-text").innerText = "Awaiting simulated alert. Click 'Landslide' on Dashboard to activate.";
          }
          if (document.getElementById("sim-soil")) document.getElementById("sim-soil").innerText = "42.0%";
          if (document.getElementById("sim-temp")) document.getElementById("sim-temp").innerText = "26.5°C";
          if (document.getElementById("sim-hum")) document.getElementById("sim-hum").innerText = "52.0%";
          if (document.getElementById("sim-led")) {
            const ledEl = document.getElementById("sim-led");
            ledEl.innerText = "GREEN";
            ledEl.className = "text-success";
          }
          if (document.getElementById("sim-buzzer")) {
            const buzEl = document.getElementById("sim-buzzer");
            buzEl.innerText = "OFF";
            buzEl.className = "text-success";
          }
          if (document.getElementById("telemetry-node-title")) document.getElementById("telemetry-node-title").innerText = "SIMULATED_ESP8266_NODE_01";

          updateEscapeGuidance("General");
        }
      }
    })
    .catch((err) => {});
}

function handleCall112Click(event) {
  event.preventDefault();
  const modal = new bootstrap.Modal(document.getElementById("call112ConfirmModal"));
  modal.show();
}

function confirmCall112Proceed() {
  window.location.href = "tel:112";
}

function handleSimulateSosClick() {
  const modal = new bootstrap.Modal(document.getElementById("simulateSosModal"));
  modal.show();
}

function scrollToRiskMap() {
  const mapCard = document.getElementById("mobile-map-card");
  if (mapCard) {
    mapCard.scrollIntoView({ behavior: "smooth" });
  }
  if (mobileMap) {
    mobileMap.setView([30.0668, 79.0193], 12);
  }
}

function loadSafeZones(lat, lon) {
  fetch(`/api/mobile/safe-zones?lat=${lat}&lon=${lon}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success" && safeZonesGroup) {
        safeZonesGroup.clearLayers();
        (data.safe_zones || []).forEach((z) => {
          const marker = L.circleMarker([z.latitude, z.longitude], {
            radius: 7,
            fillColor: "#22c55e",
            color: "#ffffff",
            weight: 2,
            fillOpacity: 0.9
          }).bindPopup(`<b>${z.name}</b><br>${z.category}<br>Capacity: ${z.capacity}<br>Distance: ${z.distance_km} km<br><a href="tel:${z.contact_phone}" class="btn btn-sm btn-success py-0 mt-1">Call Shelter</a>`);
          safeZonesGroup.addLayer(marker);
        });
      }
    })
    .catch((err) => {});
}

function updateEscapeGuidance(disasterType) {
  const container = document.getElementById("escape-guidance-list");
  if (!container) return;

  let tips = [];
  if (disasterType === "Flood") {
    tips = [
      "Move to higher ground immediately if it is safe to do so.",
      "NEVER walk, swim, or drive through floodwater or moving currents.",
      "Stay clear of drains, electrical poles, and submerged wires.",
      "Gather medicines, water, ID, and phone if evacuating safely.",
      "Call 112 if you are trapped or water is entering your home."
    ];
  } else if (disasterType === "Forest_Fire") {
    tips = [
      "Move away from smoke and fire in the direction advised by authorities.",
      "Do not enter forest paths, narrow valleys, or smoke-filled zones.",
      "Cover your nose and mouth with a wet cloth or mask.",
      "Stay clear of power lines and dry vegetation.",
      "Call 112 immediately if fire approaches your location."
    ];
  } else if (disasterType === "Landslide") {
    tips = [
      "Move away from steep slopes, gullies, retaining walls, and river channels.",
      "Watch for cracking soil, falling rocks, leaning trees, or unusual loud sounds.",
      "Do not return to a slope after a slide has occurred.",
      "Avoid travelling on mountain roads under heavy rainfall.",
      "Call 112 if anyone is trapped or injured."
    ];
  } else if (disasterType === "Air_Pollution") {
    tips = [
      "Move indoors if possible and close doors and windows.",
      "Limit physical exertion outdoors.",
      "Use a well-fitting mask (N95/KN95) if going outside.",
      "High-risk individuals (asthma, heart conditions, elderly) should take extra care.",
      "Seek medical help immediately for severe chest pain or breathing difficulty."
    ];
  } else {
    tips = [
      "Keep phone charged and emergency contacts saved.",
      "Follow official bulletins from SDMA, NDMA, and IMD.",
      "Do not spread unverified rumors on social media.",
      "Know your nearest emergency shelter location.",
      "For immediate danger, call 112 or follow local authority instructions."
    ];
  }

  let html = "";
  tips.forEach((t) => {
    html += `<div class="escape-tip-item"><i class="fa-solid fa-shield-halved text-info me-2"></i> ${t}</div>`;
  });
  container.innerHTML = html;
}

function playEmergencyAlertSound() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    const now = ctx.currentTime;
    
    // Play 3 high-intensity warning tones (1000 Hz / 800 Hz alternating)
    for (let i = 0; i < 4; i++) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(i % 2 === 0 ? 1000 : 800, now + i * 0.25);
      
      gain.gain.setValueAtTime(0.4, now + i * 0.25);
      gain.gain.exponentialRampToValueAtTime(0.01, now + (i + 1) * 0.25 - 0.03);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start(now + i * 0.25);
      osc.stop(now + (i + 1) * 0.25 - 0.03);
    }
  } catch (e) {
    console.warn("Could not play emergency alert sound:", e);
  }
}

function triggerAutoEscapeGuidance(a) {
  const container = document.getElementById("chat-messages-container");
  if (!container) return;

  // Play audible emergency alert tone when Landslide SOS is dispatched/received
  playEmergencyAlertSound();

  const guidanceMsg = {
    message: `🚨 <b>ALERT DISPATCHED FROM GROUND STATION</b><br><br><b>Disaster Event:</b> ${(a.disaster_type || 'Landslide').toUpperCase()}<br><b>Risk Level:</b> ${a.risk_level || 'CRITICAL'}<br><br><b>🚨 D-SQUARE GPT AUTOMATIC ESCAPE & SHELTER GUIDANCE:</b><br>1. ⛰️ <b>Immediate Action:</b> Move perpendicular to the landslide path immediately. Avoid steep slopes, gullies, and stream channels.<br>2. 🏃 <b>Evacuation:</b> Head towards the nearest high-ground safe shelter: <b>Almora Evacuation Shelter</b> (3.4 km East).<br>3. ⚠️ <b>Watch For:</b> Soil slumping, falling rocks, tilting trees, or sudden changes in water runoff.<br>4. 📱 <b>Alerting:</b> Notify saved emergency contacts using the SOS button above.`,
    call_112_recommended: true,
    disclaimer: "DEMO MODE — Automated AI Disaster Escape Guidance based on Ground Station Telemetry."
  };

  appendAssistantBubble(guidanceMsg);
}

function openSosModal() {
  const modal = new bootstrap.Modal(document.getElementById("sosConfirmModal"));
  modal.show();
}

function confirmAndSendSos() {
  const msgText = document.getElementById("sos-custom-message").value || "EMERGENCY SOS: I need help! Here is my live GPS location.";
  const statusBadge = document.getElementById("sos-dispatch-status");
  if (statusBadge) {
    statusBadge.className = "badge bg-warning text-dark";
    statusBadge.innerText = "Dispatching SOS...";
  }

  fetch("/api/mobile/sos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_session_id: userSessionId,
      latitude: userLat,
      longitude: userLon,
      message: msgText,
      consent: true
    })
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        if (statusBadge) {
          statusBadge.className = "badge bg-success";
          statusBadge.innerText = "SOS Dispatched!";
        }
        alert(`SOS Sent Successfully! Shared with ${data.message}`);
      } else {
        if (statusBadge) {
          statusBadge.className = "badge bg-danger";
          statusBadge.innerText = "Failed";
        }
        alert(data.message || "Failed to send SOS");
      }
    })
    .catch((err) => {
      alert("Error sending SOS: " + err);
    });
}

function loadTrustedContacts() {
  fetch(`/api/mobile/contacts?session_id=${userSessionId}`)
    .then((res) => res.json())
    .then((data) => {
      const listEl = document.getElementById("trusted-contacts-list");
      if (listEl && data.contacts) {
        if (data.contacts.length === 0) {
          listEl.innerHTML = '<li class="text-muted small py-1">No trusted contacts saved yet. Add family members below.</li>';
          return;
        }
        let html = "";
        data.contacts.forEach((c) => {
          html += `<li class="d-flex justify-content-between align-items-center py-1 border-bottom border-secondary small">
            <span><i class="fa-solid fa-user-shield text-info me-1"></i> <strong>${c.contact_name}</strong> (${c.relationship}) - ${c.phone_number}</span>
            <button class="btn btn-sm btn-outline-danger py-0 px-1" onclick="deleteContact(${c.id})"><i class="fa-solid fa-trash"></i></button>
          </li>`;
        });
        listEl.innerHTML = html;
      }
    })
    .catch((err) => {});
}

function addTrustedContact() {
  const name = document.getElementById("new-contact-name").value;
  const phone = document.getElementById("new-contact-phone").value;
  const rel = document.getElementById("new-contact-rel").value || "Family";

  if (!name || !phone) {
    alert("Please enter both contact name and phone number.");
    return;
  }

  fetch("/api/mobile/contacts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_session_id: userSessionId,
      contact_name: name,
      phone_number: phone,
      relationship: rel
    })
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        document.getElementById("new-contact-name").value = "";
        document.getElementById("new-contact-phone").value = "";
        loadTrustedContacts();
      } else {
        alert(data.message || "Error adding contact");
      }
    })
    .catch((err) => {});
}

function deleteContact(id) {
  fetch(`/api/mobile/contacts/${id}?session_id=${userSessionId}`, { method: "DELETE" })
    .then((res) => res.json())
    .then(() => loadTrustedContacts())
    .catch((err) => {});
}

function sendAssistantQuery(quickText) {
  const inputEl = document.getElementById("assistant-input");
  const query = quickText || (inputEl ? inputEl.value : "");
  if (!query || query.trim() === "") return;

  if (inputEl) inputEl.value = "";

  appendChatBubble(query, "user");

  fetch("/api/mobile/assistant", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: query,
      latitude: userLat,
      longitude: userLon,
      language: "en"
    })
  })
    .then((res) => res.json())
    .then((data) => {
      appendAssistantBubble(data);
    })
    .catch((err) => {
      appendChatBubble("Error communicating with safety assistant. Call 112 for immediate danger.", "assistant");
    });
}

function appendChatBubble(text, sender) {
  const container = document.getElementById("chat-messages-container");
  if (!container) return;

  const div = document.createElement("div");
  div.className = `chat-bubble ${sender === "user" ? "chat-bubble-user" : "chat-bubble-assistant"}`;
  div.innerHTML = text.replace(/\n/g, "<br>");
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendAssistantBubble(data) {
  const container = document.getElementById("chat-messages-container");
  if (!container) return;

  const div = document.createElement("div");
  div.className = "chat-bubble chat-bubble-assistant";

  let html = `<div>${(data.message || "").replace(/\n/g, "<br>")}</div>`;

  if (data.call_112_recommended) {
    html += `<div class="mt-2 p-2 bg-danger text-white rounded text-center fw-bold small">
      <i class="fa-solid fa-phone me-1"></i> Immediate Danger Detected! Call 112 Now.
      <a href="tel:112" class="btn btn-sm btn-light py-0 px-2 ms-2 fw-bold text-danger">Call 112</a>
    </div>`;
  }

  if (data.disclaimer) {
    html += `<div class="mt-1 text-muted" style="font-size: 0.72rem;">${data.disclaimer}</div>`;
  }

  div.innerHTML = html;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function fetchGroundStationStatus() {
  fetch("/api/mobile/ground-station-status")
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success" && data.telemetry) {
        const t = data.telemetry;
        const nodeBadge = document.getElementById("gs-node-status");
        if (nodeBadge) {
          nodeBadge.innerText = `${data.node_id || "ESP8266_NODE_01"} ONLINE`;
        }
        const tempEl = document.getElementById("gs-temp");
        if (tempEl && t.temperature_c !== undefined) tempEl.innerText = `${t.temperature_c}°C`;
        const humEl = document.getElementById("gs-hum");
        if (humEl && t.humidity_pct !== undefined) humEl.innerText = `${t.humidity_pct}%`;
        const soilEl = document.getElementById("gs-soil");
        if (soilEl && t.soil_moisture_pct !== undefined) soilEl.innerText = `${t.soil_moisture_pct}%`;
        const smokeEl = document.getElementById("gs-smoke");
        if (smokeEl && t.smoke_ppm !== undefined) smokeEl.innerText = `${t.smoke_ppm} PPM`;
        const waterEl = document.getElementById("gs-water");
        if (waterEl && t.water_level_cm !== undefined) waterEl.innerText = `${t.water_level_cm} cm`;
        const tiltEl = document.getElementById("gs-tilt");
        if (tiltEl && t.mpu_tilt_deg !== undefined) tiltEl.innerText = `${t.mpu_tilt_deg}°`;
      }
    })
    .catch((err) => {});
}
