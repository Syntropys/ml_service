"""
Admin Router — /api/admin/*

All endpoints require admin role (via ``require_admin`` dependency).

Endpoints:
    POST /api/admin/ingest/bps           Trigger BPS data ingestion
    POST /api/admin/ingest/nasa          Trigger NASA POWER data ingestion
    POST /api/admin/cluster/recompute    Re-run K-means clustering
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from core.metrics import ADMIN_ACTIONS
from core.security import require_admin
from schemas.admin import (
    AdminActionResponse,
    BpsIngestRequest,
    ClusterRecomputeRequest,
    NasaIngestRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# BPS Ingestion  (design doc §7.4 POST /api/admin/ingest/bps)
# ---------------------------------------------------------------------------

@router.post(
    "/ingest/bps",
    response_model=AdminActionResponse,
    summary="Trigger Ingestion Data BPS",
    description=(
        "Memicu proses ingest data produksi padi dari BPS untuk tahun tertentu. "
        "Menulis ke tabel ``production_history`` dan mencatat di ``audit_log``."
    ),
)
async def trigger_bps_ingestion(
    request: BpsIngestRequest,
    user: dict = Depends(require_admin),
):
    """
    Trigger BPS production data ingestion.
    Phase 2: actual scrape/CSV import → Supabase production_history upsert.
    Current: audit log entry + mock response.
    """
    actor_id = user.get("sub", "unknown")

    ADMIN_ACTIONS.labels(action_type="ingest.bps").inc()

    try:
        from services.supabase_client import insert_audit_log

        audit_id = insert_audit_log(
            actor_id=actor_id,
            action="data.ingest.bps",
            entity_type="production_history",
            metadata={"year": request.year, "source_url": request.source_url},
        )

        return AdminActionResponse(
            status="success",
            message=f"Ingestion data BPS untuk tahun {request.year} telah dimulai.",
            audit_log_id=audit_id,
        )

    except RuntimeError:
        # Supabase not configured — return mock
        return AdminActionResponse(
            status="success",
            message=f"Ingestion data BPS untuk tahun {request.year} telah dimulai (mock).",
        )


# ---------------------------------------------------------------------------
# NASA POWER Ingestion  (design doc §7.4 POST /api/admin/ingest/nasa)
# ---------------------------------------------------------------------------

@router.post(
    "/ingest/nasa",
    response_model=AdminActionResponse,
    summary="Trigger Ingestion Data NASA POWER",
    description=(
        "Memicu proses ingest data cuaca dari NASA POWER API untuk rentang tahun tertentu. "
        "Menulis ke tabel ``weather_history`` dan mencatat di ``audit_log``."
    ),
)
async def trigger_nasa_ingestion(
    request: NasaIngestRequest,
    user: dict = Depends(require_admin),
):
    """
    Trigger NASA POWER weather data ingestion.
    Phase 2: actual NASA POWER API pull → Supabase weather_history upsert.
    Current: audit log entry + mock response.
    """
    actor_id = user.get("sub", "unknown")

    if request.year_from > request.year_to:
        raise HTTPException(
            status_code=400,
            detail="year_from harus lebih kecil atau sama dengan year_to.",
        )

    ADMIN_ACTIONS.labels(action_type="ingest.nasa").inc()

    try:
        from services.supabase_client import insert_audit_log

        audit_id = insert_audit_log(
            actor_id=actor_id,
            action="data.ingest.nasa",
            entity_type="weather_history",
            metadata={"year_from": request.year_from, "year_to": request.year_to},
        )

        return AdminActionResponse(
            status="success",
            message=(
                f"Ingestion data NASA POWER dari {request.year_from} "
                f"sampai {request.year_to} telah dimulai."
            ),
            audit_log_id=audit_id,
        )

    except RuntimeError:
        return AdminActionResponse(
            status="success",
            message=(
                f"Ingestion data NASA POWER dari {request.year_from} "
                f"sampai {request.year_to} telah dimulai (mock)."
            ),
        )


# ---------------------------------------------------------------------------
# Cluster Recompute  (design doc §7.4 POST /api/admin/cluster/recompute)
# ---------------------------------------------------------------------------

@router.post(
    "/cluster/recompute",
    response_model=AdminActionResponse,
    summary="Recompute K-Means Clustering",
    description=(
        "Menjalankan ulang algoritma K-Means clustering untuk tahun referensi tertentu. "
        "Mengganti ``cluster_assignments`` yang ada dan mencatat di ``audit_log``."
    ),
)
async def trigger_cluster_recompute(
    request: ClusterRecomputeRequest,
    user: dict = Depends(require_admin),
):
    """
    Re-run K-means clustering and replace cluster_assignments.
    Phase 2: actual scikit-learn K-means computation.
    Current: audit log entry + mock response.
    """
    actor_id = user.get("sub", "unknown")

    ADMIN_ACTIONS.labels(action_type="cluster.recompute").inc()

    try:
        from services.supabase_client import insert_audit_log

        audit_id = insert_audit_log(
            actor_id=actor_id,
            action="cluster.recompute",
            entity_type="cluster_assignments",
            metadata={
                "reference_year": request.reference_year,
                "n_clusters": request.n_clusters,
            },
        )

        return AdminActionResponse(
            status="success",
            message=(
                f"Rekomputasi {request.n_clusters} cluster untuk tahun "
                f"{request.reference_year} telah dimulai."
            ),
            audit_log_id=audit_id,
        )

    except RuntimeError:
        return AdminActionResponse(
            status="success",
            message=(
                f"Rekomputasi {request.n_clusters} cluster untuk tahun "
                f"{request.reference_year} telah dimulai (mock)."
            ),
        )
