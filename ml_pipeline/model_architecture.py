"""
D-SQUARE 2.0 Multi-Fusion ML Pipeline: Model Architecture
Implements PyTorch Multi-Modal Fusion Neural Network (1D CNN + Bi-LSTM + ResNet + Transformer Attention)
with multi-task heads for Disaster Classification, Severity Classification, Regression, and Confidence Scoring.
"""

import math
from typing import Dict, Any, List, Tuple, Optional

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_PYTORCH = True
except ImportError:
    HAS_PYTORCH = False


if HAS_PYTORCH:

    class IoTBranch(nn.Module):
        """1D CNN + Bi-LSTM branch for IoT time-series sensor telemetry"""
        def __init__(self, input_dim: int = 12, hidden_dim: int = 64):
            super().__init__()
            self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
            self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
            self.lstm = nn.LSTM(input_size=64, hidden_size=hidden_dim, num_layers=2, batch_first=True, bidirectional=True)
            self.fc = nn.Linear(hidden_dim * 2, 64)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (batch_size, input_dim) -> (batch_size, 1, input_dim)
            x = x.unsqueeze(1)
            x = F.relu(self.conv1(x))
            x = F.relu(self.conv2(x))
            x = x.permute(0, 2, 1)  # (batch_size, seq_len, channels)
            out, _ = self.lstm(x)
            out = self.fc(out[:, -1, :])
            return out

    class SatelliteBranch(nn.Module):
        """Spectral & ResNet-style Conv branch for satellite remote sensing imagery/indices"""
        def __init__(self, input_dim: int = 4, hidden_dim: int = 64):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.BatchNorm1d(64),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, hidden_dim),
                nn.ReLU()
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)

    class WeatherBranch(nn.Module):
        """Deep Dense network for weather forecast & SPI drought/flood indices"""
        def __init__(self, input_dim: int = 4, hidden_dim: int = 64):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Linear(64, hidden_dim),
                nn.ReLU()
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)

    class HistoricalTransformerBranch(nn.Module):
        """Transformer Encoder for historical susceptibility & past disaster event sequences"""
        def __init__(self, input_dim: int = 4, hidden_dim: int = 64):
            super().__init__()
            self.embedding = nn.Linear(input_dim, hidden_dim)
            encoder_layer = nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=4, batch_first=True)
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
            self.fc = nn.Linear(hidden_dim, hidden_dim)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (batch_size, input_dim) -> (batch_size, 1, input_dim)
            x_emb = self.embedding(x).unsqueeze(1)
            trans_out = self.transformer(x_emb)
            return self.fc(trans_out[:, 0, :])

    class MultiModalDisasterFusionModel(nn.Module):
        """
        Complete Multi-Modal Neural Network Architecture for D-SQUARE 2.0.
        Combines IoT, Satellite, Weather, and Historical branches with Cross-Modal Self-Attention.
        """
        def __init__(self, feature_dim: int = 24):
            super().__init__()
            self.iot_branch = IoTBranch(input_dim=12, hidden_dim=64)
            self.sat_branch = SatelliteBranch(input_dim=4, hidden_dim=64)
            self.wx_branch = WeatherBranch(input_dim=4, hidden_dim=64)
            self.hist_branch = HistoricalTransformerBranch(input_dim=4, hidden_dim=64)

            # Cross-Modal Attention Layer
            self.attention = nn.MultiheadAttention(embed_dim=64, num_heads=4, batch_first=True)
            self.fusion_fc = nn.Sequential(
                nn.Linear(64 * 4, 128),
                nn.BatchNorm1d(128),
                nn.ReLU(),
                nn.Dropout(0.25),
                nn.Linear(128, 64),
                nn.ReLU()
            )

            # Multi-Task Heads
            self.disaster_type_head = nn.Linear(64, 6)     # FLOOD, FIRE, EARTHQUAKE, CYCLONE, DROUGHT, LANDSLIDE
            self.severity_head = nn.Linear(64, 4)          # LOW, MEDIUM, HIGH, CRITICAL
            self.area_regression_head = nn.Linear(64, 1)   # Affected Area km² / Inundation Depth
            self.confidence_head = nn.Linear(64, 1)        # Confidence Score (Sigmoid)

        def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
            # Slice feature vector into sub-branch inputs
            # Feature vector layout (24 features):
            # 0-11: IoT Telemetry (12)
            # 12-15: Spatial / Socioeconomic (4) -> Historical branch
            # 16-19: Derived Disaster Indices (4) -> Satellite / Weather branch
            # 20-23: Trends & Lag (4)
            iot_x = x[:, 0:12]
            hist_x = x[:, 12:16]
            sat_x = x[:, 16:20]
            wx_x = x[:, 20:24]

            f_iot = self.iot_branch(iot_x)
            f_sat = self.sat_branch(sat_x)
            f_wx = self.wx_branch(wx_x)
            f_hist = self.hist_branch(hist_x)

            # Stack modalities for attention: (batch_size, 4, 64)
            modalities = torch.stack([f_iot, f_sat, f_wx, f_hist], dim=1)
            attn_out, _ = self.attention(modalities, modalities, modalities)

            # Concatenate fused modality features: (batch_size, 256)
            fused_flat = attn_out.reshape(attn_out.size(0), -1)
            embedding = self.fusion_fc(fused_flat)

            # Compute Multi-Task Outputs
            logits_disaster = self.disaster_type_head(embedding)
            logits_severity = self.severity_head(embedding)
            pred_area = F.relu(self.area_regression_head(embedding))
            pred_confidence = torch.sigmoid(self.confidence_head(embedding))

            return logits_disaster, logits_severity, pred_area, pred_confidence

else:

    class MultiModalDisasterFusionModel:
        """Lightweight Scikit-Learn style fallback model if PyTorch is absent"""
        def __init__(self, feature_dim: int = 24):
            self.feature_dim = feature_dim
