"""
Schemas for /api/forecast/* endpoints.
Handles async forecast job creation and status queries.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from schemas.common import JobStatus, ModelName


# ---------------------------------------------------------------------------
# Forecast Custom  (design doc §7.4 POST /api/forecast/custom)
# ---------------------------------------------------------------------------

class ForecastCustomRequest(BaseModel):
    """
    Request for on-demand custom prediction (B3 hybrid).
    Enqueues a forecast_job for async execution.
    """
    region_id: str = Field(..., description="UUID of the target region")
    horizon: int = Field(..., ge=1, le=5, description="Forecast horizon in years")
    models: list[ModelName] = Field(
        ...,
        min_length=1,
        description="Models to include in the forecast",
    )
    custom_inputs: dict[str, Any] | None = Field(
        None,
        description="Optional custom parameters for the forecast",
    )


# ---------------------------------------------------------------------------
# Forecast Job Response  (design doc §7.4 GET /api/forecast/jobs/{job_id})
# ---------------------------------------------------------------------------

class ForecastJobResponse(BaseModel):
    """Status and result of a forecast job."""
    job_id: str = Field(..., description="UUID of the forecast job")
    status: JobStatus
    message: str | None = None
    result: dict[str, Any] | None = Field(
        None,
        description="Forecast result payload (available when status=done)",
    )
    error: str | None = Field(
        None,
        description="Error message (available when status=error)",
    )
