import React, { useState } from 'react';
import { ShieldCheck, X, AlertTriangle, Send, User, CheckCircle2 } from 'lucide-react';
import { initAudioContext } from '../utils/audio';

export default function TriggerSosConfirmationModal({
  isOpen,
  onClose,
  activeAlert,
  telemetry,
  onConfirmSos,
  user
}) {
  if (!isOpen) return null;

  const defaultDisaster = activeAlert ? (activeAlert.disaster_type || "fire") : "landslide";
  const [disasterType, setDisasterType] = useState(defaultDisaster);
  const [severity, setSeverity] = useState("CRITICAL");
  const [verificationNote, setVerificationNote] = useState("Verified slope movement and sensor telemetry stream on PC Dashboard.");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const operatorEmail = user?.email || "operator@dsquare.gov.in";
  const nodeId = activeAlert?.node_id || telemetry?.node_id || "D-SQUARE_NODE_01";
  const locationName = activeAlert?.location_name || "Uttarakhand Slope Sector 4";
  const confidence = activeAlert ? Math.round((activeAlert.confidence || 0.95) * 100) : 95;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Initialize Web Audio API on click flow
    initAudioContext();

    try {
      const incidentPayload = {
        source_event_id: activeAlert?.event_id || `EVT-HW-${Date.now().toString().slice(-6)}`,
        source_node_id: nodeId,
        disaster_type: disasterType,
        severity: severity,
        confidence: confidence / 100,
        location_name: locationName,
        latitude: activeAlert?.latitude || 30.0668,
        longitude: activeAlert?.longitude || 79.0193,
        sensor_readings: activeAlert?.sensor_readings || {
          temperature_c: telemetry?.temperature || 31.2,
          humidity_pct: telemetry?.humidity || 47.0,
          soil_moisture_pct: telemetry?.soil_moisture || 42.0,
          soil_raw: telemetry?.soil_raw || 850,
          mq2_smoke: telemetry?.mq2_gas || 0,
          flame: telemetry?.flame || 0
        },
        verified_by: operatorEmail,
        verification_note: verificationNote
      };

      await onConfirmSos(incidentPayload);
      onClose();
    } catch (err) {
      console.error("SOS Trigger Error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full shadow-2xl overflow-hidden text-slate-100">
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-rose-700 to-red-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-white/10 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-heading font-bold text-lg text-white tracking-wide">
                Authorized Human Operator Verification Gate
              </h3>
              <p className="text-xs text-rose-100/90">D-SQUARE 2.0 Emergency SOS Dispatch Control</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-white/80 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-xs text-rose-200 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">OPERATOR NOTICE:</strong> Confirming this SOS incident will create a verified incident in Firebase (<code className="font-mono text-rose-300">/incidents/&#123;incident_id&#125;</code>), play confirmation audio beeps, and dispatch parallel alerts to <strong>D-SQUARE GPT</strong> and <strong>Rescue GPT</strong>.
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {/* Operator Email */}
            <div>
              <label className="block text-slate-400 text-[11px] uppercase font-bold mb-1">
                AUTHORIZED OPERATOR *
              </label>
              <div className="flex items-center gap-2 bg-slate-950 border border-slate-700 px-3 py-2 rounded-lg text-slate-200">
                <User className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-mono text-xs truncate">{operatorEmail}</span>
              </div>
            </div>

            {/* Target Node */}
            <div>
              <label className="block text-slate-400 text-[11px] uppercase font-bold mb-1">
                GROUND STATION NODE ID
              </label>
              <input
                type="text"
                readOnly
                value={nodeId}
                className="w-full bg-slate-950 border border-slate-700 px-3 py-2 rounded-lg text-slate-300 font-mono text-xs"
              />
            </div>

            {/* Disaster Type */}
            <div>
              <label className="block text-slate-400 text-[11px] uppercase font-bold mb-1">
                DISASTER TYPE *
              </label>
              <select
                value={disasterType}
                onChange={(e) => setDisasterType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 px-3 py-2 rounded-lg text-slate-100 text-xs focus:outline-none focus:border-cyan-500"
              >
                <option value="fire">🔥 WILDFIRE / STRUCTURAL FIRE</option>
                <option value="landslide">⛰️ LANDSLIDE / SLOPE DISPLACEMENT</option>
                <option value="flood">🌊 FLASH FLOOD / INUNDATION</option>
                <option value="earthquake">🌋 EARTHQUAKE / SEISMIC SHOCK</option>
                <option value="cyclone">🌀 CYCLONE SURGE</option>
              </select>
            </div>

            {/* Severity Level */}
            <div>
              <label className="block text-slate-400 text-[11px] uppercase font-bold mb-1">
                INCIDENT SEVERITY *
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 px-3 py-2 rounded-lg text-slate-100 text-xs focus:outline-none focus:border-rose-500"
              >
                <option value="CRITICAL">🔴 CRITICAL (IMMINENT THREAT)</option>
                <option value="HIGH">🟠 HIGH (EVACUATION ADVISORY)</option>
                <option value="MEDIUM">🟡 MEDIUM (ALERT MONITORING)</option>
              </select>
            </div>
          </div>

          {/* Verification Notes */}
          <div>
            <label className="block text-slate-400 text-[11px] uppercase font-bold mb-1">
              VERIFICATION NOTE &amp; TELEMETRY AUDIT *
            </label>
            <textarea
              required
              rows={3}
              value={verificationNote}
              onChange={(e) => setVerificationNote(e.target.value)}
              placeholder="Document sentinel video observations, sensor evidence, radar metrics..."
              className="w-full bg-slate-950 border border-slate-700 p-3 rounded-lg text-slate-100 text-xs focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Footer Action Buttons */}
          <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-colors"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-700 hover:to-red-800 text-white font-bold text-xs shadow-lg shadow-rose-600/30 flex items-center gap-2 transition-all"
            >
              {isSubmitting ? (
                <span>Broadcasting SOS...</span>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>CONFIRM &amp; TRIGGER SOS NOW</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
