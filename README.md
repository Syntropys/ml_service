# 🌾 Agrolytics ML Bridge API v3.0

> Unified ML service for the **Agrolytics** Smart Agricultural BI platform.
> Single-service architecture with embedded models — optimized for Railway free tier.

## Architecture

```
Frontend (Vercel) → FastAPI Bridge (Railway) → Supabase (PostgreSQL)
                         ↓
                  Embedded Models:
                  ├── Disease Detection (TFLite Ensemble)
                  └── Yield Prediction (XGBoost)
```

### What changed in v3.0?
- **Before**: 3 separate containers (FastAPI Bridge + ML Service + Predictive ML Service) 
  connected via HTTP. Required Docker Hub images, MLflow serving, ~2 GB RAM.
- **Now**: 1 single service with models loaded in-process. ~310 MB RAM. 
  No external ML containers needed.

## Quick Start (Local)

```bash
# 1. Clone & enter
git clone https://github.com/Syntropys/ml_service.git
cd ml_service

# 2. Set up env
cp .env.example .env
# Edit .env with your Supabase keys

# 3. (Optional) Add TFLite model files for disease detection
# Download from Google Drive and place in fastapi/models/disease/
# See fastapi/models/README.md for details

# 4. Run with Docker (v3.0 Single-Service)
docker compose up --build

# 5. Test
curl http://localhost:8000/api/health
curl http://localhost:8000/docs  # Swagger UI
```

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/predict/disease` | Disease classification (base64) | Optional |
| `POST` | `/api/predict/disease/upload` | Disease classification (file) | Optional |
| `POST` | `/api/predict/yield` | Yield prediction | JWT |
| `POST` | `/api/forecast/custom` | Custom forecast job | JWT |
| `GET` | `/api/forecast/jobs/{id}` | Forecast job status | JWT |
| `GET` | `/api/health` | Health check | No |
| `GET` | `/metrics` | Prometheus metrics | No |
| `GET` | `/docs` | Swagger UI | No |

## Models

| Model | Type | Size | Target |
|-------|------|------|--------|
| Disease Ensemble | TFLite (DenseNet121 + MobileNetV2) | 37 MB | 10-class paddy disease |
| XGBoost | joblib | 0.47 MB | Yield prediction (ton) |

## Deploy to Railway

See [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md) for step-by-step instructions.

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **ML Runtime**: tflite-runtime (disease), XGBoost + scikit-learn (predictive)
- **Database**: Supabase PostgreSQL
- **Auth**: Supabase JWT
- **Monitoring**: Prometheus metrics
- **Container**: Docker (Python 3.12 slim)

## License

See [LICENSE](LICENSE).
