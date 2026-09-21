"""
D-SQUARE 2.0 Satellite Upload & Scene Processor
Handles inspection, GeoTIFF processing, and spectral index calculations.
"""

import os
import uuid
import math
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional, Tuple

import tempfile

def get_writable_previews_dir():
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "previews")
    try:
        os.makedirs(base, exist_ok=True)
        test_file = os.path.join(base, ".write_test")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return base
    except (OSError, PermissionError):
        tmp = os.path.join(tempfile.gettempdir(), "dsquare", "uploads", "previews")
        os.makedirs(tmp, exist_ok=True)
        return tmp

PREVIEWS_DIR = get_writable_previews_dir()


def inspect_uploaded_scene(file_path: str) -> Dict[str, Any]:
    """Inspects uploaded image file and returns dimension and channels."""
    ext = os.path.splitext(file_path)[1].lower()
    img = Image.open(file_path)
    width, height = img.size
    mode = img.mode
    bands = len(img.getbands())

    return {
        "filename": os.path.basename(file_path),
        "width": width,
        "height": height,
        "bands_count": bands,
        "format": ext,
        "demo_mode": "IMAGE_ONLY" if bands <= 3 else "MULTISPECTRAL"
    }
