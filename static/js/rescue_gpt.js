/* D-SQUARE Rescue GPT Voice & Navigation Script */

let currentRole = "victim";
let userLat = 30.0668;
let userLon = 79.0193;
let voiceEnabled = true;
let rescueMap = null;

const CLOUD_TUNNEL_URL = "https://competitors-insert-peas-above.trycloudflare.com";

document.addEventListener("DOMContentLoaded", () => {
  initRescueMap();
  calculateSurvivalProb();
});

function initRescueMap() {
  const mapEl = document.getElementById("rescue-map");
  if (!mapEl) return;
  rescueMap = L.map("rescue-map").setView([userLat, userLon], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18 }).addTo(rescueMap);

  L.marker([userLat, userLon]).addTo(rescueMap).bindPopup("Victim Location").openPopup();
  L.circle([30.0820, 79.0310], { color: "green", radius: 500 }).addTo(rescueMap).bindPopup("District Relief Shelter");
}

function setRole(role) {
  currentRole = role;
  document.getElementById("btn-role-victim").classList.toggle("active", role === "victim");
  document.getElementById("btn-role-rescue").classList.toggle("active", role === "rescue_team");
  document.getElementById("chat-title").innerHTML = role === "victim" ? 
    '<i class="fa-solid fa-robot me-2"></i>Civilian Survival Assistant' : 
    '<i class="fa-solid fa-truck-medical me-2"></i>NDRF Rescue Team Route Optimizer';
}

function toggleVoiceOutput() {
  voiceEnabled = !voiceEnabled;
  document.getElementById("voice-status").innerText = voiceEnabled ? "ON" : "OFF";
}

function speakText(text) {
  if (!voiceEnabled || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const cleanText = text.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
}

function startSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. Please use Chrome/Edge.");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("user-input").value = transcript;
    sendRescueQuery();
  };
  recognition.start();
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
    user_type: currentRole,
    message: msg,
    disaster_type: "landslide",
    location: { lat: userLat, lon: userLon }
  };

  fetch("/api/rescue_chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .catch(() => fetch(`${CLOUD_TUNNEL_URL}/api/rescue_chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(r => r.json()))
  .then(res => {
    if (!res) return;
    chatBox.innerHTML += `<div class="chat-bubble-ai">${res.response}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
    speakText(res.response);
  });
}

function calculateSurvivalProb() {
  const time = document.getElementById("trapped-time").value || 120;
  const injury = document.getElementById("injury-type").value || "none";

  fetch(`/api/survival_probability?time_trapped=${time}&injury_type=${injury}&temp=25`)
    .then(r => r.json())
    .then(data => {
      document.getElementById("survival-score").innerText = `${data.percentage}%`;
      document.getElementById("survival-rec").innerText = data.recommendation;
    });
}
