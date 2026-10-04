import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, ShieldAlert } from 'lucide-react';

export default function HardwareWarningBanner({ alert, onOpenSosModal }) {
  if (!alert || alert.event_status !== "ACTIVE") return null;

  const disasterType = (alert.disaster_type || "fire").toUpperCase();
  const confidence = Math.round((alert.confidence || 0.95) * 100);
  const location = alert.location_name || "Uttarakhand Slope Sector 4";
  const nodeId = alert.node_id || "D-SQUARE_NODE_01";
  const readings = alert.sensor_readings || {};

  return (
    <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-amber-950/80 via-slate-900 to-amber-950/80 border border-amber-500/80 text-amber-200 shadow-xl shadow-amber-950/30">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Banner Left Info */}
        <div className="flex items-start gap-3">
          <div className="p-3 rounded-xl bg-amber-500/20 text-amber-400 shrink-0 mt-0.5 border border-amber-500/40">
            <AlertTriangle className="w-6 h-6 animate-pulse" />
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-heading font-extrabold text-base text-amber-300 tracking-wide">
                ⚠️ SILENT HARDWARE WARNING: {disasterType} ANOMALY INGESTED
              </span>
              <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                {confidence}% CONFIDENCE
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                NO AUDIO / SILENT
              </span>
            </div>

            <p className="text-xs text-amber-200/90 mt-1 max-w-3xl">
              Raw sensor telemetry from <strong className="text-white font-mono">{nodeId}</strong> at <strong className="text-white">{location}</strong> indicates elevated hazard parameters. Transmitting live telemetry and pixel location to Alert Center.
            </p>

            {/* Sensor Evidence Snippet */}
            <div className="flex flex-wrap items-center gap-3 mt-2 text-xs font-mono text-slate-300 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
              <span className="text-amber-400 font-bold">Evidence:</span>
              {readings.temperature_c && <span>Temp: <strong className="text-white">{readings.temperature_c}°C</strong></span>}
              {readings.humidity_pct && <span>Hum: <strong className="text-white">{readings.humidity_pct}%</strong></span>}
              {readings.soil_moisture_pct && <span>Soil: <strong className="text-white">{readings.soil_moisture_pct}%</strong></span>}
              {readings.mq2_smoke === 1 && <span className="text-rose-400 font-bold">MQ-2 Smoke: DETECTED</span>}
              {readings.flame === 1 && <span className="text-rose-400 font-bold">IR Flame: ACTIVE</span>}
              <span className="text-amber-400 italic">| Awaiting Operator Verification</span>
            </div>
          </div>
        </div>

        {/* Action Button: Navigate to Single Alert Center Dashboard */}
        <div className="shrink-0 flex items-center gap-2">
          <Link
            to="/alert-center"
            className="w-full lg:w-auto px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 via-rose-600 to-red-600 hover:from-amber-600 hover:to-red-700 text-white font-bold text-xs shadow-lg shadow-rose-600/30 flex items-center justify-center gap-2 transition-all transform hover:scale-[1.02]"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>OPEN ALERT CENTER &amp; DISPATCH →</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
