# 🚀 Panduan MLOps: Deploy Agrolytics ke Railway (Free Tier)

> **Arsitektur v3.0** — Single service dengan embedded models.  
> Cocok untuk Railway free tier ($5 trial / 1 bulan).

---

## Prasyarat

- Akun GitHub (baru atau existing)
- Akun [Railway.app](https://railway.app/) (signup gratis via GitHub)
- Model TFLite dari Google Drive (opsional, untuk disease detection)

---

## Langkah 1: Fork Repository

1. Buka [github.com/Syntropys/ml_service](https://github.com/Syntropys/ml_service)
2. Klik **Fork** → pilih akun GitHub kamu
3. Pastikan branch `dev` ter-fork

> **Alternatif** (jika pakai akun GitHub baru):
> ```bash
> git clone https://github.com/Syntropys/ml_service.git
> cd ml_service
> git remote set-url origin https://github.com/AKUN_BARU/ml_service.git
> git push -u origin dev
> ```

---

## Langkah 2: Upload Model Files (Opsional)

### A. XGBoost (sudah included)
File `fastapi/models/predictive/xgboost.joblib` (0.47 MB) sudah ada di repo.
Predictive analytics langsung jalan tanpa setup tambahan.

### B. Disease Detection TFLite (download dari Google Drive)
1. Download dari: [Google Drive - TFLite Models](https://drive.google.com/drive/folders/16dD8uWfEgzGmnSivoeHQ5gGtINxSsL_T?usp=drive_link)
2. Copy `mobilenet_v1.tflite` (9.7 MB) dan `densenet.tflite` (27.6 MB) ke:
   ```
   fastapi/models/disease/mobilenet_v1.tflite
   fastapi/models/disease/densenet.tflite
   ```
3. Commit & push:
   ```bash
   # TFLite files are in .gitignore, so force add:
   git add -f fastapi/models/disease/*.tflite
   git commit -m "feat(models): add TFLite disease detection models"
   git push
   ```

> **Tanpa file TFLite**: API akan tetap jalan, tapi disease detection
> akan return error. Predictive analytics tetap berfungsi normal.

---

## Langkah 3: Buat Project Railway

1. Buka [railway.app](https://railway.app/) → **Login with GitHub**
2. Klik **New Project** → **Deploy from GitHub repo**
3. Pilih repo `ml_service` yang sudah di-fork
4. Railway akan mulai build otomatis — **hentikan dulu** (atau biarkan gagal)

---

## Langkah 4: Konfigurasi Service

### A. Set Root Directory
1. Klik service yang baru dibuat
2. Buka tab **Settings**
3. Di bagian **Build** → **Root Directory**: isi `/fastapi`
4. Railway akan menggunakan `Dockerfile` di dalam folder `/fastapi`

### B. Set Environment Variables
Buka tab **Variables** dan tambahkan:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | `https://mawewomqcdnsqnxmkjlq.supabase.co` |
| `SUPABASE_ANON_KEY` | `eyJ...` (dari Supabase dashboard) |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` (dari Supabase dashboard) |
| `SUPABASE_JWT_SECRET` | JWT secret dari Supabase |
| `DEBUG` | `false` |

### C. Deploy
1. Klik **Deploy** atau push commit baru ke trigger auto-deploy
2. Tunggu build selesai (~3-5 menit)
3. Cek **Deploy Logs** untuk memastikan:
   ```
   🚀 Starting Paddy ML Bridge API v3.0.0
      Model directory: /app/models
      XGBoost model loaded from /app/models/predictive/xgboost.joblib
   ```

---

## Langkah 5: Generate Public URL

1. Di service Railway, buka tab **Settings**
2. Scroll ke **Networking** → **Public Networking**
3. Klik **Generate Domain**
4. Catat URL (contoh: `agrolytics-ml-production.up.railway.app`)

---

## Langkah 6: Hubungkan ke Frontend

Di file `.env.local` frontend (atau Vercel dashboard):

```env
VITE_DISEASE_API_URL=https://agrolytics-ml-production.up.railway.app
```

Frontend akan memanggil:
- `POST /api/predict/disease/upload` → Disease detection
- `POST /api/predict/yield` → Yield prediction
- `POST /api/forecast/custom` → Custom forecast
- `GET /api/health` → Health check

---

## Verifikasi

### Test Health
```bash
curl https://YOUR-RAILWAY-URL.up.railway.app/api/health
```

Response:
```json
{
  "status": "ok",
  "version": "3.0.0",
  "services": [
    {"name": "disease-model", "status": "ok"},
    {"name": "predictive-model", "status": "ok"},
    {"name": "supabase", "status": "ok"}
  ]
}
```

### Test Disease Detection
```bash
curl -X POST https://YOUR-RAILWAY-URL.up.railway.app/api/predict/disease/upload \
  -F file=@foto_daun_padi.jpg
```

### Test Yield Prediction
```bash
curl -X POST https://YOUR-RAILWAY-URL.up.railway.app/api/predict/yield \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT" \
  -d '{"region_id": "uuid", "year": 2026, "model": "xgboost"}'
```

---

## Estimasi Resource Railway Free Tier

| Komponen | RAM | Disk |
|----------|-----|------|
| FastAPI + Uvicorn | ~50 MB | - |
| tflite-runtime | ~30 MB | 5 MB |
| 2x TFLite models | ~80 MB | 37 MB |
| XGBoost + scikit-learn | ~50 MB | 0.5 MB |
| Python + deps | ~100 MB | ~200 MB |
| **Total** | **~310 MB** | **~243 MB** |
| Railway Free Tier Limit | **512 MB** | **1 GB** |

✅ Muat di free tier!

---

## Troubleshooting

### Build gagal: `tflite-runtime` not found
Beberapa platform tidak support `tflite-runtime`. Ganti di `requirements.txt`:
```
# Hapus tflite-runtime, gunakan tensorflow-cpu
tensorflow-cpu>=2.14.0
```
⚠️ Ini akan menambah ~300 MB RAM. Mungkin melebihi free tier.

### Disease detection error: "Model belum dimuat"
TFLite files belum di-upload. Ikuti Langkah 2B di atas.

### Memory exceeded (OOMKilled)
Upgrade ke Railway Hobby plan ($5/bulan, 8 GB RAM) atau nonaktifkan
disease detection (hapus TFLite files, hanya gunakan XGBoost).

---

## Arsitektur

```
┌──────────────────────────────────────────────────┐
│  Railway (1 Service, ~310 MB RAM)                │
│                                                  │
│  FastAPI v3.0 — Embedded Models                  │
│  ├── /api/predict/disease/upload                 │
│  │   └── TFLite Ensemble (in-process)            │
│  │       ├── MobileNetV2 (9.7 MB, w=0.4954)      │
│  │       └── DenseNet121 (27.6 MB, w=0.5046)      │
│  ├── /api/predict/yield                          │
│  │   └── XGBoost .joblib (0.47 MB, in-process)   │
│  ├── /api/forecast/custom                        │
│  │   └── XGBoost .joblib (shared)                │
│  ├── /api/health                                 │
│  └── /metrics (Prometheus)                       │
│                                                  │
│  Connects to: Supabase (external)                │
└──────────────────────────────────────────────────┘
```
