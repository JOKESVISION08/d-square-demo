import React, { useState } from 'react';
import { Flame, Truck, ShieldAlert, CheckSquare, Clock, ChevronDown } from 'lucide-react';

export default function RescueGptDispatchCard({ incident, isDispatched = true, onUpdateStatus }) {
  const inc = incident || {};
  const [rescueStatus, setRescueStatus] = useState(inc.rescue_status || "Team Assigned");

  const dType = (inc.disaster_type || "fire").toUpperCase();
  const severity = (inc.severity || "CRITICAL").toUpperCase();
  const location = inc.location_name || "Uttarakhand Slope Sector 4";
  const readings = inc.sensor_readings || {};

  const handleStatusChange = (newStatus) => {
    setRescueStatus(newStatus);
    if (onUpdateStatus) {
      onUpdateStatus(inc.incident_id, newStatus);
    }
  };

  return (
    <div className="panel-card p-4 border-rose-500/40 bg-gradient-to-br from-slate-900 via-slate-900 to-rose-950/20 shadow-lg">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400">
            <Truck className="w-4 h-4" />
          </div>
          <h4 className="font-heading font-bold text-xs text-rose-300 uppercase tracking-wider">
            Rescue GPT Authority Command Feed
          </h4>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
            isDispatched
              ? "bg-rose-950 text-rose-300 border-rose-500/40 animate-pulse"
              : "bg-slate-800 text-slate-400 border-slate-700"
          }`}>
            {isDispatched ? "DISPATCHED" : "PENDING"}
          </span>
        </div>
      </div>

      <div className="space-y-3 text-xs">
        {/* Banner Status Header */}
        <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-200">
          <div className="font-bold flex items-center justify-between text-rose-300">
            <span className="flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>🚨 RESCUE GPT ALERT DISPATCHED — HIGH PRIORITY COMMAND</span>
            </span>
            <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-rose-900 text-rose-200">
              PRIORITY: P1
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-300">
            Tactical incident <strong>{inc.incident_id || "DSQ-SOS-001"}</strong> assigned to First Responder Units at <strong>{location}</strong>.
          </p>
        </div>

        {/* Tactical Sensor Evidence */}
        <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px]">
          <div className="text-slate-400 font-semibold mb-1">Sensor Telemetry Evidence:</div>
          <div className="grid grid-cols-2 gap-1 text-slate-300 text-[10px]">
            <div>Disaster Type: <span className="text-rose-400 font-bold">{dType}</span></div>
            <div>Severity: <span className="text-rose-400 font-bold">{severity}</span></div>
            <div>Coordinates: <span className="text-cyan-400">{inc.latitude || 30.0668}°N, {inc.longitude || 79.0193}°E</span></div>
            <div>Verified By: <span className="text-slate-200">{inc.verified_by || "operator@dsquare.gov.in"}</span></div>
          </div>
        </div>

        {/* Resource Checklist */}
        <div className="space-y-1.5">
          <div className="text-slate-400 font-semibold text-[11px]">Tactical Resource Checklist:</div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 font-mono text-[10px]">
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800 flex items-center gap-1 text-emerald-400">
              <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>NDRF Team 04 (Active)</span>
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800 flex items-center gap-1 text-emerald-400">
              <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>2 ALS Ambulances</span>
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800 flex items-center gap-1 text-amber-400">
              <CheckSquare className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span>Fire Rescue Unit 02</span>
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800 flex items-center gap-1 text-cyan-400">
              <CheckSquare className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span>Hospital Hotline Active</span>
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800 flex items-center gap-1 text-cyan-400">
              <CheckSquare className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span>District Shelter 850 Beds</span>
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800 flex items-center gap-1 text-indigo-400">
              <CheckSquare className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span>Drone Recon Flight</span>
            </div>
          </div>
        </div>

        {/* Rescue Status Selector */}
        <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
          <span className="text-slate-400 font-semibold text-[11px]">Response Status:</span>
          <div className="relative">
            <select
              value={rescueStatus}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="bg-slate-950 text-rose-300 font-semibold border border-rose-500/40 rounded-lg px-2.5 py-1 text-xs focus:outline-none cursor-pointer"
            >
              <option value="Pending">Pending</option>
              <option value="Acknowledged">Acknowledged</option>
              <option value="Team Assigned">Team Assigned</option>
              <option value="En Route">En Route</option>
              <option value="On Site">On Site</option>
              <option value="Resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
