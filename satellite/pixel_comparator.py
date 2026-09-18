"""
D-SQUARE 2.0 Historical Satellite Pixel-and-Patch Comparator Engine
Scientifically compares current satellite spectral/SAR patch observations against verified and demo
historical disaster scenes using z-score standardized feature vectors, missing-data-safe similarity,
class-level top-3 ranking, and baseline anomaly scoring.
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


def calculate_spectral_indices(pixel_values: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Calculates spectral indices with safe division safeguards:
    - NDVI  = (NIR - Red) / (NIR + Red)
    - NDWI  = (Green - NIR) / (Green + NIR)
    - MNDWI = (Green - SWIR1) / (Green + SWIR1)
    - NBR   = (NIR - SWIR2) / (NIR + SWIR2)
    - LST   = Thermal (if available)
    Returns None if denominator is zero or required bands are missing.
    """
    def to_float(val):
        try:
            return float(val) if val not in [None, "", "null", "None"] else None
        except Exception:
            return None

    red = to_float(pixel_values.get("red"))
    green = to_float(pixel_values.get("green"))
    nir = to_float(pixel_values.get("nir"))
    swir1 = to_float(pixel_values.get("swir1", pixel_values.get("swir")))
    swir2 = to_float(pixel_values.get("swir2", pixel_values.get("swir")))
    thermal = to_float(pixel_values.get("thermal"))

    eps = 1e-6
    indices = {
        "ndvi": None,
        "ndwi": None,
        "mndwi": None,
        "nbr": None,
        "lst": thermal
    }

    if nir is not None and red is not None:
        denom = nir + red
        if abs(denom) > eps:
            indices["ndvi"] = round(float((nir - red) / denom), 4)

    if green is not None and nir is not None:
        denom = green + nir
        if abs(denom) > eps:
            indices["ndwi"] = round(float((green - nir) / denom), 4)

    if green is not None and swir1 is not None:
        denom = green + swir1
        if abs(denom) > eps:
            indices["mndwi"] = round(float((green - swir1) / denom), 4)

    if nir is not None and swir2 is not None:
        denom = nir + swir2
        if abs(denom) > eps:
            indices["nbr"] = round(float((nir - swir2) / denom), 4)

    return indices


def calculate_patch_statistics(pixel_matrix: List[Dict[str, Any]], patch_size: int = 5) -> Dict[str, Any]:
    """
    Calculates spatial patch statistics (mean, std, median, valid_pixel_count)
    across an ROI patch for key spectral indicators (NDVI, NBR, LST).
    """
    if not pixel_matrix:
        return {
            "patch_size": patch_size,
            "valid_pixel_count": 0,
            "ndvi": {"mean": None, "std": None, "median": None},
            "nbr": {"mean": None, "std": None, "median": None},
            "lst": {"mean": None, "std": None, "median": None}
        }

    valid_count = len(pixel_matrix)
    
    def compute_stats(key):
        vals = []
        for p in pixel_matrix:
            if key in p and p[key] is not None:
                vals.append(float(p[key]))
            else:
                idx = calculate_spectral_indices(p)
                if idx.get(key) is not None:
                    vals.append(float(idx[key]))
        if not vals:
            return {"mean": None, "std": None, "median": None}
        arr = np.array(vals, dtype=np.float64)
        return {
            "mean": round(float(np.mean(arr)), 4),
            "std": round(float(np.std(arr)), 4),
            "median": round(float(np.median(arr)), 4)
        }

    return {
        "patch_size": patch_size,
        "valid_pixel_count": valid_count,
        "ndvi": compute_stats("ndvi"),
        "nbr": compute_stats("nbr"),
        "lst": compute_stats("lst")
    }


def calculate_feature_statistics(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Calculates feature-wise mean and std across historical records for z-score normalization."""
    if not records:
        return {}

    feature_keys = [
        "red", "green", "blue", "nir", "swir1", "swir2", "thermal",
        "sar_l_band_db", "sar_s_band_db", "sar_vv_db", "sar_vh_db",
        "sar_coherence", "ground_deformation_mm", "ndvi", "ndwi",
        "mndwi", "nbr", "lst", "soil_moisture", "rainfall", "slope"
    ]

    stats = {}
    for key in feature_keys:
        vals = []
        for r in records:
            # Check direct key or inside features dict
            val = r.get(key)
            if val is None and isinstance(r.get("features"), dict):
                val = r["features"].get(key)
            if val not in [None, "", "null", "None"]:
                try:
                    vals.append(float(val))
                except Exception:
                    pass
        if vals:
            arr = np.array(vals, dtype=np.float64)
            std_val = float(np.std(arr))
            stats[key] = {
                "mean": float(np.mean(arr)),
                "std": std_val if std_val >= 1e-5 else 1.0,
                "count": len(vals)
            }
    return stats


def build_feature_vector(record: Dict[str, Any], feature_stats: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """Standardizes available numeric features using z-score: z = (value - mean) / max(std, 1e-6)."""
    feature_keys = [
        "red", "green", "blue", "nir", "swir1", "swir2", "thermal",
        "sar_l_band_db", "sar_s_band_db", "sar_vv_db", "sar_vh_db",
        "sar_coherence", "ground_deformation_mm", "ndvi", "ndwi",
        "mndwi", "nbr", "lst", "soil_moisture", "rainfall", "slope"
    ]

    z_vector = {}
    raw_feats = record.get("features", record) if isinstance(record.get("features"), dict) else record

    for key in feature_keys:
        val = raw_feats.get(key)
        if val not in [None, "", "null", "None"]:
            try:
                fval = float(val)
                st = feature_stats.get(key)
                if st:
                    mean = st["mean"]
                    std = max(st["std"], 1e-6)
                    z_vector[key] = (fval - mean) / std
                else:
                    z_vector[key] = fval
            except Exception:
                pass
    return z_vector


def compare_current_to_historical(
    current_record: Dict[str, Any],
    historical_records: List[Dict[str, Any]],
    feature_stats: Optional[Dict[str, Dict[str, float]]] = None
) -> Dict[str, Any]:
    """
    Compares standardized current satellite observations against historical records.
    Uses missing-data-safe distance and computes normalized similarity score (0.0 to 1.0 / 0 to 100%).
    Returns top 10 matches, class-level top-3 averages, best pattern match, and metadata.
    """
    if not feature_stats:
        feature_stats = calculate_feature_statistics(historical_records + [current_record])

    cur_z = build_feature_vector(current_record, feature_stats)

    matches = []
    for h in historical_records:
        h_z = build_feature_vector(h, feature_stats)
        
        # Find overlapping features between current and historical records
        common_keys = [k for k in cur_z if k in h_z]
        if not common_keys:
            continue

        # Missing-data-safe Euclidean distance normalized by feature count
        sq_dist_sum = sum((cur_z[k] - h_z[k]) ** 2 for k in common_keys)
        n_feat = len(common_keys)
        norm_dist = math.sqrt(sq_dist_sum) / math.sqrt(n_feat)

        # Convert distance to similarity score: exp(-distance / sqrt(n_features))
        sim = math.exp(-norm_dist / math.sqrt(n_feat))
        sim_percent = round(sim * 100.0, 2)

        raw_feats = h.get("features", h) if isinstance(h.get("features"), dict) else h
        
        matches.append({
            "id": h.get("id"),
            "event_id": h.get("event_id", "EVT_HIST_01"),
            "disaster_type": h.get("disaster_type", "None"),
            "acquisition_date": h.get("acquisition_date", "N/A"),
            "satellite": h.get("satellite", "Unknown"),
            "product": h.get("product", "Unknown Product"),
            "latitude": float(h.get("latitude", 0.0)),
            "longitude": float(h.get("longitude", 0.0)),
            "similarity": round(sim, 4),
            "similarity_percent": sim_percent,
            "verification_status": h.get("verification_status", "DEMO"),
            "quality_flag": h.get("quality_flag", "NOT_FOR_SCIENTIFIC_VALIDATION"),
            "label_source": h.get("label_source", "Historical Archive"),
            "source_url": h.get("source_url"),
            "cloud_cover": h.get("cloud_cover"),
            "common_feature_count": n_feat,
            "features": {k: raw_feats.get(k) for k in common_keys if raw_feats.get(k) is not None}
        })

    # Sort matches by highest similarity
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    top_10 = matches[:10]

    class_scores = summarize_disaster_matches(matches)

    best_match = top_10[0] if top_10 else {
        "event_id": "NONE",
        "disaster_type": "None",
        "similarity_percent": 0.0,
        "verification_status": "DEMO",
        "acquisition_date": "N/A"
    }

    return {
        "top_matches": top_10,
        "class_level_scores": class_scores,
        "best_historical_pattern": best_match,
        "compared_sample_count": len(historical_records)
    }


def summarize_disaster_matches(matches: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculates category-level scores based on mean of top 3 matches per disaster type."""
    disasters = ["Forest_Fire", "Flood", "Landslide", "Air_Pollution", "None"]
    by_cat = {d: [] for d in disasters}

    for m in matches:
        dtype = m.get("disaster_type", "None")
        if dtype in by_cat:
            by_cat[dtype].append(m)

    summary = {}
    for dtype, cat_matches in by_cat.items():
        if cat_matches:
            top_3 = cat_matches[:3]
            mean_sim = float(np.mean([x["similarity"] for x in top_3]))
            mean_sim_pct = round(mean_sim * 100.0, 2)
            verified_count = sum(1 for x in top_3 if x.get("verification_status") == "VERIFIED")
            summary[dtype] = {
                "similarity_score": round(mean_sim, 4),
                "similarity_percent": mean_sim_pct,
                "top_match_event": top_3[0]["event_id"],
                "sample_count": len(cat_matches),
                "verified_sample_count": verified_count
            }
        else:
            summary[dtype] = {
                "similarity_score": 0.0,
                "similarity_percent": 0.0,
                "top_match_event": "N/A",
                "sample_count": 0,
                "verified_sample_count": 0
            }
    return summary


def calculate_anomaly_score(
    current_record: Dict[str, Any],
    baseline_records: List[Dict[str, Any]],
    feature_stats: Optional[Dict[str, Dict[str, float]]] = None
) -> Dict[str, Any]:
    """
    Calculates anomaly score (0–100%) against Normal baseline scenes.
    Outputs feature contribution deltas (NDVI, NBR, LST, Soil Moisture, SAR, Water Index)
    and status: NORMAL (0-29%), WATCH (30-49%), HIGH (50-74%), CRITICAL (75-100%).
    """
    if not baseline_records:
        return {
            "score_percent": 15.0,
            "status": "NORMAL",
            "feature_contributions": {}
        }

    if not feature_stats:
        feature_stats = calculate_feature_statistics(baseline_records)

    cur_feats = current_record.get("features", current_record) if isinstance(current_record.get("features"), dict) else current_record
    cur_z = build_feature_vector(current_record, feature_stats)

    # Compute baseline mean feature vector
    base_feats_list = [r.get("features", r) if isinstance(r.get("features"), dict) else r for r in baseline_records]
    base_stats = calculate_feature_statistics(base_feats_list)

    contributions = {}
    total_z_anomaly = 0.0
    count = 0

    key_map = {
        "delta_ndvi": ("ndvi", "NDVI Vegetation Anomaly"),
        "delta_nbr": ("nbr", "NBR Burn Anomaly"),
        "delta_lst": ("lst", "LST Surface Temp Anomaly (°C)"),
        "delta_soil_moisture": ("soil_moisture", "Soil Moisture Anomaly (%)"),
        "delta_sar_backscatter": ("sar_l_band_db", "SAR Backscatter Anomaly (dB)"),
        "delta_water_index": ("ndwi", "NDWI Water Index Anomaly")
    }

    for c_key, (f_key, label) in key_map.items():
        c_val = cur_feats.get(f_key)
        b_st = base_stats.get(f_key)
        if c_val not in [None, ""] and b_st:
            try:
                cv = float(c_val)
                bm = b_st["mean"]
                delta = round(cv - bm, 4)
                z_dist = abs(cur_z.get(f_key, 0.0))
                total_z_anomaly += z_dist
                count += 1
                contributions[c_key] = {
                    "delta": delta,
                    "current_value": cv,
                    "baseline_mean": round(bm, 4),
                    "z_anomaly": round(z_dist, 2),
                    "label": label
                }
            except Exception:
                pass

    if count > 0:
        mean_z = total_z_anomaly / count
        # Map z-score distance (0.0 -> 0%, 3.0 -> 100%)
        score_pct = round(min(max((mean_z / 3.0) * 100.0, 0.0), 100.0), 1)
    else:
        score_pct = 15.0

    if score_pct >= 75.0:
        status = "CRITICAL"
    elif score_pct >= 50.0:
        status = "HIGH"
    elif score_pct >= 30.0:
        status = "WATCH"
    else:
        status = "NORMAL"

    return {
        "score_percent": score_pct,
        "status": status,
        "feature_contributions": contributions
    }


class HistoricalPixelComparator:
    """
    Backwards-compatible wrapper class for Historical Satellite Pixel-and-Patch Comparison.
    """
    def __init__(self, db_path: str = None):
        pass

    @staticmethod
    def calculate_spectral_indices(pixel_values: Dict[str, Any]) -> Dict[str, Optional[float]]:
        return calculate_spectral_indices(pixel_values)

    def compare_pixels(
        self,
        current_pixels: Dict[str, float],
        target_disaster_type: str = "Forest_Fire",
        location_lat: float = 30.0668,
        location_lon: float = 79.0193
    ) -> Dict[str, Any]:
        """Backwards compatible pixel comparison wrapper."""
        from database import get_historical_pixel_samples
        hist_samples = get_historical_pixel_samples(limit=1000)
        
        # Build current record structure
        indices = calculate_spectral_indices(current_pixels)
        cur_record = {
            "latitude": location_lat,
            "longitude": location_lon,
            "features": {**current_pixels, **indices}
        }
        
        comp_res = compare_current_to_historical(cur_record, hist_samples)
        baseline_samples = [r for r in hist_samples if r.get("disaster_type") in ["None", "Normal"]]
        anom_res = calculate_anomaly_score(cur_record, baseline_samples)
        
        best = comp_res["best_historical_pattern"]
        
        return {
            "status": "success",
            "target_disaster_type": target_disaster_type,
            "current_indices": indices,
            "historical_matches": comp_res["top_matches"],
            "best_match_event": best,
            "highest_similarity": best.get("similarity", 0.0),
            "similarity_2021_fire": comp_res["class_level_scores"].get("Forest_Fire", {}).get("similarity_score", 0.0),
            "similarity_2022_fire": comp_res["class_level_scores"].get("Forest_Fire", {}).get("similarity_score", 0.0),
            "class_level_scores": comp_res["class_level_scores"],
            "anomaly": anom_res
        }
