import React from 'react';
import { AlertCircle, MapPin, Cpu, Clock, ShieldCheck } from 'lucide-react';

export default function HardwareAlertDetails({ alert }) {
  if (!alert) {
    return (
      <div className="panel-card p-4 text-center text-slate-500 text-xs">
        No active raw hardware warnings detected. Telemetry normal.
      </div>
    );
  }

  const readings = alert.sensor_readings || {};

  return (
    <div className="panel-card p-4 border-amber-500/40 bg-slate-900/90">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400" />
          <h4 className="font-heading font-bold text-xs text-amber-300 uppercase tracking-wider">
            Raw Hardware Warning Evidence Log
          </h4>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-500/30">
          EVENT: {alert.event_id || "EVT-HW-001"}
        </span>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between items-center">
          <span className="text-slate-400 flex items-center gap-1"><Cpu className="w-3.5 h-3.5 text-slate-500" /> Sensor Node:</span>
          <span className="font-mono text-slate-200 font-semibold">{alert.node_id}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-slate-400 flex items-center gap-1"><MapPin className="w-3.5 h-3.5 text-slate-500" /> Target Sector:</span>
          <span className="text-slate-200 font-medium">{alert.location_name}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-slate-400">Disaster Type &amp; Confidence:</span>
          <span className="font-bold text-amber-400 uppercase">
            {(alert.disaster_type || "FIRE").toUpperCase()} ({Math.round((alert.confidence || 0.95) * 100)}%)
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-slate-400 flex items-center gap-1"><Clock className="w-3.5 h-3.5 text-slate-500" /> Timestamp:</span>
          <span className="font-mono text-slate-400">{new Date(alert.updated_at || Date.now()).toLocaleString()}</span>
        </div>

        <div className="mt-3 pt-2 border-t border-slate-800/80">
          <div className="text-[11px] font-semibold text-slate-400 mb-1.5">Sensor Reading Evidence:</div>
          <div className="grid grid-cols-2 gap-1.5 font-mono text-[11px] bg-slate-950 p-2.5 rounded-lg border border-slate-800">
            <div>Temp: <span className="text-cyan-400">{readings.temperature_c ?? 25.0}°C</span></div>
            <div>Hum: <span className="text-blue-400">{readings.humidity_pct ?? 50.0}%</span></div>
            <div>Soil Moisture: <span className="text-amber-400">{readings.soil_moisture_pct ?? 42.0}%</span></div>
            <div>Soil Raw: <span className="text-slate-300">{readings.soil_raw ?? 850}</span></div>
            <div>MQ-2 Smoke: <span className={readings.mq2_smoke === 1 ? "text-rose-400 font-bold" : "text-emerald-400"}>{readings.mq2_smoke === 1 ? "ACTIVE" : "CLEAN"}</span></div>
            <div>IR Flame: <span className={readings.flame === 1 ? "text-rose-400 font-bold" : "text-emerald-400"}>{readings.flame === 1 ? "ACTIVE" : "SAFE"}</span></div>
          </div>
        </div>

        <div className="mt-2.5 p-2 rounded bg-amber-950/40 border border-amber-500/30 text-[11px] text-amber-300 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0" />
          <span>Verification Status: <strong>Awaiting Operator Verification</strong></span>
        </div>
      </div>
    </div>
  );
}
