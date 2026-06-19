"""
Paddy ML Bridge API — Application Entry Point

FastAPI gateway with embedded ML models for the Agrolytics platform:
    • Soft Voting Ensemble (DenseNet121 + MobileNetV2) via TFLite
    • XGBoost yield prediction via joblib
    • Supabase PostgreSQL integration
    • Prometheus metrics

v3.0 — Single-service architecture (no external ML containers)
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from api.routers import admin, forecast, predict
from core.config import settings
from schemas.common import HealthResponse, ServiceHealth

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown resource management
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — load models at startup."""
    logger.info("🚀 Starting %s v%s", settings.PROJECT_NAME, settings.VERSION)
    logger.info("   Model directory: %s", settings.MODEL_DIR)
    logger.info("   Supabase URL:    %s", settings.SUPABASE_URL)
    logger.info("   Debug mode:      %s", settings.DEBUG)

    # Load embedded ML models
    from services.ml_engine import load_models as load_disease_models
    from services.forecast_engine import load_models as load_predictive_models

    load_disease_models()
    load_predictive_models()

    yield

    logger.info("👋 Shutting down %s", settings.PROJECT_NAME)


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Unified ML service for Agrolytics — Smart Agricultural BI. "
        "Embeds Soft Voting Ensemble (TFLite) for disease detection and "
        "XGBoost for yield prediction. Single-service architecture for "
        "Railway free tier deployment."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — Vercel rewrites integration
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API Routers
# ---------------------------------------------------------------------------

app.include_router(predict.router,  prefix="/api/predict",  tags=["🔬 Prediction"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["📊 Forecast"])
app.include_router(admin.router,    prefix="/api/admin",    tags=["🔒 Admin"])


# ---------------------------------------------------------------------------
# Prometheus Metrics Endpoint
# ---------------------------------------------------------------------------

@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Expose Prometheus metrics (custom metrics from core/metrics.py)."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Health Check — /api/health
# ---------------------------------------------------------------------------

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["❤️ Health"],
    summary="Status Kesehatan API",
    description="Cek status API dan seluruh dependensi (ML Models, Supabase).",
)
async def health_check():
    """
    Aggregate health check across all dependencies.
    Reports individual service status and overall API health.
    """
    from core.metrics import ML_SERVICE_HEALTHY, SUPABASE_HEALTHY
    from services.ml_engine import is_loaded as disease_loaded, get_load_error as disease_error
    from services.forecast_engine import is_loaded as predictive_loaded, get_load_error as predictive_error

    services: list[ServiceHealth] = []
    all_healthy = True

    # Check Disease Detection Model
    disease_ok = disease_loaded()
    ML_SERVICE_HEALTHY.set(1.0 if disease_ok else 0.0)
    services.append(ServiceHealth(
        name="disease-model",
        status="ok" if disease_ok else "not-loaded",
        latency_ms=0.0,
    ))
    if not disease_ok:
        all_healthy = False
        logger.debug("Disease model status: %s", disease_error())

    # Check Predictive Model
    pred_ok = predictive_loaded()
    services.append(ServiceHealth(
        name="predictive-model",
        status="ok" if pred_ok else "not-loaded",
        latency_ms=0.0,
    ))
    if not pred_ok:
        all_healthy = False
        logger.debug("Predictive model status: %s", predictive_error())

    # Check Supabase
    try:
        from services.supabase_client import check_supabase_health
        sb_ok, sb_latency = check_supabase_health()
        SUPABASE_HEALTHY.set(1.0 if sb_ok else 0.0)
        services.append(ServiceHealth(
            name="supabase",
            status="ok" if sb_ok else "down",
            latency_ms=round(sb_latency, 2),
        ))
        if not sb_ok:
            all_healthy = False
    except Exception:
        SUPABASE_HEALTHY.set(0.0)
        services.append(ServiceHealth(name="supabase", status="degraded"))

    return HealthResponse(
        status="ok" if all_healthy else "degraded",
        version=settings.VERSION,
        services=services,
    )


# ---------------------------------------------------------------------------
# Root — API info
# ---------------------------------------------------------------------------

@app.get("/", tags=["❤️ Health"])
async def root():
    """Root endpoint — basic API information."""
    from services.ml_engine import is_loaded as disease_loaded
    from services.forecast_engine import is_loaded as predictive_loaded

    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "architecture": "single-service-embedded",
        "models": {
            "disease_detection": "loaded" if disease_loaded() else "not-loaded",
            "predictive_analytics": "loaded" if predictive_loaded() else "not-loaded",
        },
        "docs": "/docs",
        "health": "/api/health",
        "metrics": "/metrics",
    }
