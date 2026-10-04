import React, { useState, useEffect } from 'react';
import { Terminal, Database, Shield, Flame, Waves, CheckCircle, RefreshCw, Volume2, VolumeX, Radio } from 'lucide-react';
import { isUsingEmulator } from '../firebase/config';
import {
  seedNormalTelemetry,
  seedFireHardwareWarning,
  seedLandslideHardwareWarning,
  clearHardwareWarning,
  resetAllDemoData
} from '../dev/seedDemoData';
import { getAudioMuted, setAudioMuted, initAudioContext } from '../utils/audio';

export default function DevelopmentToolsPanel({ activeAlert, activeIncident, user, onOpenSosModal }) {
  // Only render in local development mode
  if (!import.meta.env.DEV) return null;

  const [isMuted, setIsMutedState] = useState(getAudioMuted());
  const [lastUpdate, setLastUpdate] = useState(new Date().toLocaleTimeString());
  const [audioState, setAudioState] = useState("Uninitialized");

  useEffect(() => {
    setLastUpdate(new Date().toLocaleTimeString());
  }, [activeAlert, activeIncident]);

  const handleToggleSound = () => {
    const nextMute = !isMuted;
    setAudioMuted(nextMute);
    setIsMutedState(nextMute);
  };

  const handleTestAudio = () => {
    initAudioContext();
    setAudioState("Active / Initialized");
  };

  return (
    <div className="mb-6 p-4 rounded-xl bg-slate-950 border border-cyan-500/40 text-slate-200 shadow-2xl">
      {/* Dev Badge Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400">
            <Terminal className="w-4 h-4" />
          </div>
          <span className="font-heading font-extrabold text-xs text-cyan-300 uppercase tracking-wider">
            LOCAL TEST MODE — FIREBASE EMULATOR TOOLBAR
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-500/40">
            DEV ONLY
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-slate-300">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            <span>Target:</span>
            <span className={`font-bold ${isUsingEmulator ? "text-emerald-400" : "text-amber-400"}`}>
              {isUsingEmulator ? "Emulator (localhost:9000)" : "Firebase Cloud Project"}
            </span>
          </div>
        </div>
      </div>

      {/* Dev Status Overview Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 text-[11px] font-mono bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
        <div>
          <span className="text-slate-500">Auth User:</span>{" "}
          <strong className="text-slate-200">{user ? user.email : "Not Authenticated"}</strong>
        </div>
        <div>
          <span className="text-slate-500">Hardware Alert:</span>{" "}
          <strong className={activeAlert ? "text-amber-400" : "text-emerald-400"}>
            {activeAlert ? `${activeAlert.disaster_type.toUpperCase()} (ACTIVE)` : "CLEARED"}
          </strong>
        </div>
        <div>
          <span className="text-slate-500">SOS Incident:</span>{" "}
          <strong className={activeIncident ? "text-rose-400" : "text-slate-400"}>
            {activeIncident ? activeIncident.incident_id : "None"}
          </strong>
        </div>
        <div>
          <span className="text-slate-500">AudioContext:</span>{" "}
          <strong className="text-cyan-400">{audioState}</strong>
        </div>
      </div>

      {/* Action Buttons Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={async () => { await seedNormalTelemetry(); setLastUpdate(new Date().toLocaleTimeString()); }}
          className="px-3 py-1.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-500/40 text-xs font-bold flex items-center gap-1.5 transition-colors"
        >
          <CheckCircle className="w-3.5 h-3.5" />
          <span>Load Normal Telemetry</span>
        </button>

        <button
          onClick={async () => { await seedFireHardwareWarning(); setLastUpdate(new Date().toLocaleTimeString()); }}
          className="px-3 py-1.5 rounded-lg bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-500/40 text-xs font-bold flex items-center gap-1.5 transition-colors"
        >
          <Flame className="w-3.5 h-3.5 text-rose-400" />
          <span>Simulate Fire Warning</span>
        </button>

        <button
          onClick={async () => { await seedLandslideHardwareWarning(); setLastUpdate(new Date().toLocaleTimeString()); }}
          className="px-3 py-1.5 rounded-lg bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-500/40 text-xs font-bold flex items-center gap-1.5 transition-colors"
        >
          <Waves className="w-3.5 h-3.5 text-amber-400" />
          <span>Simulate Landslide Warning</span>
        </button>

        <button
          onClick={async () => { await clearHardwareWarning(); setLastUpdate(new Date().toLocaleTimeString()); }}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Clear Warning</span>
        </button>

        <button
          onClick={onOpenSosModal}
          className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-700 hover:to-red-800 text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow-md"
        >
          <Shield className="w-3.5 h-3.5" />
          <span>Trigger Test SOS</span>
        </button>

        <button
          onClick={async () => { await resetAllDemoData(); setLastUpdate(new Date().toLocaleTimeString()); }}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 text-xs font-medium transition-colors"
        >
          Reset Test Database
        </button>

        <button
          onClick={handleToggleSound}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-colors ml-auto"
        >
          {isMuted ? <VolumeX className="w-3.5 h-3.5 text-rose-400" /> : <Volume2 className="w-3.5 h-3.5 text-cyan-400" />}
          <span>{isMuted ? "Sound: Muted" : "Sound: Enabled"}</span>
        </button>

        <button
          onClick={handleTestAudio}
          className="px-2.5 py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-500/30 text-xs font-mono"
        >
          Init Audio
        </button>
      </div>
    </div>
  );
}
