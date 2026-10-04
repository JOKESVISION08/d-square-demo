import React from 'react';
import { Satellite, Activity } from 'lucide-react';

export default function NisarSarTelemetryPanel({ telemetry, satelliteData }) {
  const isAvailable = satelliteData && satelliteData.status !== "UNAVAILABLE";

  if (!isAvailable) {
    return (
      <div className="panel-card p-4 h-full flex flex-col justify-between border-slate-800 bg-slate-900/90 shadow-md text-slate-400">
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-slate-800 text-slate-400">
                <Satellite className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-heading font-bold text-sm text-slate-300 tracking-wide">
                  Satellite / NISAR SAR Data Feed
                </h3>
                <p className="text-[11px] text-slate-500">ISRO / Sentinel / Landsat Product Stream</p>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              UNAVAILABLE
            </span>
          </div>

          <div className="my-6 p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-center space-y-2">
            <div className="text-xs font-semibold text-amber-400">
              📡 Satellite data unavailable — hardware-only monitoring active.
            </div>
            <p className="text-[11px] text-slate-400 max-w-md mx-auto">
              Waiting for real satellite/NISAR product upload or authorized API stream connection.
            </p>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs font-mono">
          <span className="text-slate-500">Source: Hardware Only</span>
          <span className="text-slate-500">Status: Standby</span>
        </div>
      </div>
    );
  }

  const lBand = typeof satelliteData?.l_band_db === 'number' ? satelliteData.l_band_db : (telemetry?.sar_l_band_db || -14.5);
  const sBand = typeof satelliteData?.s_band_db === 'number' ? satelliteData.s_band_db : (telemetry?.sar_s_band_db || -8.2);
  const coherence = typeof satelliteData?.coherence === 'number' ? satelliteData.coherence : (telemetry?.sar_coherence || 0.42);
  const deformation = typeof satelliteData?.deformation_mm_yr === 'number' ? satelliteData.deformation_mm_yr : (telemetry?.ground_deformation_mm_yr || -34.8);
  const isDeforming = Math.abs(deformation) > 10.0;

  return (
    <div className="panel-card p-4 h-full flex flex-col justify-between border-cyan-500/30 bg-gradient-to-br from-slate-900 to-slate-900/90 shadow-md">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <Satellite className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-heading font-bold text-sm text-cyan-400 tracking-wide">
                NISAR Dual-Band SAR Radar Metrics ({satelliteData.source})
              </h3>
              <p className="text-[11px] text-slate-400">Acquired: {new Date(satelliteData.acquisition_time).toLocaleDateString()}</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">
            {satelliteData.status}
          </span>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-3">
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            <div className="text-[10px] uppercase font-semibold text-slate-400">L-Band</div>
            <div className="text-base font-bold text-cyan-400 mt-0.5">{Number(lBand).toFixed(1)} dB</div>
          </div>

          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            <div className="text-[10px] uppercase font-semibold text-slate-400">S-Band</div>
            <div className="text-base font-bold text-cyan-400 mt-0.5">{Number(sBand).toFixed(1)} dB</div>
          </div>

          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            <div className="text-[10px] uppercase font-semibold text-slate-400">Coherence</div>
            <div className="text-base font-bold text-emerald-400 mt-0.5">{Number(coherence).toFixed(2)}</div>
          </div>

          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            <div className="text-[10px] uppercase font-semibold text-slate-400">Displacement</div>
            <div className={`text-base font-bold mt-0.5 ${isDeforming ? "text-rose-400" : "text-emerald-400"}`}>
              {Number(deformation).toFixed(1)} mm/yr
            </div>
          </div>
        </div>
      </div>

      <div className="mt-2 p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span>Product Status:</span>
          <span className="font-semibold text-cyan-300">{satelliteData.message}</span>
        </div>
      </div>
    </div>
  );
}
