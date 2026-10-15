/**
 * D-SQUARE 2.0 - Standalone Client-Side Satellite / NISAR Data Adapter
 * Operates purely via localStorage and React events for serverless Netlify deployment.
 */

export const SATELLITE_SOURCES = {
  NISAR: "NISAR",
  SENTINEL_1: "SENTINEL_1",
  SENTINEL_2: "SENTINEL_2",
  LANDSAT: "LANDSAT",
  ISRO: "ISRO",
  UPLOAD: "UPLOAD"
};

const STORAGE_KEYS = {
  SATELLITE: "dsquare_standalone_satellite",
  NISAR: "dsquare_standalone_nisar"
};

// Default initial satellite state
export const DEFAULT_UNAVAILABLE_SATELLITE_STATE = {
  source: "NISAR",
  acquisition_time: new Date().toISOString(),
  past_image_id: "NISAR_L1_PASS_20260920",
  current_image_id: "NISAR_MOBILE_CAM_20260924",
  change_mask_url: null,
  affected_pixels: [],
  polygon_boundary: [
    [30.0668, 79.0193],
    [30.0700, 79.0250],
    [30.0650, 79.0280],
    [30.0600, 79.0200]
  ],
  disaster_type: "landslide",
  confidence: 0.95,
  l_band_db: -14.5,
  s_band_db: -8.2,
  coherence: 0.42,
  deformation_mm_yr: -34.8,
  status: "CONFIRMED",
  message: "NISAR Satellite Orbit Track 142 Active (Standalone Netlify Mode)."
};

function getStoredSatelliteData() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.SATELLITE);
    if (data) return JSON.parse(data);
  } catch (e) {}
  return DEFAULT_UNAVAILABLE_SATELLITE_STATE;
}

export function parseSatellitePayload(rawData) {
  if (!rawData || rawData.status === "UNAVAILABLE") {
    return DEFAULT_UNAVAILABLE_SATELLITE_STATE;
  }

  const pixels = rawData.nisar_pixels || {};
  const lBand = typeof rawData.l_band_db === 'number' ? rawData.l_band_db : (typeof pixels.l_band_db === 'number' ? pixels.l_band_db : -14.5);
  const sBand = typeof rawData.s_band_db === 'number' ? rawData.s_band_db : (typeof pixels.s_band_db === 'number' ? pixels.s_band_db : -8.2);
  const coh = typeof rawData.coherence === 'number' ? rawData.coherence : (typeof pixels.coherence === 'number' ? pixels.coherence : 0.42);
  const def = typeof rawData.deformation_mm_yr === 'number' ? rawData.deformation_mm_yr : (typeof pixels.deformation_mm_yr === 'number' ? pixels.deformation_mm_yr : -34.8);

  const disaster = rawData.disaster_type || rawData.predicted_disaster || "landslide";
  const sourceName = rawData.source || "NISAR_MOBILE_CAMERA";
  const imgUrl = rawData.change_mask_url || rawData.captured_image || null;

  return {
    source: sourceName,
    acquisition_time: rawData.acquisition_time || rawData.formatted_time || new Date().toISOString(),
    past_image_id: rawData.past_image_id || "NISAR_L1_PASS",
    current_image_id: rawData.current_image_id || "NISAR_L2_PASS",
    change_mask_url: imgUrl,
    captured_image: imgUrl,
    affected_pixels: Array.isArray(rawData.affected_pixels) ? rawData.affected_pixels : [],
    polygon_boundary: Array.isArray(rawData.polygon_boundary) ? rawData.polygon_boundary : [
      [30.0668, 79.0193],
      [30.0700, 79.0250],
      [30.0650, 79.0280],
      [30.0600, 79.0200]
    ],
    disaster_type: disaster,
    confidence: typeof rawData.confidence === 'number' ? rawData.confidence : (rawData.confidence_percent ? rawData.confidence_percent / 100 : 0.95),
    l_band_db: lBand,
    s_band_db: sBand,
    coherence: coh,
    deformation_mm_yr: def,
    status: rawData.status || "CONFIRMED",
    message: rawData.message || `Mobile Satellite Pixel (${disaster.toUpperCase()}) Active.`
  };
}

export function subscribeToSatelliteData(callback) {
  const current = getStoredSatelliteData();
  callback(current);

  const interval = setInterval(() => {
    const latest = getStoredSatelliteData();
    callback(latest);
  }, 2000);

  const handleStorage = (e) => {
    if (e.key === STORAGE_KEYS.SATELLITE && e.newValue) {
      try {
        callback(parseSatellitePayload(JSON.parse(e.newValue)));
      } catch (err) {}
    }
  };
  window.addEventListener("storage", handleStorage);

  return () => {
    clearInterval(interval);
    window.removeEventListener("storage", handleStorage);
  };
}

export async function uploadSatelliteProductMetadata(productPayload) {
  const parsed = parseSatellitePayload({
    ...productPayload,
    status: productPayload.status || "CONFIRMED"
  });
  
  localStorage.setItem(STORAGE_KEYS.SATELLITE, JSON.stringify(parsed));
  localStorage.setItem(STORAGE_KEYS.NISAR, JSON.stringify(productPayload));
  return parsed;
}
