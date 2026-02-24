from __future__ import annotations

import math
import os

from app.core.config_models import CalibrationConfig


DEFAULT_K = float(os.getenv("GSTI_CALIBRATION_K", "8.0"))
DEFAULT_X0 = float(os.getenv("GSTI_CALIBRATION_X0", "0.5"))
DEFAULT_CONFIG = CalibrationConfig(k=DEFAULT_K, x0=DEFAULT_X0)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def calibrate(raw: float, k: float | None = None, x0: float | None = None, config: CalibrationConfig | None = None) -> float:
    cfg = config or DEFAULT_CONFIG
    slope = cfg.k if k is None else k
    center = cfg.x0 if x0 is None else x0
    calibrated = 1.0 / (1.0 + math.exp(-slope * (raw - center)))
    return clamp01(calibrated)
