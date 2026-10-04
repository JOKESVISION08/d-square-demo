import React, { useState } from 'react';
import SatelliteUploadPanel from '../components/SatelliteUploadPanel';
import ImageComparePanel from '../components/ImageComparePanel';
import LiveDisasterMap from '../components/LiveDisasterMap';
import { Brain, Info, AlertTriangle } from 'lucide-react';

export default function MLFusionPage() {
  const [pastPreview, setPastPreview] = useState(null);
  const [currPreview, setCurrPreview] = useState(null);
  const [disasterType, setDisasterType] = useState("LANDSLIDE");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [customPolygon, setCustomPolygon] = useState(null);

  const handleFileSelect = (type, file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      if (type === 'past') setPastPreview(e.target.result);
      else setCurrPreview(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleRunPrediction = () => {
    setIsAnalyzing(true);
    setTimeout(() => {
      const mockResult = {
        disaster_type: disasterType,
        confidence: 0.96,
        affected_area_km2: 0.034,
        affected_pixels_count: 84,
        polygon_boundary: [
          [30.0668, 79.0193],
          [30.0700, 79.0250],
          [30.0650, 79.0280],
          [30.0600, 79.0200]
        ]
      };
      setAnalysisResult(mockResult);
      setCustomPolygon(mockResult.polygon_boundary);
      setIsAnalyzing(false);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-4 rounded-xl bg-slate-900 border border-cyan-500/30">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-heading font-extrabold text-lg text-white tracking-wide">
              Multi-Modal AI Fusion Center &amp; Satellite Pixel Change Analyzer
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              PyTorch U-Net Change Detection (PAST vs CURRENT Image Comparison &amp; GeoJSON Polygon Generator)
            </p>
          </div>
        </div>
      </div>

      {/* Prototype Notice Disclaimer */}
      <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-200">PROTOTYPE NOTICE:</strong> This frontend interface demonstrates satellite change detection, image preview comparisons, and GeoJSON polygon generation. Real production ML inference requiring GPU compute should run in Cloud/Netlify Functions or dedicated ML backend nodes.
        </div>
      </div>

      {/* Upload and Compare Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SatelliteUploadPanel
          pastPreview={pastPreview}
          currPreview={currPreview}
          onFileSelect={handleFileSelect}
          onRunPrediction={handleRunPrediction}
          isAnalyzing={isAnalyzing}
          disasterType={disasterType}
          setDisasterType={setDisasterType}
        />

        <ImageComparePanel
          pastPreview={pastPreview}
          currPreview={currPreview}
          analysisResult={analysisResult}
        />
      </div>

      {/* Interactive GeoJSON Change Map */}
      <LiveDisasterMap
        customPolygon={customPolygon}
        height="400px"
      />
    </div>
  );
}
