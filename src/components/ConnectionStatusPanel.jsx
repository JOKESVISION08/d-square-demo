import React from 'react';
import { Cpu, Satellite, Cloud, CheckCircle2, AlertTriangle, WifiOff, Clock } from 'lucide-react';
import { calculateNodeHealth } from '../firebase/realtime';

export default function ConnectionStatusPanel({ telemetry, satelliteData, connectionStatus = "CONNECTED" }) {
  const nodeHealth = calculateNodeHealth(telemetry);
  
  const satStatus = satelliteData?.status || "UNAVAILABLE";
  const satLastUpdate = satelliteData?.acquisition_time 
    ? new Date(satelliteData.acquisition_time).toLocaleTimeString() 
    : "None";

  const cloudState = connectionStatus === "online" || connectionStatus === "CONNECTED"
    ? { label: "CONNECTED", color: "text-emerald-400 bg-emerald-950/80 border-emerald-500/40", icon: CheckCircle2 }
    : { label: "DISCONNECTED", color: "text-rose-400 bg-rose-950/80 border-rose-500/40", icon: WifiOff };

  const nodeBadgeClass = nodeHealth.status === "ONLINE"
    ? "text-emerald-400 bg-emerald-950/80 border-emerald-500/40"
    : nodeHealth.status === "STALE"
    ? "text-amber-400 bg-amber-950/80 border-amber-500/40"
    : "text-rose-400 bg-rose-950/80 border-rose-500/40";

  const satBadgeClass = satStatus === "CONFIRMED" || satStatus === "CONNECTED"
    ? "text-emerald-400 bg-emerald-950/80 border-emerald-500/40"
    : satStatus === "PROCESSING"
    ? "text-cyan-400 bg-cyan-950/80 border-cyan-500/40"
    : "text-slate-400 bg-slate-900 border-slate-700";

  return (
    <div className="panel-card p-4 bg-slate-900/90 border-slate-800 text-slate-100">
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between border-b border-slate-800 pb-2">
        <span className="flex items-center gap-1.5 text-cyan-400 font-heading">
          <Cloud className="w-3.5 h-3.5" /> Live Production Connections
        </span>
        <span className="text-[10px] font-mono text-slate-400">REAL ARCHITECTURE</span>
      </div>

      <div className="space-y-3 text-xs font-mono">
        {/* ESP8266 Hardware Status */}
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <div>
              <div className="font-bold text-slate-200">ESP8266 Node</div>
              <div className="text-[10px] text-slate-400">
                Last seen: {nodeHealth.lastSeen ? nodeHealth.lastSeen.toLocaleTimeString() : "Never"}
              </div>
            </div>
          </div>
          <span className={`px-2.5 py-1 rounded text-[10px] font-bold border ${nodeBadgeClass}`}>
            {nodeHealth.status}
          </span>
        </div>

        {/* Satellite / NISAR Status */}
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800">
          <div className="flex items-center gap-2">
            <Satellite className="w-4 h-4 text-purple-400" />
            <div>
              <div className="font-bold text-slate-200">Satellite / NISAR</div>
              <div className="text-[10px] text-slate-400">
                Last update: {satLastUpdate}
              </div>
            </div>
          </div>
          <span className={`px-2.5 py-1 rounded text-[10px] font-bold border ${satBadgeClass}`}>
            {satStatus}
          </span>
        </div>

        {/* Firebase Cloud Status */}
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800">
          <div className="flex items-center gap-2">
            <Cloud className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="font-bold text-slate-200">Firebase Cloud</div>
              <div className="text-[10px] text-slate-400">HTTPS RTDB Connection</div>
            </div>
          </div>
          <span className={`px-2.5 py-1 rounded text-[10px] font-bold border ${cloudState.color}`}>
            {cloudState.label}
          </span>
        </div>
      </div>
    </div>
  );
}
