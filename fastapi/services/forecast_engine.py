"""
Forecast Engine Service — Embedded XGBoost Predictive Analytics.

Loads the XGBoost model (.joblib) at startup and runs yield prediction
in-process. No external HTTP calls needed.
"""
from __future__ import annotations

import logging
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from schemas.common import JobStatus
from core.config import settings
from core.metrics import YIELD_PREDICTION_LATENCY, YIELD_PREDICTION_REQUESTS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level model state (loaded once at startup)
# ---------------------------------------------------------------------------
_xgb_model = None
_models_loaded: bool = False
_load_error: str | None = None

# The 8 features the XGBoost model expects (in order).
# NOTE: The notebook drops kabupaten, produksi, produktivitas from the dataset.
# The remaining columns are: luas_panen, tahun, provinsi(?), curah_hujan_rataan,
# curah_hujan_total, suhu_rataan, suhu_maksimum, suhu_minimum, kelembapan_rataan.
# We send 8 numeric features (without provinsi) as the bridge's API contract.
FEATURE_COLUMNS = [
    "luas_panen",
    "tahun",
    "curah_hujan_rataan",
    "curah_hujan_total",
    "suhu_rataan",
    "suhu_maksimum",
    "suhu_minimum",
    "kelembapan_rataan",
]


def load_models() -> None:
    """
    Load XGBoost model at application startup.
    Called from main.py lifespan.
    """
    global _xgb_model, _models_loaded, _load_error

    model_dir = Path(settings.MODEL_DIR) / "predictive"
    model_path = model_dir / "xgboost.joblib"

    if not model_path.exists():
        _load_error = f"xgboost.joblib not found at {model_path}"
        logger.warning("Predictive model NOT loaded: %s", _load_error)
        return

    try:
        import joblib

        _xgb_model = joblib.load(model_path)
        _models_loaded = True
        _load_error = None

        n_features = getattr(_xgb_model, "n_features_in_", "unknown")
        logger.info(
            "XGBoost model loaded from %s (n_features=%s, size=%.2f MB)",
            model_path,
            n_features,
            model_path.stat().st_size / 1024 / 1024,
        )
    except Exception as exc:
        _load_error = f"Failed to load XGBoost model: {exc}"
        logger.error("Predictive model NOT loaded: %s", _load_error)


def is_loaded() -> bool:
    """Check if predictive model is loaded."""
    return _models_loaded


def get_load_error() -> str | None:
    """Get error message if model failed to load."""
    return _load_error


# In-memory job store
_jobs: dict[str, dict[str, Any]] = {}


async def create_job(
    region_id: str,
    horizon: int,
    models: list[str],
    user_id: str,
    custom_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a forecast job and execute immediately using embedded XGBoost.
    """
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "region_id": region_id,
        "horizon": horizon,
        "models": models,
        "custom_inputs": custom_inputs,
        "user_id": user_id,
        "status": JobStatus.running.value,
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _jobs[job_id] = job

    start = time.perf_counter()
    try:
        if not _models_loaded:
            raise RuntimeError(
                f"Model prediktif belum dimuat. {_load_error or 'Periksa log server.'}"
            )

        if not custom_inputs:
            raise ValueError("custom_inputs diperlukan untuk prediksi")

        # Build feature vector in the correct order
        row = [float(custom_inputs.get(col, 0.0)) for col in FEATURE_COLUMNS]
        X = np.array([row], dtype=np.float64)

        # Run prediction
        predicted_value = float(_xgb_model.predict(X)[0])

        elapsed_ms = (time.perf_counter() - start) * 1000
        YIELD_PREDICTION_LATENCY.observe(elapsed_ms / 1000)
        YIELD_PREDICTION_REQUESTS.labels(model_name="xgboost", region_id=region_id).inc()

        job["result"] = {
            "predicted_produksi": predicted_value,
            "inference_time_ms": elapsed_ms,
        }
        job["status"] = JobStatus.done.value

    except Exception as e:
        logger.error("Predictive inference error: %s", e, exc_info=True)
        job["status"] = JobStatus.error.value
        job["error"] = str(e)

    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    return job


def get_job(job_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    job = _jobs.get(job_id)
    if job is None or (user_id and job.get("user_id") != user_id):
        return None
    return job
