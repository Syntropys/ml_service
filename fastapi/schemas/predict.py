"""
Schemas for /api/predict/* endpoints.
Covers both Paddy Disease Classification and Yield Prediction.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.common import ModelName


# ---------------------------------------------------------------------------
# Disease Prediction  (Soft Voting Ensemble → MLflow)
# ---------------------------------------------------------------------------

class DiseasePredictionRequest(BaseModel):
    """Base64-encoded image for disease classification."""
    image_base64: str = Field(
        ...,
        description="Base64-encoded paddy leaf image",
    )


class TopKPrediction(BaseModel):
    """A single class prediction with its probability."""
    class_name: str
    probability: float


class DiseasePredictionResponse(BaseModel):
    """
    Response from the Soft Voting Ensemble model.
    Maps to inference API output keys from handoff_manifest.json.
    """
    predicted_class: str = Field(..., examples=["bacterial_blight"])
    confidence: float = Field(..., examples=[0.92])
    top_k_predictions: list[TopKPrediction] = []
    model_used: str = Field(
        default="Paddy_SoftVoting_Ensemble/latest",
        description="Ensemble model identifier",
    )
    inference_time_ms: float | None = Field(
        None,
        description="End-to-end inference time in milliseconds",
    )


# ---------------------------------------------------------------------------
# Yield Prediction  (design doc §7.4 POST /api/predict/yield)
# ---------------------------------------------------------------------------

class YieldPredictionRequest(BaseModel):
    """Request body for paddy yield prediction."""
    region_id: str = Field(..., description="UUID of the target region")
    year: int = Field(..., ge=2018, le=2030, description="Target prediction year")
    model: ModelName = Field(..., description="ML model to use")


class YieldPredictionResponse(BaseModel):
    """
    Predicted yield with confidence intervals.
    Maps to design doc §7.4 POST /api/predict/yield response.
    """
    predicted_yield: float = Field(..., description="Predicted yield in ton/ha")
    predicted_prod_ton: float = Field(..., description="Predicted production in tons")
    confidence_lower: float = Field(..., description="95% CI lower bound")
    confidence_upper: float = Field(..., description="95% CI upper bound")
    model_version: str = Field(..., examples=["lstm_v1"])
