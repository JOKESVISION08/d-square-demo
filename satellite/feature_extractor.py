"""
D-SQUARE 2.0 Feature Extractor & Scene Comparison Engine
Extracts ROI spatial patch feature vectors (3x3, 5x5, 9x9), standardizes features via z-scores,
computes missing-data-safe similarity, baseline anomaly scores, weighted disaster matching,
and multi-modal fusion engine input payloads.
"""

import os
import math
import numpy as np
from typing import Dict, Any, List, Optional
from satellite.upload_processor import (
    read_multiband_geotiff, extract_patch_at_coordinate, calculate_patch_statistics,
    calculate_indices, calculate_scene_quality, compare_scene_compatibility
)


def extract_scene_features(
    scene_record: Any,
    patch_size: int = 5,
    latitude: float = 30.0668,
    longitude: float = 79.0193,
    band_mapping: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Extracts spatial patch statistics and spectral indices from an uploaded satellite scene.
    Handles GeoTIFF multiband data as well as RGB image-only demo files safely.
    """
    if isinstance(scene_record, str):
        file_path = scene_record
        is_rgb_demo = file_path.endswith((".png", ".jpg", ".jpeg"))
    else:
        file_path = scene_record.get("stored_path") or scene_record.get("file_path", "")
        is_rgb_demo = scene_record.get("quality_flag") == "IMAGE_ONLY_DEMO" or file_path.endswith((".png", ".jpg", ".jpeg"))

    features = {
        "patch_size": patch_size,
        "valid_pixel_count": patch_size * patch_size,
        "red_mean": None, "green_mean": None, "blue_mean": None,
        "nir_mean": None, "swir1_mean": None, "swir2_mean": None,
        "thermal_mean": None, "sar_l_band_db_mean": None, "sar_s_band_db_mean": None,
        "sar_vv_db_mean": None, "sar_vh_db_mean": None,
        "ndvi_mean": None, "ndvi_std": None,
        "ndwi_mean": None, "ndwi_std": None,
        "mndwi_mean": None, "mndwi_std": None,
        "nbr_mean": None, "nbr_std": None,
        "lst_mean": None, "lst_std": None,
        "soil_moisture_mean": None,
        "quality_score": 50.0,
        "raw_pixels": {}
    }

    if not file_path or not os.path.exists(file_path):
        # Return default structure if file not found
        features["quality_score"] = 30.0
        return features

    try:
        arr, meta = read_multiband_geotiff(file_path)
        patch = extract_patch_at_coordinate(arr, latitude, longitude, patch_size=patch_size)

        n_bands = patch.shape[0]

        if is_rgb_demo:
            # Ordinary RGB photo/screenshot: RGB channels available, no physical spectral indices
            r_patch = patch[0] / 255.0 if patch.max() > 1.0 else patch[0]
            g_patch = patch[1] / 255.0 if patch.ndim > 1 and patch.shape[0] > 1 and patch.max() > 1.0 else (patch[1] if patch.ndim > 1 and patch.shape[0] > 1 else r_patch)
            b_patch = patch[2] / 255.0 if patch.ndim > 2 and patch.shape[0] > 2 and patch.max() > 1.0 else (patch[2] if patch.ndim > 2 and patch.shape[0] > 2 else r_patch)

            r_stats = calculate_patch_statistics(r_patch)
            g_stats = calculate_patch_statistics(g_patch)
            b_stats = calculate_patch_statistics(b_patch)

            features["red_mean"] = r_stats["mean"]
            features["green_mean"] = g_stats["mean"]
            features["blue_mean"] = b_stats["mean"]
            features["valid_pixel_count"] = r_stats["valid_pixel_count"]
            features["quality_score"] = 40.0
            features["raw_pixels"] = {"red": r_stats["mean"], "green": g_stats["mean"], "blue": b_stats["mean"]}
            return features

        # Multiband GeoTIFF / Band mapped processing
        b_map = band_mapping or {}
        r_idx = b_map.get("red", 1) - 1
        g_idx = b_map.get("green", 2) - 1
        b_idx = b_map.get("blue", 3) - 1
        nir_idx = b_map.get("nir", 4) - 1 if n_bands >= 4 else None
        sw1_idx = b_map.get("swir1", 5) - 1 if n_bands >= 5 else None
        sw2_idx = b_map.get("swir2", 6) - 1 if n_bands >= 6 else None
        th_idx = b_map.get("thermal", 7) - 1 if n_bands >= 7 else None

        def safe_stats(idx):
            if idx is not None and 0 <= idx < n_bands:
                band_p = patch[idx]
                # Scale reflectivity to 0.0-1.0 if uint8/uint16
                if band_p.max() > 10.0:
                    band_p = band_p / (10000.0 if band_p.max() > 255.0 else 255.0)
                return calculate_patch_statistics(band_p)
            return {"mean": None, "std": None, "median": None, "valid_pixel_count": 0}

        r_st = safe_stats(r_idx)
        g_st = safe_stats(g_idx)
        b_st = safe_stats(b_idx)
        nir_st = safe_stats(nir_idx)
        sw1_st = safe_stats(sw1_idx)
        sw2_st = safe_stats(sw2_idx)
        th_st = safe_stats(th_idx)

        features["red_mean"] = r_st["mean"]
        features["green_mean"] = g_st["mean"]
        features["blue_mean"] = b_st["mean"]
        features["nir_mean"] = nir_st["mean"]
        features["swir1_mean"] = sw1_st["mean"]
        features["swir2_mean"] = sw2_st["mean"]
        features["thermal_mean"] = th_st["mean"]
        features["lst_mean"] = th_st["mean"]
        features["lst_std"] = th_st["std"]

        # SAR default placeholders if SAR bands assigned
        sar_l_idx = b_map.get("sar_l_band", 8) - 1 if n_bands >= 8 else None
        if sar_l_idx is not None and 0 <= sar_l_idx < n_bands:
            sar_st = safe_stats(sar_l_idx)
            features["sar_l_band_db_mean"] = sar_st["mean"]

        raw_p = {
            "red": r_st["mean"],
            "green": g_st["mean"],
            "blue": b_st["mean"],
            "nir": nir_st["mean"],
            "swir1": sw1_st["mean"],
            "swir2": sw2_st["mean"],
            "thermal": th_st["mean"]
        }
        features["raw_pixels"] = raw_p

        # Compute physical spectral indices strictly when required bands exist
        indices = calculate_indices(raw_p)
        features["ndvi_mean"] = indices.get("ndvi")
        features["ndwi_mean"] = indices.get("ndwi")
        features["mndwi_mean"] = indices.get("mndwi")
        features["nbr_mean"] = indices.get("nbr")

        # Standard deviation proxies for indices
        if features["ndvi_mean"] is not None:
            features["ndvi_std"] = round(abs(r_st["std"] + (nir_st["std"] or 0.0)) / 2.0, 4)
        if features["nbr_mean"] is not None:
            features["nbr_std"] = round(abs((nir_st["std"] or 0.0) + (sw2_st["std"] or 0.0)) / 2.0, 4)

        features["quality_score"] = calculate_scene_quality(scene_record, features)
        return features

    except Exception as e:
        features["quality_score"] = 30.0
        return features


def compare_features_zscore(
    historical_scene: Dict[str, Any],
    current_scene: Dict[str, Any],
    patch_size: int = 5,
    latitude: float = 30.0668,
    longitude: float = 79.0193,
    disaster_type_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compares historical and current satellite scene patch feature vectors.
    Evaluates scene compatibility, feature-wise deltas, z-score distance,
    missing-data-safe similarity %, baseline anomaly score, risk assessment,
    and returns fusion engine input payload.
    """
    import os  # Guard import
    compatibility = compare_scene_compatibility(historical_scene, current_scene)

    h_feats = historical_scene.get("features") or extract_scene_features(historical_scene, patch_size, latitude, longitude)
    c_feats = current_scene.get("features") or extract_scene_features(current_scene, patch_size, latitude, longitude)

    # Feature key list
    keys = [
        "red", "green", "blue", "nir", "swir1", "swir2", "thermal",
        "sar_l_band_db", "sar_s_band_db", "sar_vv_db", "sar_vh_db",
        "ndvi", "ndwi", "mndwi", "nbr", "lst", "soil_moisture"
    ]

    def get_val(fdict, key):
        if not isinstance(fdict, dict):
            return None
        v = fdict.get(key)
        if v is None:
            v = fdict.get(f"{key}_mean")
        if v in [None, "", "null", "None"]:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    comparison_table = []
    sq_dist_sum = 0.0
    n_common = 0

    veg_sim_sum = 0.0
    veg_count = 0
    thermal_sim_sum = 0.0
    thermal_count = 0

    for k in keys:
        h_v = get_val(h_feats, k)
        c_v = get_val(c_feats, k)

        if h_v is not None and c_v is not None:
            delta = round(c_v - h_v, 4)
            pct_change = round(((c_v - h_v) / (abs(h_v) + 1e-6)) * 100.0, 2)
            # z-score normalized distance proxy
            z_dist = abs(c_v - h_v) / (0.1 if "sar" not in k and "lst" not in k and "thermal" not in k else 5.0)
            sq_dist_sum += z_dist ** 2
            n_common += 1

            if k in ["ndvi", "nbr", "green", "nir"]:
                veg_sim_sum += max(0.0, 1.0 - z_dist)
                veg_count += 1
            if k in ["thermal", "lst"]:
                thermal_sim_sum += max(0.0, 1.0 - z_dist)
                thermal_count += 1

            comparison_table.append({
                "parameter": k,
                "historical_patch_mean": h_v,
                "current_patch_mean": c_v,
                "delta": delta,
                "percent_change": pct_change,
                "anomaly_contribution": round(z_dist, 2),
                "availability": "VALID"
            })
        else:
            comparison_table.append({
                "parameter": k,
                "historical_patch_mean": h_v,
                "current_patch_mean": c_v,
                "delta": None,
                "percent_change": None,
                "anomaly_contribution": 0.0,
                "availability": "MISSING_BAND"
            })

    # Overall similarity calculation
    if n_common > 0:
        norm_dist = math.sqrt(sq_dist_sum) / math.sqrt(n_common)
        overall_sim = math.exp(-norm_dist / math.sqrt(n_common))
        overall_sim_pct = round(overall_sim * 100.0, 2)
    else:
        overall_sim_pct = 15.0 if compatibility["level"] != "VISUAL_ONLY" else 50.0

    veg_sim_pct = round((veg_sim_sum / max(veg_count, 1)) * 100.0, 2) if veg_count > 0 else overall_sim_pct
    thermal_sim_pct = round((thermal_sim_sum / max(thermal_count, 1)) * 100.0, 2) if thermal_count > 0 else overall_sim_pct
    water_sim_pct = round(100.0 - abs(get_val(c_feats, "ndwi") or 0.0 - (get_val(h_feats, "ndwi") or 0.0)) * 100.0, 2)

    similarity_breakdown = {
        "overall_percent": overall_sim_pct,
        "spectral_percent": overall_sim_pct,
        "thermal_percent": thermal_sim_pct,
        "sar_percent": None,
        "vegetation_percent": veg_sim_pct,
        "water_percent": water_sim_pct
    }

    # Baseline Anomaly Score
    c_lst = get_val(c_feats, "lst") or get_val(c_feats, "thermal") or 25.0
    c_nbr = get_val(c_feats, "nbr") or 0.0
    c_ndvi = get_val(c_feats, "ndvi") or 0.60

    anomaly_score = round(float(np.clip((abs(0.75 - c_ndvi) * 50.0) + max(0.0, (c_lst - 30.0) * 2.0), 5.0, 95.0)), 1)
    if anomaly_score >= 75.0:
        anom_status = "CRITICAL"
    elif anomaly_score >= 50.0:
        anom_status = "HIGH"
    elif anomaly_score >= 30.0:
        anom_status = "WATCH"
    else:
        anom_status = "NORMAL"

    # Disaster Risk Assessment
    h_disaster = historical_scene.get("disaster_type") or disaster_type_hint or "Forest_Fire"
    if overall_sim_pct > 60.0 and h_disaster != "None":
        leading_disaster = h_disaster
    elif c_lst > 45.0 or c_nbr < -0.2:
        leading_disaster = "Forest_Fire"
    elif (get_val(c_feats, "ndwi") or 0.0) > 0.4:
        leading_disaster = "Flood"
    else:
        leading_disaster = "None"

    ver_status = historical_scene.get("verification_status", "UPLOADED_UNVERIFIED")
    h_qual = float(historical_scene.get("quality_score", 50.0) if hasattr(historical_scene, "get") else 50.0)
    c_qual = float(current_scene.get("quality_score", 50.0) if hasattr(current_scene, "get") else 50.0)
    data_quality_score = round((h_qual + c_qual) / 2.0, 1)

    # Scientific explanation
    if compatibility["level"] == "VISUAL_ONLY":
        exp = (
            f"Comparison between '{historical_scene.get('original_filename', 'Historical')}' and '{current_scene.get('original_filename', 'Current')}' "
            f"is VISUAL-ONLY because ordinary RGB image format was uploaded without physical spectral bands. "
            f"Disaster risk estimate relies on visual pattern similarity ({overall_sim_pct}%)."
        )
    elif leading_disaster != "None":
        exp = (
            f"Uploaded current scene shows {overall_sim_pct}% spectral similarity to historical {leading_disaster.replace('_', ' ')} scene "
            f"('{historical_scene.get('event_id', 'Historical Scene')}'). "
            f"Baseline anomaly score is {anomaly_score}% ({anom_status}). Ground sensor telemetry or field survey is required before issuing emergency warnings."
        )
    else:
        exp = (
            "Normal baseline spectral profile detected across uploaded current and historical satellite scenes. "
            f"Baseline anomaly score remains low at {anomaly_score}%."
        )

    risk_assessment = {
        "leading_disaster_pattern": leading_disaster,
        "historical_evidence_score": round(overall_sim_pct / 100.0, 4),
        "requires_ground_confirmation": True,
        "requires_human_review": True
    }

    fusion_input = {
        "historical_similarity_score": round(overall_sim_pct / 100.0, 4),
        "anomaly_score": anomaly_score,
        "data_quality_score": data_quality_score,
        "verification_status": ver_status,
        "compatibility_level": compatibility["level"]
    }

    return {
        "status": "success",
        "compatibility": compatibility,
        "evaluation": compatibility,
        "historical_scene": historical_scene,
        "current_scene": current_scene,
        "historical_patch": h_feats,
        "current_patch": c_feats,
        "feature_comparison": comparison_table,
        "feature_deltas": {item["parameter"]: item for item in comparison_table},
        "similarity": similarity_breakdown,
        "similarity_distance_percent": round(100.0 - overall_sim_pct, 2),
        "anomaly": {
            "score_percent": anomaly_score,
            "status": anom_status,
            "feature_contributions": {}
        },
        "anomaly_score_percent": anomaly_score,
        "leading_disaster_pattern": leading_disaster,
        "risk_assessment": risk_assessment,
        "fusion_input": fusion_input,
        "explanation": exp,
        "scientific_explanation": exp
    }
