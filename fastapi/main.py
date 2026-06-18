"""
Paddy ML Bridge API — Application Entry Point

FastAPI gateway bridging the Agrolytics frontend (Vercel) with:
    • Soft Voting Ensemble ML service (Paddy Disease Detection)
    • Supabase PostgreSQL (predictions, ingestion, audit)
    • Prometheus + Grafana (monitoring & observability)

Endpoints are routed via Vercel rewrites:
    /api/predict/*  → this service
    /api/forecast/* → this service
    /api/admin/*    → this service
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
    """Manage application lifecycle resources."""
    logger.info("🚀 Starting %s v%s", settings.PROJECT_NAME, settings.VERSION)
    logger.info("   ML Service URL: %s", settings.ML_SERVICE_URL)
    logger.info("   Supabase URL:   %s", settings.SUPABASE_URL)
    logger.info("   Debug mode:     %s", settings.DEBUG)
    yield
    # Shutdown: close async HTTP client
    from services.ml_engine import close_client
    await close_client()
    logger.info("👋 Shutting down %s", settings.PROJECT_NAME)


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Bridge API untuk Soft Voting Ensemble model (DenseNet121 + MobileNetV2_v3), "
        "MLflow tracking, Grafana monitoring, dan Prometheus metrics. "
        "Bagian dari platform Agrolytics — Smart Agricultural BI."
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
# API Routers  (MUST be registered before Prometheus instrumentation)
# ---------------------------------------------------------------------------

app.include_router(predict.router,  prefix="/api/predict",  tags=["🔬 Prediction"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["📊 Forecast"])
app.include_router(admin.router,    prefix="/api/admin",    tags=["🔒 Admin"])


# ---------------------------------------------------------------------------
# Prometheus Metrics Endpoint
# NOTE: prometheus-fastapi-instrumentator is DISABLED because it crashes
# on nested APIRouter objects (AttributeError: '_IncludedRouter' has no
# attribute 'path'). Custom metrics from core/metrics.py (prediction
# counts, inference latency, confidence gauges) are still collected and
# exposed here.
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
    description="Cek status API dan seluruh dependensi (ML Service, Supabase).",
)
async def health_check():
    """
    Aggregate health check across all dependencies.
    Reports individual service status and overall API health.
    """
    from core.metrics import ML_SERVICE_HEALTHY, SUPABASE_HEALTHY

    services: list[ServiceHealth] = []
    all_healthy = True

    # Check ML Service
    try:
        from services.ml_engine import check_ml_service_health
        ml_ok, ml_latency = await check_ml_service_health()
        ML_SERVICE_HEALTHY.set(1.0 if ml_ok else 0.0)
        services.append(ServiceHealth(
            name="ml-service",
            status="ok" if ml_ok else "down",
            latency_ms=round(ml_latency, 2),
        ))
        if not ml_ok:
            all_healthy = False
    except Exception:
        ML_SERVICE_HEALTHY.set(0.0)
        services.append(ServiceHealth(name="ml-service", status="down"))
        all_healthy = False

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
        # Supabase failure is non-critical (mock fallback exists)

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
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "metrics": "/metrics",
    }
