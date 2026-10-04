import React from 'react';
import { Upload, FileImage, Sparkles } from 'lucide-react';

export default function SatelliteUploadPanel({
  pastPreview,
  currPreview,
  onFileSelect,
  onRunPrediction,
  isAnalyzing,
  disasterType,
  setDisasterType
}) {
  return (
    <div className="panel-card p-4 border-cyan-500/30 bg-slate-900/90">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Upload className="w-4 h-4 text-cyan-400" />
          <h3 className="font-heading font-bold text-xs text-cyan-300 uppercase tracking-wider">
            Satellite Data Upload Space (PAST vs CURRENT)
          </h3>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">
          U-Net 10m-30m Prototype
        </span>
      </div>

      {/* Drag & Drop Upload Zones */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
        {/* PAST Image Upload */}
        <div
          onClick={() => document.getElementById("past-input").click()}
          className="border-2 border-dashed border-cyan-500/40 hover:border-cyan-400 rounded-xl p-3 text-center bg-slate-950/70 cursor-pointer transition-colors"
        >
          <input
            type="file"
            id="past-input"
            className="hidden"
            accept="image/*,.tif,.tiff"
            onChange={(e) => e.target.files[0] && onFileSelect('past', e.target.files[0])}
          />
          {pastPreview ? (
            <img src={pastPreview} alt="PAST Satellite" className="h-24 mx-auto object-cover rounded-lg border border-slate-700" />
          ) : (
            <div className="py-2">
              <FileImage className="w-7 h-7 mx-auto text-cyan-400 mb-1" />
              <div className="text-xs font-bold text-slate-200">PAST Scene</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Drop baseline scene (.tif, .png)</div>
            </div>
          )}
        </div>

        {/* CURRENT Image Upload */}
        <div
          onClick={() => document.getElementById("curr-input").click()}
          className="border-2 border-dashed border-amber-500/40 hover:border-amber-400 rounded-xl p-3 text-center bg-slate-950/70 cursor-pointer transition-colors"
        >
          <input
            type="file"
            id="curr-input"
            className="hidden"
            accept="image/*,.tif,.tiff"
            onChange={(e) => e.target.files[0] && onFileSelect('curr', e.target.files[0])}
          />
          {currPreview ? (
            <img src={currPreview} alt="CURRENT Satellite" className="h-24 mx-auto object-cover rounded-lg border border-slate-700" />
          ) : (
            <div className="py-2">
              <FileImage className="w-7 h-7 mx-auto text-amber-400 mb-1" />
              <div className="text-xs font-bold text-slate-200">CURRENT Scene</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Drop current scene (.tif, .png)</div>
            </div>
          )}
        </div>
      </div>

      {/* Controls & Trigger */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-400 uppercase shrink-0">Disaster Target:</label>
          <select
            value={disasterType}
            onChange={(e) => setDisasterType(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 font-semibold focus:outline-none"
          >
            <option value="LANDSLIDE">⛰️ LANDSLIDE SCARP</option>
            <option value="FIRE">🔥 WILDFIRE BURN</option>
            <option value="FLOOD">🌊 FLOOD INUNDATION</option>
            <option value="EARTHQUAKE">🌋 EARTHQUAKE DAMAGE</option>
          </select>
        </div>

        <button
          onClick={onRunPrediction}
          disabled={isAnalyzing}
          className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-600 hover:to-indigo-700 text-slate-950 font-extrabold text-xs shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 transition-all"
        >
          <Sparkles className="w-4 h-4" />
          <span>{isAnalyzing ? "RUNNING U-NET AI ANALYSIS..." : "RUN AUTOMATIC AI DISASTER PREDICTION"}</span>
        </button>
      </div>
    </div>
  );
}
