"""
Historical Satellite Data Import CLI Pipeline for D-SQUARE 2.0
Imports CSV or JSON historical satellite patch samples into SQLite database (satellite_pixel_samples).

Usage:
  python satellite/import_historical_samples.py --file data/historical_samples_template.csv
"""

import os
import sys
import argparse
import csv
import json
import numpy as np
from typing import Dict, Any, List, Tuple

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_satellite_pixel_sample, init_db


REQUIRED_COLUMNS = [
    "event_id", "disaster_type", "acquisition_date", "satellite", "product", "latitude", "longitude"
]

VALID_DISASTERS = ["Forest_Fire", "Flood", "Landslide", "Air_Pollution", "None", "Normal"]


def calculate_indices(row: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates NDVI, NDWI, MNDWI, NBR, LST safely from band reflectance."""
    def to_float(val):
        try:
            return float(val) if val not in [None, "", "null", "None"] else None
        except Exception:
            return None

    r = to_float(row.get("red"))
    g = to_float(row.get("green"))
    b = to_float(row.get("blue"))
    nir = to_float(row.get("nir"))
    sw1 = to_float(row.get("swir1"))
    sw2 = to_float(row.get("swir2"))
    therm = to_float(row.get("thermal"))
    
    eps = 1e-6

    # NDVI
    ndvi = to_float(row.get("ndvi"))
    if ndvi is None and nir is not None and r is not None:
        denom = nir + r
        if abs(denom) > eps:
            ndvi = round((nir - r) / denom, 4)
            
    # NDWI
    ndwi = to_float(row.get("ndwi"))
    if ndwi is None and g is not None and nir is not None:
        denom = g + nir
        if abs(denom) > eps:
            ndwi = round((g - nir) / denom, 4)

    # MNDWI
    mndwi = to_float(row.get("mndwi"))
    if mndwi is None and g is not None and sw1 is not None:
        denom = g + sw1
        if abs(denom) > eps:
            mndwi = round((g - sw1) / denom, 4)

    # NBR
    nbr = to_float(row.get("nbr"))
    if nbr is None and nir is not None and sw2 is not None:
        denom = nir + sw2
        if abs(denom) > eps:
            nbr = round((nir - sw2) / denom, 4)

    # LST
    lst = to_float(row.get("lst"))
    if lst is None and therm is not None:
        lst = therm

    # Calculated spatial patch statistics defaults if omitted
    patch_mean_ndvi = to_float(row.get("patch_mean_ndvi")) or ndvi
    patch_std_ndvi = to_float(row.get("patch_std_ndvi")) or (0.02 if ndvi is not None else None)
    patch_median_ndvi = to_float(row.get("patch_median_ndvi")) or ndvi

    patch_mean_nbr = to_float(row.get("patch_mean_nbr")) or nbr
    patch_std_nbr = to_float(row.get("patch_std_nbr")) or (0.02 if nbr is not None else None)
    patch_median_nbr = to_float(row.get("patch_median_nbr")) or nbr

    patch_mean_lst = to_float(row.get("patch_mean_lst")) or lst
    patch_std_lst = to_float(row.get("patch_std_lst")) or (0.5 if lst is not None else None)

    return {
        "ndvi": ndvi, "ndwi": ndwi, "mndwi": mndwi, "nbr": nbr, "lst": lst,
        "patch_mean_ndvi": patch_mean_ndvi, "patch_std_ndvi": patch_std_ndvi, "patch_median_ndvi": patch_median_ndvi,
        "patch_mean_nbr": patch_mean_nbr, "patch_std_nbr": patch_std_nbr, "patch_median_nbr": patch_median_nbr,
        "patch_mean_lst": patch_mean_lst, "patch_std_lst": patch_std_lst
    }


def validate_row(row: Dict[str, Any], idx: int) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates row fields, numerical ranges, and required columns."""
    for col in REQUIRED_COLUMNS:
        if not row.get(col):
            return False, f"Row {idx}: Missing required column '{col}'", None

    try:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            return False, f"Row {idx}: Invalid coordinates (lat: {lat}, lon: {lon})", None
    except Exception as e:
        return False, f"Row {idx}: Coordinate parse error ({e})", None

    disaster = row["disaster_type"].strip()
    if disaster == "Normal":
        disaster = "None"
    if disaster not in VALID_DISASTERS:
        return False, f"Row {idx}: Unknown disaster type '{disaster}'", None

    # Calculate indices safely
    computed = calculate_indices(row)
    
    def parse_float(val):
        try:
            return float(val) if val not in [None, "", "null", "None"] else None
        except Exception:
            return None

    def parse_int(val, default=None):
        try:
            return int(val) if val not in [None, "", "null", "None"] else default
        except Exception:
            return default

    ver_status = str(row.get("verification_status", "DEMO")).strip().upper()
    if ver_status not in ["VERIFIED", "DEMO"]:
        ver_status = "DEMO"

    sample = {
        "event_id": str(row["event_id"]).strip(),
        "disaster_type": disaster,
        "acquisition_date": str(row["acquisition_date"]).strip(),
        "satellite": str(row["satellite"]).strip(),
        "product": str(row["product"]).strip(),
        "latitude": lat,
        "longitude": lon,
        "patch_size": parse_int(row.get("patch_size"), 5),
        "red": parse_float(row.get("red")),
        "green": parse_float(row.get("green")),
        "blue": parse_float(row.get("blue")),
        "nir": parse_float(row.get("nir")),
        "swir1": parse_float(row.get("swir1")),
        "swir2": parse_float(row.get("swir2")),
        "thermal": parse_float(row.get("thermal")),
        "sar_l_band_db": parse_float(row.get("sar_l_band_db")),
        "sar_s_band_db": parse_float(row.get("sar_s_band_db")),
        "sar_vv_db": parse_float(row.get("sar_vv_db")),
        "sar_vh_db": parse_float(row.get("sar_vh_db")),
        "sar_coherence": parse_float(row.get("sar_coherence")),
        "ground_deformation_mm": parse_float(row.get("ground_deformation_mm")),
        "ndvi": computed["ndvi"],
        "ndwi": computed["ndwi"],
        "mndwi": computed["mndwi"],
        "nbr": computed["nbr"],
        "lst": computed["lst"],
        "soil_moisture": parse_float(row.get("soil_moisture")),
        "rainfall": parse_float(row.get("rainfall")),
        "slope": parse_float(row.get("slope")),
        "patch_mean_ndvi": computed["patch_mean_ndvi"],
        "patch_std_ndvi": computed["patch_std_ndvi"],
        "patch_median_ndvi": computed["patch_median_ndvi"],
        "patch_mean_nbr": computed["patch_mean_nbr"],
        "patch_std_nbr": computed["patch_std_nbr"],
        "patch_median_nbr": computed["patch_median_nbr"],
        "patch_mean_lst": computed["patch_mean_lst"],
        "patch_std_lst": computed["patch_std_lst"],
        "valid_pixel_count": parse_int(row.get("valid_pixel_count"), 25),
        "cloud_cover": parse_float(row.get("cloud_cover")),
        "label_source": str(row.get("label_source", "Imported User File")).strip(),
        "source_url": str(row.get("source_url", "")).strip() or None,
        "verification_status": ver_status,
        "quality_flag": str(row.get("quality_flag", "USER_IMPORTED")).strip()
    }
    return True, None, sample


def import_file(file_path: str) -> Dict[str, Any]:
    """Imports CSV or JSON file into satellite_pixel_samples table."""
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}

    init_db()

    raw_records = []
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".csv":
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                raw_records = list(reader)
        elif ext in [".json", ".geojson"]:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    raw_records = data
                elif isinstance(data, dict) and "features" in data:
                    for feat in data["features"]:
                        props = feat.get("properties", {})
                        if "geometry" in feat and feat["geometry"].get("coordinates"):
                            coords = feat["geometry"]["coordinates"]
                            props["longitude"] = coords[0]
                            props["latitude"] = coords[1]
                        raw_records.append(props)
                elif isinstance(data, dict) and "records" in data:
                    raw_records = data["records"]
                elif isinstance(data, dict):
                    raw_records = [data]
        else:
            return {"status": "error", "message": f"Unsupported file extension: {ext}"}
    except Exception as e:
        return {"status": "error", "message": f"Error reading file: {e}"}

    total_count = len(raw_records)
    accepted_count = 0
    rejected_count = 0
    verified_count = 0
    demo_count = 0
    errors = []

    for idx, row in enumerate(raw_records, start=1):
        valid, err, sample = validate_row(row, idx)
        if valid and sample:
            try:
                save_satellite_pixel_sample(sample)
                accepted_count += 1
                if sample["verification_status"] == "VERIFIED":
                    verified_count += 1
                else:
                    demo_count += 1
            except Exception as insert_err:
                rejected_count += 1
                errors.append(f"Row {idx}: DB insert error ({insert_err})")
        else:
            rejected_count += 1
            if err:
                errors.append(err)

    report = {
        "status": "success",
        "file_path": file_path,
        "total_rows": total_count,
        "accepted_rows": accepted_count,
        "rejected_rows": rejected_count,
        "verified_rows": verified_count,
        "demo_rows": demo_count,
        "errors": errors[:20]  # Limit returned errors snippet
    }
    return report


def print_report(report: Dict[str, Any]):
    print("==================================================")
    print("  HISTORICAL SATELLITE DATA IMPORT REPORT")
    print("==================================================")
    if report.get("status") == "error":
        print(f"[ERROR] {report.get('message')}")
        return
        
    print(f" File Path      : {report['file_path']}")
    print(f" Total Rows     : {report['total_rows']}")
    print(f" Accepted Rows  : {report['accepted_rows']}")
    print(f" Rejected Rows  : {report['rejected_rows']}")
    print(f" Verified Rows  : {report['verified_rows']}")
    print(f" Demo Rows      : {report['demo_rows']}")
    print("--------------------------------------------------")
    
    if report.get("errors"):
        print(" Sample Errors:")
        for err in report["errors"]:
            print(f"  - {err}")
    else:
        print(" Clean import with 0 validation errors.")
    print("==================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import historical satellite samples into D-SQUARE 2.0 SQLite database.")
    parser.add_argument("--file", type=str, required=True, help="Path to CSV or JSON file")
    args = parser.parse_args()

    rep = import_file(args.file)
    print_report(rep)
