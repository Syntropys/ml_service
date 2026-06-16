"""
Forecast Engine Service — manages async forecast job lifecycle.

Phase 2 initial: in-memory job queue.
Future: backed by Supabase ``forecast_jobs`` table.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from schemas.common import JobStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory job store (Phase 2 MVP — migrate to Supabase later)
# ---------------------------------------------------------------------------

_jobs: dict[str, dict[str, Any]] = {}


def create_job(
    region_id: str,
    horizon: int,
    models: list[str],
    user_id: str,
    custom_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a new forecast job entry.
    Returns the job dict with status='queued'.
    """
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "region_id": region_id,
        "horizon": horizon,
        "models": models,
        "custom_inputs": custom_inputs,
        "user_id": user_id,
        "status": JobStatus.queued.value,
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _jobs[job_id] = job
    logger.info("Forecast job created: %s (region=%s, horizon=%d)", job_id, region_id, horizon)
    return job


def get_job(job_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    """
    Retrieve a job by ID.
    If user_id is provided, only return the job if it belongs to that user.
    """
    job = _jobs.get(job_id)
    if job is None:
        return None
    if user_id and job.get("user_id") != user_id:
        return None
    return job


def update_job_status(
    job_id: str,
    status: JobStatus,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any] | None:
    """Update job status and optionally set result or error."""
    job = _jobs.get(job_id)
    if job is None:
        return None
    job["status"] = status.value
    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    if result is not None:
        job["result"] = result
    if error is not None:
        job["error"] = error
    return job


def list_jobs(user_id: str | None = None) -> list[dict[str, Any]]:
    """List all jobs, optionally filtered by user."""
    if user_id:
        return [j for j in _jobs.values() if j.get("user_id") == user_id]
    return list(_jobs.values())
