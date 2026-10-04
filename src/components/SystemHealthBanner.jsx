import React from 'react';
import { ShieldCheck, AlertTriangle, Radio, CheckCircle } from 'lucide-react';
import { resolveIncident } from '../firebase/realtime';

export default function SystemHealthBanner({ telemetry, activeAlert, activeIncident, nodeName = "D-SQUARE_NODE_01" }) {
  const isSosActive = activeIncident && activeIncident.status === "SOS_ACTIVE";
  const isHardwareWarning = activeAlert && activeAlert.event_status === "ACTIVE";

  if (isSosActive) {
    return (
      <div className="mb-4 p-4 rounded-xl bg-rose-950/80 border border-rose-500 text-rose-200 shadow-lg shadow-rose-900/30 animate-glow-red">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-rose-900/80 text-rose-300">
              <Radio className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="font-heading font-bold text-base text-white tracking-wide">
                🚨 VERIFIED SOS INCIDENT ACTIVE — PARALLEL DISPATCH OPERATIONAL
              </div>
              <div className="text-xs text-rose-300/90 mt-0.5">
                Authorized incident <span className="font-mono font-bold text-white">{activeIncident.incident_id}</span> confirmed by {activeIncident.verified_by}. D-SQUARE GPT &amp; Rescue GPT feeds active.
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right text-xs font-mono bg-rose-900/40 px-3 py-1.5 rounded-lg border border-rose-500/30">
              <div>DISASTER: <span className="text-white font-bold">{activeIncident.disaster_type.toUpperCase()}</span></div>
              <div>SEVERITY: <span className="text-rose-400 font-bold">{activeIncident.severity}</span></div>
            </div>

            <button
              onClick={() => resolveIncident(activeIncident.incident_id)}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-300 font-bold text-xs border border-emerald-500/40 flex items-center gap-1 transition-colors"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>MARK RESOLVED</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isHardwareWarning) {
    return (
      <div className="mb-4 p-4 rounded-xl bg-amber-950/70 border border-amber-500/80 text-amber-200 shadow-lg shadow-amber-900/20">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-900/60 text-amber-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <div className="font-heading font-bold text-base text-amber-300 tracking-wide">
                ⚠️ SILENT HARDWARE ANOMALY DETECTED (NO AUDIO ALARM / NO AUTO DISPATCH)
              </div>
              <div className="text-xs text-amber-200/90 mt-0.5">
                Raw sensor readings indicate elevated <span className="font-bold text-white">{activeAlert.disaster_type.toUpperCase()}</span> risk on {activeAlert.node_id}. Requires human operator verification.
              </div>
            </div>
          </div>
          <div className="text-right text-xs font-mono bg-amber-900/40 px-3 py-1.5 rounded-lg border border-amber-500/30">
            <div className="text-amber-400 font-bold">AWAITING VERIFICATION</div>
            <div className="text-slate-300">{new Date(activeAlert.updated_at || Date.now()).toLocaleTimeString()}</div>
          </div>
        </div>
      </div>
    );
  }

  if (!telemetry && !activeAlert && !isSosActive) {
    return (
      <div className="mb-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-400">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-slate-800 text-cyan-400">
              <Radio className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="font-heading font-bold text-sm text-cyan-300 tracking-wide">
                📡 Waiting for real ESP8266 telemetry...
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                Listening for live HTTPS REST/Database stream on node <span className="font-mono text-slate-200">{nodeName}</span>.
              </div>
            </div>
          </div>
          <div className="text-right text-xs font-mono text-slate-500">
            <div>STATUS: <span className="text-amber-400 font-bold">CONNECTING</span></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4 p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-200">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-900/40 text-emerald-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="font-heading font-bold text-sm text-emerald-300 tracking-wide">
              ✅ ALL SYSTEMS OPERATIONAL — REAL ESP8266 TELEMETRY STREAM
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Ground sensors on <span className="font-mono text-slate-200 font-semibold">{nodeName}</span> operating within safe parameters.
            </div>
          </div>
        </div>
        <div className="text-right text-xs font-mono text-slate-400">
          <div>MODE: <span className="text-emerald-400 font-bold">REAL PRODUCTION</span></div>
        </div>
      </div>
    </div>
  );
}
