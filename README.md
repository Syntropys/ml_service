# ⚡ Agrolytics Model Inference API

![Status](https://img.shields.io/badge/Repo_Status-Evolving-1F2937?style=flat-square)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-1F2937?style=flat-square)](https://github.com/Syntropys/ml_service/blob/main/LICENSE)
[![Lead Dev](https://img.shields.io/badge/Lead_Dev-@Zevhys-1F2937?style=flat-square)]()
[![Dev](https://img.shields.io/badge/Dev-@brayone--no--xv-1F2937?style=flat-square)]()
[![Dev](https://img.shields.io/badge/Dev-@rohidrivaldi-1F2937?style=flat-square)]()
![Created](https://img.shields.io/badge/Created-18--May--2026-1F2937?style=flat-square)
![Version](https://img.shields.io/badge/Version-v0.1.0--beta-1F2937?style=flat-square)
![Repo Size](https://img.shields.io/github/repo-size/Syntropys/ml_service?label=Repo%20Size&color=1F2937&style=flat-square)
![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FSyntropys%2Fml_service&countColor=%231F2937&style=flat-square&labelStyle=none)
[![Issues Welcome](https://img.shields.io/badge/Issues-Welcome-1F2937.svg?style=flat-square)](https://github.com/Syntropys/ml_service/issues)
[![Pull Requests Welcome](https://img.shields.io/badge/Pull%20Requests-Welcome-1F2937.svg?style=flat-square)](https://github.com/Syntropys/ml_service/pulls)

This repository holds the backend API for the **Agrolytics** machine learning project. It acts as the bridge between our trained models and the frontend web interface. The main job of this service is to handle incoming data securely via Supabase JWT, perform real-time inference using our specialized MLflow containers, and smoothly deliver the prediction results back to the user.

## 🛠 Tech Stack

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white"/> <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/> <img src="https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white"/> <img src="https://img.shields.io/badge/Uvicorn-499848?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMyAyTDQuMDkzIDEyLjY4OGMtLjM0Ny40MTYtLjUyMS42MjQtLjUyMy44LS4wMDIuMTUzLjA2Ni4yOTguMTg1LjM5NS4xMzcuMTEyLjQwOC4xMTIuOTQ5LjExMmg2LjI5NkwxMSAyMmw4LjkwNy0xMC42ODhjLjM0Ny0uNDE2LjUyMS0uNjI0LjUyMy0uOC4wMDItLjE1My0uMDY2LS4yOTgtLjE4NS0uMzk1LS4xMzctLjExMi0uNDA4LS4xMTItLjk0OS0uMTEySDEzVjJ6Ii8+PC9zdmc+&logoColor=white"/> <img src="https://img.shields.io/badge/Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white"/> <img src="https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white"/> <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white"/> <img src="https://img.shields.io/badge/Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white"/> <img src="https://img.shields.io/badge/MLflow-0194E2?style=flat-square&logo=mlflow&logoColor=white"/> <img src="https://img.shields.io/badge/Prometheus-E6522C?style=flat-square&logo=prometheus&logoColor=white"/> <img src="https://img.shields.io/badge/Grafana-F46800?style=flat-square&logo=grafana&logoColor=white"/>

---

## 🏗️ Architecture Overview

The backend uses a **Bridge Pattern Architecture** to completely decouple the API Gateway from the heavy Machine Learning inference workloads. 

1. **FastAPI Bridge (`fastapi-ml-bridge`)**: A lightweight gateway that authenticates requests using Supabase, validates inputs, and acts as a reverse proxy.
2. **Disease Classification Service (`ml-service`)**: An MLflow-served container using a SoftVoting Ensemble (MobileNetV1 + DenseNet121) built on TensorFlow 2.15.
3. **Predictive Analytics Service (`predictive-ml-service`)**: An MLflow-served container using Scikit-Learn models for agricultural yield predictions.
4. **MLOps Monitoring**: MLflow server for experiment tracking, alongside Prometheus and Grafana for system and model metrics.

---

## 🚀 Setup & MLOps Infrastructure

Follow these steps to spin up the entire local development environment including the API Gateway, Machine Learning models, and the MLOps monitoring stack.

### 1. Prerequisites
- **Git** installed on your system.
- **Docker & Docker Compose** installed.
- **Python 3.10+** (if running the FastAPI bridge natively).

### 2. Clone the Repository
```bash
git clone https://github.com/Syntropys/ml_service.git
cd ml_service
```

### 3. Environment Configuration
Copy the sample environment file and adjust it to your needs.
```bash
cp .env.example .env
```
Inside your `.env` file, configure the following:
```ini
# Supabase Configuration (Required for Authentication)
SUPABASE_URL=https://mawewomqcdnsqnxmkjlq.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

# ML Services URLs (Handled automatically by Docker Compose)
ML_SERVICE_URL=http://ml-service:8080
PREDICTIVE_ML_SERVICE_URL=http://predictive-ml-service:8080
```

### 4. Running the Complete Infrastructure (Docker Compose)
We use Docker Compose to orchestrate the entire ML ecosystem.

```bash
docker compose up -d --build
```

This single command will spin up the following containers:
- 🟢 **FastAPI Gateway**: `http://localhost:8000`
- 🧠 **Disease Classification ML**: `http://localhost:5000` (Internal: 8080)
- 📈 **Predictive Analytics ML**: `http://localhost:5002` (Internal: 8080)
- 📊 **MLflow Tracking Server**: `http://localhost:5001`
- 🔭 **Prometheus**: `http://localhost:9090`
- 📉 **Grafana**: `http://localhost:3000`

### 5. Verify the Installation
Check if the API Gateway is running correctly by accessing the health endpoint:
```bash
curl http://localhost:8000/api/health
```

---

## 🔌 API Endpoints

Once running, you can access the interactive Swagger UI documentation provided automatically by FastAPI:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

### Key Endpoints:
- `GET /api/health` — Check system status and ML service connectivity.
- `POST /api/predict/disease/upload` — Upload an image (Paddy leaf) for disease classification (Requires Bearer Token).
- `POST /api/predict/yield` — Submit agricultural parameters to get crop yield predictions (Requires Bearer Token).

*Note: All prediction endpoints require a valid Supabase JWT token passed in the `Authorization: Bearer <token>` header.*

---

## 📈 MLOps Tracking & Monitoring

Our infrastructure provides deep observability into the ML models and the system.

- **MLflow Tracking Dashboard (`http://localhost:5001`)**: View experiment runs, model versions, artifacts, and parameters.
- **Prometheus (`http://localhost:9090`)**: Scrapes hardware and application metrics from the Docker containers.
- **Grafana (`http://localhost:3000`)**: Visualizes Prometheus metrics. Use this to monitor GPU/CPU usage, inference latency, and memory consumption during high-load periods.

---

## 🚢 Production Deployment (Railway)

This repository is optimized for deployment on **Railway.app** using separate services for each component.

1. **Deploy FastAPI Bridge**:
   - Connect Railway to the GitHub repository.
   - Set the `Root Directory` to `/fastapi`.
   - Add all `.env` variables in the Railway dashboard.
2. **Deploy ML Services**:
   - Deploy the models directly from Docker Hub or Railway CLI using their respective `Dockerfile`s (which include `EXPOSE 8080`).
   - For detailed Railway instructions, see [`RAILWAY_DEPLOYMENT_GUIDE.md`](./RAILWAY_DEPLOYMENT_GUIDE.md).

---

## 🧪 Testing

To run the unit and integration tests locally using `pytest`:

```bash
# Ensure you are in a virtual environment
pip install -r requirements.txt
pip install pytest httpx

# Run tests
pytest tests/ -v
```

---

## 🤝 Contributing

Contributions are very welcome! We are always looking for ways to improve inference latency and model accuracy. 

1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add some amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

If you encounter any issues with the ML setup, please create an issue!

---

## ⚖️ License

This project is licensed under the GNU AGPLv3. See the [LICENSE](LICENSE) file for more details.