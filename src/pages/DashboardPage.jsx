import React, { useState } from 'react';
import SystemHealthBanner from '../components/SystemHealthBanner';
import HardwareWarningBanner from '../components/HardwareWarningBanner';
import HardwareAlertDetails from '../components/HardwareAlertDetails';
import NisarSarTelemetryPanel from '../components/NisarSarTelemetryPanel';
import MobileCameraPanel from '../components/MobileCameraPanel';
import SensorGrid from '../components/SensorGrid';
import LiveDisasterMap from '../components/LiveDisasterMap';
import SOSDispatchPanel from '../components/SOSDispatchPanel';
import IncidentHistoryTable from '../components/IncidentHistoryTable';
import AlertHistoryTable from '../components/AlertHistoryTable';
import ConnectionStatusPanel from '../components/ConnectionStatusPanel';
import SatelliteUploadPanel from '../components/SatelliteUploadPanel';
import ImageComparePanel from '../components/ImageComparePanel';
import { Brain } from 'lucide-react';

export default function DashboardPage({
  telemetry,
  activeAlert,
  incidents = [],
  alertHistory = [],
  currentNode,
  onOpenSosModal,
  satelliteData
}) {
  const latestVerifiedIncident = incidents.find(i => i.status === "SOS_ACTIVE") || null;

  // ML Fusion Engine State integrated directly into PC Dashboard
  const [pastPreview, setPastPreview] = useState(null);
  const [currPreview, setCurrPreview] = useState(null);
  const [disasterType, setDisasterType] = useState("LANDSLIDE");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [mlPolygon, setMlPolygon] = useState(null);

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
      setMlPolygon(mockResult.polygon_boundary);
      setIsAnalyzing(false);
    }, 1200);
  };

  // Combine ML Fusion Polygon and Satellite Adapter Polygon
  const activePolygon = mlPolygon || satelliteData?.polygon_boundary || null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* 1. Top System Health Banner (Clean operational status - No default alerts before real detection) */}
      <SystemHealthBanner
        telemetry={telemetry}
        activeAlert={activeAlert}
        activeIncident={latestVerifiedIncident}
        nodeName={currentNode}
      />

      {/* 2. Silent Hardware Warning Banner (Active ONLY when real hardware alert detected) */}
      <HardwareWarningBanner
        alert={activeAlert}
        onOpenSosModal={onOpenSosModal}
      />

      {/* 3. Integrated Satellite & Mobile Sentinel Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <NisarSarTelemetryPanel telemetry={telemetry} satelliteData={satelliteData} />
        <MobileCameraPanel />
      </div>

      {/* 4. Combined Multi-Modal AI Fusion Model Engine (Satellite Image Compare & Pixel Change Analyzer) */}
      <div className="panel-card p-5 bg-slate-900/90 border-cyan-500/30 space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
          <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-heading font-extrabold text-sm text-cyan-300 uppercase tracking-wide">
              Multi-Modal AI Fusion Engine &amp; Satellite Pixel Change Analyzer
            </h3>
            <p className="text-[11px] text-slate-400">
              PyTorch U-Net Satellite Image Comparison &amp; Change Polygon Boundary Generator
            </p>
          </div>
        </div>

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
      </div>

      {/* 5. Live Ground Telemetry Sensor Cards Grid */}
      <SensorGrid telemetry={telemetry} />

      {/* 6. Unified GIS Map & Evidence / Connection Status */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8">
          <LiveDisasterMap
            telemetry={telemetry}
            activeAlert={activeAlert}
            activeIncident={latestVerifiedIncident}
            customPolygon={activePolygon}
            height="440px"
          />
        </div>

        <div className="lg:col-span-4 space-y-4">
          <HardwareAlertDetails alert={activeAlert} />
          <ConnectionStatusPanel telemetry={telemetry} satelliteData={satelliteData} />
        </div>
      </div>

      {/* 7. Parallel Multi-Agent GPT Dispatch Feeds */}
      <SOSDispatchPanel activeIncident={latestVerifiedIncident} />

      {/* 8. Incident & Alert Audit Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <IncidentHistoryTable incidents={incidents} />
        <AlertHistoryTable alertHistory={alertHistory} />
      </div>
    </div>
  );
}
