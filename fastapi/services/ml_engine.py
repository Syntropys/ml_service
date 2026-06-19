"""
ML Engine Service — Embedded Disease Detection (TFLite).

Loads DenseNet121 + MobileNetV2 TFLite models at startup and performs
weighted soft voting ensemble inference in-process. No external HTTP
calls needed.

Falls back to a clear error if model files are not present.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

from core.config import settings
from core.metrics import (
    CONFIDENCE_GAUGE,
    INFERENCE_LATENCY,
    PREDICTED_CLASS_COUNTER,
    PREDICTION_REQUESTS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level model state (loaded once at startup)
# ---------------------------------------------------------------------------
_mobilenet_interpreter = None
_densenet_interpreter = None
_w_mobile: float = 0.4954
_w_dense: float = 0.5046
_class_names: list[str] = []
_index_to_class: dict[int, str] = {}
_models_loaded: bool = False
_load_error: str | None = None


def load_models() -> None:
    """
    Load TFLite models and config at application startup.
    Called from main.py lifespan.
    """
    global _mobilenet_interpreter, _densenet_interpreter
    global _w_mobile, _w_dense, _class_names, _index_to_class
    global _models_loaded, _load_error

    model_dir = Path(settings.MODEL_DIR) / "disease"

    # Load config
    config_path = model_dir / "ensemble_config.json"
    mapping_path = model_dir / "class_mapping.json"

    if not config_path.exists():
        _load_error = f"ensemble_config.json not found at {config_path}"
        logger.warning("Disease models NOT loaded: %s", _load_error)
        return

    with open(config_path) as f:
        config = json.load(f)

    with open(mapping_path) as f:
        mapping = json.load(f)

    _class_names = mapping.get("class_names", config.get("class_names", []))
    _index_to_class = {int(k): v for k, v in mapping.get("index_to_class", {}).items()}

    # Extract ensemble weights
    for model_info in config.get("models", []):
        name = model_info["name"]
        weight = model_info["ensemble_weight"]
        if "mobilenet" in name.lower():
            _w_mobile = weight
        elif "densenet" in name.lower() or "dense" in name.lower():
            _w_dense = weight

    logger.info("Ensemble weights: MobileNetV2=%.4f, DenseNet121=%.4f", _w_mobile, _w_dense)

    # Load TFLite models
    mobilenet_path = model_dir / "mobilenet_v1.tflite"
    densenet_path = model_dir / "densenet.tflite"

    if not mobilenet_path.exists() or not densenet_path.exists():
        _load_error = (
            f"TFLite model files not found. "
            f"Expected: {mobilenet_path} and {densenet_path}. "
            f"Download from Google Drive (see README) and place in {model_dir}/"
        )
        logger.warning("Disease models NOT loaded: %s", _load_error)
        return

    try:
        import tflite_runtime.interpreter as tflite
    except ImportError:
        try:
            import tensorflow.lite as tflite
        except ImportError:
            _load_error = (
                "Neither tflite_runtime nor tensorflow is installed. "
                "Install with: pip install tflite-runtime"
            )
            logger.error("Disease models NOT loaded: %s", _load_error)
            return

    try:
        _mobilenet_interpreter = tflite.Interpreter(model_path=str(mobilenet_path))
        _mobilenet_interpreter.allocate_tensors()

        _densenet_interpreter = tflite.Interpreter(model_path=str(densenet_path))
        _densenet_interpreter.allocate_tensors()

        _models_loaded = True
        _load_error = None
        logger.info(
            "Disease TFLite models loaded: MobileNetV2 (%.1f MB) + DenseNet121 (%.1f MB)",
            mobilenet_path.stat().st_size / 1024 / 1024,
            densenet_path.stat().st_size / 1024 / 1024,
        )
    except Exception as exc:
        _load_error = f"Failed to load TFLite models: {exc}"
        logger.error("Disease models NOT loaded: %s", _load_error)


def _run_tflite_inference(interpreter, img_array: np.ndarray) -> np.ndarray:
    """Run inference on a single TFLite interpreter."""
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]["index"], img_array)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]["index"])
    return output[0]  # Remove batch dimension


def _preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess image bytes to model input format.
    Resize to 224x224, normalize to [0, 1].
    """
    from PIL import Image
    import io

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((224, 224), Image.BILINEAR)
    img_array = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(img_array, axis=0)  # (1, 224, 224, 3)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_loaded() -> bool:
    """Check if models are loaded and ready."""
    return _models_loaded


def get_load_error() -> str | None:
    """Get the error message if models failed to load."""
    return _load_error


async def predict_disease_from_bytes(
    image_bytes: bytes, filename: str = "image.jpg"
) -> dict[str, Any]:
    """
    Run disease classification on raw image bytes using embedded TFLite models.
    Returns dict with predicted_class, confidence, probabilities, inference_time_ms.
    """
    if not _models_loaded:
        raise RuntimeError(
            f"Model penyakit belum dimuat. {_load_error or 'Periksa log server.'}"
        )

    PREDICTION_REQUESTS.inc()
    start = time.perf_counter()

    try:
        img_array = _preprocess_image(image_bytes)

        # Ensemble: weighted soft voting
        prob_mobile = _run_tflite_inference(_mobilenet_interpreter, img_array)
        prob_dense = _run_tflite_inference(_densenet_interpreter, img_array)
        prob_ensemble = (_w_mobile * prob_mobile) + (_w_dense * prob_dense)

        # Get prediction
        pred_idx = int(np.argmax(prob_ensemble))
        confidence = float(prob_ensemble[pred_idx])
        predicted_class = _index_to_class.get(pred_idx, f"class_{pred_idx}")

        # Build top-k
        top_k_indices = np.argsort(prob_ensemble)[::-1][:3]
        top_k_predictions = [
            {
                "class_name": _index_to_class.get(int(idx), f"class_{idx}"),
                "probability": float(prob_ensemble[idx]),
            }
            for idx in top_k_indices
        ]

        elapsed_ms = (time.perf_counter() - start) * 1000

        result = {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": prob_ensemble.tolist(),
            "top_k_predictions": top_k_predictions,
            "inference_time_ms": elapsed_ms,
        }

        # Prometheus metrics
        INFERENCE_LATENCY.observe(elapsed_ms / 1000)
        PREDICTED_CLASS_COUNTER.labels(predicted_class=predicted_class).inc()
        CONFIDENCE_GAUGE.labels(predicted_class=predicted_class).set(confidence)

        return result

    except RuntimeError:
        raise
    except Exception as exc:
        logger.error("Inference failed: %s", exc, exc_info=True)
        raise RuntimeError(f"Inferensi gagal: {exc}") from exc


async def predict_disease_from_base64(image_base64: str) -> dict[str, Any]:
    """
    Run disease classification on a base64-encoded image.
    Decodes and delegates to predict_disease_from_bytes.
    """
    import base64

    image_bytes = base64.b64decode(image_base64)
    return await predict_disease_from_bytes(image_bytes)


# ---------------------------------------------------------------------------
# Health Probe
# ---------------------------------------------------------------------------

async def check_ml_service_health() -> tuple[bool, float]:
    """
    Check if embedded ML models are loaded and functional.
    Returns (is_healthy, latency_ms).
    """
    start = time.perf_counter()
    is_healthy = _models_loaded
    latency_ms = (time.perf_counter() - start) * 1000
    return is_healthy, latency_ms
