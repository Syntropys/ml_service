"""
Common schemas shared across all API endpoints.
Defines error envelopes, enums, and health check models.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ModelName(str, Enum):
    """ML model identifiers for yield prediction."""
    lstm = "lstm"
    xgboost = "xgboost"
    random_forest = "random_forest"
    linear = "linear"


class JobStatus(str, Enum):
    """Status lifecycle for async forecast jobs."""
    queued = "queued"
    running = "running"
    done = "done"
    error = "error"


# ---------------------------------------------------------------------------
# Error Envelope  (design doc §7.5)
# ---------------------------------------------------------------------------

class ApiError(BaseModel):
    """Consistent error response — messages always in Bahasa Indonesia."""
    code: str = Field(..., examples=["auth/invalid-credentials"])
    message: str = Field(..., examples=["Kredensial tidak valid"])
    details: Any | None = None


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class ServiceHealth(BaseModel):
    """Health status of an individual dependency."""
    name: str
    status: str = Field(..., examples=["ok", "degraded", "down"])
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    """Aggregate health check response."""
    status: str = Field(..., examples=["ok", "degraded"])
    version: str
    services: list[ServiceHealth] = []
