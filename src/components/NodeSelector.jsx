import React from 'react';
import { Cpu } from 'lucide-react';

export default function NodeSelector({ currentNode = "D-SQUARE_NODE_01", onSelectNode }) {
  return (
    <div className="flex items-center gap-2 bg-slate-900 border border-slate-700/70 rounded-lg px-2.5 py-1 text-xs text-slate-200">
      <Cpu className="w-3.5 h-3.5 text-cyan-400" />
      <select
        value={currentNode}
        onChange={(e) => onSelectNode && onSelectNode(e.target.value)}
        className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer pr-1"
      >
        <option value="D-SQUARE_NODE_01" className="bg-slate-900 text-slate-200">
          Node 01: Uttarakhand Himalayan Sector
        </option>
        <option value="D-SQUARE_NODE_02" className="bg-slate-900 text-slate-200">
          Node 02: High-Altitude Landslide Zone
        </option>
      </select>
    </div>
  );
}
