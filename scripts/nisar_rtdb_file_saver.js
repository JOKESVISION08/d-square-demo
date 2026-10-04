/**
 * NISAR Real-Time Database File Saver Daemon
 * Listens to Firebase RTDB /satellite.json and /nisar.json endpoints
 * and automatically saves every incoming pixel payload and image frame into the local nisar/ folder.
 */

import fs from 'fs';
import path from 'path';
import https from 'https';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const nisarDir = path.join(__dirname, '..', 'nisar');

if (!fs.existsSync(nisarDir)) {
  fs.mkdirSync(nisarDir, { recursive: true });
}

const RTDB_BASE = "https://d-sqaure-default-rtdb.firebaseio.com";
let lastSavedTimestamp = 0;

function fetchJson(url) {
  return new Promise((resolve) => {
    https.get(url, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          resolve(null);
        }
      });
    }).on('error', () => resolve(null));
  });
}

async function processNisarSync() {
  const satData = await fetchJson(`${RTDB_BASE}/satellite.json`);
  const nisarData = await fetchJson(`${RTDB_BASE}/nisar.json`);

  const activeData = nisarData || satData;
  if (!activeData) return;

  const currentTs = activeData.timestamp || (activeData.acquisition_time ? new Date(activeData.acquisition_time).getTime() : Date.now());

  if (currentTs === lastSavedTimestamp) return;
  lastSavedTimestamp = currentTs;

  const now = new Date();
  const timestampStr = now.toISOString().replace(/[-:T.]/g, '').slice(0, 14);
  const formattedTime = now.toISOString().replace('T', ' ').slice(0, 19);

  const pixels = activeData.nisar_pixels || {};
  const lBand = typeof activeData.l_band_db === 'number' ? activeData.l_band_db : (typeof pixels.l_band_db === 'number' ? pixels.l_band_db : -14.5);
  const sBand = typeof activeData.s_band_db === 'number' ? activeData.s_band_db : (typeof pixels.s_band_db === 'number' ? pixels.s_band_db : -8.2);
  const coh = typeof activeData.coherence === 'number' ? activeData.coherence : (typeof pixels.coherence === 'number' ? pixels.coherence : 0.42);
  const def = typeof activeData.deformation_mm_yr === 'number' ? activeData.deformation_mm_yr : (typeof pixels.deformation_mm_yr === 'number' ? pixels.deformation_mm_yr : -34.8);

  const disaster = activeData.disaster_type || activeData.predicted_disaster || "landslide";

  const cleanJsonPayload = {
    timestamp: currentTs,
    formatted_time: formattedTime,
    nisar_pixels: {
      red: pixels.red || 0.62,
      green: pixels.green || 0.48,
      blue: pixels.blue || 0.35,
      nir: pixels.nir || 0.18,
      swir: pixels.swir || 0.45,
      thermal: pixels.thermal || activeData.thermal || 48.5,
      l_band_db: lBand,
      s_band_db: sBand,
      coherence: coh,
      deformation_mm_yr: def
    },
    predicted_disaster: disaster,
    risk_level: activeData.risk_level || "HIGH",
    confidence_percent: activeData.confidence_percent || 92.8,
    location: {
      lat: activeData.location?.lat || activeData.latitude || 30.0668,
      lon: activeData.location?.lon || activeData.longitude || 79.0193,
      roi: "Uttarakhand Himalayan Grid"
    }
  };

  const jsonStr = JSON.stringify(cleanJsonPayload, null, 2);

  // Write latest_nisar_data.json directly into nisar/ folder
  const latestJsonPath = path.join(nisarDir, 'latest_nisar_data.json');
  fs.writeFileSync(latestJsonPath, jsonStr, 'utf8');

  // Write timestamped JSON into nisar/ folder
  const timeJsonPath = path.join(nisarDir, `nisar_pixel_${timestampStr}.json`);
  fs.writeFileSync(timeJsonPath, jsonStr, 'utf8');

  // Extract base64 image if available and save latest_nisar_capture.png directly into nisar/ folder
  const base64Img = activeData.captured_image || activeData.change_mask_url;
  if (base64Img && typeof base64Img === 'string' && base64Img.includes('data:image')) {
    try {
      const base64Data = base64Img.replace(/^data:image\/\w+;base64,/, "");
      const buffer = Buffer.from(base64Data, 'base64');
      const latestImgPath = path.join(nisarDir, 'latest_nisar_capture.png');
      const timestampImgPath = path.join(nisarDir, `nisar_capture_${timestampStr}.png`);
      fs.writeFileSync(latestImgPath, buffer);
      fs.writeFileSync(timestampImgPath, buffer);
      console.log(`📸 Saved captured camera image to nisar/latest_nisar_capture.png`);
    } catch (err) {
      console.warn("Image buffer write notice:", err);
    }
  }

  console.log(`📡 [NISAR SYNC OK] Saved satellite pixel frame to nisar/latest_nisar_data.json & nisar/nisar_pixel_${timestampStr}.json`);
}

// Poll RTDB every 1.5 seconds for incoming mobile NISAR satellite pixels
setInterval(processNisarSync, 1500);
processNisarSync();
console.log("🚀 NISAR RTDB File Saver Daemon active — automatically receiving satellite pixels into nisar/ folder.");
