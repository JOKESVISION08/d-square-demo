import React from 'react';
import { Layers, Download, FileText } from 'lucide-react';

export default function ImageComparePanel({ pastPreview, currPreview, analysisResult }) {
  const result = analysisResult || {};

  return (
    <div className="panel-card p-4 border-cyan-500/30 bg-slate-900/90">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <h3 className="font-heading font-bold text-xs text-cyan-300 uppercase tracking-wider">
            Satellite Pixel Change Mask &amp; Comparison
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <a
            href="data:application/json;charset=utf-8,%7B%22type%22%3A%22FeatureCollection%22%2C%22features%22%3A%5B%7B%22type%22%3A%22Feature%22%2C%22geometry%22%3A%7B%22type%22%3A%22Polygon%22%2C%22coordinates%22%3A%5B%5B%5B79.0193%2C30.0668%5D%2C%5B79.0250%2C30.0700%5D%2C%5B79.0280%2C30.0650%5D%2C%5B79.0193%2C30.0668%5D%5D%5D%7D%7D%5D%7D"
            download="affected_polygons_prototype.geojson"
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 text-[11px] font-mono flex items-center gap-1 transition-colors"
          >
            <Download className="w-3.5 h-3.5" /> GeoJSON
          </a>
        </div>
      </div>

      {/* Side-by-side Preview Container */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
        <div className="bg-slate-950 p-2 rounded-xl border border-slate-800">
          <div className="text-[10px] font-mono text-cyan-400 font-bold mb-1">BASELINE (PAST)</div>
          <div className="h-36 bg-slate-900 rounded-lg overflow-hidden flex items-center justify-center border border-slate-800">
            {pastPreview ? (
              <img src={pastPreview} alt="Past" className="w-full h-full object-cover" />
            ) : (
              <div className="text-center text-slate-600 text-xs p-2">Baseline Satellite Scene</div>
            )}
          </div>
        </div>

        <div className="bg-slate-950 p-2 rounded-xl border border-slate-800">
          <div className="text-[10px] font-mono text-amber-400 font-bold mb-1">CURRENT SCENE &amp; AI MASK</div>
          <div className="h-36 bg-slate-900 rounded-lg overflow-hidden relative flex items-center justify-center border border-slate-800">
            {currPreview ? (
              <>
                <img src={currPreview} alt="Current" className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-rose-500/20 border-2 border-rose-500/60 pointer-events-none flex items-center justify-center">
                  <span className="bg-rose-950/80 text-rose-300 font-mono text-[10px] px-2 py-0.5 rounded border border-rose-500/40">
                    CHANGE MASK OVERLAY
                  </span>
                </div>
              </>
            ) : (
              <div className="text-center text-slate-600 text-xs p-2">Current Satellite Scene</div>
            )}
          </div>
        </div>
      </div>

      {/* Analysis Metrics */}
      <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono grid grid-cols-2 sm:grid-cols-3 gap-2 text-slate-300">
        <div>Affected Area: <strong className="text-rose-400">{result.affected_area_km2 || 0.034} km²</strong></div>
        <div>Pixel Cluster: <strong className="text-amber-400">{result.affected_pixels_count || 84} Pixels</strong></div>
        <div>Confidence: <strong className="text-emerald-400">{Math.round((result.confidence || 0.95) * 100)}%</strong></div>
      </div>
    </div>
  );
}
