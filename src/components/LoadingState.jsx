import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingState({ message = "Loading D-SQUARE 2.0 Disaster Surveillance Control..." }) {
  return (
    <div className="min-h-[300px] flex flex-col items-center justify-center p-8 text-center">
      <div className="relative mb-4">
        <div className="w-12 h-12 rounded-full border-4 border-cyan-500/20 border-t-cyan-400 animate-spin"></div>
        <Loader2 className="w-6 h-6 text-cyan-400 absolute inset-0 m-auto animate-pulse" />
      </div>
      <p className="text-xs font-mono text-cyan-400 font-semibold">{message}</p>
      <span className="text-[10px] text-slate-500 mt-1">Connecting to Firebase Realtime Database...</span>
    </div>
  );
}
