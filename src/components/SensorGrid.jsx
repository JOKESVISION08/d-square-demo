import React from 'react';
import { Thermometer, Droplet, Waves, Flame, CloudFog, Activity, Droplets } from 'lucide-react';
import SensorCard from './SensorCard';

export default function SensorGrid({ telemetry }) {
  const t = telemetry || {};

  const temp = typeof t.temperature === 'number' ? t.temperature : (t.temperature_c || 25.0);
  const hum = typeof t.humidity === 'number' ? t.humidity : (t.humidity_pct || 50.0);
  const soilPct = typeof t.soil_moisture === 'number' ? t.soil_moisture : (t.soil_moisture_pct || 42.0);
  const soilRaw = typeof t.soil_raw === 'number' ? t.soil_raw : 850;
  const mq2 = t.mq2_gas === 1 || t.mq2_smoke === 1 ? 1 : 0;
  const flame = t.flame === 1 ? 1 : 0;
  const waterLevel = typeof t.water_level === 'number' ? t.water_level : 5.0;

  // Status Evaluations
  const tempStatus = temp > 45 ? 'danger' : temp > 38 ? 'warn' : 'normal';
  const humStatus = hum > 85 ? 'danger' : hum > 75 ? 'warn' : 'normal';
  const soilStatus = (soilRaw < 600 || soilPct >= 80) ? 'danger' : (soilRaw < 800 || soilPct >= 60) ? 'warn' : 'normal';
  const gasStatus = mq2 === 1 ? 'danger' : 'normal';
  const flameStatus = flame === 1 ? 'danger' : 'normal';
  const waterStatus = waterLevel > 50 ? 'danger' : waterLevel > 30 ? 'warn' : 'normal';

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span>Live Ground Telemetry (6 Core Sensors)</span>
        </h3>
        <span className="text-[11px] font-mono text-slate-500">Node: D-SQUARE_NODE_01</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* 1. Temperature */}
        <SensorCard
          icon={Thermometer}
          label="Temperature"
          value={temp.toFixed(1)}
          unit="°C"
          subtext="DHT11 • Pin D5"
          status={tempStatus}
          colorClass="bg-amber-500/10 text-amber-400"
        />

        {/* 2. Humidity */}
        <SensorCard
          icon={Droplet}
          label="Humidity"
          value={hum.toFixed(1)}
          unit="%"
          subtext="DHT11 • Optimal 40-70%"
          status={humStatus}
          colorClass="bg-blue-500/10 text-blue-400"
        />

        {/* 3. Soil Moisture */}
        <SensorCard
          icon={Waves}
          label="Soil Moisture"
          value={soilPct.toFixed(1)}
          unit="%"
          subtext={`Raw ADC: ${soilRaw}`}
          status={soilStatus}
          colorClass="bg-cyan-500/10 text-cyan-400"
        />

        {/* 4. MQ-2 Gas/Smoke */}
        <SensorCard
          icon={CloudFog}
          label="MQ-2 Smoke"
          value={mq2 === 1 ? "DETECTED" : "CLEAN"}
          subtext="MQ-2 Module • Pin D6"
          status={gasStatus}
          colorClass="bg-slate-700 text-slate-300"
        />

        {/* 5. IR Flame Sensor */}
        <SensorCard
          icon={Flame}
          label="IR Flame"
          value={flame === 1 ? "FLAME ON" : "SAFE"}
          subtext="IR Sensor • Pin D2"
          status={flameStatus}
          colorClass="bg-rose-500/10 text-rose-400"
        />

        {/* 6. Water Level Sensor */}
        <SensorCard
          icon={Droplets}
          label="Water Level"
          value={waterLevel.toFixed(1)}
          unit="cm"
          subtext="Submersible Depth"
          status={waterStatus}
          colorClass="bg-sky-500/10 text-sky-400"
        />
      </div>
    </div>
  );
}
