import React from 'react';
import { Wifi, WifiOff, Database } from 'lucide-react';

export default function ConnectionStatus({ status = "online", label }) {
  const isOnline = status === "online";
  const isCached = status === "cached";
  const isConnecting = status === "connecting";

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
        isOnline
          ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
          : isCached
          ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
          : isConnecting
          ? "bg-cyan-500/15 text-cyan-400 border-cyan-500/30 animate-pulse"
          : "bg-rose-500/15 text-rose-400 border-rose-500/30"
      }`}
    >
      <span className="relative flex h-2 w-2">
        <span
          className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
            isOnline ? "bg-emerald-400" : isCached ? "bg-amber-400" : "bg-rose-400"
          }`}
        ></span>
        <span
          className={`relative inline-flex rounded-full h-2 w-2 ${
            isOnline ? "bg-emerald-500" : isCached ? "bg-amber-500" : "bg-rose-500"
          }`}
        ></span>
      </span>
      <span>{label || (isOnline ? "FIREBASE CONNECTED" : isCached ? "CACHED DATA" : isConnecting ? "CONNECTING..." : "OFFLINE")}</span>
    </div>
  );
}
