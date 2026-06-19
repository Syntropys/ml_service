# 🌾 Agrolytics ML Service

![Status](https://img.shields.io/badge/Repo_Status-Completed-1F2937?style=flat-square)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-1F2937?style=flat-square)](https://github.com/Syntropys/ml_service/blob/main/LICENSE)
[![Lead Dev](https://img.shields.io/badge/Lead_Dev-@Zevhys-1F2937?style=flat-square)]()
[![Dev](https://img.shields.io/badge/Dev-@brayone--no--xv-1F2937?style=flat-square)]()
![Created](https://img.shields.io/badge/Created-19--May--2026-1F2937?style=flat-square)
![Version](https://img.shields.io/badge/Version-v3.0.0-1F2937?style=flat-square)
![Repo Size](https://img.shields.io/github/repo-size/Syntropys/ml_service?label=Repo%20Size&color=1F2937&style=flat-square)
![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FSyntropys%2Fml_service&countColor=%231F2937&style=flat-square&labelStyle=none)
[![Issues Welcome](https://img.shields.io/badge/Issues-Welcome-1F2937.svg?style=flat-square)](https://github.com/Syntropys/ml_service/issues)
[![Pull Requests Welcome](https://img.shields.io/badge/Pull%20Requests-Welcome-1F2937.svg?style=flat-square)](https://github.com/Syntropys/ml_service/pulls)

Unified ML inference service for the **Agrolytics** Smart Agricultural BI platform. Single-service architecture with embedded TFLite ensemble and XGBoost models — optimized for Railway free tier (~310 MB RAM).

# 🏗️ Architecture

```
Frontend (Vercel) → FastAPI Bridge (Railway) → Supabase (PostgreSQL)
                         ↓
                  Embedded Models:
                  ├── Disease Detection (TFLite Ensemble)
                  └── Yield Prediction (XGBoost)
```

### What changed in v3.0?
- **Before**: 3 separate containers (FastAPI Bridge + ML Service + Predictive ML Service) connected via HTTP. Required Docker Hub images, MLflow serving, ~2 GB RAM.
- **Now**: 1 single service with models loaded in-process. ~310 MB RAM. No external ML containers needed.

# 🛠 Tech Stack

<img src="https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white"/> <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/> <img src="https://img.shields.io/badge/TFLite-FF6F00?style=flat-square&logo=tensorflow&logoColor=white"/> <img src="https://img.shields.io/badge/XGBoost-EC4E20?style=flat-square"/> <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white"/> <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white"/> <img src="https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white"/> <img src="https://img.shields.io/badge/Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white"/> <img src="https://img.shields.io/badge/Prometheus-E6522C?style=flat-square&logo=prometheus&logoColor=white"/>

| Layer | Technology | Purpose |
| :---- | :--------- | :------ |
| **Framework** | FastAPI + Uvicorn | Async REST API server |
| **Disease ML** | tflite-runtime (DenseNet121 + MobileNetV2) | 10-class paddy disease ensemble |
| **Predictive ML** | XGBoost + scikit-learn | Yield prediction (ton/ha) |
| **Database** | Supabase PostgreSQL | Data storage with JWT auth |
| **Monitoring** | Prometheus metrics | `/metrics` endpoint |
| **Container** | Docker (Python 3.12 slim) | Reproducible builds |
| **Hosting** | Railway | Auto-deploy from Git |

# 📡 API Endpoints

| Method | Path | Description | Auth |
| :----- | :--- | :---------- | :--- |
| `POST` | `/api/predict/disease` | Disease classification (base64 image) | Optional |
| `POST` | `/api/predict/disease/upload` | Disease classification (file upload) | Optional |
| `POST` | `/api/predict/yield` | Yield prediction | JWT |
| `POST` | `/api/forecast/custom` | Custom forecast job | JWT |
| `GET` | `/api/forecast/jobs/{id}` | Forecast job status | JWT |
| `GET` | `/api/health` | Health check (services status) | No |
| `GET` | `/metrics` | Prometheus metrics | No |
| `GET` | `/docs` | Swagger UI documentation | No |

# 🧠 Models

| Model | Type | Size | Target |
| :---- | :--- | :--- | :----- |
| Disease Ensemble | TFLite (DenseNet121 + MobileNetV2) | 37 MB | 10-class paddy disease |
| XGBoost | joblib | 0.47 MB | Yield prediction (ton) |

# 🚀 Getting Started

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Syntropys/ml_service.git
   cd ml_service
   ```

2. **Set up environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your Supabase keys
   ```

3. **(Optional) Add TFLite model files:**

   ```bash
   # Download from Google Drive and place in fastapi/models/disease/
   # See fastapi/models/README.md for details
   ```

4. **Run with Docker:**

   ```bash
   docker compose up --build
   ```

5. **Test:**

   ```bash
   curl http://localhost:8000/api/health
   curl http://localhost:8000/docs  # Swagger UI
   ```

# 🚂 Deploy to Railway

See [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md) for step-by-step instructions.

# 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements or want to report an issue, feel free to open a pull request or create an issue. Thank you for helping to make this project better!

# ⚖️ License

This project is licensed under the GNU AGPLv3. See the [LICENSE](LICENSE) file for more details.
