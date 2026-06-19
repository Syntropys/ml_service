"""
Prediction Router — /api/predict/*

Endpoints:
    POST /api/predict/disease      Disease classification (base64 image)
    POST /api/predict/disease/upload   Disease classification (file upload)
    POST /api/predict/yield        Yield prediction for a region+year+model
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.metrics import YIELD_PREDICTION_LATENCY, YIELD_PREDICTION_REQUESTS
from core.security import verify_supabase_jwt
from schemas.predict import (
    DiseasePredictionRequest,
    DiseasePredictionResponse,
    TopKPrediction,
    YieldPredictionRequest,
    YieldPredictionResponse,
)
from services.ml_engine import predict_disease_from_base64, predict_disease_from_bytes

router = APIRouter()


# ---------------------------------------------------------------------------
# Disease Prediction — Base64
# ---------------------------------------------------------------------------

@router.post(
    "/disease",
    response_model=DiseasePredictionResponse,
    summary="Klasifikasi Penyakit Padi (Base64)",
    description=(
        "Kirim gambar daun padi dalam format base64 untuk diklasifikasi "
        "menggunakan model Soft Voting Ensemble (DenseNet121 + MobileNetV2_v3)."
    ),
)
async def predict_disease(request: DiseasePredictionRequest):
    """
    Disease classification via base64-encoded image.
    Calls the ML service (Paddy Detection) and exposes metrics to Prometheus.
    Auth is optional for this endpoint (can be enabled by uncommenting the dependency).
    """
    try:
        result = await predict_disease_from_base64(request.image_base64)

        # Build top-k predictions list if available
        top_k: list[TopKPrediction] = []
        raw_top_k = result.get("top_k_predictions", [])
        if isinstance(raw_top_k, list):
            for item in raw_top_k:
                if isinstance(item, dict):
                    top_k.append(TopKPrediction(
                        class_name=item.get("class", item.get("class_name", "unknown")),
                        probability=float(item.get("probability", item.get("confidence", 0.0))),
                    ))

        return DiseasePredictionResponse(
            predicted_class=result.get("predicted_class", "unknown"),
            confidence=float(result.get("confidence", 0.0)),
            top_k_predictions=top_k,
            model_used="Paddy_SoftVoting_Ensemble/latest",
            inference_time_ms=result.get("inference_time_ms"),
        )

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference gagal: {exc}")


# ---------------------------------------------------------------------------
# Disease Prediction — File Upload
# ---------------------------------------------------------------------------

@router.post(
    "/disease/upload",
    response_model=DiseasePredictionResponse,
    summary="Klasifikasi Penyakit Padi (File Upload)",
    description=(
        "Upload gambar daun padi langsung sebagai file untuk diklasifikasi "
        "menggunakan model Soft Voting Ensemble."
    ),
)
async def predict_disease_upload(file: UploadFile = File(...)):
    """
    Disease classification via direct file upload.
    Accepts image files and forwards to the ML service.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File harus berupa gambar (image/jpeg, image/png, dll.)",
        )

    try:
        contents = await file.read()
        result = await predict_disease_from_bytes(contents, filename=file.filename or "image.jpg")

        top_k: list[TopKPrediction] = []
        raw_top_k = result.get("top_k_predictions", [])
        if isinstance(raw_top_k, list):
            for item in raw_top_k:
                if isinstance(item, dict):
                    top_k.append(TopKPrediction(
                        class_name=item.get("class", item.get("class_name", "unknown")),
                        probability=float(item.get("probability", item.get("confidence", 0.0))),
                    ))

        return DiseasePredictionResponse(
            predicted_class=result.get("predicted_class", "unknown"),
            confidence=float(result.get("confidence", 0.0)),
            top_k_predictions=top_k,
            model_used="Paddy_SoftVoting_Ensemble/latest",
            inference_time_ms=result.get("inference_time_ms"),
        )

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Inference gagal: {exc}\n\nTraceback:\n{tb}")


# ---------------------------------------------------------------------------
# Yield Prediction  (design doc §7.4 POST /api/predict/yield)
# ---------------------------------------------------------------------------

@router.post(
    "/yield",
    response_model=YieldPredictionResponse,
    summary="Prediksi Produktivitas Padi",
    description=(
        "Prediksi yield (ton/ha) untuk wilayah dan tahun tertentu "
        "menggunakan model ML pilihan (LSTM, XGBoost, Random Forest, Linear)."
    ),
)
async def predict_yield(
    request: YieldPredictionRequest,
    user: dict = Depends(verify_supabase_jwt),
):
    """
    Yield prediction endpoint.
    Phase 2: queries pre-computed predictions from Supabase.
    Falls back to a mock response if no data is found.
    """
    start = time.perf_counter()
    model_name = request.model.value

    YIELD_PREDICTION_REQUESTS.labels(
        model_name=model_name,
        region_id=request.region_id,
    ).inc()

    try:
        # Try fetching pre-computed prediction from Supabase
        from services.supabase_client import get_predictions_by_region

        predictions = get_predictions_by_region(
            region_id=request.region_id,
            model_name=model_name,
            target_year=request.year,
        )

        if predictions:
            pred = predictions[0]
            response = YieldPredictionResponse(
                predicted_yield=float(pred.get("predicted_yield", 0)),
                predicted_prod_ton=float(pred.get("predicted_prod_ton", 0)),
                confidence_lower=float(pred.get("confidence_lower", 0)),
                confidence_upper=float(pred.get("confidence_upper", 0)),
                model_version=pred.get("model_version", f"{model_name}_v1"),
            )
        else:
            # Fallback: mock response for regions without pre-computed data
            response = YieldPredictionResponse(
                predicted_yield=4.5,
                predicted_prod_ton=150000.0,
                confidence_lower=4.1,
                confidence_upper=4.9,
                model_version=f"{model_name}_v1-mock",
            )

        elapsed = time.perf_counter() - start
        YIELD_PREDICTION_LATENCY.observe(elapsed)

        return response

    except RuntimeError:
        # Supabase not configured — return mock
        return YieldPredictionResponse(
            predicted_yield=4.5,
            predicted_prod_ton=150000.0,
            confidence_lower=4.1,
            confidence_upper=4.9,
            model_version=f"{model_name}_v1-mock",
        )
