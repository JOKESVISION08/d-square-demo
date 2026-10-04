import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Radio, Brain, Volume2, VolumeX, LogOut, ShieldAlert, Satellite } from 'lucide-react';
import ConnectionStatus from './ConnectionStatus';
import NodeSelector from './NodeSelector';
import { getAudioMuted, setAudioMuted } from '../utils/audio';
import { logoutUser } from '../firebase/auth';

export default function Header({
  connectionStatus,
  currentNode,
  onSelectNode,
  user
}) {
  const [isMuted, setIsMutedState] = useState(getAudioMuted());
  const [liveClock, setLiveClock] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const isStandalonePortal = location.pathname === '/dsquare-gpt' || location.pathname === '/rescue-gpt' || location.pathname === '/mobile-nisar';

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setLiveClock(now.toLocaleTimeString('en-US', { timeZone: 'Asia/Kolkata', hour12: false }));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleToggleSound = () => {
    const nextMute = !isMuted;
    setAudioMuted(nextMute);
    setIsMutedState(nextMute);
  };

  const handleLogout = async () => {
    await logoutUser();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 px-4 py-2.5 shadow-lg">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Left: Brand & Navigation */}
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20 group-hover:scale-105 transition-transform">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <span className="font-heading font-extrabold text-lg bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-300 bg-clip-text text-transparent">
                D-SQUARE 2.0
              </span>
              {!isStandalonePortal && (
                <span className="hidden sm:inline-block ml-2 text-xs text-slate-400 font-medium">
                  Disaster Emergency Response System
                </span>
              )}
            </div>
          </Link>

          {/* Clock */}
          <div className="hidden lg:block text-xs font-mono text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded border border-slate-700/50">
            <span className="text-cyan-400 font-semibold">{liveClock}</span> IST
          </div>
        </div>

        {/* Right Controls */}
        <div className="flex items-center gap-2.5">
          {/* Connection Status */}
          <ConnectionStatus status={connectionStatus} />

          {/* Node Selector (Hidden on standalone portals) */}
          {!isStandalonePortal && (
            <NodeSelector currentNode={currentNode} onSelectNode={onSelectNode} />
          )}

          {/* Sound Toggle */}
          <button
            onClick={handleToggleSound}
            title={isMuted ? "Unmute confirmed SOS sounds" : "Mute confirmed SOS sounds"}
            className={`p-2 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              isMuted
                ? "bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200"
                : "bg-cyan-500/10 text-cyan-400 border-cyan-500/30 hover:bg-cyan-500/20"
            }`}
          >
            {isMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4 text-cyan-400" />}
          </button>

          {/* ML Fusion Page Link (Hidden on standalone portals) */}
          {!isStandalonePortal && (
            <Link
              to="/ml-fusion"
              className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
                location.pathname === '/ml-fusion'
                  ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                  : "bg-slate-800 text-cyan-400 border border-cyan-500/30 hover:bg-slate-700"
              }`}
            >
              <Brain className="w-4 h-4" />
              <span>ML FUSION</span>
            </Link>
          )}

          {/* Alert Center Dashboard Link */}
          <Link
            to="/alert-center"
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
              location.pathname === '/alert-center'
                ? "bg-rose-600 text-white shadow-md shadow-rose-600/20"
                : "bg-rose-950/80 text-rose-300 border border-rose-500/40 hover:bg-rose-900"
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>ALERT CENTER</span>
          </Link>

          {/* Diagnostics Page Link (Hidden on standalone portals) */}
          {!isStandalonePortal && (
            <Link
              to="/diagnostics"
              className={`px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                location.pathname === '/diagnostics'
                  ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                  : "bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700"
              }`}
            >
              DIAGNOSTICS
            </Link>
          )}

          {/* Mobile NISAR Link */}
          <Link
            to="/mobile-nisar"
            className={`px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1 transition-all ${
              location.pathname === '/mobile-nisar'
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "bg-cyan-950 text-cyan-300 border border-cyan-500/40 hover:bg-cyan-900"
            }`}
          >
            <Satellite className="w-3.5 h-3.5 text-cyan-400" />
            <span>MOBILE NISAR</span>
          </Link>

          {/* User Role & Logout */}
          {user ? (
            <div className="flex items-center gap-2 ml-1 pl-2 border-l border-slate-800">
              <span className="text-[11px] font-semibold text-slate-300 hidden md:inline-block">
                {user.email.split("@")[0]}
              </span>
              <button
                onClick={handleLogout}
                title="Sign out operator"
                className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="text-xs text-slate-400 hover:text-cyan-400 px-2 py-1 rounded transition-colors"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
