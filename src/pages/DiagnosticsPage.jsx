import React, { useState, useEffect } from 'react';
import { Activity, Database, Cpu, Satellite, Copy, Check, ShieldCheck, AlertCircle } from 'lucide-react';
import { fetchSystemDiagnostics, calculateNodeHealth } from '../firebase/realtime';

export default function DiagnosticsPage({ currentNode = "D-SQUARE_NODE_01" }) {
  const [diagData, setDiagData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      const data = await fetchSystemDiagnostics(currentNode);
      setDiagData(data);
      setIsLoading(false);
    }
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [currentNode]);

  const handleCopyReport = () => {
    if (!diagData) return;
    const report = {
      timestamp: new Date().toISOString(),
      node_id: diagData.node_id,
      connection_state: diagData.connection_state,
      database_url: diagData.database_url,
      http_status: diagData.http_status,
      firmware_version: diagData.firmware_version,
      last_telemetry: diagData.last_telemetry,
      last_hardware_alert: diagData.last_hardware_alert,
      satellite_status: diagData.satellite_data?.status || "UNAVAILABLE"
    };

    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const health = calculateNodeHealth(diagData?.last_telemetry);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-heading font-extrabold text-lg text-slate-100 uppercase tracking-wide">
              Production System Diagnostics
            </h1>
            <p className="text-xs text-slate-400">Live Health, Telemetry Audit &amp; System State</p>
          </div>
        </div>

        <button
          onClick={handleCopyReport}
          className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-2 transition-all shadow-lg shadow-cyan-600/30"
        >
          {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
          <span>{copied ? "Report Copied to Clipboard!" : "Copy Diagnostic Report"}</span>
        </button>
      </div>

      {/* Grid Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Node Connection */}
        <div className="panel-card p-4 bg-slate-900 border-slate-800">
          <div className="text-[11px] font-bold uppercase text-slate-400 mb-1 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Node Status
          </div>
          <div className="text-lg font-mono font-extrabold text-slate-100">{health.status}</div>
          <div className="text-[11px] text-slate-400 mt-1">{health.message}</div>
        </div>

        {/* Database Health */}
        <div className="panel-card p-4 bg-slate-900 border-slate-800">
          <div className="text-[11px] font-bold uppercase text-slate-400 mb-1 flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-emerald-400" /> Database Connection
          </div>
          <div className="text-lg font-mono font-extrabold text-emerald-400">{diagData?.connection_state || "UNKNOWN"}</div>
          <div className="text-[11px] text-slate-400 mt-1">HTTP Status Code: {diagData?.http_status || 200}</div>
        </div>

        {/* Firmware Version */}
        <div className="panel-card p-4 bg-slate-900 border-slate-800">
          <div className="text-[11px] font-bold uppercase text-slate-400 mb-1 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-purple-400" /> Firmware Version
          </div>
          <div className="text-lg font-mono font-extrabold text-purple-300">{diagData?.firmware_version || "2.0.0-PROD"}</div>
          <div className="text-[11px] text-slate-400 mt-1">HTTPS Encryption Enabled</div>
        </div>

        {/* Satellite State */}
        <div className="panel-card p-4 bg-slate-900 border-slate-800">
          <div className="text-[11px] font-bold uppercase text-slate-400 mb-1 flex items-center gap-1.5">
            <Satellite className="w-3.5 h-3.5 text-amber-400" /> Satellite Product
          </div>
          <div className="text-lg font-mono font-extrabold text-amber-300">{diagData?.satellite_data?.status || "UNAVAILABLE"}</div>
          <div className="text-[11px] text-slate-400 mt-1">
            {diagData?.satellite_data?.source || "Hardware-Only Monitoring Active"}
          </div>
        </div>
      </div>

      {/* Raw JSON Diagnostics Panel */}
      <div className="panel-card p-5 bg-slate-900 border-slate-800">
        <h3 className="font-heading font-bold text-xs uppercase tracking-wider text-slate-300 mb-3">
          Raw Firebase Production Data Audit Log
        </h3>
        <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-cyan-300 overflow-x-auto max-h-96">
          {JSON.stringify(diagData, null, 2)}
        </pre>
      </div>
    </div>
  );
}
