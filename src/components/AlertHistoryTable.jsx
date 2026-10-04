import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function AlertHistoryTable({ alertHistory = [] }) {
  if (!alertHistory || alertHistory.length === 0) {
    return (
      <div className="panel-card p-4 text-center text-slate-500 text-xs">
        No raw hardware alert events logged in recent history.
      </div>
    );
  }

  return (
    <div className="panel-card p-4">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400" />
          <h3 className="font-heading font-bold text-xs text-amber-300 uppercase tracking-wider">
            Raw Hardware Warning Log History ({alertHistory.length})
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500">Firebase /nodes/alert_history</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase">
              <th className="py-2 px-2">Event ID</th>
              <th className="py-2 px-2">Node</th>
              <th className="py-2 px-2">Type</th>
              <th className="py-2 px-2">Confidence</th>
              <th className="py-2 px-2">Timestamp</th>
              <th className="py-2 px-2 text-right">Verification</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
            {alertHistory.map((a, idx) => (
              <tr key={a.event_id || idx} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-2.5 px-2 font-bold text-amber-400">{a.event_id || `EVT-${idx}`}</td>
                <td className="py-2.5 px-2 text-slate-300">{a.node_id || "D-SQUARE_NODE_01"}</td>
                <td className="py-2.5 px-2 uppercase font-semibold text-white">{(a.disaster_type || "fire").toUpperCase()}</td>
                <td className="py-2.5 px-2 text-cyan-400">{Math.round((a.confidence || 0.95) * 100)}%</td>
                <td className="py-2.5 px-2 text-slate-400 text-[11px]">{new Date(a.updated_at || Date.now()).toLocaleString()}</td>
                <td className="py-2.5 px-2 text-right">
                  <span className="text-[10px] text-amber-400 font-bold bg-amber-950 px-2 py-0.5 rounded border border-amber-500/30">
                    REQUIRED
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
