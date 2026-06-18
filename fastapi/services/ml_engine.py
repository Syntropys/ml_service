"""
ML Engine Service — async bridge to the dedicated Paddy Disease Detection API.

Uses httpx.AsyncClient to communicate with the separate ML service that hosts
the Soft Voting Ensemble (DenseNet121 + MobileNetV2_v3) via MLflow.
Prometheus latency tracking is applied to every inference call.
"""
from __future__ import annotations

import base64
import logging
import time
from typing import Any

import httpx

from core.config import settings
from core.metrics import (
    CONFIDENCE_GAUGE,
    INFERENCE_LATENCY,
    PREDICTED_CLASS_COUNTER,
    PREDICTION_REQUESTS,
)

logger = logging.getLogger(__name__)

# Reusable async client — created once, shared across requests.
_http_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Lazy-init a module-level async HTTP client."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=settings.ML_SERVICE_URL,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    return _http_client


async def close_client() -> None:
    """Shutdown hook — close the HTTP client gracefully."""
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


# ---------------------------------------------------------------------------
# Disease Prediction (Soft Voting Ensemble)
# ---------------------------------------------------------------------------

async def predict_disease_from_base64(image_base64: str) -> dict[str, Any]:
    """
    Send a base64-encoded image to the ML service for disease classification.

    The ML service (paddy_detection/app) exposes ``POST /predict`` that accepts
    a file upload. We decode the base64 string and send it as multipart form data.

    Returns the raw JSON dict from the ML service containing:
        predicted_class, confidence, top_k_predictions, inference_time_ms, probabilities
    """
    PREDICTION_REQUESTS.inc()
    start = time.perf_counter()

    try:
        client = _get_client()
        
        # MLflow model (SoftVotingEnsemble) now supports decoding base64 natively
        # Send payload to MLflow /invocations endpoint
        payload = {
            "dataframe_split": {
                "columns": ["image_base64"],
                "data": [[image_base64]]
            }
        }
        
        response = await client.post(
            "/invocations",
            json=payload
        )
        response.raise_for_status()
        
        # MLflow returns {"predictions": [...]}
        mlflow_resp = response.json()
        predictions = mlflow_resp.get("predictions", [])
        if not predictions:
            raise RuntimeError("MLflow returned empty predictions list")
            
        # The PyFunc model returns a dict for the batch, we sent 1 item
        # PyFunc output: {"predicted_class": ["class"], "confidence": [0.99], "probabilities": [[...]]}
        pred_data = predictions if isinstance(predictions, dict) else predictions[0]
        
        predicted_class = pred_data.get("predicted_class", ["unknown"])[0]
        confidence = pred_data.get("confidence", [0.0])[0]
        
        result = {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": pred_data.get("probabilities", [[]])[0],
            "inference_time_ms": (time.perf_counter() - start) * 1000,
            "top_k_predictions": []  # Can calculate from probabilities if needed
        }

        # --- Prometheus metrics ---
        elapsed_ms = (time.perf_counter() - start) * 1000
        INFERENCE_LATENCY.observe(elapsed_ms / 1000)  # seconds

        predicted_class = result.get("predicted_class", "unknown")
        confidence = float(result.get("confidence", 0.0))
        PREDICTED_CLASS_COUNTER.labels(predicted_class=predicted_class).inc()
        CONFIDENCE_GAUGE.labels(predicted_class=predicted_class).set(confidence)

        return result

    except httpx.HTTPStatusError as exc:
        logger.error("ML service returned %s: %s", exc.response.status_code, exc.response.text)
        raise RuntimeError(
            f"ML Service error ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Failed to reach ML service at %s: %s", settings.ML_SERVICE_URL, exc)
        raise RuntimeError(
            f"Gagal menghubungi ML Service: {exc}"
        ) from exc


async def predict_disease_from_bytes(image_bytes: bytes, filename: str = "image.jpg") -> dict[str, Any]:
    """
    Send raw image bytes (e.g. from UploadFile) to the ML service.
    Thin wrapper that skips base64 encoding.
    """
    PREDICTION_REQUESTS.inc()
    start = time.perf_counter()

    try:
        # MLflow model (SoftVotingEnsemble) now supports base64 strings natively.
        # We encode the raw bytes to base64 and send it in the dataframe_split format.
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        client = _get_client()
        payload = {
            "dataframe_split": {
                "columns": ["image_base64"],
                "data": [[image_base64]]
            }
        }
        
        response = await client.post("/invocations", json=payload)
        response.raise_for_status()
        mlflow_resp = response.json()
        
        predictions = mlflow_resp.get("predictions", [])
        if not predictions:
            raise RuntimeError("MLflow returned empty predictions list")
            
        pred_data = predictions if isinstance(predictions, dict) else predictions[0]
        predicted_class = pred_data.get("predicted_class", ["unknown"])[0]
        confidence = pred_data.get("confidence", [0.0])[0]
        
        result = {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": pred_data.get("probabilities", [[]])[0],
            "inference_time_ms": (time.perf_counter() - start) * 1000,
            "top_k_predictions": []
        }

        elapsed_ms = (time.perf_counter() - start) * 1000
        INFERENCE_LATENCY.observe(elapsed_ms / 1000)

        predicted_class = result.get("predicted_class", "unknown")
        confidence = float(result.get("confidence", 0.0))
        PREDICTED_CLASS_COUNTER.labels(predicted_class=predicted_class).inc()
        CONFIDENCE_GAUGE.labels(predicted_class=predicted_class).set(confidence)

        return result

    except httpx.HTTPStatusError as exc:
        logger.error("ML service returned %s: %s", exc.response.status_code, exc.response.text)
        raise RuntimeError(
            f"ML Service error ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Failed to reach ML service at %s: %s", settings.ML_SERVICE_URL, exc)
        raise RuntimeError(
            f"Gagal menghubungi ML Service: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Health Probe
# ---------------------------------------------------------------------------

async def check_ml_service_health() -> tuple[bool, float]:
    """
    Probe the ML service root endpoint.
    Returns (is_healthy, latency_ms).
    """
    try:
        client = _get_client()
        start = time.perf_counter()
        response = await client.get("/ping", timeout=5.0)
        latency_ms = (time.perf_counter() - start) * 1000
        return response.status_code == 200, latency_ms
    except Exception:
        return False, 0.0
