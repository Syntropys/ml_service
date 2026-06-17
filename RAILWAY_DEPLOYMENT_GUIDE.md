# 🚀 Panduan Deployment ML Service ke Railway

Dokumen ini memandu Anda melakukan *deployment* layanan **Agrolytics ML Service** (FastAPI Bridge + Paddy SoftVoting Ensemble Model) ke platform *cloud* **Railway**.

Platform Railway sangat cocok untuk arsitektur ini karena Anda dapat men-*deploy* langsung dari **GitHub Repository** dan **Docker Hub** secara bersamaan dalam satu *Project*, serta menghubungkan keduanya melalui jaringan privat internal yang aman.

---

## Tahap 1: Persiapan Repositori & Image

1. **GitHub:** Pastikan Anda telah meng-*commit* dan mem-*push* seluruh kode (termasuk folder `ml_service/fastapi`) ke repositori GitHub Anda.
2. **Docker Hub:** Pastikan *image* Docker model MLflow (`agrolytics/agrolytics_paddy_softvoting_ensemble:v1`) sudah 100% terunggah ke Docker Hub.

---

## Tahap 2: Membuat Proyek Railway Baru

1. Buka [Railway.app](https://railway.app/) dan masuk menggunakan akun GitHub Anda.
2. Klik tombol **New Project** di *Dashboard*.
3. Pilih **Empty Project** (Proyek Kosong).

Di dalam proyek ini, kita akan membangun dua *service* utama:
- **ML Model Service** (Berisi model *machine learning* raksasa dari Docker Hub).
- **FastAPI Bridge** (Jembatan komunikasi dari GitHub).

---

## Tahap 3: Deploy Model AI (Docker Image)

Terdapat dua skenario untuk men-*deploy* model Anda:

### Opsi A: Menggunakan Image dari Docker Hub (Setup Cepat / Default)
Karena *image* berukuran besar (>1.6 GB), menariknya dari Docker Hub jauh lebih efisien.
1. Di proyek Railway Anda, klik **New** -> **Docker Image**.
2. Masukkan nama *image*: `agrolytics/agrolytics_paddy_softvoting_ensemble:v1`
3. Tekan **Enter** agar Railway mulai menarik *image*.

### Opsi B: Build Image Secara Lokal via Docker Compose
Jika direktori repositori *machine learning* (`paddy_detection`) sudah tersedia secara lokal dan posisinya berdampingan dengan direktori ini (`ml_service`), Anda tidak perlu lagi masuk ke dalam foldernya secara manual!

Cukup manfaatkan file `docker-compose.yml` yang sudah dikonfigurasi untuk melakukan kompilasi (*build*) secara otomatis:
```bash
# Pastikan Anda berada di direktori agrolytics/ml_service
docker-compose build ml-service

# Setelah build berhasil, push image ke Docker Hub
docker push agrolytics/agrolytics_paddy_softvoting_ensemble:v1
```
*Setelah proses push selesai, lanjutkan ke langkah konfigurasi Railway di Opsi A.*

### 🛠️ Mengamankan Konfigurasi MLflow
Railway dan *docker-compose* telah dikonfigurasikan untuk mengalokasikan (me-*mount*) folder `mlruns` dan berkas `mlruns.db` di dalam `ml-service` maupun `fastapi-ml-bridge`. Hal ini memastikan seluruh metrik *tracking* MLflow dipusatkan pada satu tempat meskipun kontainer mati-nyala.

4. **Konfigurasi Tambahan di Railway:**
   - Klik *service* tersebut, buka tab **Settings**.
   - Ubah **Service Name** menjadi `ml-service` agar rapi dan mudah dikenali.
   - Gulir ke bagian **Networking** -> **Private Network**.
   - Railway akan secara otomatis membaca *port* dari Docker (contoh: 8080 atau 8000). Catat domain privat internalnya (contoh: `ml-service.railway.internal`).

---

## Tahap 4: Deploy FastAPI Bridge (via GitHub)

Ini adalah *backend* utama yang akan diakses oleh *frontend* Next.js/Vercel Anda.

1. Kembali ke proyek Railway, klik **New** -> **GitHub Repo**.
2. Pilih repositori **agrolytics** milik Anda.
3. *Service* baru akan muncul. **Segera hentikan proses build-nya** (atau biarkan gagal sementara) karena direktori *root*-nya belum diatur!
4. Klik *service* GitHub tersebut, lalu buka tab **Settings**.
5. Gulir ke bagian **Build**:
   - Cari kolom **Root Directory**.
   - Isi dengan path menuju *backend*: `/fastapi` (karena repositori GitHub Anda sudah bernama `ml_service`, maka foldernya langsung berada di *root*).
   - Railway kini akan mem-*build* menggunakan `Dockerfile` yang ada di dalam folder `/fastapi` tersebut.

### Konfigurasi Variabel Lingkungan (.env)

Agar FastAPI dapat terhubung ke Supabase dan Model ML, kita perlu memasukkan *Environment Variables*:

1. Buka tab **Variables** di *service* FastAPI Anda.
2. Tambahkan variabel berikut satu per satu:

| Variable Name | Value / Keterangan |
| :--- | :--- |
| `ML_SERVICE_URL` | `http://ml-service.railway.internal:8080` (Sesuaikan domain internal dan port dengan Tahap 3) |
| `SUPABASE_URL` | `https://[PROJECT-ID].supabase.co` |
| `SUPABASE_ANON_KEY` | `ey...` (Kunci `anon` dari dashboard API Supabase) |
| `SUPABASE_SERVICE_ROLE_KEY` | `ey...` (Kunci rahasia `service_role` Supabase) |
| `SUPABASE_JWT_SECRET` | Kunci otentikasi JWT Supabase Anda |
| `DEBUG` | `false` |

---

## Tahap 5: Ekspos FastAPI ke Publik (Vercel)

Agar halaman *Frontend* Anda bisa melakukan pemanggilan (*fetch*) API ke layanan ini:

1. Di *service* FastAPI, buka tab **Settings**.
2. Gulir ke bawah ke bagian **Networking**.
3. Di bawah **Public Networking**, klik tombol **Generate Domain**.
4. Railway akan membuatkan URL publik dengan SSL (contoh: `fastapi-bridge-production.up.railway.app`).
5. **Selesai!** Salin URL publik ini, buka proyek Vercel Anda (atau file `.env.local` frontend), lalu masukkan sebagai nilai untuk variabel `NEXT_PUBLIC_API_URL`.

---

## 📊 Integrasi Metrik & Pemantauan (Opsional)

**Catatan tentang Prometheus & Grafana:**  
Untuk efisiensi dan penghematan biaya produksi (*production*) awal, sebaiknya **jangan** melakukan *deploy* Prometheus dan Grafana secara terpisah di Railway.
Platform Railway sudah memiliki fitur **Metrics Dashboard** bawaan secara gratis untuk setiap *service* yang berjalan (memonitor CPU, RAM, dan *Network Requests*). 

Jika di kemudian hari Anda membutuhkan analisis tingkat lanjut (seperti RED metrics dan kustomisasi kueri PromQL), barulah Anda menambahkan layanan Prometheus menggunakan volume persisten di Railway.
