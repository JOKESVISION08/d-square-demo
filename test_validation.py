"""
D-SQUARE 2.0 Comprehensive Testing & Validation Suite
Evaluates system metrics across 100 test samples (20 per disaster category).
Calculates Overall Accuracy, Precision, Recall, F1-Score, False Positive Rate (FPR),
False Negative Rate (FNR), and Latency benchmarks.
"""

import os
import time
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from models.fusion_engine import MultiModalFusionEngine

def generate_validation_dataset(samples_per_class: int = 20):
    """
    Generates 100 balanced test samples across 5 disaster categories:
    - Forest_Fire (20)
    - Flood (20)
    - Landslide (20)
    - Air_Pollution (20)
    - None / Normal (20)
    """
    dataset = []
    categories = ["Forest_Fire", "Flood", "Landslide", "Air_Pollution", "None"]

    for cat in categories:
        for _ in range(samples_per_class):
            if cat == "Forest_Fire":
                sat_data = {"red": 0.65, "green": 0.15, "blue": 0.10, "nir": 0.10} # Burnt scar / fire
                sensor_data = {"temperature": 52.0, "humidity": 14.0, "smoke": 850.0, "soil_moisture": 5.0, "water_level": 2.0, "flame": 1.0, "vibration": 0.5}
                cam_data = {"mean_r": 0.85, "mean_g": 0.15, "mean_b": 0.10, "flicker": 0.8, "smoke_haziness": 0.7}
            elif cat == "Flood":
                sat_data = {"red": 0.10, "green": 0.35, "blue": 0.80, "nir": 0.05} # Flood water coverage
                sensor_data = {"temperature": 21.0, "humidity": 94.0, "smoke": 180.0, "soil_moisture": 96.0, "water_level": 75.0, "flame": 0.0, "vibration": 0.8}
                cam_data = {"mean_r": 0.15, "mean_g": 0.45, "mean_b": 0.82, "flicker": 0.3, "smoke_haziness": 0.1}
            elif cat == "Landslide":
                sat_data = {"red": 0.25, "green": 0.35, "blue": 0.20, "nir": 0.35} # Vegetative loss / soil slide
                sensor_data = {"temperature": 20.0, "humidity": 88.0, "smoke": 220.0, "soil_moisture": 92.0, "water_level": 25.0, "flame": 0.0, "vibration": 14.5}
                cam_data = {"mean_r": 0.35, "mean_g": 0.35, "mean_b": 0.30, "flicker": 0.5, "smoke_haziness": 0.3}
            elif cat == "Air_Pollution":
                sat_data = {"red": 0.40, "green": 0.40, "blue": 0.40, "nir": 0.40} # Dense optical thickness
                sensor_data = {"temperature": 36.0, "humidity": 45.0, "smoke": 880.0, "soil_moisture": 30.0, "water_level": 5.0, "flame": 0.0, "vibration": 0.3}
                cam_data = {"mean_r": 0.55, "mean_g": 0.55, "mean_b": 0.50, "flicker": 0.2, "smoke_haziness": 0.8}
            else: # None / Normal
                sat_data = {"red": 0.15, "green": 0.55, "blue": 0.15, "nir": 0.75} # Healthy forest
                sensor_data = {"temperature": 26.5, "humidity": 52.0, "smoke": 185.0, "soil_moisture": 42.0, "water_level": 4.5, "flame": 0.0, "vibration": 0.2}
                cam_data = {"mean_r": 0.15, "mean_g": 0.70, "mean_b": 0.15, "flicker": 0.05, "smoke_haziness": 0.05}

            dataset.append({
                "true_label": cat,
                "sat_data": sat_data,
                "sensor_data": sensor_data,
                "cam_data": cam_data
            })

    return dataset


def run_system_validation():
    print("==================================================")
    print("  D-SQUARE 2.0 Benchmark Testing & Validation")
    print("==================================================")

    fusion = MultiModalFusionEngine()
    test_samples = generate_validation_dataset(samples_per_class=20)

    y_true = []
    y_pred = []
    latencies = []

    # Historical 30-day dummy sequence
    ts_data = [{"ndvi": 0.7, "lst": 0.4, "soil_m": 0.45} for _ in range(30)]

    for sample in test_samples:
        t0 = time.time()
        res = fusion.evaluate_multi_modal_fusion(
            sat_data=sample["sat_data"],
            ts_data=ts_data,
            sensor_data=sample["sensor_data"],
            camera_data=sample["cam_data"]
        )
        latency = (time.time() - t0) * 1000.0
        latencies.append(latency)

        y_true.append(sample["true_label"])
        y_pred.append(res["predicted_disaster"])

    # Compute Metrics
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="weighted")
    rec = recall_score(y_true, y_pred, average="weighted")
    f1 = f1_score(y_true, y_pred, average="weighted")

    # Compute Confusion Matrix and FPR / FNR
    labels = ["Forest_Fire", "Flood", "Landslide", "Air_Pollution", "None"]
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    # Calculate False Positive Rate (FPR) and False Negative Rate (FNR) for Normal class vs Disasters
    total_samples = len(y_true)
    correct_count = sum([1 for t, p in zip(y_true, y_pred) if t == p])
    false_positives = sum([1 for t, p in zip(y_true, y_pred) if t == "None" and p != "None"])
    false_negatives = sum([1 for t, p in zip(y_true, y_pred) if t != "None" and p == "None"])

    fpr = (false_positives / 20.0) * 100.0
    fnr = (false_negatives / 80.0) * 100.0

    avg_latency = np.mean(latencies)

    print("\n--------------------------------------------------")
    print("           VALIDATION RESULTS & METRICS")
    print("--------------------------------------------------")
    print(f" Total Test Samples      : {total_samples}")
    print(f" Overall System Accuracy : {acc * 100.0:.2f}%  (Target: 95.0%+)")
    print(f" Weighted Precision      : {prec * 100.0:.2f}%  (Target: 90.0%+)")
    print(f" Weighted Recall         : {rec * 100.0:.2f}%  (Target: 90.0%+)")
    print(f" Weighted F1-Score       : {f1 * 100.0:.2f}%  (Target: 90.0%+)")
    print(f" False Positive Rate     : {fpr:.2f}%     (Target: <5.0%)")
    print(f" False Negative Rate     : {fnr:.2f}%     (Target: <5.0%)")
    print(f" Average AI Latency      : {avg_latency:.2f} ms  (Target: <100ms)")
    print("--------------------------------------------------")

    print("\nCONFUSION MATRIX:")
    print("Labels:", labels)
    print(cm)

    print("\nCLASSIFICATION REPORT:")
    print(classification_report(y_true, y_pred, target_names=labels))

    # Pass/Fail Criteria Check
    passed = acc >= 0.95 and fpr <= 5.0 and fnr <= 5.0 and avg_latency < 100.0
    if passed:
        print("\n[SUCCESS] ALL D-SQUARE 2.0 PERFORMANCE TARGETS MET SUCCESSFULLY!")
    else:
        print("\n[WARNING] Some performance targets require tuning.")

    return {
        "accuracy": round(acc * 100.0, 2),
        "precision": round(prec * 100.0, 2),
        "recall": round(rec * 100.0, 2),
        "f1_score": round(f1 * 100.0, 2),
        "fpr": round(fpr, 2),
        "fnr": round(fnr, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "passed": passed
    }


if __name__ == "__main__":
    run_system_validation()
