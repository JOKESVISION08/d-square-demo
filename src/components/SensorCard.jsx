import React from 'react';

export default function SensorCard({
  icon: Icon,
  label,
  value,
  unit = "",
  subtext,
  status = "normal", // 'normal' | 'warn' | 'danger'
  colorClass
}) {
  const isDanger = status === "danger";
  const isWarn = status === "warn";

  return (
    <div className={`panel-card p-3.5 relative overflow-hidden transition-all ${
      isDanger
        ? "border-rose-500/60 bg-rose-950/20 shadow-md shadow-rose-950/40"
        : isWarn
        ? "border-amber-500/50 bg-amber-950/20 shadow-md shadow-amber-950/30"
        : "border-slate-800 hover:border-slate-700"
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
          colorClass || (isDanger ? "bg-rose-500/20 text-rose-400" : isWarn ? "bg-amber-500/20 text-amber-400" : "bg-cyan-500/10 text-cyan-400")
        }`}>
          {Icon && <Icon className="w-4 h-4" />}
        </div>
        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-semibold ${
          isDanger
            ? "bg-rose-950 text-rose-300 border border-rose-500/40"
            : isWarn
            ? "bg-amber-950 text-amber-300 border border-amber-500/40"
            : "bg-slate-900 text-slate-400 border border-slate-800"
        }`}>
          {isDanger ? "ALERT" : isWarn ? "ELEVATED" : "NORMAL"}
        </span>
      </div>

      <div className="text-[11px] uppercase font-semibold text-slate-400 tracking-wider">
        {label}
      </div>

      <div className={`text-xl font-bold font-heading mt-1 ${
        isDanger ? "text-rose-400" : isWarn ? "text-amber-400" : "text-white"
      }`}>
        {value} {unit && <span className="text-xs font-normal text-slate-400">{unit}</span>}
      </div>

      {subtext && (
        <div className="text-[10px] text-slate-500 mt-1 truncate">
          {subtext}
        </div>
      )}
    </div>
  );
}
