"""
Forecast Router — /api/forecast/*

Endpoints:
    POST /api/forecast/custom      Create an async custom forecast job
    GET  /api/forecast/jobs/{id}   Check forecast job status
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.metrics import FORECAST_JOBS_CREATED
from core.security import verify_supabase_jwt
from schemas.forecast import ForecastCustomRequest, ForecastJobResponse
from services import forecast_engine

router = APIRouter()


# ---------------------------------------------------------------------------
# Create Forecast Job  (design doc §7.4 POST /api/forecast/custom)
# ---------------------------------------------------------------------------

@router.post(
    "/custom",
    response_model=ForecastJobResponse,
    summary="Buat Forecast Kustom",
    description=(
        "Membuat pekerjaan forecast asinkron untuk prediksi kustom (B3 Hybrid). "
        "Hasilnya bisa diambil melalui endpoint GET /jobs/{job_id}."
    ),
)
async def create_custom_forecast(
    request: ForecastCustomRequest,
    user: dict = Depends(verify_supabase_jwt),
):
    """
    Enqueue a custom forecast job.
    Phase 2: in-memory queue → later backed by Supabase ``forecast_jobs`` table.
    """
    user_id = user.get("sub", "unknown")
    model_names = [m.value for m in request.models]

    job = forecast_engine.create_job(
        region_id=request.region_id,
        horizon=request.horizon,
        models=model_names,
        user_id=user_id,
        custom_inputs=request.custom_inputs,
    )

    FORECAST_JOBS_CREATED.inc()

    return ForecastJobResponse(
        job_id=job["job_id"],
        status=job["status"],
        message=(
            f"Forecast {request.horizon} tahun untuk wilayah {request.region_id} "
            f"menggunakan {len(model_names)} model telah diantrikan."
        ),
    )


# ---------------------------------------------------------------------------
# Get Job Status  (design doc §7.4 GET /api/forecast/jobs/{job_id})
# ---------------------------------------------------------------------------

@router.get(
    "/jobs/{job_id}",
    response_model=ForecastJobResponse,
    summary="Status Forecast Job",
    description="Cek status pekerjaan forecast yang sedang berjalan atau selesai.",
)
async def get_forecast_job(
    job_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    """
    Retrieve the status and result of a forecast job.
    Enforces ownership: users can only see their own jobs.
    """
    user_id = user.get("sub", "unknown")
    job = forecast_engine.get_job(job_id, user_id=user_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Pekerjaan forecast tidak ditemukan atau Anda tidak memiliki akses.",
        )

    return ForecastJobResponse(
        job_id=job["job_id"],
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
    )
