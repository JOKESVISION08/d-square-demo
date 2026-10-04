import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function TriggerSosButton({ onClick, hasAlert }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-xl text-xs font-bold text-white flex items-center gap-2 transition-all transform hover:scale-[1.02] shadow-lg ${
        hasAlert
          ? "bg-gradient-to-r from-amber-500 via-rose-600 to-red-600 hover:from-amber-600 hover:to-red-700 shadow-rose-600/30 animate-pulse-fast"
          : "bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-700 hover:to-red-800 shadow-rose-600/20"
      }`}
    >
      <ShieldAlert className="w-4 h-4" />
      <span>VERIFY &amp; TRIGGER SOS</span>
    </button>
  );
}
