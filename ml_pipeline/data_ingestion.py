"""
D-SQUARE 2.0 Multi-Fusion ML Pipeline: Data Ingestion & ETL
Ingests, validates, cleans, and structures multi-modal historical disaster records,
IoT time-series logs, satellite spectral data, and weather station telemetry.
"""

import os
import json
from typing import Dict, Any, List, Tuple
from ml_pipeline.dataset_generator import DisasterDatasetGenerator, DATA_DIR


class DataIngestionPipeline:
    """
    ETL Data Ingestion Pipeline loading historical disaster datasets (2005-2026),
    validating data quality, and structuring features for machine learning training.
    """

    def __init__(self):
        self.dataset_file = os.path.join(DATA_DIR, "historical_disasters_2005_2026.json")
        self.generator = DisasterDatasetGenerator()

    def load_or_create_dataset(self, num_records: int = 1500) -> List[Dict[str, Any]]:
        """Loads dataset file or generates fresh synthetic historical records if absent."""
        if not os.path.exists(self.dataset_file):
            print("Dataset file not found. Generating fresh historical disaster dataset...")
            return self.generator.generate_historical_dataset(num_records=num_records)

        try:
            with open(self.dataset_file, "r") as f:
                data = json.load(f)
            print(f"Loaded {len(data)} historical disaster records from {self.dataset_file}.")
            return data
        except Exception as e:
            print(f"Error reading dataset file: {e}. Regenerating...")
            return self.generator.generate_historical_dataset(num_records=num_records)

    def validate_and_clean(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Performs data quality checks, filtering invalid or incomplete records."""
        cleaned = []
        for r in raw_records:
            if not r.get("disaster_type") or not r.get("severity"):
                continue
            telemetry = r.get("telemetry", {})
            if "water_level_m" not in telemetry or "rainfall_mm_24h" not in telemetry:
                continue

            # Ensure valid numerical bounds
            telemetry["water_level_m"] = max(0.0, float(telemetry.get("water_level_m", 0.0)))
            telemetry["rainfall_mm_24h"] = max(0.0, float(telemetry.get("rainfall_mm_24h", 0.0)))
            telemetry["soil_moisture_percent"] = max(0.0, min(100.0, float(telemetry.get("soil_moisture_percent", 40.0))))
            telemetry["temperature_c"] = max(-20.0, min(80.0, float(telemetry.get("temperature_c", 25.0))))
            telemetry["humidity_percent"] = max(0.0, min(100.0, float(telemetry.get("humidity_percent", 50.0))))

            r["telemetry"] = telemetry
            cleaned.append(r)

        return cleaned

    def train_val_split(
        self,
        records: List[Dict[str, Any]],
        val_ratio: float = 0.20
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Splits cleaned records into training and validation sets."""
        total = len(records)
        val_size = int(total * val_ratio)
        train_records = records[:-val_size]
        val_records = records[-val_size:]
        return train_records, val_records
