import React from 'react';
import { ShieldAlert, Send, MapPin, CheckCircle2, AlertTriangle, Activity, ArrowLeft, Cpu, Satellite, Radio } from 'lucide-react';
import { Link } from 'react-router-dom';
import LiveDisasterMap from '../components/LiveDisasterMap';
import HardwareAlertDetails from '../components/HardwareAlertDetails';
import ConnectionStatusPanel from '../components/ConnectionStatusPanel';

export default function DSquareAlertCenterPage({
  telemetry,
  activeAlert,
  incidents = [],
  onOpenSosModal,
  satelliteData
}) {
  const activeIncident = incidents.find(i => i.status === "SOS_ACTIVE") || null;

  const isDsquareDispatched = activeIncident?.dispatch?.dsquare_gpt === "DISPATCHED";
  const isRescueDispatched = activeIncident?.dispatch?.rescue_gpt === "DISPATCHED";

  const nodeLat = activeAlert?.latitude || telemetry?.latitude || 30.0668;
  const nodeLng = activeAlert?.longitude || telemetry?.longitude || 79.0193;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Alert Center Dashboard Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-rose-950 via-slate-900 to-rose-950 border border-rose-500/50 shadow-2xl">
        <div className="flex items-center gap-3">
          <Link to="/" className="p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white transition-colors border border-slate-700">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="p-3 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/40">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <div>
            <h1 className="font-heading font-extrabold text-xl text-white uppercase tracking-wide">
              D-SQUARE Single Emergency Alert Center
            </h1>
            <p className="text-xs text-rose-200/90">
              Live Ground Hardware Telemetry, Satellite Pixel Location &amp; Parallel Multi-Agent Dispatch Command
            </p>
          </div>
        </div>

        <button
          onClick={onOpenSosModal}
          className="px-5 py-3 rounded-xl bg-gradient-to-r from-rose-600 via-red-600 to-rose-700 hover:from-rose-700 hover:to-red-800 text-white font-bold text-xs shadow-xl shadow-rose-600/40 flex items-center gap-2 transition-all transform hover:scale-[1.02]"
        >
          <Send className="w-4 h-4" />
          <span>VERIFY &amp; TRIGGER SOS DISPATCH</span>
        </button>
      </div>

      {/* Main Grid Layout: Interactive GIS Pixel Map + Incident Dispatch Control */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 8 Cols: Real-Time GIS Location & Satellite Pixel Map */}
        <div className="lg:col-span-8 space-y-4">
          <div className="panel-card p-4 bg-slate-900 border-slate-800">
            <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2 font-heading font-bold text-xs text-cyan-300 uppercase">
                <MapPin className="w-4 h-4 text-rose-400" /> Live Target Location &amp; Satellite Pixel Perimeter Map
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                LAT: {nodeLat}°N | LNG: {nodeLng}°E
              </span>
            </div>

            <LiveDisasterMap
              telemetry={telemetry}
              activeAlert={activeAlert}
              activeIncident={activeIncident}
              customPolygon={satelliteData?.polygon_boundary}
              height="440px"
            />
          </div>

          {/* Detailed Evidence Log */}
          <HardwareAlertDetails alert={activeAlert} />
        </div>

        {/* Right 4 Cols: Real-Time Connection Audit & Parallel GPT Channels */}
        <div className="lg:col-span-4 space-y-4">
          <ConnectionStatusPanel telemetry={telemetry} satelliteData={satelliteData} />

          <div className="panel-card p-4 bg-slate-900 border-slate-800 space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-rose-400 mb-2 flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="flex items-center gap-1.5 font-heading">
                <Activity className="w-4 h-4" /> Parallel Multi-Agent GPT Status
              </span>
              <span className="text-[10px] font-mono text-slate-400">CONCURRENT</span>
            </div>

            {/* D-SQUARE GPT Channel */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-cyan-300">D-SQUARE GPT (Citizen)</span>
                <span className={`text-[10px] font-mono px-2.5 py-0.5 rounded font-bold border ${
                  isDsquareDispatched 
                    ? "bg-emerald-950 text-emerald-300 border-emerald-500/40 animate-pulse" 
                    : "bg-slate-900 text-slate-400 border-slate-700"
                }`}>
                  {isDsquareDispatched ? "DISPATCHED" : "PENDING"}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Public Safety Advisories, Weather Risk &amp; Evacuation Directions.
              </p>
              <Link
                to="/dsquare-gpt"
                className="inline-block text-[11px] text-cyan-400 hover:underline font-semibold"
              >
                Open D-SQUARE GPT Guide →
              </Link>
            </div>

            {/* Rescue GPT Channel */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-rose-300">Rescue GPT (First Responders)</span>
                <span className={`text-[10px] font-mono px-2.5 py-0.5 rounded font-bold border ${
                  isRescueDispatched 
                    ? "bg-emerald-950 text-emerald-300 border-emerald-500/40 animate-pulse" 
                    : "bg-slate-900 text-slate-400 border-slate-700"
                }`}>
                  {isRescueDispatched ? "DISPATCHED" : "PENDING"}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                First Responders, Tactical Equipment &amp; NDRF Command Feeds.
              </p>
              <Link
                to="/rescue-gpt"
                className="inline-block text-[11px] text-rose-400 hover:underline font-semibold"
              >
                Open Rescue GPT Command →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
