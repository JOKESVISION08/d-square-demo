# D-SQUARE 2.0 — Historical Satellite Pixel-and-Patch Comparison Engine Pipeline

## Overview

The **Historical Satellite Pixel-and-Patch Comparison Engine** upgrades the D-SQUARE 2.0 Earth-observation capability from single-pixel lookups into a scientifically rigorous, multi-spectral, spatial patch comparison module. It enables real-time remote-sensing observations (from Sentinel-2, ISRO NISAR, Landsat-8, Resourcesat-2, INSAT-3D) to be benchmarked against a SQLite database of historical disaster scenes and normal baseline observations.

---

## Technical Architecture & Capabilities

```
+-----------------------------------------------------------------------------------+
|                        CURRENT SATELLITE / ROI OBSERVATION                        |
|   Spectral Bands (Red, Green, Blue, NIR, SWIR1, SWIR2, Thermal LST, SAR L/S-band)  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                           SPATIAL PATCH PROCESSOR                                 |
|               Supports 3x3 (9 px), 5x5 (25 px), 9x9 (81 px) ROI patches            |
|       Computes μ, σ, median, valid_pixel_count across NDVI, NBR, LST, SAR         |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                      z-SCORE FEATURE STANDARDIZATION                              |
|                z = (x - μ) / max(σ, 1e-6) across 21 spectral/SAR features          |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                     MISSING-DATA-SAFE SIMILARITY MATCHING                         |
|      Distance: d_norm = sqrt(Σ (z_cur - z_hist)²) / sqrt(N_available_features)    |
|               Similarity % = exp(-d_norm / sqrt(N_available)) * 100               |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                 CATEGORY-LEVEL RANKING & BASELINE ANOMALY GAUGE                   |
|     - Top 10 matches + Top-3 class averages (Forest Fire, Flood, Landslide, etc.)|
|     - Baseline Anomaly Score (0-100%) against Normal scenes                       |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                    MULTI-MODAL FUSION ENGINE INTEGRATION                          |
|    - 4 Core Models (25% each: Satellite CNN, LSTM Time-Series, RF IoT, CV Camera) |
|    - Calibrated Historical Evidence Adjustment (10-15% max, reduced if DEMO)     |
|    - SMS Safeguard: SMS alerts dispatch ONLY if ground sensors/CV verify risk    |
+-----------------------------------------------------------------------------------+
```

---

## Database Schema Specification

The engine uses two dedicated SQLite tables in `disasters.db`:

### 1. `satellite_pixel_samples` (Historical Archive)
Stores verified historical scenes and synthetic demo samples.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID |
| `event_id` | TEXT | Historical event ID (e.g., `EVT_2021_ALMORA_FIRE_01`) |
| `disaster_type` | TEXT | Disaster class: `Forest_Fire`, `Flood`, `Landslide`, `Air_Pollution`, `None` |
| `acquisition_date` | TEXT | YYYY-MM-DD timestamp |
| `satellite` | TEXT | Sensor platform (`Sentinel-2`, `NISAR`, `Landsat-8`, etc.) |
| `product` | TEXT | Processing level (`L2A Surface Reflectance`, `L-Band SAR`) |
| `latitude`, `longitude` | REAL | Geographic coordinates |
| `patch_size` | INTEGER | Default patch dimension (e.g. 5 for 5x5) |
| `red`, `green`, `blue`, `nir`, `swir1`, `swir2`, `thermal` | REAL | Spectral reflectance & thermal values |
| `sar_l_band_db`, `sar_s_band_db`, `sar_vv_db`, `sar_vh_db` | REAL | Synthetic Aperture Radar backscatter (dB) |
| `ndvi`, `ndwi`, `mndwi`, `nbr`, `lst`, `soil_moisture` | REAL | Spectral indices and land surface metrics |
| `patch_mean_ndvi`, `patch_std_ndvi`, `patch_median_ndvi` | REAL | 5x5 spatial patch statistics for NDVI |
| `patch_mean_nbr`, `patch_std_nbr`, `patch_median_nbr` | REAL | 5x5 spatial patch statistics for NBR |
| `patch_mean_lst`, `patch_std_lst` | REAL | 5x5 spatial patch statistics for LST |
| `valid_pixel_count` | INTEGER | Number of non-cloud/valid pixels in patch |
| `cloud_cover` | REAL | Scene cloud cover percentage |
| `label_source` | TEXT | Ground truth provenance (`ISRO Bhuvan Archive`, `NASA FIRMS`, `Synthetic prototype scenario`) |
| `verification_status` | TEXT | `VERIFIED` (ground-truthed) or `DEMO` (synthetic prototype) |
| `quality_flag` | TEXT | Data quality level (`VALIDATED_GROUND_TRUTH`, `NOT_FOR_SCIENTIFIC_VALIDATION`) |

### 2. `current_satellite_samples` (Live Query Log)
Stores every current ROI observation evaluated against the historical archive.

---

## CSV Import Pipeline

### Importing Data via CLI
Import historical satellite observations into the SQLite database:
```bash
.venv\Scripts\python.exe satellite/import_historical_samples.py --file data/historical_samples_template.csv
```

### CSV Schema Header Requirement
```csv
event_id,disaster_type,acquisition_date,satellite,product,latitude,longitude,patch_size,red,green,blue,nir,swir1,swir2,thermal,sar_l_band_db,sar_s_band_db,sar_vv_db,sar_vh_db,sar_coherence,ground_deformation_mm,ndvi,ndwi,mndwi,nbr,lst,soil_moisture,rainfall,slope,patch_mean_ndvi,patch_std_ndvi,patch_median_ndvi,patch_mean_nbr,patch_std_nbr,patch_median_nbr,patch_mean_lst,patch_std_lst,valid_pixel_count,cloud_cover,label_source,source_url,verification_status,quality_flag
```

---

## API Endpoints Reference

### 1. `POST /api/historical_comparison`
Evaluates current satellite observations against the historical database.
**Request Body**:
```json
{
  "patch_size": 5,
  "disaster_type": "Forest_Fire",
  "latitude": 30.0668,
  "longitude": 79.0193,
  "pixel_values": {
    "red": 0.26, "green": 0.21, "blue": 0.18,
    "nir": 0.16, "swir1": 0.31, "thermal": 44.8
  }
}
```
**Response**:
Includes `patch_size`, `query_sample`, `multi_spectral_patch_stats`, `z_score_vector`, `top_matches`, `class_level_scores`, `best_historical_pattern`, `anomaly`, `fusion_result`.

### 2. `GET /api/historical_events_summary`
Returns database record counts by disaster type, satellite, verification status, and feature statistics.

### 3. `GET /api/satellite_history_trend`
Returns 30-day temporal trend data for Chart.js rendering (NDVI, LST, Soil Moisture, Anomaly Score).

### 4. `POST /api/import_historical_samples`
Upload CSV files dynamically via multi-part form data (`file`) or raw CSV string (`csv_text`).

---

## Dashboard UI Integration Guide

The software dashboard at `http://127.0.0.1:5001/` includes:
- **Spatial Patch Size Selector**: Dropdown to toggle between $3 \times 3$, $5 \times 5$, and $9 \times 9$ patch grids.
- **Disaster Class Filter**: Filter comparison against specific disaster types or all classes.
- **Multi-Spectral Patch Table**: Displays center pixel, mean ($\mu$), standard deviation ($\sigma$), median, and valid pixel counts.
- **Verified vs DEMO Badges**: Clearly distinguishes verified historical records from synthetic demo prototypes.
- **Top 5 Matches List**: Ranks closest historical event matches by similarity %.
- **Baseline Anomaly Gauge**: Displays Himalayan baseline anomaly score % and alert status.
- **30-Day Satellite Temporal Trend Chart**: Interactive Chart.js line graph displaying 30-day remote sensing trends.
- **Leaflet GIS Map Overlay**: Draws dashed orange patch ROI rectangle and plots color-coded historical match markers.

---

## Verification & Testing

Run the full 11-step test suite:
```bash
.venv\Scripts\python.exe test_historical_pixel.py
```

All 11 unit tests validate spectral indices, spatial patch stats, z-score standardization, missing-data-safe similarity, anomaly scoring, fusion evidence, SMS safeguards, and Flask endpoints.
