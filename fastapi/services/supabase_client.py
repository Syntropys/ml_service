"""
Supabase client service for server-side read/write operations.

Uses the **Service Role Key** to bypass RLS for admin operations
(data ingestion, cluster recomputation, audit logging).
For public reads, uses the Anon Key.
"""
from __future__ import annotations

import logging
from typing import Any

from supabase import Client, create_client

from core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client singletons
# ---------------------------------------------------------------------------

_admin_client: Client | None = None
_public_client: Client | None = None


def get_admin_client() -> Client:
    """
    Supabase client authenticated with the Service Role Key.
    Bypasses RLS — use only in admin-guarded endpoints.
    """
    global _admin_client
    if _admin_client is None:
        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_SERVICE_ROLE_KEY belum dikonfigurasi. "
                "Set variabel environment ini untuk mengaktifkan admin operations."
            )
        _admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _admin_client


def get_public_client() -> Client:
    """
    Supabase client authenticated with the Anon Key.
    Respects RLS policies — safe for user-facing reads.
    """
    global _public_client
    if _public_client is None:
        if not settings.SUPABASE_ANON_KEY:
            raise RuntimeError(
                "SUPABASE_ANON_KEY belum dikonfigurasi. "
                "Set variabel environment ini untuk mengaktifkan public reads."
            )
        _public_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
        )
    return _public_client


# ---------------------------------------------------------------------------
# Prediction reads (public / auth-gated via RLS)
# ---------------------------------------------------------------------------

def get_predictions_by_region(
    region_id: str,
    model_name: str | None = None,
    target_year: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch pre-computed predictions for a region from Supabase."""
    client = get_public_client()
    query = client.table("predictions").select("*").eq("region_id", region_id)
    if model_name:
        query = query.eq("model_name", model_name)
    if target_year:
        query = query.eq("target_year", target_year)
    response = query.execute()
    return response.data or []


def get_baseline_predictions(year: int) -> list[dict[str, Any]]:
    """Fetch baseline predictions for all regions for a given year."""
    client = get_public_client()
    response = (
        client.table("predictions")
        .select("*")
        .eq("target_year", year)
        .eq("is_baseline", True)
        .execute()
    )
    return response.data or []


# ---------------------------------------------------------------------------
# Admin write operations (requires Service Role Key)
# ---------------------------------------------------------------------------

def upsert_production_history(rows: list[dict[str, Any]]) -> int:
    """Bulk upsert BPS production data. Returns count of rows affected."""
    client = get_admin_client()
    response = client.table("production_history").upsert(
        rows,
        on_conflict="region_id,year,month",
    ).execute()
    return len(response.data) if response.data else 0


def upsert_weather_history(rows: list[dict[str, Any]]) -> int:
    """Bulk upsert NASA POWER weather data. Returns count of rows affected."""
    client = get_admin_client()
    response = client.table("weather_history").upsert(
        rows,
        on_conflict="region_id,year,month",
    ).execute()
    return len(response.data) if response.data else 0


def replace_cluster_assignments(
    reference_year: int,
    assignments: list[dict[str, Any]],
) -> int:
    """
    Replace cluster assignments for a reference year.
    Deletes existing entries for the year, then inserts new ones.
    """
    client = get_admin_client()

    # Delete existing assignments for this reference year
    client.table("cluster_assignments").delete().eq(
        "reference_year", reference_year
    ).execute()

    # Insert new assignments
    response = client.table("cluster_assignments").insert(assignments).execute()
    return len(response.data) if response.data else 0


def insert_audit_log(
    actor_id: str,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """
    Write an entry to the audit_log table.
    Returns the ID of the created log entry.
    """
    client = get_admin_client()
    row: dict[str, Any] = {
        "actor_id": actor_id,
        "action": action,
    }
    if entity_type:
        row["entity_type"] = entity_type
    if entity_id:
        row["entity_id"] = entity_id
    if metadata:
        row["metadata"] = metadata

    response = client.table("audit_log").insert(row).execute()
    if response.data:
        return response.data[0].get("id")
    return None


# ---------------------------------------------------------------------------
# Health Probe
# ---------------------------------------------------------------------------

def check_supabase_health() -> tuple[bool, float]:
    """
    Quick health check against the Supabase regions table (public read).
    Returns (is_healthy, latency_ms).
    """
    import time

    try:
        client = get_public_client()
        start = time.perf_counter()
        response = client.table("regions").select("id").limit(1).execute()
        latency_ms = (time.perf_counter() - start) * 1000
        return bool(response.data), latency_ms
    except Exception as exc:
        logger.warning("Supabase health check failed: %s", exc)
        return False, 0.0
