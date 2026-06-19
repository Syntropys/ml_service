"""
Schemas for /api/admin/* endpoints.
Handles data ingestion triggers and cluster recomputation.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# BPS Ingestion  (design doc §7.4 POST /api/admin/ingest/bps)
# ---------------------------------------------------------------------------

class BpsIngestRequest(BaseModel):
    """Trigger BPS production data ingestion for a given year."""
    year: int = Field(..., ge=2015, le=2030, description="Target ingestion year")
    source_url: str | None = Field(
        None,
        description="Optional URL to a BPS data source (CSV/API)",
    )


# ---------------------------------------------------------------------------
# NASA POWER Ingestion  (design doc §7.4 POST /api/admin/ingest/nasa)
# ---------------------------------------------------------------------------

class NasaIngestRequest(BaseModel):
    """Trigger NASA POWER weather data ingestion for a year range."""
    year_from: int = Field(..., ge=2015, le=2030)
    year_to: int = Field(..., ge=2015, le=2030)


# ---------------------------------------------------------------------------
# Cluster Recompute  (design doc §7.4 POST /api/admin/cluster/recompute)
# ---------------------------------------------------------------------------

class ClusterRecomputeRequest(BaseModel):
    """Re-run K-means clustering for a reference year."""
    reference_year: int = Field(..., ge=2015, le=2030)
    n_clusters: int = Field(default=3, ge=2, le=10)


# ---------------------------------------------------------------------------
# Admin Responses
# ---------------------------------------------------------------------------

class AdminActionResponse(BaseModel):
    """Generic response for admin actions."""
    status: str = Field(..., examples=["success", "queued"])
    message: str
    rows_affected: int | None = None
    audit_log_id: str | None = Field(
        None,
        description="UUID of the audit_log entry created for this action",
    )
