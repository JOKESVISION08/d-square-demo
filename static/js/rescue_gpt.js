/* D-SQUARE Rescue GPT Voice & Navigation Script */

let currentRole = "victim";
let currentLanguage = "en";
let userLat = 19.0760;
let userLon = 72.8777;
let voiceEnabled = true;
let rescueMap = null;

const CLOUD_TUNNEL_URL = "https://competitors-insert-peas-above.trycloudflare.com";

document.addEventListener("DOMContentLoaded", () => {
  initRescueMap();
  calculateSurvivalProb();
  fetchRescueOperationsSummary();
  checkActiveRescueSOSAlert();
  setInterval(checkActiveRescueSOSAlert, 5000);
});

function checkActiveRescueSOSAlert() {
  fetch("/api/sos/active_parallel_alerts")
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success" && data.count > 0) {
        const alert = data.alerts[0];
        const rescue = alert.rescue_payload || {};
        const loc = rescue.location || {};
        
        let alertBadge = document.getElementById("data-mode-badge");
        if (alertBadge) {
          alertBadge.className = "badge bg-danger px-3 py-2 fw-bold";
          alertBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation me-1"></i> ACTIVE PARALLEL SOS: ${alert.disaster_type} (${alert.severity})`;
        }
      }
    })
    .catch((err) => console.log("Rescue GPT alert listener:", err));
}

function initRescueMap() {
  const mapEl = document.getElementById("rescue-map");
  if (!mapEl) return;
  rescueMap = L.map("rescue-map").setView([userLat, userLon], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18 }).addTo(rescueMap);

  L.marker([userLat, userLon]).addTo(rescueMap).bindPopup("<b>Your Location</b><br>Mumbai Coastal Restricted Zone").openPopup();
  L.circle([19.0910, 72.8920], { color: "green", radius: 600 }).addTo(rescueMap).bindPopup("<b>School XYZ Emergency Shelter</b><br>Beds: 320 Available");
}

function setRole(role) {
  currentRole = role;
  document.getElementById("btn-role-victim").classList.toggle("active", role === "victim");
  document.getElementById("btn-role-rescue").classList.toggle("active", role === "rescue_team");
  
  const chatTitle = document.getElementById("chat-title");
  const opsCard = document.getElementById("rescue-ops-card");

  if (role === "victim") {
    if (chatTitle) chatTitle.innerHTML = '<i class="fa-solid fa-robot me-2"></i>D-SQUARE GPT (Public Safety Assistant)';
    if (opsCard) opsCard.style.display = "none";
  } else {
    if (chatTitle) chatTitle.innerHTML = '<i class="fa-solid fa-shield-halved me-2"></i>Rescue GPT (Operations Fleet Dispatcher)';
    if (opsCard) opsCard.style.display = "block";
    fetchRescueOperationsSummary();
  }
}

function onLanguageChange() {
  const langSelect = document.getElementById("lang-select");
  if (langSelect) currentLanguage = langSelect.value;
  sendQuickQuery("Where is the nearest shelter?");
}

function toggleVoiceOutput() {
  voiceEnabled = !voiceEnabled;
  const statusEl = document.getElementById("voice-status");
  if (statusEl) statusEl.innerText = voiceEnabled ? "ON" : "OFF";
}

function speakText(text) {
  if (!voiceEnabled || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const cleanText = text.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.0;
  if (currentLanguage === "hi") utterance.lang = 'hi-IN';
  else if (currentLanguage === "mr") utterance.lang = 'mr-IN';
  else utterance.lang = 'en-US';

  window.speechSynthesis.speak(utterance);
}

function startSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. Please type your query.");
    return;
  }
  const recognition = new SpeechRecognition();
  if (currentLanguage === "hi") recognition.lang = 'hi-IN';
  else if (currentLanguage === "mr") recognition.lang = 'mr-IN';
  else recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("user-input").value = transcript;
    sendRescueQuery();
  };
  recognition.start();
}

function sendQuickQuery(queryText) {
  const input = document.getElementById("user-input");
  if (input) input.value = queryText;
  sendRescueQuery();
}

function sendRescueQuery() {
  const input = document.getElementById("user-input");
  const msg = input ? input.value.trim() : "";
  if (!msg) return;

  const chatBox = document.getElementById("chat-box");
  chatBox.innerHTML += `<div class="chat-bubble-user"><strong>You:</strong> ${msg}</div>`;
  input.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  const payload = {
    query: msg,
    language: currentLanguage,
    user_type: currentRole,
    disaster_type: "FLOOD",
    location: { lat: userLat, lon: userLon }
  };

  const endpoint = currentRole === "victim" ? "/api/public/assistant_query" : "/api/rescue_chat";

  fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .catch(() => fetch(`${CLOUD_TUNNEL_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(r => r.json()))
  .then(res => {
    if (!res) return;
    const responseText = res.response || res.message || "Query processed.";
    let extraHTML = "";

    if (res.safety_instructions && res.safety_instructions.length > 0) {
      extraHTML += `<br><strong class="text-warning">✅ Actionable Safety Steps:</strong><br>${res.safety_instructions.join("<br>")}`;
    }

    chatBox.innerHTML += `<div class="chat-bubble-ai"><strong>D-SQUARE GPT:</strong><br>${responseText}${extraHTML}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
    speakText(responseText);
  });
}

function triggerParallelSOSDemo() {
  const payload = {
    disaster_type: "FLOOD",
    severity: "HIGH",
    latitude: userLat,
    longitude: userLon,
    area_name: "Mumbai Coastal Zone",
    affected_population: 5000
  };

  fetch("/api/sos/trigger_parallel", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(res => {
    if (res && res.status === "success") {
      const banner = document.getElementById("parallel-sos-banner");
      if (banner) {
        banner.style.display = "flex";
        document.getElementById("sos-banner-title").innerText = `🚨 ${res.rescue_gpt_alert.severity} ${res.rescue_gpt_alert.disaster_type} SOS ALERT DISPATCHED!`;
        document.getElementById("sos-banner-msg").innerText = `Dispatched in ${res.dispatch_latency_ms}ms to Rescue Teams (108/112) & Citizens in 3 Languages!`;
        document.getElementById("sos-banner-route").href = res.dsquare_gpt_alert.evacuation_route;
      }
      sendQuickQuery("Where is the nearest shelter?");
    }
  });
}

function fetchRescueOperationsSummary() {
  fetch("/api/rescue/dashboard_summary")
  .then(r => r.json())
  .then(data => {
    if (data && data.status === "success" && data.rescue_resources) {
      const tbody = document.getElementById("resource-table-body");
      if (!tbody) return;
      tbody.innerHTML = "";

      data.rescue_resources.forEach(r => {
        const badgeClass = r.status === "DEPLOYED" ? "bg-danger" : (r.status === "STANDBY" ? "bg-warning text-dark" : "bg-success");
        tbody.innerHTML += `
          <tr>
            <td><strong>${r.resource_type}</strong></td>
            <td>${r.assigned_area}</td>
            <td><span class="badge ${badgeClass}">${r.status}</span></td>
            <td>${r.quantity}</td>
            <td><button class="btn btn-sm btn-outline-info py-0" onclick="updateResource('${r.resource_id}')">Update</button></td>
          </tr>
        `;
      });
    }
  }).catch(() => {});
}

function updateResource(resourceId) {
  fetch("/api/rescue/resource_allocation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resource_id: resourceId, status: "DEPLOYED", assigned_area: "Sector 2 Emergency Zone" })
  })
  .then(r => r.json())
  .then(res => {
    alert(res.message);
    fetchRescueOperationsSummary();
  });
}

function calculateSurvivalProb() {
  const minutes = parseFloat(document.getElementById("trapped-time").value) || 0;
  const injury = document.getElementById("injury-type").value;

  let baseProb = 99.0;
  baseProb -= (minutes / 60.0) * 8.5;
  if (injury === "bleeding") baseProb -= 25.0;
  if (injury === "crush") baseProb -= 18.0;

  baseProb = Math.max(5.0, Math.min(99.0, baseProb));
  const scoreEl = document.getElementById("survival-score");
  const recEl = document.getElementById("survival-rec");

  if (scoreEl) {
    scoreEl.innerText = `${baseProb.toFixed(1)}%`;
    scoreEl.className = baseProb > 70 ? "fs-3 fw-bold text-success" : (baseProb > 40 ? "fs-3 fw-bold text-warning" : "fs-3 fw-bold text-danger");
  }

  if (recEl) {
    if (baseProb < 50.0) recEl.innerText = "CRITICAL: Urgent priority rescue dispatch required!";
    else recEl.innerText = "Conserve phone battery, remain calm and signal rescue teams.";
  }
}
