import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, ShieldAlert, CloudRain, Thermometer, Wind, PhoneCall, ArrowLeft, LifeBuoy, Sparkles, FileText, AlertTriangle, VolumeX, Volume2, Mic, MicOff, Volume1 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { startContinuousSosAlarm, stopContinuousSosAlarm } from '../utils/audio';
import { speakText, stopSpeaking, isCurrentlySpeaking, startVoiceRecognition } from '../utils/voiceAssistant';

export default function DSquareGptPage({ incidents = [], telemetry }) {
  const activeIncident = incidents.find(i => i.status === "SOS_ACTIVE") || null;
  const isDispatched = activeIncident && (activeIncident.dispatch?.dsquare_gpt === "DISPATCHED" || activeIncident.status === "SOS_ACTIVE");

  const temp = typeof telemetry?.temperature === 'number' ? telemetry.temperature : 28.5;
  const hum = typeof telemetry?.humidity === 'number' ? telemetry.humidity : 54.0;
  const soil = typeof telemetry?.soil_moisture === 'number' ? telemetry.soil_moisture : 42.0;

  const [isAlarmActive, setIsAlarmActive] = useState(false);

  // Voice Assistant States
  const [isListening, setIsListening] = useState(false);
  const [speakingIndex, setSpeakingIndex] = useState(null);
  const [voiceNotice, setVoiceNotice] = useState(null);
  const recognitionRef = useRef(null);

  // Trigger & Control Continuous SOS Alarm Sound on Alert Reception
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
      stopSpeaking();
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
      text: `Hello! I am D-SQUARE GPT, your AI Public Disaster Survival & Evacuation Assistant. Current local conditions: Temperature ${temp}°C, Humidity ${hum}%, Soil Moisture ${soil}%. How can I guide your evacuation or safety plan today?`
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");

  // Handle Speech Readout for any AI message
  const handleReadoutMessage = (index, text) => {
    if (speakingIndex === index) {
      stopSpeaking();
      setSpeakingIndex(null);
    } else {
      setSpeakingIndex(index);
      speakText(
        text,
        () => setSpeakingIndex(null),
        (err) => {
          setSpeakingIndex(null);
          setVoiceNotice("Voice readout notice: " + (err || "Unable to play voice"));
        }
      );
    }
  };

  // Handle Voice Input (Speech-to-Text Microphone)
  const toggleVoiceInput = () => {
    if (isListening) {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
      setIsListening(false);
      return;
    }

    setVoiceNotice(null);
    setIsListening(true);
    recognitionRef.current = startVoiceRecognition({
      onResult: (transcript) => {
        setInputQuery(transcript);
      },
      onError: (err) => {
        setIsListening(false);
        setVoiceNotice(typeof err === 'string' ? err : "Voice recognition stopped.");
      },
      onEnd: () => {
        setIsListening(false);
      }
    });
  };

  // Automatically insert emergency escape guidance into chat when active incident occurs
  useEffect(() => {
    if (activeIncident) {
      const emergencyGuidance = `🚨 CONTINUOUS EMERGENCY GUIDANCE INITIATED:
Official evacuation broadcast for ${activeIncident.location_name}.
1. PACK CRITICAL DOCUMENTS: Place National ID, Passports, Medical Records, Property Deeds into a sealed waterproof pouch.
2. EVACUATE HIGH RISK ZONE: Move perpendicular to hazard trajectory towards NH-58 Relief Shelter.
3. CONNECT TO RESCUE: Tap 'DEPLOY RESCUE MANAGEMENT 🚒' below to signal NDRF & Medical First Responders.`;

      setChatMessages(prev => {
        if (!prev.some(m => m.isEmergencyAutoMsg)) {
          return [{ sender: "ai", text: emergencyGuidance, isEmergencyAutoMsg: true }, ...prev];
        }
        return prev;
      });
    }
  }, [activeIncident]);

  const handleSendMessage = (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    const userMsg = { sender: "user", text: query };
    let aiResponse = "";

    const lower = query.toLowerCase();
    if (lower.includes("fire") || lower.includes("smoke") || lower.includes("heat")) {
      aiResponse = "🔥 WILDFIRE ESCAPE GUIDANCE:\n1. Move perpendicular to wind direction away from dense brush.\n2. Cover nose & mouth with wet cloth.\n3. Gather essential identity and medical documents in a waterproof pouch.\n4. Proceed immediately to District Relief Shelter 04 along NH-58 North.";
    } else if (lower.includes("landslide") || lower.includes("slope") || lower.includes("mud")) {
      aiResponse = "⛰️ LANDSLIDE ESCAPE GUIDANCE:\n1. Move immediately away from slope scarps, gullies, and stream channels.\n2. Seek elevated, hard-bedrock ground.\n3. Secure important identity and medical documents.\n4. Avoid low-lying river beds where debris flows accumulate.";
    } else if (lower.includes("document") || lower.includes("paper") || lower.includes("id")) {
      aiResponse = "📁 IMPORTANT DOCUMENTS ADVISORY:\nPlace National ID, Passport, Medical Prescriptions, Insurance Policies, Property Deeds, and Emergency Cash in a sealed waterproof bag. Keep it inside your primary grab-and-go emergency kit.";
    } else {
      aiResponse = `🛡️ PUBLIC EMERGENCY ADVISORY:\nEvacuation arterial routes are currently open towards District Relief Shelter 04. Follow NDRF wardens on key crossroads. Emergency Helplines: NDRF 1078 | Disaster Helpline 112.`;
    }

    setChatMessages(prev => [...prev, userMsg, { sender: "ai", text: aiResponse }]);
    setInputQuery("");

    // Read AI response out loud using Voice Assistant
    speakText(aiResponse);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">
          🌐 D-SQUARE GPT Standalone Citizen Safety Portal
        </span>
        <span className="text-xs font-mono text-slate-400">Public Emergency Channel</span>
      </div>

      {/* Main Broadcast Panel */}
      <div className="panel-card p-6 border-cyan-500/40 bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/40 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              <Bot className="w-7 h-7" />
            </div>
            <div>
              <h1 className="font-heading font-extrabold text-xl text-white">
                D-SQUARE GPT — Public Disaster Safety Portal
              </h1>
              <p className="text-xs text-slate-400">Standalone Citizen Application — Automatic Alarm, Evacuation AI &amp; Rescue Gateway</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Alarm Status & Silence Button */}
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
                <span>{isAlarmActive ? "SILENCE CONTINUOUS ALARM 🔇" : "UNMUTE SOS BEEP 🔊"}</span>
              </button>
            )}

            {/* High-Visibility Deploy Rescue Management Button */}
            <Link
              to="/rescue-gpt"
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 via-red-600 to-rose-700 hover:from-rose-700 hover:to-red-800 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-rose-600/40 transition-all transform hover:scale-[1.02]"
            >
              <LifeBuoy className="w-4 h-4" />
              <span>DEPLOY RESCUE MANAGEMENT 🚒</span>
            </Link>
          </div>
        </div>

        {/* ACTIVE DISPATCH BEEP & ALERT INSTRUCTION CARD */}
        {activeIncident && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-950/80 border border-rose-500/80 text-rose-100 shadow-xl space-y-3 animate-fadeIn">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-heading font-bold text-sm text-white uppercase">
                <AlertTriangle className="w-5 h-5 text-rose-400 animate-bounce" />
                <span>🚨 CONTINUOUS SOS ALERT RECEIVED: {(activeIncident.disaster_type || "DISASTER").toUpperCase()} EMERGENCY</span>
              </div>
              <span className="text-xs font-mono bg-rose-900/60 px-2.5 py-1 rounded text-rose-200 border border-rose-500/30">
                INCIDENT: {activeIncident.incident_id}
              </span>
            </div>

            <p className="text-xs text-rose-200/90 leading-relaxed">
              Official verified emergency broadcast received for <strong>{activeIncident.location_name}</strong>. Evacuation &amp; safety guidance activated automatically.
            </p>

            {/* IMPORTANT DOCUMENTS ADVISORY BOX */}
            <div className="p-3.5 rounded-xl bg-slate-950/90 border border-amber-500/50 text-amber-200 text-xs font-mono flex items-start gap-3">
              <FileText className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-amber-300 block text-xs mb-1">📁 CRITICAL PERSONAL DOCUMENTS ADVISORY:</strong>
                Before evacuating your premises, place all essential identity &amp; medical documents (National ID Cards, Passports, Medical Records, Property Deeds, Bank Cards) into a sealed waterproof pouch in your emergency kit.
              </div>
            </div>
          </div>
        )}

        {/* Live Weather Metrics Overview */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4 font-mono text-xs">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <div className="text-slate-400 text-[10px] uppercase flex items-center gap-1">
              <Thermometer className="w-3.5 h-3.5 text-amber-400" /> Temperature
            </div>
            <div className="text-lg font-bold text-slate-100 mt-1">{temp.toFixed(1)}°C</div>
            <div className="text-[10px] text-emerald-400">Normal Range</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <div className="text-slate-400 text-[10px] uppercase flex items-center gap-1">
              <CloudRain className="w-3.5 h-3.5 text-blue-400" /> Humidity
            </div>
            <div className="text-lg font-bold text-slate-100 mt-1">{hum.toFixed(1)}%</div>
            <div className="text-[10px] text-slate-500">Relative Saturation</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <div className="text-slate-400 text-[10px] uppercase flex items-center gap-1">
              <Wind className="w-3.5 h-3.5 text-cyan-400" /> Soil Moisture
            </div>
            <div className="text-lg font-bold text-slate-100 mt-1">{soil.toFixed(1)}%</div>
            <div className="text-[10px] text-cyan-400">Ground ADC Stream</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <div className="text-slate-400 text-[10px] uppercase flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" /> Disaster Safety Index
            </div>
            <div className="text-lg font-bold text-emerald-400 mt-1">SAFE (0.95)</div>
            <div className="text-[10px] text-slate-500">Ground Sensor Verified</div>
          </div>
        </div>

        {/* Interactive Conversational Chat Window */}
        <div className="space-y-4">
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-heading flex items-center gap-1.5">
            <Bot className="w-4 h-4" /> D-SQUARE GPT Conversational AI Guidance Window
          </div>

          {/* Voice Notice Banner */}
          {voiceNotice && (
            <div className="p-2.5 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-cyan-300 text-xs font-mono flex items-center justify-between">
              <span>🗣️ {voiceNotice}</span>
              <button onClick={() => setVoiceNotice(null)} className="text-slate-400 hover:text-white font-bold ml-2">✕</button>
            </div>
          )}

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 max-h-80 overflow-y-auto font-sans text-xs">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-xl max-w-2xl leading-relaxed whitespace-pre-line relative group ${
                  msg.sender === "user"
                    ? "bg-cyan-950/80 border border-cyan-500/40 text-cyan-100 ml-auto font-mono"
                    : msg.isEmergencyAutoMsg
                    ? "bg-rose-950/90 border border-rose-500/60 text-rose-100 font-mono shadow-md"
                    : "bg-slate-900 border border-slate-800 text-slate-200"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <strong className="block text-[10px] font-mono text-slate-400">
                    {msg.sender === "user" ? "YOU (CITIZEN)" : "D-SQUARE GPT (AI DISASTER ASSISTANT)"}
                  </strong>
                  {msg.sender !== "user" && (
                    <button
                      onClick={() => handleReadoutMessage(idx, msg.text)}
                      title={speakingIndex === idx ? "Stop Voice Readout" : "Listen via Voice Assistant"}
                      className={`px-2 py-0.5 rounded text-[10px] font-mono flex items-center gap-1 transition-colors cursor-pointer ${
                        speakingIndex === idx
                          ? "bg-cyan-500 text-slate-950 font-bold animate-pulse"
                          : "bg-slate-800 text-cyan-300 hover:bg-slate-700"
                      }`}
                    >
                      {speakingIndex === idx ? (
                        <>
                          <Volume2 className="w-3 h-3 text-slate-950 animate-bounce" />
                          <span>Speaking...</span>
                        </>
                      ) : (
                        <>
                          <Volume1 className="w-3 h-3 text-cyan-400" />
                          <span>Read Out 🔊</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
                {msg.text}
              </div>
            ))}
          </div>

          {/* Quick Prompt Chips */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 text-[11px] font-mono">Quick Survival Prompts:</span>
            <button
              onClick={() => handleSendMessage("How do I safely evacuate from a wildfire?")}
              className="px-2.5 py-1 rounded-lg bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-500/40 font-mono text-[11px] cursor-pointer"
            >
              🔥 Wildfire Evacuation
            </button>
            <button
              onClick={() => handleSendMessage("What should I do if a landslide threatens my area?")}
              className="px-2.5 py-1 rounded-lg bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-500/40 font-mono text-[11px] cursor-pointer"
            >
              ⛰️ Landslide Escape
            </button>
            <button
              onClick={() => handleSendMessage("Which important documents should I pack before evacuating?")}
              className="px-2.5 py-1 rounded-lg bg-blue-950/80 hover:bg-blue-900 text-blue-300 border border-blue-500/40 font-mono text-[11px] cursor-pointer"
            >
              📁 Documents Checklist
            </button>
          </div>

          {/* Chat Input Bar with Voice Input (Mic) */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
            className="flex items-center gap-2"
          >
            {/* Mic Voice Input Button */}
            <button
              type="button"
              onClick={toggleVoiceInput}
              title={isListening ? "Listening... Click to stop mic" : "Click to speak with Voice Assistant"}
              className={`p-2.5 rounded-xl border flex items-center justify-center transition-all cursor-pointer ${
                isListening
                  ? "bg-rose-600 text-white border-rose-400 animate-pulse shadow-lg shadow-rose-600/50"
                  : "bg-slate-900 text-cyan-400 border-cyan-500/40 hover:bg-cyan-500/20"
              }`}
            >
              {isListening ? <MicOff className="w-5 h-5 text-white animate-spin" /> : <Mic className="w-5 h-5 text-cyan-400" />}
            </button>

            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder={isListening ? "🎙️ Listening to your voice... Speak now!" : "Ask D-SQUARE GPT or tap mic to speak..."}
              className={`flex-1 bg-slate-950 border px-4 py-2.5 rounded-xl text-xs text-slate-100 focus:outline-none transition-colors ${
                isListening ? "border-rose-500 text-rose-200" : "border-slate-800 focus:border-cyan-500"
              }`}
            />

            <button
              type="submit"
              className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <Send className="w-4 h-4" />
              <span>Ask AI</span>
            </button>
          </form>
        </div>

        {/* Footer Actions & Helpline */}
        <div className="mt-6 p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <PhoneCall className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Emergency Helplines: <strong className="text-emerald-400">NDRF: 1078 | Disaster Response: 112</strong></span>
          </div>

          <Link
            to="/rescue-gpt"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-700 hover:to-red-800 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-rose-600/30 transition-all font-mono"
          >
            <LifeBuoy className="w-4 h-4" />
            <span>DEPLOY RESCUE MANAGEMENT 🚒</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
