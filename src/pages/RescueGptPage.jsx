import React, { useState, useEffect } from 'react';
import { Truck, ArrowLeft, Bot, Send, ShieldAlert, MapPin, Activity, Flame, Droplets, Compass, CheckSquare, LifeBuoy, Volume2, VolumeX } from 'lucide-react';
import { Link } from 'react-router-dom';
import RescueGptDispatchCard from '../components/RescueGptDispatchCard';
import LiveDisasterMap from '../components/LiveDisasterMap';
import { startContinuousSosAlarm, stopContinuousSosAlarm } from '../utils/audio';

export default function RescueGptPage({ incidents = [], telemetry, activeAlert }) {
  const activeIncident = incidents.find(i => i.status === "SOS_ACTIVE") || incidents[0] || {
    incident_id: "DSQ-SOS-2026-ACTIVE",
    disaster_type: "Flash Flood & Slope Landslide",
    severity: "CRITICAL",
    location_name: "Uttarakhand Slope Sector 4",
    latitude: 30.0668,
    longitude: 79.0193,
    status: "SOS_ACTIVE",
    rescue_status: "Team Assigned",
    verified_by: "operator@dsquare.gov.in",
    timestamp: new Date().toISOString(),
    sensor_readings: {
      displacement: "48.2 mm",
      rain_rate: "112 mm/hr",
      vibration: "7.8 Hz"
    }
  };

  const isDispatched = activeIncident && (activeIncident.dispatch?.rescue_gpt === "DISPATCHED" || activeIncident.status === "SOS_ACTIVE");
  const [isAlarmActive, setIsAlarmActive] = useState(false);

  // Trigger & Control Continuous SOS Alert Sound from sossound folder
  useEffect(() => {
    if (isDispatched) {
      startContinuousSosAlarm();
      setIsAlarmActive(true);
    } else {
      stopContinuousSosAlarm();
      setIsAlarmActive(false);
    }

    return () => {
      stopContinuousSosAlarm();
    };
  }, [isDispatched]);

  const toggleAlarmSound = () => {
    if (isAlarmActive) {
      stopContinuousSosAlarm();
      setIsAlarmActive(false);
    } else {
      startContinuousSosAlarm();
      setIsAlarmActive(true);
    }
  };

  const [chatMessages, setChatMessages] = useState([
    {
      sender: "ai",
      text: "🚨 Rescue GPT First Responder Tactical AI active. Operational sector: Uttarakhand Slope 4 (30.0668°N, 79.0193°E). Ask me for tactical safety parameter thresholds, structural collapse stand-off distances, flood water current limits, or hazmat PPE guidelines."
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");

  const handleSendMessage = (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    const userMsg = { sender: "user", text: query };
    let aiResponse = "";

    const lower = query.toLowerCase();
    if (lower.includes("slope") || lower.includes("landslide") || lower.includes("stability")) {
      aiResponse = "🛡️ SLOPE SAFETY PARAMETERS:\n• Factor of Safety (FS): FS < 1.0 is CRITICAL (Imminent failure). FS > 1.3 required for safe responder entry.\n• Displacement Velocity: > 15 mm/hr indicates rapid mass movement.\n• Action: Maintain 150m standoff perimeter north of scarp. Do not park heavy rescue vehicles on unanchored slope lips.";
    } else if (lower.includes("flood") || lower.includes("water") || lower.includes("velocity") || lower.includes("current")) {
      aiResponse = "🌊 FLOOD WATER SAFETY PARAMETERS:\n• Max Wade Depth: 0.5m for unassisted responders.\n• Current Velocity Limit: > 1.5 m/s requires tethered powerboats & Type V PFDs.\n• Debris Flow Hazard: High turbidity & floating debris requires structural safety cables before boat deployment.";
    } else if (lower.includes("fire") || lower.includes("thermal") || lower.includes("collapse") || lower.includes("radius")) {
      aiResponse = "🔥 THERMAL & COLLAPSE SAFETY PARAMETERS:\n• Collapse Standoff Zone: 1.5 × Height of damaged structure.\n• Thermal Radiation Standoff: 50m minimum for unshielded responders.\n• Structural Integrity: If tilt sensor exceeds 3.5°, evacuate internal search crews immediately.";
    } else if (lower.includes("ppe") || lower.includes("scba") || lower.includes("hazmat") || lower.includes("gas")) {
      aiResponse = "🧯 RESPONDER PPE & HAZMAT PROTOCOLS:\n• SCBA Requirement: Mandatory when CO > 50 ppm or AQI > 300.\n• Structural Collapse Gear: Helmet with headlamp, Kevlar gloves, steel-toe boots, and personal locator beacon (PLB).\n• Chemical Safety: Level A/B suits required if toxic industrial gas sensors trigger.";
    } else {
      aiResponse = `📋 TACTICAL ADVISORY: Incident ${activeIncident.incident_id} at ${activeIncident.location_name}. All responder teams must maintain VHF Ch. 16 communications. NDRF Team 04 & 2 ALS Ambulances deployed on site.`;
    }

    setChatMessages(prev => [...prev, userMsg, { sender: "ai", text: aiResponse }]);
    setInputQuery("");
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-rose-400 font-bold uppercase tracking-wider">
          🚒 Rescue GPT Standalone First Responder Command Portal
        </span>
        <span className="text-xs font-mono text-slate-400">Restricted Tactical Channel</span>
      </div>

      {/* Main Container */}
      <div className="panel-card p-6 border-rose-500/40 bg-gradient-to-br from-slate-900 via-slate-900 to-rose-950/30 shadow-xl space-y-6">
        {/* Banner Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-rose-500/20 text-rose-400 border border-rose-500/30">
              <Truck className="w-7 h-7" />
            </div>
            <div>
              <h1 className="font-heading font-extrabold text-xl text-white">
                Rescue GPT — First Responder Tactical Safety &amp; Command AI
              </h1>
              <p className="text-xs text-slate-400">Tactical Safety Parameters, Real-Time Disaster Risk Map &amp; Resource Dispatch</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {isDispatched && (
              <button
                onClick={toggleAlarmSound}
                className={`px-3 py-1.5 rounded-xl font-mono text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                  isAlarmActive
                    ? "bg-rose-950 text-rose-300 border border-rose-500/60 animate-pulse hover:bg-rose-900"
                    : "bg-slate-800 text-slate-400 border border-slate-700 hover:text-slate-200"
                }`}
              >
                {isAlarmActive ? <Volume2 className="w-4 h-4 text-rose-400" /> : <VolumeX className="w-4 h-4 text-slate-400" />}
                <span>{isAlarmActive ? "SILENCE SOS ALARM 🔇" : "UNMUTE SOS ALARM 🔊"}</span>
              </button>
            )}
            <span className="text-xs font-mono bg-rose-950 text-rose-300 border border-rose-500/40 px-3 py-1 rounded-full font-bold animate-pulse">
              🚨 TACTICAL COMMAND ACTIVE
            </span>
          </div>
        </div>

        {/* SECTION 1: DISASTER RISK MAP & TELEMETRY */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-heading font-bold text-sm text-rose-300 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-rose-400" />
              <span>LIVE DISASTER RISK MAP &amp; IMPACT PERIMETER</span>
            </h2>
            <span className="text-[11px] font-mono text-slate-400">
              Uttarakhand Sector 4 (30.0668°N, 79.0193°E)
            </span>
          </div>

          {/* Disaster Risk Map Component */}
          <LiveDisasterMap
            telemetry={telemetry}
            activeAlert={activeAlert}
            activeIncident={activeIncident}
            height="340px"
          />

          {/* Risk Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400 text-[10px] uppercase flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-rose-400" /> Slope Safety Index (FS)
              </div>
              <div className="text-lg font-bold text-rose-400 mt-1">0.82 (UNSAFE)</div>
              <div className="text-[10px] text-rose-300">Standoff Required</div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400 text-[10px] uppercase flex items-center gap-1">
                <Droplets className="w-3.5 h-3.5 text-blue-400" /> Flood Velocity
              </div>
              <div className="text-lg font-bold text-amber-400 mt-1">1.8 m/s</div>
              <div className="text-[10px] text-amber-300">Powerboats Required</div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400 text-[10px] uppercase flex items-center gap-1">
                <Flame className="w-3.5 h-3.5 text-amber-400" /> Collapse Standoff
              </div>
              <div className="text-lg font-bold text-slate-100 mt-1">45 Meters</div>
              <div className="text-[10px] text-slate-400">1.5× Height Margin</div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400 text-[10px] uppercase flex items-center gap-1">
                <Compass className="w-3.5 h-3.5 text-cyan-400" /> Sector Risk Rating
              </div>
              <div className="text-lg font-bold text-rose-500 mt-1">HIGH (LEVEL 4)</div>
              <div className="text-[10px] text-rose-400">Active Evacuation</div>
            </div>
          </div>
        </div>

        {/* SECTION 2: CONVERSATIONAL AI ABOUT SAFETY PARAMETERS */}
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-rose-400 uppercase tracking-wider font-heading flex items-center gap-1.5">
              <Bot className="w-4 h-4" /> Rescue GPT Conversational AI — Responder Safety Assistant
            </div>
            <span className="text-[10px] font-mono text-slate-400">Tactical Knowledge Base v2.0</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 max-h-80 overflow-y-auto font-sans text-xs">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-xl max-w-2xl leading-relaxed whitespace-pre-line ${
                  msg.sender === "user"
                    ? "bg-rose-950/80 border border-rose-500/40 text-rose-100 ml-auto font-mono"
                    : "bg-slate-900 border border-slate-800 text-slate-200"
                }`}
              >
                <strong className="block text-[10px] font-mono text-slate-400 mb-1">
                  {msg.sender === "user" ? "FIRST RESPONDER COMMAND" : "RESCUE GPT (SAFETY PARAMETER AI)"}
                </strong>
                {msg.text}
              </div>
            ))}
          </div>

          {/* Quick Safety Parameter Prompts */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 text-[11px] font-mono">Quick Safety Parameter Queries:</span>
            <button
              onClick={() => handleSendMessage("What are the slope stability safety parameters for landslides?")}
              className="px-2.5 py-1 rounded-lg bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-500/40 font-mono text-[11px] cursor-pointer"
            >
              🛡️ Slope Safety Thresholds
            </button>
            <button
              onClick={() => handleSendMessage("What is the maximum safe water current velocity for flood rescue?")}
              className="px-2.5 py-1 rounded-lg bg-blue-950/80 hover:bg-blue-900 text-blue-300 border border-blue-500/40 font-mono text-[11px] cursor-pointer"
            >
              🌊 Flood Velocity Limits
            </button>
            <button
              onClick={() => handleSendMessage("What is the safe collapse standoff distance for burning buildings?")}
              className="px-2.5 py-1 rounded-lg bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-500/40 font-mono text-[11px] cursor-pointer"
            >
              🔥 Structural Standoff Radius
            </button>
            <button
              onClick={() => handleSendMessage("When is SCBA required for responders during hazmat or smoke?")}
              className="px-2.5 py-1 rounded-lg bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-500/40 font-mono text-[11px] cursor-pointer"
            >
              🧯 SCBA & PPE Rules
            </button>
          </div>

          {/* Chat Input Bar */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask Rescue GPT about safety parameters, standoff distances, or PPE requirements..."
              className="flex-1 bg-slate-950 border border-slate-800 px-4 py-2.5 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
            />
            <button
              type="submit"
              className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-md shadow-rose-600/30"
            >
              <Send className="w-4 h-4" />
              <span>Query AI</span>
            </button>
          </form>
        </div>

        {/* SECTION 3: TACTICAL DISPATCH FEED CARD */}
        <div className="pt-4 border-t border-slate-800">
          <RescueGptDispatchCard incident={activeIncident} isDispatched={true} />
        </div>
      </div>
    </div>
  );
}
