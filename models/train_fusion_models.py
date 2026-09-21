"""
D-SQUARE 2.0 ML Training Pipeline for Multi-Modal Fusion Engine
Trains Random Forest Classifier & Anomaly Autoencoder model on satellite + IoT features.
Saves model weights to models/saved/ directory.
"""

import os
import pickle
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved")


def train_and_save_fusion_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    if not HAS_SKLEARN:
        print("[WARN] scikit-learn not available. Skipping model training file creation.")
        return False

    # Synthetic Multi-Modal Feature Matrix (100 samples)
    # Features: [NDVI_anomaly_pct, NDWI, SAR_soil_index, GPM_rain_mm, soil_moisture, temp, tilt, vibration, flame, slope_deg]
    np.random.seed(42)

    # 50 Positive (Disaster / Landslide / Fire) samples
    pos_samples = np.random.normal(loc=[-15.0, 0.45, 0.85, 55.0, 85.0, 26.0, 1.0, 1.0, 0.0, 38.0], scale=[3.0, 0.05, 0.05, 10.0, 5.0, 2.0, 0.0, 0.0, 0.0, 2.0], size=(50, 10))
    pos_labels = np.ones(50)

    # 50 Negative (Normal / Safe) samples
    neg_samples = np.random.normal(loc=[-2.0, 0.20, 0.40, 12.0, 42.0, 25.0, 0.0, 0.0, 0.0, 20.0], scale=[2.0, 0.04, 0.05, 5.0, 8.0, 3.0, 0.0, 0.0, 0.0, 4.0], size=(50, 10))
    neg_labels = np.zeros(50)

    X = np.vstack((pos_samples, neg_samples))
    y = np.hstack((pos_labels, neg_labels))

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = RandomForestClassifier(n_estimators=25, random_state=42)
    clf.fit(X_scaled, y)

    rf_path = os.path.join(MODELS_DIR, "fusion_rf_model.pkl")
    scaler_path = os.path.join(MODELS_DIR, "fusion_scaler.pkl")

    with open(rf_path, "wb") as f:
        pickle.dump(clf, f)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    print(f"[SUCCESS] Multi-modal fusion model trained and saved to {rf_path}")
    return True


if __name__ == "__main__":
    train_and_save_fusion_models()
