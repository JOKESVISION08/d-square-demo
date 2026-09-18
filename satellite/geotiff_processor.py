"""
GeoTIFF Preprocessing & Multi-Spectral Image Generator
Handles 4-band satellite raster imagery (Red, Green, Blue, Near-Infrared),
bounding box extraction, ROI averaging, and normalization for deep learning input.
"""

import numpy as np
from PIL import Image
import os
from typing import Dict, Tuple, Any

class GeoTIFFProcessor:
    """
    Processes GeoTIFF multi-spectral satellite imagery.
    Synthesizes and handles 4-band imagery (R, G, B, NIR) at 256x256 resolution.
    """

    LAND_COVER_CLASSES = [
        "Forest",
        "Water",
        "Urban",
        "Agricultural",
        "Burnt_Scar",
        "Flood"
    ]

    def __init__(self, target_size: Tuple[int, int] = (256, 256)):
        self.target_size = target_size

    def generate_synthetic_satellite_image(self, land_cover_type: str = "Forest") -> np.ndarray:
        """
        Generates a synthetic 256x256x4 numpy array representing (Red, Green, Blue, NIR) bands.
        Values are float32 scaled [0.0, 1.0].
        """
        h, w = self.target_size
        image = np.zeros((h, w, 4), dtype=np.float32)

        # Base noise
        base_noise = np.random.normal(0.5, 0.05, (h, w))

        if land_cover_type == "Forest":
            # High NIR (Band 4), Moderate Green (Band 2), Low Red/Blue
            image[:, :, 0] = np.clip(0.1 + base_noise * 0.1, 0, 1)  # Red
            image[:, :, 1] = np.clip(0.4 + base_noise * 0.2, 0, 1)  # Green
            image[:, :, 2] = np.clip(0.1 + base_noise * 0.1, 0, 1)  # Blue
            image[:, :, 3] = np.clip(0.8 + base_noise * 0.15, 0, 1) # NIR

        elif land_cover_type == "Burnt_Scar":
            # Low NIR, High Red/SWIR, dark ash signatures
            image[:, :, 0] = np.clip(0.6 + base_noise * 0.2, 0, 1)  # Red
            image[:, :, 1] = np.clip(0.2 + base_noise * 0.1, 0, 1)  # Green
            image[:, :, 2] = np.clip(0.15 + base_noise * 0.1, 0, 1) # Blue
            image[:, :, 3] = np.clip(0.1 + base_noise * 0.1, 0, 1)  # Low NIR

        elif land_cover_type == "Flood" or land_cover_type == "Water":
            # High Blue, Low Red, Very Low NIR (Water absorbs NIR heavily)
            image[:, :, 0] = np.clip(0.1 + base_noise * 0.1, 0, 1)  # Red
            image[:, :, 1] = np.clip(0.3 + base_noise * 0.15, 0, 1) # Green
            image[:, :, 2] = np.clip(0.7 + base_noise * 0.2, 0, 1)  # Blue
            image[:, :, 3] = np.clip(0.05 + base_noise * 0.05, 0, 1) # Absorbed NIR

        elif land_cover_type == "Urban":
            # Balanced reflective concrete/asphalt across RGB
            image[:, :, 0] = np.clip(0.5 + base_noise * 0.15, 0, 1)
            image[:, :, 1] = np.clip(0.5 + base_noise * 0.15, 0, 1)
            image[:, :, 2] = np.clip(0.55 + base_noise * 0.15, 0, 1)
            image[:, :, 3] = np.clip(0.3 + base_noise * 0.1, 0, 1)

        else: # Agricultural
            image[:, :, 0] = np.clip(0.3 + base_noise * 0.1, 0, 1)
            image[:, :, 1] = np.clip(0.6 + base_noise * 0.15, 0, 1)
            image[:, :, 2] = np.clip(0.2 + base_noise * 0.1, 0, 1)
            image[:, :, 3] = np.clip(0.65 + base_noise * 0.15, 0, 1)

        return image

    def compute_spectral_indices(self, image_4band: np.ndarray) -> Dict[str, float]:
        """
        Computes NDVI and NDWI from 4-band image array.
        NDVI = (NIR - Red) / (NIR + Red)
        NDWI = (Green - NIR) / (Green + NIR)
        """
        red = image_4band[:, :, 0]
        green = image_4band[:, :, 1]
        nir = image_4band[:, :, 3]

        eps = 1e-6
        ndvi_map = (nir - red) / (nir + red + eps)
        ndwi_map = (green - nir) / (green + nir + eps)

        avg_ndvi = float(np.mean(ndvi_map))
        avg_ndwi = float(np.mean(ndwi_map))

        return {
            "avg_ndvi": round(avg_ndvi, 4),
            "avg_ndwi": round(avg_ndwi, 4),
            "max_ndvi": round(float(np.max(ndvi_map)), 4),
            "min_ndvi": round(float(np.min(ndvi_map)), 4),
        }

    def compute_6band_spectral_indices(self, image_6band: np.ndarray) -> Dict[str, float]:
        """
        Computes NDVI, NDWI, NBR, and LST from 6-band image array:
        [Red, Green, Blue, NIR, SWIR, Thermal]
        """
        red = image_6band[:, :, 0]
        green = image_6band[:, :, 1]
        blue = image_6band[:, :, 2]
        nir = image_6band[:, :, 3]
        swir = image_6band[:, :, 4]
        thermal = image_6band[:, :, 5]

        eps = 1e-6
        ndvi_map = (nir - red) / (nir + red + eps)
        ndwi_map = (green - nir) / (green + nir + eps)
        nbr_map = (nir - swir) / (nir + swir + eps)

        return {
            "avg_ndvi": round(float(np.mean(ndvi_map)), 4),
            "avg_ndwi": round(float(np.mean(ndwi_map)), 4),
            "avg_nbr": round(float(np.mean(nbr_map)), 4),
            "avg_lst": round(float(np.mean(thermal * 50.0)), 1), # Scale normalized thermal to Celsius
        }

    def extract_roi_bbox(self, full_image: np.ndarray, bbox: Tuple[float, float, float, float]) -> np.ndarray:
        """
        Crops Region of Interest using bounding box percentages (ymin, xmin, ymax, xmax).
        """
        h, w, _ = full_image.shape
        ymin, xmin, ymax, xmax = bbox

        y1, y2 = int(ymin * h), int(ymax * h)
        x1, x2 = int(xmin * w), int(xmax * w)

        cropped = full_image[y1:y2, x1:x2, :]
        # Resize back to 256x256
        pil_img = Image.fromarray((cropped[:, :, :3] * 255).astype(np.uint8))
        pil_img = pil_img.resize(self.target_size)
        resized_rgb = np.array(pil_img, dtype=np.float32) / 255.0

        # Construct 4-band result
        resized_nir = np.mean(cropped[:, :, 3]) * np.ones((self.target_size[0], self.target_size[1], 1), dtype=np.float32)
        return np.concatenate([resized_rgb, resized_nir], axis=-1)
