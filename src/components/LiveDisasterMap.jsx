import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { MapPin, Layers } from 'lucide-react';

export default function LiveDisasterMap({
  telemetry,
  activeAlert,
  activeIncident,
  customPolygon,
  customPixels,
  height = "380px"
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layersGroupRef = useRef(null);

  const defaultLat = 30.0668;
  const defaultLng = 79.0193;

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [defaultLat, defaultLng],
        zoom: 12,
        zoomControl: true
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
      }).addTo(map);

      mapInstanceRef.current = map;
      layersGroupRef.current = L.layerGroup().addTo(map);
    }

    const map = mapInstanceRef.current;
    const group = layersGroupRef.current;

    group.clearLayers();

    // 1. Ground Station Node Marker (Cyan/Blue)
    const nodeIcon = L.divIcon({
      className: 'custom-leaflet-marker',
      html: `<div style="background-color: #06b6d4; width: 16px; height: 16px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 0 10px rgba(6,182,212,0.8);"></div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });

    const nodeMarker = L.marker([defaultLat, defaultLng], { icon: nodeIcon })
      .bindPopup(`
        <div style="font-size: 12px; color: #f8fafc;">
          <strong style="color: #38bdf8;">D-SQUARE NODE 01</strong><br/>
          Uttarakhand Slope Sector 4<br/>
          Lat: ${defaultLat}°N, Lng: ${defaultLng}°E<br/>
          Telemetry: Active
        </div>
      `);
    group.addLayer(nodeMarker);

    // 2. Hardware Alert Marker (Amber)
    if (activeAlert && activeAlert.event_status === "ACTIVE") {
      const alertLat = activeAlert.latitude || defaultLat;
      const alertLng = activeAlert.longitude || defaultLng;

      const amberIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div style="background-color: #f59e0b; width: 22px; height: 22px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 0 15px rgba(245,158,11,0.9); animation: pulse 1s infinite;"></div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });

      const alertMarker = L.marker([alertLat, alertLng], { icon: amberIcon })
        .bindPopup(`
          <div style="font-size: 12px; color: #f8fafc;">
            <strong style="color: #fbbf24;">⚠️ RAW HARDWARE ANOMALY</strong><br/>
            Disaster: ${(activeAlert.disaster_type || "fire").toUpperCase()}<br/>
            Severity: ${activeAlert.severity || "CRITICAL"}<br/>
            Status: Awaiting Operator Verification
          </div>
        `);
      group.addLayer(alertMarker);
    }

    // 3. Confirmed SOS Incident Marker (Red)
    if (activeIncident && activeIncident.status === "SOS_ACTIVE") {
      const sosLat = activeIncident.latitude || defaultLat;
      const sosLng = activeIncident.longitude || defaultLng;

      const redIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div style="background-color: #ef4444; width: 26px; height: 26px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 0 25px rgba(239,68,68,1); animation: pulse 0.8s infinite;"></div>`,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const sosMarker = L.marker([sosLat, sosLng], { icon: redIcon })
        .bindPopup(`
          <div style="font-size: 12px; color: #f8fafc;">
            <strong style="color: #fca5a5;">🚨 VERIFIED SOS INCIDENT</strong><br/>
            ID: ${activeIncident.incident_id}<br/>
            Disaster: ${(activeIncident.disaster_type || "fire").toUpperCase()}<br/>
            Verified By: ${activeIncident.verified_by}<br/>
            Dispatch: GPT Feeds Active
          </div>
        `);
      group.addLayer(sosMarker);

      // GeoJSON Polygon for Confirmed SOS
      const sosPolyCoords = [
        [sosLat + 0.003, sosLng - 0.003],
        [sosLat + 0.004, sosLng + 0.004],
        [sosLat - 0.002, sosLng + 0.005],
        [sosLat - 0.003, sosLng - 0.002]
      ];
      const sosPoly = L.polygon(sosPolyCoords, {
        color: '#ef4444',
        fillColor: '#dc2626',
        fillOpacity: 0.35,
        weight: 2.5,
        dashArray: '5, 8'
      }).bindPopup("<b>AI DISASTER POLYGON BOUNDARY</b><br>High-risk impact perimeter.");
      group.addLayer(sosPoly);
    }

    // 4. Custom ML Fusion Polygon Overlay
    if (customPolygon && customPolygon.length > 0) {
      const polyCoords = customPolygon.map(p => Array.isArray(p) ? p : [p.lat || p[0], p.lng || p.lon || p[1]]);
      const customPoly = L.polygon(polyCoords, {
        color: '#38bdf8',
        fillColor: '#0284c7',
        fillOpacity: 0.3,
        weight: 2
      }).bindPopup("<b>ML FUSION CHANGE POLYGON</b><br>Satellite image change analysis overlay.");
      group.addLayer(customPoly);
    }

  }, [telemetry, activeAlert, activeIncident, customPolygon]);

  return (
    <div className="panel-card p-4 relative overflow-hidden bg-slate-900 border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-cyan-400" />
          <h3 className="font-heading font-bold text-xs text-cyan-300 uppercase tracking-wider">
            Interactive Disaster GIS Map (Uttarakhand Sector 4)
          </h3>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-[10px] font-mono text-slate-300 bg-slate-950/80 px-2.5 py-1 rounded border border-slate-800">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Normal
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Warning
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-rose-500"></span> Confirmed SOS
          </span>
        </div>
      </div>

      {/* Leaflet Map Box */}
      <div
        ref={mapContainerRef}
        style={{ height: height }}
        className="w-full rounded-xl border border-slate-800 z-10"
      />
    </div>
  );
}
