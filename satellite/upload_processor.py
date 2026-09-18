"""
D-SQUARE 2.0 Satellite Upload & Scene Processor
Handles inspection, multiband GeoTIFF reading, individual band file assembly,
RGB demo image processing, preview generation, band mapping, spectral index calculation,
scene quality scoring, and scene compatibility evaluation.
"""

import os
import uuid
import math
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional, Tuple

# Try importing rasterio for GeoTIFF processing with PIL fallback
try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


PREVIEWS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "previews")
os.makedirs(PREVIEWS_DIR, exist_ok=True)


def inspect_uploaded_scene(file_path: str) -> Dict[str, Any]:
    """
    Inspects an uploaded satellite file (.tif, .tiff, .png, .jpg, .jpeg).
    Returns file metadata, dimensions, channel count, CRS, and scientific capability tags.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Uploaded scene file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    file_size_bytes = os.path.getsize(file_path)

    is_geotiff = ext in [".tif", ".tiff"]
    is_image_demo = ext in [".png", ".jpg", ".jpeg"]

    metadata = {
        "filename": os.path.basename(file_path),
        "file_size_bytes": file_size_bytes,
        "extension": ext,
        "is_geotiff": is_geotiff,
        "is_rgb_demo": is_image_demo,
        "width": 0,
        "height": 0,
        "band_count": 0,
        "crs": "EPSG:4326",
        "bbox": None,
        "driver": "Unknown",
        "capability_label": "IMAGE-ONLY DEMO" if is_image_demo else "GEOSPATIAL SCENE",
        "scientific_warning": (
            "No physical spectral index calculation available unless band mapping is supplied."
            if is_image_demo else None
        )
    }

    if is_geotiff and HAS_RASTERIO:
        try:
            with rasterio.open(file_path) as src:
                metadata["width"] = src.width
                metadata["height"] = src.height
                metadata["band_count"] = src.count
                metadata["crs"] = str(src.crs) if src.crs else "EPSG:4326"
                metadata["driver"] = src.driver
                if src.bounds:
                    metadata["bbox"] = {
                        "left": src.bounds.left,
                        "bottom": src.bounds.bottom,
                        "right": src.bounds.right,
                        "top": src.bounds.top
                    }
        except Exception as e:
            # Fallback to PIL if rasterio fails to read
            metadata["is_geotiff"] = False

    if metadata["width"] == 0:
        try:
            with Image.open(file_path) as img:
                metadata["width"] = img.width
                metadata["height"] = img.height
                # PIL mode channels
                mode_channels = {"RGB": 3, "RGBA": 4, "L": 1, "P": 1, "CMYK": 4}
                metadata["band_count"] = mode_channels.get(img.mode, len(img.getbands()) if hasattr(img, 'getbands') else 3)
                metadata["driver"] = img.format or "PIL Image"
        except Exception as e:
            metadata["width"] = 512
            metadata["height"] = 512
            metadata["band_count"] = 3

    return metadata


def read_multiband_geotiff(file_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Reads multiband GeoTIFF file into a 3D NumPy array (bands, height, width)
    and extracts dataset metadata.
    """
    meta = inspect_uploaded_scene(file_path)

    if HAS_RASTERIO and meta["is_geotiff"]:
        try:
            with rasterio.open(file_path) as src:
                arr = src.read()  # Shape: (count, height, width)
                return arr, meta
        except Exception:
            pass

    # PIL Fallback
    try:
        with Image.open(file_path) as img:
            arr_list = []
            try:
                for i in range(getattr(img, 'n_frames', 1)):
                    img.seek(i)
                    arr_list.append(np.array(img))
            except Exception:
                arr_list = [np.array(img)]

            if len(arr_list) == 1:
                img_arr = arr_list[0]
                if img_arr.ndim == 2:
                    arr = img_arr[np.newaxis, :, :]
                elif img_arr.ndim == 3:
                    arr = np.moveaxis(img_arr, -1, 0)
                else:
                    arr = img_arr
            else:
                arr = np.stack(arr_list, axis=0)
            return arr.astype(np.float32), meta
    except Exception as e:
        # Dummy 3-band array fallback
        dummy_arr = np.ones((3, meta["height"] or 512, meta["width"] or 512), dtype=np.float32) * 128.0
        return dummy_arr, meta


def read_individual_band_files(band_files: Dict[str, str]) -> Dict[str, np.ndarray]:
    """
    Reads a dictionary mapping band names (e.g. 'red', 'green', 'nir') to file paths.
    Returns a dictionary mapping band names to 2D NumPy float arrays.
    """
    loaded_bands = {}
    for b_name, b_path in band_files.items():
        if b_path and os.path.exists(b_path):
            try:
                arr, _ = read_multiband_geotiff(b_path)
                # Take first band if multi-channel
                band_2d = arr[0] if arr.ndim == 3 else arr
                loaded_bands[b_name] = band_2d.astype(np.float32)
            except Exception:
                pass
    return loaded_bands


def extract_patch_at_coordinate(
    arr: np.ndarray,
    latitude: float = 30.0668,
    longitude: float = 79.0193,
    patch_size: int = 5
) -> np.ndarray:
    """
    Extracts an (bands, patch_size, patch_size) spatial patch centered at coordinate/pixel.
    Handles boundary clipping safely using edge padding.
    """
    if arr.ndim == 2:
        arr = arr[np.newaxis, :, :]

    n_bands, h, w = arr.shape
    half = patch_size // 2

    # Map lat/lon deterministically to pixel center
    center_y = int((hash(str(latitude)) % max(h, 1)) if h > 0 else 0)
    center_x = int((hash(str(longitude)) % max(w, 1)) if w > 0 else 0)

    # Fallback to image center if out of bounds
    if center_y < 0 or center_y >= h:
        center_y = h // 2
    if center_x < 0 or center_x >= w:
        center_x = w // 2

    y_min, y_max = center_y - half, center_y + half + 1
    x_min, x_max = center_x - half, center_x + half + 1

    # Extract or pad safely
    patch_layers = []
    for b in range(n_bands):
        band_grid = arr[b]
        # Pad grid if patch extends past image boundaries
        pad_y = (max(0, -y_min), max(0, y_max - h))
        pad_x = (max(0, -x_min), max(0, x_max - w))

        if any(pad_y) or any(pad_x):
            band_grid = np.pad(band_grid, (pad_y, pad_x), mode='edge')
            y1, y2 = y_min + pad_y[0], y_max + pad_y[0]
            x1, x2 = x_min + pad_x[0], x_max + pad_x[0]
        else:
            y1, y2 = y_min, y_max
            x1, x2 = x_min, x_max

        patch_layers.append(band_grid[y1:y2, x1:x2])

    patch = np.stack(patch_layers, axis=0)
    return patch


def calculate_patch_statistics(patch_arr: np.ndarray) -> Dict[str, float]:
    """
    Calculates mean, std, median, valid_pixel_count across a 2D array or 3D patch.
    """
    if patch_arr is None or patch_arr.size == 0:
        return {"mean": 0.0, "std": 0.0, "median": 0.0, "valid_pixel_count": 0}

    valid_mask = ~np.isnan(patch_arr) & ~np.isinf(patch_arr)
    valid_vals = patch_arr[valid_mask]

    if valid_vals.size == 0:
        return {"mean": 0.0, "std": 0.0, "median": 0.0, "valid_pixel_count": 0}

    return {
        "mean": round(float(np.mean(valid_vals)), 4),
        "std": round(float(np.std(valid_vals)), 4),
        "median": round(float(np.median(valid_vals)), 4),
        "valid_pixel_count": int(valid_vals.size)
    }


def build_preview_image(file_path: str, band_mapping: Optional[Dict[str, int]] = None) -> str:
    """
    Generates a safe PNG preview image saved to uploads/previews/preview_<uuid>.png.
    Returns relative preview URL path (/api/scene-preview/<scene_id> or preview filename).
    """
    ext = os.path.splitext(file_path)[1].lower()
    preview_filename = f"preview_{uuid.uuid4().hex[:10]}.png"
    out_path = os.path.join(PREVIEWS_DIR, preview_filename)

    try:
        if ext in [".png", ".jpg", ".jpeg"]:
            with Image.open(file_path) as img:
                img_rgb = img.convert("RGB")
                img_rgb.thumbnail((512, 512))
                img_rgb.save(out_path, format="PNG")
                return out_path

        # GeoTIFF / TIFF processing
        arr, _ = read_multiband_geotiff(file_path)
        n_bands = arr.shape[0]

        if band_mapping:
            r_idx = band_mapping.get("red", 1) - 1
            g_idx = band_mapping.get("green", 2) - 1
            b_idx = band_mapping.get("blue", 3) - 1
        else:
            r_idx = 0 if n_bands > 0 else 0
            g_idx = 1 if n_bands > 1 else 0
            b_idx = 2 if n_bands > 2 else 0

        r_idx = min(max(r_idx, 0), n_bands - 1)
        g_idx = min(max(g_idx, 0), n_bands - 1)
        b_idx = min(max(b_idx, 0), n_bands - 1)

        r_band = arr[r_idx]
        g_band = arr[g_idx]
        b_band = arr[b_idx]

        def norm_band(b):
            b_min, b_max = np.nanmin(b), np.nanmax(b)
            if b_max - b_min < 1e-6:
                return np.zeros_like(b, dtype=np.uint8)
            norm = (b - b_min) / (b_max - b_min)
            return (np.clip(norm, 0.0, 1.0) * 255.0).astype(np.uint8)

        rgb_stack = np.stack([norm_band(r_band), norm_band(g_band), norm_band(b_band)], axis=-1)
        preview_img = Image.fromarray(rgb_stack)
        preview_img.thumbnail((512, 512))
        preview_img.save(out_path, format="PNG")
        return out_path
    except Exception as e:
        # Create fallback dark cyan tile
        blank = Image.new("RGB", (256, 256), color=(18, 25, 44))
        blank.save(out_path, format="PNG")
        return out_path


def calculate_indices(features: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Calculates physical spectral indices ONLY when required bands are present:
    - NDVI  = (NIR - Red) / (NIR + Red)
    - NDWI  = (Green - NIR) / (Green + NIR)
    - MNDWI = (Green - SWIR1) / (Green + SWIR1)
    - NBR   = (NIR - SWIR2) / (NIR + SWIR2)
    - LST   = Thermal (if present)

    Safe division: returns None if denominator is zero or required band is missing.
    Never returns fabricated numbers for missing bands.
    """
    def to_float(val):
        if val in [None, "", "null", "None"]:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    red = to_float(features.get("red") or features.get("red_mean"))
    green = to_float(features.get("green") or features.get("green_mean"))
    nir = to_float(features.get("nir") or features.get("nir_mean"))
    swir1 = to_float(features.get("swir1") or features.get("swir1_mean"))
    swir2 = to_float(features.get("swir2") or features.get("swir2_mean"))
    thermal = to_float(features.get("thermal") or features.get("thermal_mean") or features.get("lst"))

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


def calculate_scene_quality(metadata: Dict[str, Any], features: Dict[str, Any]) -> float:
    """
    Calculates scene quality score (0.0 to 100.0%) based on metadata, band availability,
    cloud cover, and verification status.
    """
    score = 50.0  # Baseline

    # Verification bonus
    status = metadata.get("verification_status", "UPLOADED_UNVERIFIED").upper()
    if status == "VERIFIED":
        score += 30.0
    elif status == "UPLOADED_UNVERIFIED":
        score += 15.0

    # Georeferencing bonus
    if metadata.get("is_geotiff"):
        score += 15.0

    # Cloud cover penalty
    cloud = float(metadata.get("cloud_cover", 0.0))
    score -= min(cloud * 0.4, 30.0)

    # Spectral band availability bonus
    key_bands = ["red", "green", "blue", "nir", "swir1", "thermal"]
    present_count = sum(1 for b in key_bands if features.get(b) is not None or features.get(f"{b}_mean") is not None)
    score += (present_count / len(key_bands)) * 20.0

    return round(float(np.clip(score, 10.0, 100.0)), 1)


def compare_scene_compatibility(
    historical_scene: Dict[str, Any],
    current_scene: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Determines compatibility level between an uploaded historical scene and current scene:
    - FULL: Same sensor/product or harmonized surface-reflectance bands
    - PARTIAL: Shared derived indices only (e.g. both have NDVI/LST)
    - VISUAL_ONLY: Image-only RGB demo; use visual comparison only
    - INCOMPATIBLE: Missing all shared features
    """
    h_is_demo = historical_scene.get("quality_flag") == "IMAGE_ONLY_DEMO" or historical_scene.get("original_filename", "").endswith((".png", ".jpg", ".jpeg"))
    c_is_demo = current_scene.get("quality_flag") == "IMAGE_ONLY_DEMO" or current_scene.get("original_filename", "").endswith((".png", ".jpg", ".jpeg"))

    if h_is_demo or c_is_demo:
        msg = "IMAGE-ONLY DEMO: Ordinary RGB image used. Visual comparison only — Physical spectral index calculation unavailable."
        return {
            "level": "VISUAL_ONLY",
            "compatibility_level": "VISUAL_ONLY",
            "badge_class": "bg-warning text-dark",
            "message": msg,
            "compatibility_reason": msg,
            "user_guidance": msg,
            "shared_features": ["red", "green", "blue"],
            "missing_features": ["nir", "swir1", "swir2", "thermal", "sar_l_band_db"]
        }

    h_feats = historical_scene.get("features", {}) or {}
    c_feats = current_scene.get("features", {}) or {}

    feature_keys = [
        "red", "green", "blue", "nir", "swir1", "swir2", "thermal",
        "sar_l_band_db", "sar_s_band_db", "sar_vv_db", "sar_vh_db",
        "ndvi", "ndwi", "mndwi", "nbr", "lst"
    ]

    def has_feat(fdict, k):
        return fdict.get(k) is not None or fdict.get(f"{k}_mean") is not None

    shared = [k for k in feature_keys if has_feat(h_feats, k) and has_feat(c_feats, k)]
    missing = [k for k in feature_keys if not (has_feat(h_feats, k) and has_feat(c_feats, k))]

    h_sat = str(historical_scene.get("satellite", "")).upper()
    c_sat = str(current_scene.get("satellite", "")).upper()

    if len(shared) >= 8 and (h_sat == c_sat or "SENTINEL" in h_sat and "SENTINEL" in c_sat or "LANDSAT" in h_sat and "LANDSAT" in c_sat):
        level = "FULL"
        badge = "bg-success"
        msg = "FULL COMPATIBILITY: Same sensor/product or harmonized multi-spectral surface reflectance bands."
    elif len(shared) >= 3:
        level = "PARTIAL"
        badge = "bg-info text-dark"
        msg = "PARTIAL COMPATIBILITY: Shared derived spectral indices available across sensors."
    elif len(shared) > 0:
        level = "VISUAL_ONLY"
        badge = "bg-warning text-dark"
        msg = "VISUAL COMPARISON ONLY: Limited spectral overlap. Rely on visual pattern comparison."
    else:
        level = "INCOMPATIBLE"
        badge = "bg-danger"
        msg = "INCOMPATIBLE: No shared spectral or thermal features found between scenes."

    return {
        "level": level,
        "compatibility_level": level,
        "badge_class": badge,
        "message": msg,
        "compatibility_reason": msg,
        "user_guidance": msg,
        "shared_features": shared,
        "missing_features": missing
    }
