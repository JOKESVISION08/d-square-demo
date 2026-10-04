import React from 'react';
import DSquareGptDispatchCard from './DSquareGptDispatchCard';
import RescueGptDispatchCard from './RescueGptDispatchCard';

export default function SOSDispatchPanel({ activeIncident }) {
  if (!activeIncident || activeIncident.status !== "SOS_ACTIVE") {
    return (
      <div className="mb-6 p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-500 text-xs text-center font-mono">
        Parallel GPT Dispatch Channels on Standby. (Requires Operator Verified SOS Incident)
      </div>
    );
  }

  const isDSquareDispatched = activeIncident.dispatch?.dsquare_gpt === "DISPATCHED";
  const isRescueDispatched = activeIncident.dispatch?.rescue_gpt === "DISPATCHED";

  return (
    <div className="mb-6 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2 font-heading">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
          <span>Parallel Multi-Agent GPT Dispatch Channels (Concurrent Live Feeds)</span>
        </h3>
        <span className="text-[11px] font-mono text-slate-400">
          INCIDENT: <strong className="text-white">{activeIncident.incident_id}</strong>
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* D-SQUARE GPT Public Safety Channel */}
        <DSquareGptDispatchCard
          incident={activeIncident}
          isDispatched={isDSquareDispatched}
        />

        {/* Rescue GPT First Responders Command Feed */}
        <RescueGptDispatchCard
          incident={activeIncident}
          isDispatched={isRescueDispatched}
        />
      </div>
    </div>
  );
}
