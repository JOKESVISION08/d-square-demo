import React from 'react';
import { History, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function IncidentHistoryTable({ incidents = [] }) {
  if (!incidents || incidents.length === 0) {
    return (
      <div className="panel-card p-4 text-center text-slate-500 text-xs">
        No verified SOS incident records found in Firebase history.
      </div>
    );
  }

  return (
    <div className="panel-card p-4">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-cyan-400" />
          <h3 className="font-heading font-bold text-xs text-cyan-300 uppercase tracking-wider">
            Verified SOS Incident Audit History ({incidents.length})
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500">Firebase /incidents</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase">
              <th className="py-2 px-2">Incident ID</th>
              <th className="py-2 px-2">Disaster</th>
              <th className="py-2 px-2">Severity</th>
              <th className="py-2 px-2">Verified By</th>
              <th className="py-2 px-2">Timestamp</th>
              <th className="py-2 px-2 text-right">GPT Dispatch</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
            {incidents.map((inc) => (
              <tr key={inc.incident_id} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-2.5 px-2 font-bold text-cyan-400">{inc.incident_id}</td>
                <td className="py-2.5 px-2 uppercase font-semibold text-white">{(inc.disaster_type || "fire").toUpperCase()}</td>
                <td className="py-2.5 px-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-500/30">
                    {inc.severity || "CRITICAL"}
                  </span>
                </td>
                <td className="py-2.5 px-2 text-slate-400 text-[11px]">{inc.verified_by || "operator"}</td>
                <td className="py-2.5 px-2 text-slate-400 text-[11px]">{new Date(inc.verified_at || Date.now()).toLocaleString()}</td>
                <td className="py-2.5 px-2 text-right">
                  <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/30">
                    <CheckCircle2 className="w-3 h-3" /> DISPATCHED
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
