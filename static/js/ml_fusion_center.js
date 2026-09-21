/**
 * D-SQUARE 2.0 PC Multi-Fusion ML Control Center JavaScript
 * Handles real-time inference predictions, model training triggers, SHAP explainability rendering,
 * and disaster-specific parameter matrix inspection.
 */

document.addEventListener("DOMContentLoaded", function () {
  fetchModelMetrics();
  fetchShapExplainability();
});

function fetchModelMetrics() {
  fetch("/api/ml/metrics")
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success" && data.metrics) {
        const m = data.metrics;
        document.getElementById("metric-precision").innerText = `${(m.precision * 100).toFixed(1)}%`;
        document.getElementById("metric-recall").innerText = `${(m.recall * 100).toFixed(1)}%`;
        document.getElementById("metric-f1").innerText = m.f1_score;
        document.getElementById("metric-auc").innerText = m.auc_roc;
        document.getElementById("metric-dataset-count").innerText = `${m.dataset_records || 1200} Records`;
      }
    })
    .catch((err) => console.log("Metrics fetch error:", err));
}

function fetchShapExplainability() {
  fetch("/api/ml/explainability")
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success" && data.shap_importance) {
        renderShapBars(data.shap_importance);
      }
    })
    .catch((err) => console.log("SHAP fetch error:", err));
}

function renderShapBars(shapObj) {
  const container = document.getElementById("shap-bars-container");
  if (!container) return;

  container.innerHTML = "";
  for (const [feat, score] of Object.entries(shapObj)) {
    const pct = (score * 100).toFixed(1);
    const item = document.createElement("div");
    item.className = "mb-2";
    item.innerHTML = `
      <div class="d-flex justify-content-between small text-white mb-1">
        <span><b>${feat}</b></span>
        <span class="text-info">${pct}%</span>
      </div>
      <div class="progress bg-dark border border-secondary" style="height: 10px;">
        <div class="progress-bar bg-info progress-bar-striped" role="progressbar" style="width: ${pct}%"></div>
      </div>
    `;
    container.appendChild(item);
  }
}

function runRealTimeInference() {
  const btn = document.getElementById("btn-run-inference");
  const origHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i> RUNNING INFERENCE...`;

  const payload = {
    disaster_type: document.getElementById("inf-disaster-type").value,
    latitude: parseFloat(document.getElementById("inf-lat").value) || 19.0760,
    longitude: parseFloat(document.getElementById("inf-lon").value) || 72.8777,
    telemetry: {
      water_level_m: parseFloat(document.getElementById("inf-water").value) || 2.5,
      rainfall_mm_24h: parseFloat(document.getElementById("inf-rain").value) || 150.0,
      soil_moisture_percent: parseFloat(document.getElementById("inf-soil").value) || 88.0,
      temperature_c: parseFloat(document.getElementById("inf-temp").value) || 32.0,
      wind_speed_kmh: parseFloat(document.getElementById("inf-wind").value) || 45.0,
      pga_g: parseFloat(document.getElementById("inf-pga").value) || 0.05
    }
  };

  fetch("/api/ml/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then((res) => res.json())
    .then((data) => {
      btn.disabled = false;
      btn.innerHTML = origHtml;

      if (data.status === "success") {
        renderInferenceResults(data);
      } else {
        alert("Inference error: " + (data.message || "Unknown error"));
      }
    })
    .catch((err) => {
      btn.disabled = false;
      btn.innerHTML = origHtml;
      alert("Network error running inference: " + err.message);
    });
}

function renderInferenceResults(data) {
  const container = document.getElementById("inference-result-box");
  container.style.display = "block";
  container.scrollIntoView({ behavior: "smooth" });

  document.getElementById("res-disaster-type").innerText = data.disaster_type;
  document.getElementById("res-severity").innerText = data.severity;

  const sevBadge = document.getElementById("res-severity-badge");
  sevBadge.innerText = data.severity;
  sevBadge.className = `badge ${data.severity === "CRITICAL" ? "bg-danger" : data.severity === "HIGH" ? "bg-warning text-dark" : "bg-info text-dark"} fs-6 px-3 py-2`;

  document.getElementById("res-confidence").innerText = `${data.confidence_score}%`;
  document.getElementById("res-latency").innerText = `${data.inference_latency_ms} ms (< 50ms SLA)`;
  document.getElementById("res-area").innerText = `${data.affected_area_km2} km²`;

  // Render Actions
  const actionsList = document.getElementById("res-actions-list");
  actionsList.innerHTML = "";
  (data.recommended_actions || []).forEach((act) => {
    const li = document.createElement("li");
    li.className = "mb-1";
    li.innerHTML = `<i class="fa-solid fa-angle-right text-info me-2"></i>${act}`;
    actionsList.appendChild(li);
  });

  // Render SHAP
  if (data.shap_feature_importance) {
    renderShapBars(data.shap_feature_importance);
  }
}

function triggerModelTraining() {
  const btn = document.getElementById("btn-trigger-training");
  const origHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i> TRAINING PYTORCH MODEL...`;

  document.getElementById("training-status-log").innerText = "⏳ Initializing DataLoader, loading 1,200 historical dataset records, compiling AdamW optimizer...";

  fetch("/api/ml/train", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ epochs: 15 })
  })
    .then((res) => res.json())
    .then((data) => {
      btn.disabled = false;
      btn.innerHTML = origHtml;

      if (data.status === "success") {
        const m = data.metrics;
        document.getElementById("training-status-log").innerText = `✅ Training completed in ${m.training_duration_sec}s over ${m.epochs_trained} epochs!\nModel saved to: ${m.model_path || 'data/models/multi_fusion_v2.pt'}\nPrecision: ${(m.precision*100).toFixed(1)}% | Recall: ${(m.recall*100).toFixed(1)}% | F1: ${m.f1_score} | AUC-ROC: ${m.auc_roc}`;
        fetchModelMetrics();
      } else {
        document.getElementById("training-status-log").innerText = "⚠️ Training encountered error: " + (data.message || "Unknown error");
      }
    })
    .catch((err) => {
      btn.disabled = false;
      btn.innerHTML = origHtml;
      document.getElementById("training-status-log").innerText = "⚠️ Network error during model training: " + err.message;
    });
}
