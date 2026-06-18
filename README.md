# Agrolytics ML Service & FastAPI Bridge

Ini adalah repositori utama untuk layanan Backend dan Machine Learning dari **Agrolytics**. Infrastruktur ini menggunakan **FastAPI** sebagai *API Gateway* dan mengandalkan **Docker Compose** untuk menjalankan model-model AI secara terdekopel (Microservices).

## Setup Lokal (Tanpa Repositori `ai_models`)

Seandainya Anda ingin men-setup Agrolytics di lingkungan lokal namun **belum memiliki** atau tidak ingin mengunduh direktori `ai_models` (yang ukurannya sangat besar), Anda dapat langsung menarik (*pull*) *Docker Image* model AI tersebut dari Docker Hub.

File `docker-compose.yml` di direktori ini sudah dikonfigurasi untuk secara otomatis mengunduh image berikut:

- **Predictive Analytics (Random Forest)**:
  👉 [agrolytics/agrolytics_predictive_analytics](https://hub.docker.com/r/agrolytics/agrolytics_predictive_analytics)
- **Disease Classification (Ensemble CNN)**:
  👉 [agrolytics/agrolytics_disease_classification](https://hub.docker.com/r/agrolytics/agrolytics_disease_classification)

### Langkah-Langkah Menjalankan

1. **Siapkan Direktori Pelacakan (Tracking) MLflow**
   Agar Docker tidak salah mengenali file database sebagai folder ketika di-*mount*, Anda wajib membuat kerangka kosong `mlruns` dan `mlruns.db` di dalam direktori `ml_service` ini terlebih dahulu:
   ```bash
   mkdir -p mlruns
   touch mlruns.db
   ```

2. **Tarik Image dan Jalankan Tanpa Build**
   Karena file `docker-compose.yml` masih mempertahankan konfigurasi `build` untuk keperluan *development*, Anda yang **tidak memiliki** folder `ai_models` harus menariknya secara manual dari Docker Hub lalu menjalankannya dengan *flag* `--no-build` agar Docker tidak mencoba mencari folder yang hilang:
   ```bash
   # Tarik image dari Docker Hub
   docker-compose pull
   
   # Jalankan tanpa melakukan build lokal
   docker-compose up -d --no-build
   ```

Setelah selesai, FastAPI Bridge Anda akan menyala di `http://localhost:8000` dan siap melayani *request* dari *Frontend* tanpa perlu proses kompilasi model secara lokal!