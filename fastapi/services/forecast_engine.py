"""
Forecast Engine Service — manages async forecast job lifecycle.

Phase 2 initial: in-memory job queue.
Future: backed by Supabase ``forecast_jobs`` table.
"""
from __future__ import annotations

import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Any
import httpx

from schemas.common import JobStatus
from core.config import settings
from core.metrics import INFERENCE_LATENCY

logger = logging.getLogger(__name__)

# Reusable async client
_http_client: httpx.AsyncClient | None = None

def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=settings.PREDICTIVE_ML_SERVICE_URL,
            timeout=httpx.Timeout(10.0),
        )
    return _http_client

async def close_client() -> None:
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None

# In-memory job store for caching results temporarily
_jobs: dict[str, dict[str, Any]] = {}

async def create_job(
    region_id: str,
    horizon: int,
    models: list[str],
    user_id: str,
    custom_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a forecast job and execute it immediately against the MLflow service.
    """
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "region_id": region_id,
        "horizon": horizon,
        "models": models,
        "custom_inputs": custom_inputs,
        "user_id": user_id,
        "status": JobStatus.processing.value,
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _jobs[job_id] = job
    
    # Executing the prediction
    start = time.perf_counter()
    try:
        if not custom_inputs:
            raise ValueError("custom_inputs is required for predictive analytics")

        # Expecting these exact 8 features in custom_inputs based on MLmodel schema
        # luas_panen, tahun, curah_hujan_rataan, curah_hujan_total, suhu_rataan, suhu_maksimum, suhu_minimum, kelembapan_rataan
        row = [
            float(custom_inputs.get("luas_panen", 0.0)),
            float(custom_inputs.get("tahun", datetime.now().year)),
            float(custom_inputs.get("curah_hujan_rataan", 0.0)),
            float(custom_inputs.get("curah_hujan_total", 0.0)),
            float(custom_inputs.get("suhu_rataan", 0.0)),
            float(custom_inputs.get("suhu_maksimum", 0.0)),
            float(custom_inputs.get("suhu_minimum", 0.0)),
            float(custom_inputs.get("kelembapan_rataan", 0.0)),
        ]

        payload = {
            "dataframe_split": {
                "columns": ["luas_panen", "tahun", "curah_hujan_rataan", "curah_hujan_total", "suhu_rataan", "suhu_maksimum", "suhu_minimum", "kelembapan_rataan"],
                "data": [row]
            }
        }

        client = _get_client()
        response = await client.post("/invocations", json=payload)
        response.raise_for_status()
        
        mlflow_resp = response.json()
        predictions = mlflow_resp.get("predictions", [])
        
        # Scikit-learn PyFunc returns array of predictions
        predicted_yield = predictions[0] if isinstance(predictions, list) else predictions
        
        job["result"] = {
            "predicted_produksi": float(predicted_yield),
            "inference_time_ms": (time.perf_counter() - start) * 1000
        }
        job["status"] = JobStatus.done.value

    except Exception as e:
        logger.error(f"Predictive ML Service error: {e}")
        job["status"] = JobStatus.error.value
        job["error"] = str(e)
        
    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    return job

def get_job(job_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    job = _jobs.get(job_id)
    if job is None or (user_id and job.get("user_id") != user_id):
        return None
    return job
