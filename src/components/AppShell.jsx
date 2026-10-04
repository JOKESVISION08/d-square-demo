import React from 'react';
import Header from './Header';

export default function AppShell({
  children,
  connectionStatus,
  currentNode,
  onSelectNode,
  onOpenSosModal,
  hasActiveAlert,
  user
}) {
  return (
    <div className="min-h-screen flex flex-col bg-[#0b1329] text-slate-100">
      <Header
        connectionStatus={connectionStatus}
        currentNode={currentNode}
        onSelectNode={onSelectNode}
        onOpenSosModal={onOpenSosModal}
        hasActiveAlert={hasActiveAlert}
        user={user}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6">
        {children}
      </main>

      <footer className="border-t border-slate-800 bg-slate-950/80 px-4 py-3 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            D-SQUARE 2.0 — Standalone Disaster Safety &amp; Emergency Alert System (Netlify + Firebase RTDB Edition)
          </div>
          <div className="text-[10px] text-slate-600">
            Operational Lead Sector: Uttarakhand Slope 4 (30.0668°N, 79.0193°E)
          </div>
        </div>
      </footer>
    </div>
  );
}
