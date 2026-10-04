import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

export default function ErrorState({ title, message, onRetry }) {
  return (
    <div className="panel-card p-6 border-rose-500/40 bg-rose-950/20 text-center my-6">
      <AlertOctagon className="w-10 h-10 text-rose-400 mx-auto mb-3 animate-pulse" />
      <h3 className="font-heading font-bold text-base text-rose-300">
        {title || "Application State Notice"}
      </h3>
      <p className="text-xs text-rose-200/80 mt-1 max-w-md mx-auto">
        {message || "Unable to connect to Realtime Database or permission denied. Please verify configuration."}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 inline-flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Connection</span>
        </button>
      )}
    </div>
  );
}
