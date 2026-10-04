import React from 'react';
import { Bot, CheckCircle2, ShieldAlert, PhoneCall, MapPin, Navigation } from 'lucide-react';

export default function DSquareGptDispatchCard({ incident, isDispatched = true }) {
  const inc = incident || {};
  const dType = (inc.disaster_type || "fire").toUpperCase();
  const severity = (inc.severity || "CRITICAL").toUpperCase();
  const location = inc.location_name || "Uttarakhand Slope Sector 4";

  return (
    <div className="panel-card p-4 border-cyan-500/40 bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/20 shadow-lg">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400">
            <Bot className="w-4 h-4" />
          </div>
          <h4 className="font-heading font-bold text-xs text-cyan-300 uppercase tracking-wider">
            D-SQUARE GPT Public Safety Dispatch Channel
          </h4>
        </div>
        <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
          isDispatched
            ? "bg-emerald-950 text-emerald-300 border-emerald-500/40 animate-pulse"
            : "bg-slate-800 text-slate-400 border-slate-700"
        }`}>
          {isDispatched ? "DISPATCHED" : "PENDING"}
        </span>
      </div>

      <div className="space-y-3 text-xs">
        {/* Banner Alert Header */}
        <div className="p-3 rounded-lg bg-cyan-950/60 border border-cyan-500/30 text-cyan-200">
          <div className="font-bold flex items-center gap-1.5 text-cyan-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>📢 D-SQUARE GPT ALERT DISPATCHED — PUBLIC ADVISORY ACTIVE</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-300">
            Automated multilingual evacuation guidance broadcasted for <strong>{dType} ({severity})</strong> at <strong>{location}</strong>.
          </p>
        </div>

        {/* Safety Instructions & Area Warnings */}
        <div className="space-y-1.5 text-slate-300">
          <div className="flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Restricted Zone Warning:</strong> Evacuate immediate {dType} hazard perimeter ({location}). Do not enter slope catchments.
            </div>
          </div>

          <div className="flex items-start gap-2">
            <Navigation className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Suggested Safety Action:</strong> Proceed immediately via designated high-ground arterial routes to nearest registered emergency shelter.
            </div>
          </div>
        </div>

        {/* Shelters & Route Placeholder */}
        <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-400">
          <div className="flex items-center justify-between text-slate-300 mb-1">
            <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5 text-cyan-400" /> Nearest Relief Shelter:</span>
            <span className="text-emerald-400 font-semibold">District Relief Center 04 (1.8 km)</span>
          </div>
          <div className="text-[10px] text-slate-500">Route: NH-58 North Access Road • Shelter Capacity: 850 Beds Available</div>
        </div>

        {/* Emergency Contacts */}
        <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
          <span className="text-slate-400 flex items-center gap-1"><PhoneCall className="w-3.5 h-3.5 text-emerald-400" /> Helpline:</span>
          <span className="font-mono text-emerald-400 font-bold">NDRF: 1078 | State Helpline: 112</span>
        </div>
      </div>
    </div>
  );
}
