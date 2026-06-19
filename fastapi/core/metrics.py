"""
Prometheus custom metrics for the Paddy ML Bridge API.

These metrics complement the auto-instrumented FastAPI metrics provided by
``prometheus-fastapi-instrumentator`` (request rate, duration, error rate).
"""
from prometheus_client import Counter, Gauge, Histogram, Summary

# ---------------------------------------------------------------------------
# Disease Prediction Metrics
# ---------------------------------------------------------------------------

PREDICTION_REQUESTS = Counter(
    "paddy_disease_predictions_total",
    "Total number of disease prediction requests received",
)

PREDICTED_CLASS_COUNTER = Counter(
    "paddy_predicted_class_total",
    "Total predictions per disease class",
    ["predicted_class"],
)

CONFIDENCE_GAUGE = Gauge(
    "paddy_prediction_confidence",
    "Confidence score of the most recent prediction",
    ["predicted_class"],
)

INFERENCE_LATENCY = Summary(
    "paddy_inference_latency_seconds",
    "Time spent running the ML inference (end-to-end including network)",
)

# ---------------------------------------------------------------------------
# Yield Prediction Metrics
# ---------------------------------------------------------------------------

YIELD_PREDICTION_REQUESTS = Counter(
    "paddy_yield_predictions_total",
    "Total number of yield prediction requests",
    ["model_name", "region_id"],
)

YIELD_PREDICTION_LATENCY = Histogram(
    "paddy_yield_prediction_duration_seconds",
    "Duration of yield prediction lookups",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

# ---------------------------------------------------------------------------
# Forecast Job Metrics
# ---------------------------------------------------------------------------

FORECAST_JOBS_CREATED = Counter(
    "paddy_forecast_jobs_created_total",
    "Total forecast jobs created",
)

FORECAST_JOBS_COMPLETED = Counter(
    "paddy_forecast_jobs_completed_total",
    "Total forecast jobs completed successfully",
)

FORECAST_JOBS_FAILED = Counter(
    "paddy_forecast_jobs_failed_total",
    "Total forecast jobs that failed",
)

# ---------------------------------------------------------------------------
# Admin Action Metrics
# ---------------------------------------------------------------------------

ADMIN_ACTIONS = Counter(
    "paddy_admin_actions_total",
    "Total admin actions performed",
    ["action_type"],
)

# ---------------------------------------------------------------------------
# Service Health Gauges
# ---------------------------------------------------------------------------

ML_SERVICE_HEALTHY = Gauge(
    "paddy_ml_service_healthy",
    "Whether the ML service is reachable (1=healthy, 0=down)",
)

SUPABASE_HEALTHY = Gauge(
    "paddy_supabase_healthy",
    "Whether Supabase is reachable (1=healthy, 0=down)",
)
