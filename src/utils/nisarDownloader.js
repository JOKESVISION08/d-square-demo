/**
 * NISAR Satellite Pixel File Downloader Utility
 * Generates and downloads NISAR pixel JSON and PNG payload files to save into the nisar/ folder.
 */

export function triggerFileDownload(content, filename, contentType = 'application/json') {
  try {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.warn("File download notice:", err);
  }
}

export function triggerImageDownload(dataUrl, filename) {
  try {
    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (err) {
    console.warn("Image download notice:", err);
  }
}

export function downloadNisarPixelBundle(payload = {}, capturedImage = null) {
  const now = new Date();
  const timestampStr = now.toISOString().replace(/[-:T.]/g, '').slice(0, 14);

  const formattedTime = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();

  const nisarJsonPayload = {
    timestamp: Date.now() / 1000,
    formatted_time: formattedTime,
    nisar_pixels: {
      red: payload.red || 0.62,
      green: payload.green || 0.48,
      blue: payload.blue || 0.35,
      nir: payload.nir || 0.18,
      swir: payload.swir || 0.45,
      thermal: payload.thermal || 48.5,
      l_band_db: payload.l_band_db || -14.5,
      s_band_db: payload.s_band_db || -8.2,
      coherence: payload.coherence || 0.42
    },
    predicted_disaster: payload.disaster_type || payload.predicted_disaster || "landslide",
    risk_level: payload.risk_level || "HIGH",
    confidence_percent: payload.confidence_percent || 92.8,
    location: {
      lat: payload.lat || 30.0668,
      lon: payload.lon || 79.0193,
      roi: "Uttarakhand Himalayan Grid"
    }
  };

  const jsonString = JSON.stringify(nisarJsonPayload, null, 2);

  // 1. Download latest_nisar_data.json
  triggerFileDownload(jsonString, 'latest_nisar_data.json', 'application/json');

  // 2. Download timestamped nisar_pixel_YYYYMMDD_HHMMSS.json
  setTimeout(() => {
    triggerFileDownload(jsonString, `nisar_pixel_${timestampStr}.json`, 'application/json');
  }, 300);

  // 3. Download latest_nisar_capture.png if camera image data exists
  if (capturedImage) {
    setTimeout(() => {
      triggerImageDownload(capturedImage, `latest_nisar_capture.png`);
    }, 600);
  }
}
