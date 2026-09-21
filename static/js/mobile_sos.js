/* D-SQUARE 2.0 Mobile SOS Script */

let userLat = 30.0668;
let userLon = 79.0193;
let sosMap = null;

const CLOUD_TUNNEL_URL = "https://competitors-insert-peas-above.trycloudflare.com";

document.addEventListener("DOMContentLoaded", () => {
  initSosMap();
  pollActiveAlerts();
  setInterval(pollActiveAlerts, 3000);
});

function initSosMap() {
  const mapEl = document.getElementById("sos-map");
  if (!mapEl) return;
  sosMap = L.map("sos-map").setView([userLat, userLon], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "OpenStreetMap"
  }).addTo(sosMap);

  L.marker([userLat, userLon]).addTo(sosMap).bindPopup("Your Location").openPopup();
  L.circle([30.0820, 79.0310], { color: "green", radius: 500 }).addTo(sosMap).bindPopup("Safe Shelter Center");
}

function pollActiveAlerts() {
  fetch("/api/mobile/active-alerts")
    .then(r => r.json())
    .catch(() => fetch(`${CLOUD_TUNNEL_URL}/api/mobile/active-alerts`).then(r => r.json()))
    .then(data => {
      if (!data) return;
      const alertCard = document.getElementById("alert-card");
      if (data.active_alert && data.active_alert.active) {
        if (alertCard) alertCard.style.display = "block";
      } else {
        if (alertCard) alertCard.style.display = "none";
      }
    });
}

function triggerMobileSOS() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      userLat = pos.coords.latitude;
      userLon = pos.coords.longitude;
      sendSosPayload();
    }, () => sendSosPayload());
  } else {
    sendSosPayload();
  }
}

function sendSosPayload() {
  fetch("/api/sos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "MOBILE_USER_01",
      latitude: userLat,
      longitude: userLon,
      disaster_type: "Landslide"
    })
  })
  .then(r => r.json())
  .then(res => {
    alert(res.message || "Emergency SOS broadcasted!");
  });
}

function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const msg = input ? input.value.trim() : "";
  if (!msg) return;

  const chatBox = document.getElementById("chat-box");
  chatBox.innerHTML += `<div class="text-white mt-1"><strong>You:</strong> ${msg}</div>`;
  input.value = "";

  fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: msg })
  })
  .then(r => r.json())
  .then(res => {
    chatBox.innerHTML += `<div class="text-info mt-1"><strong>D-SQUARE GPT:</strong> ${res.response}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
  });
}
