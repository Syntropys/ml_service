---
title: Agrolytics — Smart Agricultural BI Platform
status: approved
date: 2026-05-29
team: Pijak (PJK-GM030) × IBM Skillsbuild
authors:
  - Muhammad Rahman (MLOps & Deployment)
  - Muhammad Husain Ali Ridha (AI Engineer)
  - Siti Fitria Putri Hans (AI Engineer)
  - Muhammad Rakha Djauhari (Project Manager & QA)
  - M. Rohid Rivaldi (Front-End & AI Integration + MLOps)
---

# Agrolytics — Design Document

> Smart Agricultural Business Intelligence System untuk wilayah Kalimantan.
> Capstone project Tim Pijak × IBM Skillsbuild, durasi 5 minggu.

## 1. Executive Summary

Agrolytics adalah platform business intelligence berbasis AI yang membantu Dinas
Pertanian dan pelaku agribisnis Kalimantan mengubah data iklim NASA POWER + data
historis BPS (2018–2025) menjadi keputusan operasional. Output utama: prediksi
produktivitas padi per kabupaten, peta interaktif, clustering wilayah prioritas,
laporan PDF, dan dashboard analitik. Phase 1 (5 minggu capstone) fokus pada
pengalaman antarmuka end-to-end dengan data Supabase. Phase 2 (post-capstone)
menambahkan inference ML real-time, AI assistant, dan deteksi penyakit tanaman.

## 2. Decisions Recap

| # | Topik | Pilihan |
|---|---|---|
| 1 | Scope MVP | Phase 1 4 modul + Phase 2 mockup roadmap (opsi D) |
| 2 | Deployment | Phase 1 Vercel-only mock → Phase 2 Vercel + Railway proxy `/api/*` |
| 3 | Framework | Vite + React + TypeScript + React Router DOM (sesuai project.txt) |
| 4 | Auth & Roles | Supabase Auth + Cloudflare Turnstile + Google OAuth, 2-tier (Admin/User) |
| 5 | Map Granularity | Kabupaten/Kota Kalimantan (~56 wilayah) |
| 6 | Dashboard Modules | 5 user + 2 admin + 2 Phase 2 placeholder |
| 7 | Landing Page | 10 sections cinematic, floating glass header, parallax hero |
| 8 | Live Map Landing | Leaflet full interactive (real Supabase data, public RLS) |
| 9 | Theme | Dark Emerald + Gold accent, light theme switcher |
| 10 | Reports | A1 per-region (single kab × single tahun) + B2 multi-year overlay |
| 11 | Data | A3 Supabase from start + B3 hybrid prediction (Phase 2) |
| 12 | Polish | Bahasa Indonesia, smoke test + manual QA, Chrome desktop only |

## 3. System Architecture

### 3.1 Phase 1 (Capstone, 5 minggu) — Vercel-only

```
                  ┌──────────────────────────────────┐
                  │      User Browser (Chrome)       │
                  │  Dark/Light theme, desktop-first │
                  └────────────┬─────────────────────┘
                               │ HTTPS
                               ▼
              ┌──────────────────────────────────────┐
              │   Vercel Edge / agrolytics.my.id     │
              │   ─────────────────────────────────  │
              │   Vite SPA build (static)            │
              │   • React Router v6 (CSR)            │
              │   • shadcn/ui + Tailwind             │
              │   • GSAP / Lenis / Framer Motion     │
              │   • Leaflet + GeoJSON                │
              │   • Zustand stores                   │
              │   • TanStack Query                   │
              └────────────┬─────────────────────────┘
                           │
        ┌──────────────────┼─────────────────────────┐
        │                  │                         │
        ▼                  ▼                         ▼
  ┌──────────────┐  ┌────────────────┐    ┌──────────────────┐
  │ Supabase Auth│  │ Supabase       │    │ Supabase Storage │
  │ • Email+Pass │  │ Postgres       │    │ • avatar upload  │
  │ • Google OAu │  │ • profiles     │    │ • PDF cache opt. │
  │ • Turnstile  │  │ • regions      │    │                  │
  │ • RLS JWT    │  │ • predictions  │    └──────────────────┘
  │              │  │ • weather      │
  │              │  │ • production   │
  │              │  │ • clusters     │
  │              │  │ • audit_log    │
  └──────────────┘  └────────────────┘

External: Cloudflare Turnstile (CAPTCHA), Google OAuth (Supabase provider).
NO FastAPI di Phase 1. Semua data via Supabase JS client + RLS.
```

### 3.2 Phase 2 (Post-capstone) — Tambah Railway

```
                  ┌──────────────────────────────────┐
                  │          User Browser            │
                  └────────────┬─────────────────────┘
                               │
                               ▼
              ┌──────────────────────────────────────┐
              │   Vercel / agrolytics.my.id          │
              │   + vercel.json rewrites:            │
              │   /api/predict/*  →  Railway         │
              │   /api/forecast/* →  Railway         │
              │   /api/admin/*    →  Railway         │
              └─────┬───────────────┬────────────────┘
                    │               │
                    │               ▼
                    │   ┌──────────────────────────┐
                    │   │   Railway / FastAPI      │
                    │   │ • LSTM .h5 inference     │
                    │   │ • XGBoost / RF baseline  │
                    │   │ • K-Means clustering     │
                    │   │ • Pre-compute scheduler  │
                    │   │ • JWT verify (Supabase)  │
                    │   └────┬─────────────────────┘
                    │        │
                    ▼        ▼
        ┌────────────────────────────────────────┐
        │  Supabase (Auth + Postgres + Storage)  │
        │  + tabel baru: forecast_jobs           │
        └────────────────────────────────────────┘

GitHub Actions: lint + typecheck + build → push main → auto deploy.
```

### 3.3 Routing & Domain

- `agrolytics.my.id/` — landing (public)
- `agrolytics.my.id/login` `/register` `/forgot-password` `/auth/callback`
- `agrolytics.my.id/app/*` — protected (RequireAuth guard)
- `agrolytics.my.id/app/admin/*` — RequireAdmin guard + RLS
- `agrolytics.my.id/api/*` — Vercel rewrite ke Railway (Phase 2 only)

### 3.4 Key Architectural Decisions

1. **No FastAPI di Phase 1.** Semua data via Supabase JS langsung, RLS jadi
   security boundary. Phase 2 baru tambah Railway untuk inference ML.
2. **Vercel rewrites = magic Phase 1→2 transition.** Frontend code 0 perubahan,
   cuma `vercel.json` ditambah satu file. Service layer abstraction (lihat §6)
   yang handle swap source.
3. **Cloudflare R2 ditunda.** Phase 1 cukup Supabase Storage (free tier).
   R2 baru relevan kalau Plant Disease Detection (Phase 2) jadi diimplementasi.
4. **Single domain.** Tidak ada `api.agrolytics.my.id` subdomain — semua
   transparent via Vercel rewrites. User cuma kenal satu URL.
5. **Capacitor → PWA dulu.** Project.txt menulis Capacitor (APK), tapi keputusan
   capstone Phase 1 = PWA manifest + service worker minimal. Capacitor masuk
   Phase 2 backlog kalau ada bandwidth.

## 4. Database Schema

Schema Supabase Postgres. Phase 1 langsung pakai dengan seed dummy realistic.
Phase 2 tinggal extend (`forecast_jobs`, `plant_disease_scans`, dll).

### 4.1 Naming Convention

- `snake_case`, plural untuk nama tabel
- PK `id uuid` default `gen_random_uuid()`
- Timestamps `created_at` / `updated_at` `timestamptz` default `now()`
- Foreign key suffix `_id`
- Indeks komposit untuk query hot path (lihat per-tabel)

### 4.2 Tables

#### `profiles` — extends `auth.users` (1:1)

| Field | Type | Notes |
|---|---|---|
| id | uuid PK | FK ke `auth.users.id` |
| email | text UNIQUE NOT NULL | mirror dari auth |
| full_name | text | |
| avatar_url | text | Supabase Storage URL |
| role | text CHECK IN ('admin','user') | default `'user'` |
| status | text CHECK IN ('active','suspended') | default `'active'` |
| preferred_theme | text CHECK IN ('dark','light') | default `'dark'` |
| last_login_at | timestamptz | updated saat sign-in success |
| created_at, updated_at | timestamptz | |

Trigger: `ON auth.users INSERT → INSERT INTO profiles (...)` auto-create row.

#### `regions` — master 56 kabupaten/kota Kalimantan

| Field | Type | Notes |
|---|---|---|
| id | uuid PK | |
| bps_code | text UNIQUE NOT NULL | e.g. "6371" untuk Banjarmasin |
| name | text NOT NULL | "Kabupaten Banjar" |
| province | text NOT NULL | "Kalimantan Selatan" |
| province_code | text | "63" |
| centroid_lat | numeric(9,6) | untuk map zoom |
| centroid_lng | numeric(9,6) | |
| area_km2 | numeric | |
| geojson_id | text | match dengan property di GeoJSON file |
| created_at | timestamptz | |

#### `production_history` — BPS 2018–2025

| Field | Type | Notes |
|---|---|---|
| id | uuid PK | |
| region_id | uuid FK → regions | |
| year | int CHECK 2015–2030 | |
| month | int CHECK 1–12, NULL allowed | NULL untuk data tahunan |
| production_ton | numeric NOT NULL | |
| area_harvest_ha | numeric | luas panen |
| yield_ton_ha | numeric | produktivitas |
| source | text default 'BPS' | |
| created_at | timestamptz | |

UNIQUE `(region_id, year, month)` · INDEX `(region_id, year)`

#### `weather_history` — NASA POWER bulanan

| Field | Type | Notes |
|---|---|---|
| id | uuid PK | |
| region_id | uuid FK → regions | |
| year | int | |
| month | int CHECK 1–12 | |
| rainfall_mm | numeric | curah hujan |
| temp_avg_c | numeric | suhu rata-rata |
| temp_min_c | numeric | |
| temp_max_c | numeric | |
| humidity_pct | numeric | kelembapan |
| solar_radiation | numeric | |
| source | text default 'NASA_POWER' | |
| created_at | timestamptz | |

UNIQUE `(region_id, year, month)` · INDEX `(region_id, year, month)`

#### `predictions` — output model (Phase 1 dummy seed)

| Field | Type | Notes |
|---|---|---|
| id | uuid PK | |
| region_id | uuid FK → regions | |
| target_year | int NOT NULL | tahun prediksi |
| target_month | int NULL | optional bulanan |
| predicted_yield | numeric NOT NULL | ton/ha |
| predicted_prod_ton | numeric | |
| confidence_lower | numeric | CI 95% lower |
| confidence_upper | numeric | CI 95% upper |
| model_name | text CHECK IN ('lstm','xgboost','random_forest','linear') | |
| model_version | text | "v1-dummy" Phase 1 |
| computed_at | timestamptz default `now()` | |
| is_baseline | boolean default false | hybrid B3 pre-compute flag |

INDEX `(region_id, target_year, model_name)`

#### `cluster_assignments` — K-means hasil

| Field | Type | Notes |
|---|---|---|
| id | uuid PK | |
| region_id | uuid FK → regions | |
| cluster_label | int CHECK IN (0,1,2) | 0=high, 1=medium, 2=low |
| cluster_name | text | "Prioritas Tinggi" |
| reference_year | int NOT NULL | year basis |
| computed_at | timestamptz | |

UNIQUE `(region_id, reference_year)`

#### `audit_log` — admin actions

| Field | Type | Notes |
|---|---|---|
| id | uuid PK | |
| actor_id | uuid FK → profiles | who did it |
| action | text NOT NULL | 'user.suspend', 'data.ingest', etc |
| entity_type | text | 'profile', 'prediction', etc |
| entity_id | uuid | |
| metadata | jsonb | extra context |
| ip_address | inet | |
| user_agent | text | |
| created_at | timestamptz | |

INDEX `(created_at DESC)` · INDEX `(actor_id)`

### 4.3 Phase 2 Tables (dirancang now, NOT created Phase 1)

- `forecast_jobs` — on-demand custom prediction queue (B3 hybrid)
- `plant_disease_scans` — kalau Plant Detection jadi diimplementasi
- `chat_sessions` + `chat_messages` — kalau AI Assistant jadi diimplementasi

### 4.4 Row Level Security (RLS)

| Tabel | Public read | Auth user read/write | Admin |
|---|---|---|---|
| profiles | ❌ | own row read/update | all read/write |
| regions | ✅ | ✅ read | ✅ all |
| production_history | ✅ | ✅ read | ✅ all |
| weather_history | ✅ | ✅ read | ✅ all |
| predictions | ❌ | ✅ read | ✅ all |
| cluster_assignments | ✅ | ✅ read | ✅ all |
| audit_log | ❌ | ❌ | ✅ read |

Public read pada `regions`, `production_history`, `weather_history`, dan
`cluster_assignments` diperlukan untuk **Live Map preview di landing page**
(tanpa login). Detail prediksi dan audit log wajib auth/admin.

### 4.5 Seed Plan Phase 1

| Tabel | Row count | Sumber |
|---|---|---|
| regions | 56 | data master BPS Kalimantan |
| production_history | ~448 (56 × 8 tahun tahunan) atau ~5,376 (bulanan) | seed via SQL |
| weather_history | ~5,376 (56 × 8 × 12) | seed via SQL |
| predictions | ~224 (56 × 1 tahun × 4 model) | dummy realistic |
| cluster_assignments | 56 | random tapi reproducible |
| audit_log | empty | populated saat use |

Seed dijalankan via `supabase/seed.sql`, otomatis run di local dev. Production
deploy seed manual sekali via `supabase db reset` atau script Node.

### 4.6 Migrations Versioning

```
supabase/migrations/
  0001_init_schema.sql       — semua CREATE TABLE
  0002_rls_policies.sql      — RLS enable + policies per tabel
  0003_indexes.sql           — composite indexes
  0004_triggers.sql          — auth.users → profiles, updated_at auto
```

Phase 2 tinggal append `0005_phase2_*.sql` tanpa modify file existing.

## 5. Folder Structure & Component Tree

Shape A: single Vite app, feature-first folder layout, shadcn/ui primitives.

### 5.1 Tree

```
agrolytics/
├── public/
│   ├── geojson/
│   │   └── kalimantan-kabupaten.geojson    # simplified <500KB
│   ├── frames/hero/                         # 31 frames hero parallax
│   │   └── frame-001.jpg ... frame-031.jpg  # source: hero_parralax/ (renamed)
│   ├── lottie/                              # placeholder, pengisi nanti
│   └── og-image.png
│
├── supabase/
│   ├── migrations/
│   │   ├── 0001_init_schema.sql
│   │   ├── 0002_rls_policies.sql
│   │   ├── 0003_indexes.sql
│   │   └── 0004_triggers.sql
│   ├── seed.sql                             # 56 regions + dummy timeseries
│   └── README.md
│
├── src/
│   ├── main.tsx                             # entry, mount router + providers
│   ├── App.tsx                              # router shell + global providers
│   ├── routes.tsx                           # React Router v6 route tree
│   │
│   ├── lib/
│   │   ├── supabase.ts                      # client singleton
│   │   ├── env.ts                           # zod-validated env vars
│   │   ├── queryClient.ts                   # TanStack Query config
│   │   ├── utils.ts                         # cn(), formatNumber(), formatDate()
│   │   ├── pdf.ts                           # jsPDF + html2canvas helpers
│   │   └── errors.ts                        # error code → ID message map
│   │
│   ├── stores/                              # Zustand split per concern
│   │   ├── useAuthStore.ts
│   │   ├── useFilterStore.ts                # year, region, province global filter
│   │   └── useThemeStore.ts                 # dark/light + persist localStorage
│   │
│   ├── services/                            # business logic abstraction
│   │   ├── regions.ts
│   │   ├── production.ts
│   │   ├── weather.ts
│   │   ├── predictions.ts
│   │   ├── clusters.ts
│   │   ├── profiles.ts
│   │   ├── audit.ts
│   │   └── auth.ts
│   │
│   ├── hooks/                               # TanStack Query wrappers
│   │   ├── useRegions.ts
│   │   ├── useProductionHistory.ts
│   │   ├── useWeatherHistory.ts
│   │   ├── usePredictions.ts
│   │   ├── useClusters.ts
│   │   ├── useAuthSession.ts
│   │   ├── useExportPDF.ts
│   │   └── useAuditLog.ts
│   │
│   ├── components/
│   │   ├── ui/                              # shadcn primitives (own the code)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── table.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── tooltip.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── skeleton.tsx
│   │   │   └── ...
│   │   │
│   │   ├── shell/                           # global chrome
│   │   │   ├── FloatingHeader.tsx           # landing pill header
│   │   │   ├── DashboardSidebar.tsx
│   │   │   ├── DashboardTopbar.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   └── Footer.tsx
│   │   │
│   │   ├── chart/                           # Chart.js wrappers
│   │   │   ├── LineChart.tsx
│   │   │   ├── BarChart.tsx
│   │   │   ├── AreaChart.tsx
│   │   │   ├── RadarChart.tsx
│   │   │   └── ChartCard.tsx
│   │   │
│   │   ├── map/
│   │   │   ├── KalimantanMap.tsx            # Leaflet base
│   │   │   ├── ChoroplethLayer.tsx
│   │   │   ├── RegionPopup.tsx
│   │   │   ├── MapLegend.tsx
│   │   │   └── MapControls.tsx
│   │   │
│   │   └── motion/                          # GSAP/Framer/Lenis primitives
│   │       ├── LenisProvider.tsx
│   │       ├── ScrollPin.tsx
│   │       ├── FrameSequence.tsx
│   │       ├── ParallaxLayer.tsx
│   │       ├── NumberCounter.tsx
│   │       └── RevealOnView.tsx
│   │
│   ├── features/                            # feature-first
│   │   │
│   │   ├── auth/
│   │   │   ├── pages/
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── RegisterPage.tsx
│   │   │   │   ├── ForgotPasswordPage.tsx
│   │   │   │   └── AuthCallbackPage.tsx
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   ├── TurnstileWidget.tsx
│   │   │   │   ├── GoogleButton.tsx
│   │   │   │   └── AuthLayout.tsx
│   │   │   └── guards/
│   │   │       ├── RequireAuth.tsx
│   │   │       └── RequireAdmin.tsx
│   │   │
│   │   ├── landing/
│   │   │   ├── pages/
│   │   │   │   └── LandingPage.tsx
│   │   │   └── sections/                    # 10 cinematic sections
│   │   │       ├── HeroSection.tsx
│   │   │       ├── ProblemSection.tsx
│   │   │       ├── InsightSection.tsx
│   │   │       ├── LiveMapSection.tsx
│   │   │       ├── SolutionSection.tsx
│   │   │       ├── TechSection.tsx
│   │   │       ├── VisionSection.tsx
│   │   │       ├── TeamSection.tsx
│   │   │       └── FooterSection.tsx
│   │   │
│   │   ├── dashboard/
│   │   │   ├── pages/OverviewPage.tsx
│   │   │   └── components/
│   │   │       ├── KPICardGrid.tsx
│   │   │       ├── KPICard.tsx
│   │   │       ├── WeatherAlertBanner.tsx
│   │   │       ├── TopRegionsCard.tsx
│   │   │       └── DashboardLayout.tsx
│   │   │
│   │   ├── forecast/
│   │   │   ├── pages/ForecastPage.tsx
│   │   │   └── components/
│   │   │       ├── ForecastChart.tsx
│   │   │       ├── HorizonSelector.tsx
│   │   │       ├── ModelSelector.tsx
│   │   │       └── ConfidenceBand.tsx
│   │   │
│   │   ├── geospatial/
│   │   │   ├── pages/GeospatialPage.tsx
│   │   │   └── components/
│   │   │       ├── ProductionHeatmap.tsx
│   │   │       ├── ClusterLegend.tsx
│   │   │       └── RegionAnalyticsPanel.tsx
│   │   │
│   │   ├── historical/
│   │   │   ├── pages/HistoricalPage.tsx
│   │   │   └── components/
│   │   │       ├── YearMultiSelect.tsx
│   │   │       ├── RegionCascadeFilter.tsx
│   │   │       ├── HistoricalChart.tsx
│   │   │       └── ComparisonTable.tsx
│   │   │
│   │   ├── reports/
│   │   │   ├── pages/ReportsPage.tsx
│   │   │   └── components/
│   │   │       ├── ReportConfigForm.tsx
│   │   │       ├── ReportPreview.tsx
│   │   │       └── ExportPDFButton.tsx
│   │   │
│   │   ├── admin/
│   │   │   ├── pages/
│   │   │   │   ├── UserManagementPage.tsx
│   │   │   │   └── DataIngestionPage.tsx
│   │   │   └── components/
│   │   │       ├── UserTable.tsx
│   │   │       ├── UserActionMenu.tsx
│   │   │       ├── AuditLogTable.tsx
│   │   │       └── IngestionStatusGrid.tsx
│   │   │
│   │   └── coming-soon/
│   │       ├── PlantDetectionComingPage.tsx
│   │       └── AssistantComingPage.tsx
│   │
│   ├── types/
│   │   ├── database.ts                      # `supabase gen types`
│   │   ├── domain.ts                        # Region, Prediction, Cluster
│   │   └── api.ts                           # request/response Phase 2
│   │
│   ├── styles/
│   │   ├── globals.css                      # Tailwind base + CSS vars
│   │   └── theme.ts                         # design tokens
│   │
│   └── i18n/
│       └── id.ts                            # string constants (ID-only Phase 1)
│
├── tests/
│   ├── unit/
│   │   ├── lib/utils.test.ts
│   │   └── stores/useFilterStore.test.ts
│   └── e2e/
│       ├── landing.spec.ts
│       ├── auth.spec.ts
│       └── dashboard.spec.ts
│
├── .env.example
├── .env.local                               # gitignored
├── .eslintrc.json
├── .prettierrc
├── tailwind.config.ts
├── postcss.config.js
├── tsconfig.json
├── vite.config.ts
├── vitest.config.ts
├── playwright.config.ts
├── vercel.json                              # rewrites Phase 2 (commented)
├── package.json
├── pnpm-lock.yaml
└── README.md
```

### 5.2 Convention Rules

1. **Feature folder** punya `pages/`, `components/`, optional `hooks/`. Tidak ada
   `utils.ts` per-feature kecuali benar-benar feature-specific.
2. **shadcn primitives** stay di `components/ui/` — never di-nest. Variant
   khusus feature wrap di `features/.../components/`.
3. **Stores Zustand split per concern.** No mega `useAppStore`.
4. **Hooks = data fetching + business logic.** Komponen tidak `useQuery`
   langsung di JSX; semua via `hooks/*.ts`.
5. **Service layer** wajib — `supabase.from(...)` hanya boleh di `services/*`,
   tidak di hooks/components. Phase 1→2 swap mudah.
6. **Types** terpisah di `src/types/`. `database.ts` auto-generated via
   `supabase gen types typescript --linked > src/types/database.ts`.
7. **Routes** di satu file `src/routes.tsx` (single source of truth).

### 5.3 Estimasi File Count Phase 1

- shadcn primitives: ~15
- Shell + chart + map + motion: ~25
- Auth feature: ~10
- Landing 10 sections + sub-comp: ~25
- Dashboard 5 user pages: ~25
- Admin 2 pages: ~8
- Phase 2 placeholder: ~2

Total ~110 component files. Realistis untuk 1 frontend dev × 5 minggu.

## 6. User Flow & Sitemap

### 6.1 Sitemap (Route Tree)

```
agrolytics.my.id
│
├── /                         Landing (public, 10 sections cinematic)
├── /login                    Auth — email/password + Google + Turnstile
├── /register                 Signup — email + password + Turnstile + ToS
├── /forgot-password          Reset password (Supabase magic link)
├── /auth/callback            Google OAuth return handler
│
├── /app                      Dashboard root → redirect /app/overview
│   │                         [GUARD: RequireAuth]
│   │
│   ├── /app/overview         Overview KPIs + map preview + quick links
│   ├── /app/forecast         Forecast: LSTM vs baseline, horizon selector
│   ├── /app/map              Geospatial: full Leaflet + cluster + popup
│   ├── /app/historical       Historical: multi-year overlay, region cascade
│   ├── /app/reports          Reports: config + preview + export PDF
│   ├── /app/plant-detection  Phase 2 placeholder ("Coming Soon")
│   ├── /app/assistant        Phase 2 placeholder ("Coming Soon")
│   │
│   ├── /app/settings         User profile + theme toggle + password
│   │
│   └── /app/admin            [GUARD: RequireAdmin] → redirect /app/admin/users
│       ├── /app/admin/users         User Management (suspend/promote)
│       └── /app/admin/ingestion     Data Ingestion Log + manual trigger
│
└── /404                      Not Found
```

### 6.2 User Flow — First-time Visitor (Public)

```
[Landing /]
  → scroll cinematic 10 sections
  → [Click "Masuk" di floating header]
      ├── existing user → /login
      └── new user → click "Daftar" tab → /register
  → [Click "Lihat Dashboard" hero CTA]
      → /login (kalau belum login)
  → [Click region di Live Map section]
      → modal "Masuk untuk lihat analisis lengkap" → /login or /register
```

### 6.3 User Flow — Registration

```
/register
  ├── input: full_name, email, password, confirm_password
  ├── widget: Cloudflare Turnstile (CAPTCHA)
  ├── checkbox: "Saya setuju Syarat Layanan"
  └── button: "Daftar"
        ↓
  [Submit]
    → validate (Zod): email format, password ≥8, match, turnstile token
    → supabase.auth.signUp({ email, password, options: { captchaToken, data: { full_name } } })
        ├── on error → toast inline error
        └── on success
              → profiles row auto-created via trigger
              → email confirmation sent
              → screen: "Cek email kamu untuk konfirmasi"
              → user click email link → /auth/callback → session → /app/overview
```

### 6.4 User Flow — Login

```
/login
  ├── tabs: "Email" | "Google"
  ├── Email tab: email + password + Turnstile + "Lupa password?" link
  └── Google tab: single button
        ↓
  [Submit Email]
    → supabase.auth.signInWithPassword({ email, password, options: { captchaToken } })
        ├── error 'Invalid login credentials' → toast
        ├── error 'Email not confirmed' → toast + resend link button
        └── success
              → fetch profile → store di useAuthStore
              → if profile.status === 'suspended' → signOut + toast "Akun ditangguhkan"
              → update profiles.last_login_at
              → if intended path tersimpan → redirect; else /app/overview
```

### 6.5 User Flow — Authenticated Dashboard Navigation

```
/app/overview (default landing post-login)
  ├── KPI cards (avg yield, total prod, top region, weather alert)
  ├── Mini map thumbnail → click → /app/map
  ├── Forecast snippet → click → /app/forecast
  └── "Pilih wilayah" quick filter → updates useFilterStore

/app/map
  ├── Leaflet full screen
  ├── Layer toggle: Yield heatmap | Cluster K-means | Production raw
  ├── Click region polygon
  │     → side panel slides in
  │     → shows: yield trend mini chart, cluster label, weather summary
  │     → "Buat Laporan" button → /app/reports?region=ID&year=N
  └── Filter: year selector applies to choropleth color

/app/forecast
  ├── Region selector (cascade: provinsi → kabupaten)
  ├── Horizon: 1y aktif | 3y disabled | 5y disabled (Phase 1: hanya 1y di-seed)
  ├── Model selector: LSTM | XGBoost | Random Forest | Linear | All overlay
  ├── Chart: line dengan confidence band
  └── "Custom Forecast" button → Phase 1: tooltip "Tersedia Phase 2"

/app/historical
  ├── Filter: provinsi (single) → kabupaten (multi, max 5)
  ├── Year multi-select chips: 2018, 2019, ..., 2025 (toggleable)
  ├── Metric switch: Production (ton) | Yield (ton/ha) | Area (ha)
  ├── Chart: line overlay multi-year
  └── Comparison table: rows = year, cols = selected regions

/app/reports
  ├── Step 1 — Konfigurasi: pilih region (single) + tahun (single) + checkboxes content
  └── Step 2 — Pratinjau & Export: live A4 layout preview + "Unduh PDF" button
        → render hidden div with charts
        → html2canvas snapshot per page
        → jsPDF assemble → download .pdf
```

### 6.6 User Flow — Admin Actions

```
/app/admin/users
  ├── DataTable: avatar, name, email, role, status, last login, joined
  ├── Search + filter (role, status)
  ├── Per-row dropdown:
  │     ├── "Promote ke Admin" (kalau current = user)
  │     ├── "Demote ke User" (kalau current = admin, tidak boleh diri sendiri)
  │     ├── "Suspend Akun" (status → 'suspended')
  │     └── "Aktifkan Akun" (status → 'active')
  └── Setiap action:
        → confirm dialog
        → mutation Supabase via RPC function (e.g. `admin_set_user_role`)
        → RPC function INSERT audit_log internally (server-side, security)
        → invalidate query

  Catatan: client TIDAK pernah INSERT audit_log langsung. Semua audit log
  ditulis dari Postgres function (RPC) yang ter-trigger oleh admin action.
  RLS pada `audit_log` = read-only untuk admin, no INSERT/UPDATE dari client.

/app/admin/ingestion
  ├── Cards: "BPS Production Data", "NASA POWER Weather"
  │     → last sync timestamp, status, row count
  ├── Audit log table (recent 50)
  └── Phase 1: tombol "Trigger Manual Ingest" disabled
```

### 6.7 User Flow — Theme Switch (Everywhere)

```
ThemeToggle component (header dashboard + landing)
  → click → useThemeStore.toggle()
  → setItem localStorage 'agrolytics-theme'
  → document.documentElement.dataset.theme = 'dark' | 'light'
  → Tailwind variants apply via [data-theme="dark"] selector
  → persist Supabase profile.preferred_theme (async kalau logged in)
```

### 6.8 User Flow — Session Expiry

```
TanStack Query mount → supabase.auth.onAuthStateChange listener
  ├── SIGNED_OUT → clear queryClient + redirect /login
  ├── TOKEN_REFRESHED → silent
  └── SIGNED_IN → fetch profile → useAuthStore.set(...)

Inactivity > 1 hour → Supabase auto-refresh fails → SIGNED_OUT path
```

### 6.9 Key Decisions

1. **Tidak ada `/dashboard`, semua di `/app/*`** — convention lebih pendek.
2. **`/app` redirect ke `/app/overview`** — biar kalau nanti ada multi-app concept gampang.
3. **Phase 2 routes sudah ada (placeholder)** — URL stable dari awal, sharing link tetap bisa di-bookmark.
4. **Filter state global di Zustand** — pindah dari `/overview` ke `/forecast` filter region/year kebawa.
5. **Suspended user di-signOut otomatis** — RLS protection + UI guard, dua lapis.
6. **Audit log: trigger Postgres function**, bukan manual INSERT di client — security.

## 7. API Contracts

Phase 1: 99% data dari Supabase JS client langsung. Phase 2: tambah Railway
endpoints lewat Vercel rewrites. Design abstraction supaya Phase 1→2 swap clean.

### 7.1 Layer Abstraction

```
Component
   ↓ pakai
Hook (useRegions, usePredictions, ...)         ← TanStack Query keys + caching
   ↓ panggil
Service function (regionsService.list(), ...)  ← business logic & shape
   ↓ pakai
Supabase client (Phase 1) | fetch /api/* (Phase 2 selected)
```

Pas Phase 2, swap **service function** internal aja — hooks & components zero change.

### 7.2 Phase 1 — Service Contracts (Supabase JS)

```typescript
// src/services/regions.ts
export const regionsService = {
  list(): Promise<Region[]>
    // SELECT * FROM regions ORDER BY province, name
    // public read via RLS

  getById(id: string): Promise<Region | null>
    // SELECT * WHERE id = $1
}

// src/services/production.ts
export const productionService = {
  byRegion(regionId: string, opts?: { from?: number; to?: number }): Promise<ProductionPoint[]>
    // SELECT year, month, production_ton, area_harvest_ha, yield_ton_ha
    // FROM production_history WHERE region_id = $1 [AND year BETWEEN ...]
    // ORDER BY year, month

  multiRegionByYears(regionIds: string[], years: number[]): Promise<ProductionPoint[]>
    // untuk Historical Analytics multi-year overlay (B2)
}

// src/services/weather.ts
export const weatherService = {
  byRegion(regionId: string, opts?: { from?: number; to?: number }): Promise<WeatherPoint[]>
}

// src/services/predictions.ts
export const predictionsService = {
  byRegion(regionId: string, modelName?: ModelName): Promise<Prediction[]>
    // requires auth (RLS: authenticated only)

  baselineForAllRegions(year: number): Promise<Prediction[]>
    // hybrid B3: pre-computed baseline untuk map choropleth
    // WHERE is_baseline = true AND target_year = $1

  generateCustom(input: { regionId: string; horizon: number; models: ModelName[] }): Promise<ForecastJob>
    // Phase 2 only — Phase 1 dummy throws "not available"
}

// src/services/clusters.ts
export const clustersService = {
  current(): Promise<ClusterAssignment[]>
    // ambil cluster terbaru by reference_year DESC
}

// src/services/profiles.ts
export const profilesService = {
  me(): Promise<Profile>                        // current user
  updateMe(patch: Partial<Profile>): Promise<Profile>
  // admin only:
  list(opts?: { role?: Role; status?: Status; search?: string }): Promise<Profile[]>
  setRole(userId: string, role: Role): Promise<void>
  setStatus(userId: string, status: Status): Promise<void>
}

// src/services/audit.ts
export const auditService = {
  // admin only (RLS gated)
  list(opts?: { actorId?: string; action?: string; from?: Date; to?: Date }): Promise<AuditLog[]>
}

// src/services/auth.ts (thin wrapper di atas supabase.auth)
export const authService = {
  signUp(input: { email; password; fullName; captchaToken }): Promise<...>
  signInPassword(input: { email; password; captchaToken }): Promise<...>
  signInGoogle(): Promise<...>            // redirect flow
  signOut(): Promise<void>
  resetPassword(email: string, captchaToken: string): Promise<void>
  onAuthStateChange(cb): () => void
}
```

### 7.3 TanStack Query Keys Convention

```typescript
['regions']
['regions', regionId]
['production', regionId, { from, to }]
['weather', regionId, { from, to }]
['predictions', regionId, modelName]
['predictions', 'baseline', year]
['clusters', 'current']
['profile', 'me']
['admin', 'users', filters]
['admin', 'audit', filters]
```

`staleTime`: data master (regions, history) = 10 min. Predictions (Phase 2) = 1 min. Profile = 30s.

### 7.4 Phase 2 — Railway Endpoints (FastAPI)

Routed via Vercel rewrite (`vercel.json`):

```json
{
  "rewrites": [
    { "source": "/api/predict/(.*)",  "destination": "https://api-railway-host/predict/$1" },
    { "source": "/api/forecast/(.*)", "destination": "https://api-railway-host/forecast/$1" },
    { "source": "/api/admin/(.*)",    "destination": "https://api-railway-host/admin/$1" }
  ]
}
```

**Endpoints (FastAPI):**

```
POST   /api/predict/yield
  Body: { region_id: str, year: int, model: 'lstm' | 'xgboost' | 'random_forest' | 'linear' }
  Auth: Bearer {Supabase JWT}
  Response: { predicted_yield, predicted_prod_ton, confidence_lower, confidence_upper, model_version }

POST   /api/forecast/custom
  Body: { region_id, horizon: 1..5, models: [...], custom_inputs?: {} }
  Auth: required
  Behavior: enqueue forecast_job, return { job_id, status: 'queued' }

GET    /api/forecast/jobs/{job_id}
  Auth: required (own jobs only via RLS-mirror check)
  Response: { status: 'queued' | 'running' | 'done' | 'error', result?, error? }

POST   /api/admin/ingest/bps
  Auth: admin role required
  Body: { year: int, source_url?: str }
  Behavior: trigger BPS scrape/ingest, write production_history, audit_log

POST   /api/admin/ingest/nasa
  Auth: admin
  Body: { year_from, year_to }
  Behavior: pull NASA POWER, upsert weather_history

POST   /api/admin/cluster/recompute
  Auth: admin
  Body: { reference_year: int, n_clusters?: 3 }
  Behavior: re-run K-means, replace cluster_assignments
```

**JWT verification** di FastAPI: middleware decode Supabase JWT, attach
`request.state.user_id` & `role` dari custom claims.

### 7.5 Error Envelope (Consistent)

```typescript
type ApiError = {
  code: string         // 'auth/invalid-credentials', 'forecast/job-failed'
  message: string      // human-readable Indonesian
  details?: unknown
}

// Hooks pakai:
useQuery({ queryKey, queryFn })
  // onError → toast(error.message) handled di QueryClient defaults
```

`message` selalu Bahasa Indonesia. Mapping table di `src/lib/errors.ts`.

### 7.6 Key Decisions

1. **Service layer wajib** — bukan langsung `supabase.from(...)` di hook.
   Phase 1→2 swap mudah, testing mockable, business logic centralized.
2. **TanStack Query untuk semua fetch** — termasuk Supabase reads. Caching,
   loading state, error state, optimistic updates konsisten.
3. **Vercel rewrites untuk Phase 2 transition** — tidak pakai env var URL
   switching. `vercel.json` jadi single source of truth.
4. **Long-running prediction = job pattern** — bukan blocking POST. Cocok
   untuk LSTM yang bisa makan 10–30s.
5. **Admin actions tetap lewat Railway**, bukan Supabase langsung — karena
   ingestion butuh server compute (scrape, transform, batch insert).

## 8. Landing Page Storytelling

10 sections cinematic. Per-section: tujuan, copy direction, motion technique,
asset needs, viewport behavior, effort estimate.

### 8.1 Global Landing Mechanics

- **Lenis smooth scrolling** — wrap whole landing di `<LenisProvider>`. Lerp 0.1.
- **GSAP ScrollTrigger** untuk pin/scrub. Register sekali di `LandingPage` mount.
- **Framer Motion** untuk component-level reveal (fade-up on viewport).
- **Reduced motion**: `prefers-reduced-motion` query → skip GSAP timelines,
  fallback static layout. Wajib accessibility.
- **Scroll progress indicator** di kanan layar (thin emerald-gold bar).

### 8.2 Section 1 — Floating Header (Persistent)

- Pill shape `rounded-full`, top-center fixed, max-width 720px, padding 12px 24px
- Background: `bg-[rgba(10,31,26,0.5)] backdrop-blur-xl border border-[rgba(212,175,55,0.2)]`
- Logo "Agrolytics" (left, gold serif italic) · Nav (center: Beranda · Peta · Solusi · Tim · Cerita) · CTA "Masuk" (right, gold pill)
- **Scroll behavior**: 0–50px opacity 0.3 no border; >50px opacity 0.85 border visible
- GSAP timeline tied to scroll Y, smooth interpolate
- Mobile: collapse nav to hamburger (desktop priority)
- **Effort: 0.5 day**

### 8.3 Section 2 — Hero (100vh, Parallax)

- **Layout**: parallax 3-layer
  - Background: dark emerald gradient + subtle noise texture
  - Mid: drone aerial Kalimantan / sawah — frame sequence (31 frames @ 1280×720 JPG)
  - Foreground: floating gold particles (CSS-only or canvas)
- **Headline** (Instrument Serif, 72–96px desktop):
  > "Membaca Tanah, Menjawab Masa Depan."
  - Sub: "Platform AI agrikultur untuk Kalimantan — prediksi hasil padi, peta produktivitas, keputusan berbasis data."
- **CTA primary**: "Lihat Dashboard" (gold filled) → /login
- **CTA secondary**: "Pelajari Lebih" (ghost border) → scroll to next section
- **Scroll indicator**: thin vertical line + "Scroll" text, breathing animation
- **Frame sequence**: scroll progress 0–100vh maps ke frame 0–30. Canvas-based via `FrameSequence.tsx`.
- **Asset**: 31 frames hero (dari `hero_parralax/`, rename ke `public/frames/hero/frame-001.jpg` ... `frame-031.jpg`)
- **Effort: 1.5 days**

### 8.4 Section 3 — Problem (~120vh, Scroll-pinned)

- **Pin** section selama 100vh scroll, content swap inside
- **Beat 1**: full-screen statement
  > "Setiap tahun, petani Kalimantan menghadapi ketidakpastian iklim."
- **Beat 2**: animated stat ticker (NumberCounter):
  - "8 tahun data BPS" (2018→2025)
  - "5 provinsi · 56 kabupaten/kota"
  - "1.2 juta hektar lahan pertanian terdampak"
  - "0 platform terpadu yang menjawab itu — sampai sekarang"
- **Beat 3**: visual fade — silhouette petani / sketsa ladang
- **Asset**: stat data + 1–2 illustrative SVG (sederhana)
- **Effort: 1 day**

### 8.5 Section 4 — Insight (~100vh)

- Layout: split horizontal (60/40)
- Left: large quote
  > "Datanya sudah ada. Yang belum ada: cara membacanya."
- Right: **animated data flow diagram**
  - Node "NASA POWER" → arrow → Node "BPS Production" → arrow → Node "AI Pipeline" → arrow → Node "Dashboard"
  - Lines draw progressively as user scrolls (SVG `stroke-dasharray` animated)
- **Effort: 0.5 day**

### 8.6 Section 5 — Live Map Preview (~140vh, The Killer Section)

- **Goal**: prove "ini bukan demo cosmetic — ini app beneran"
- Header text: "Lihat Kalimantan dalam Data" + sub "Setiap kabupaten, setiap angka, setiap insight."
- **Leaflet container** 80vw × 70vh, glassmorphism wrapper card, gold border
- Layer: choropleth kabupaten by avg yield (color scale emerald light → gold → emerald deep)
- Features:
  - Hover: tooltip "Kabupaten Banjar · 4.8 ton/ha · Cluster Tinggi"
  - Click region: modal slide up → mini chart 5 tahun + button "Masuk untuk analisis lengkap" → /login
  - Top-right: legend (3 cluster colors + scale)
  - Bottom-left: Leaflet attribution + "Data: BPS & NASA POWER"
- **Mock data**: gunakan tabel `regions` + `cluster_assignments` (public RLS)
- **Bonus**: "Lihat 56 wilayah" badge animated pulse
- **Effort: 2 days**

### 8.7 Section 6 — Solution (~120vh, Horizontal Scroll)

- Pin section, content moves horizontal as user scrolls vertical (GSAP horizontal-on-vertical)
- 3 cards (1 per pillar):
  - **Pilar 1 — Predictive AI**: "Prediksi Hasil Padi 2026", "Multivariate LSTM dilatih dengan 8 tahun data NASA POWER + BPS"
  - **Pilar 2 — Geospatial Intelligence**: "Peta Hidup Kalimantan", "Choropleth interaktif, clustering K-means, popup analytics"
  - **Pilar 3 — Decision Support**: "Laporan Siap Pakai", "Export PDF per wilayah, comparison historis, insight otomatis"
- Each card: glass card, subtle gold border, hover scale 1.02
- **Effort: 1 day**

### 8.8 Section 7 — Tech (~80vh)

- Center: large number ticker "8 · 56 · 12 · 4"
  - 8 tahun data
  - 56 kabupaten
  - 12 fitur cuaca
  - 4 model ML (LSTM, XGBoost, RF, Linear)
- Below: logo grid (greyscale, hover color)
  - TensorFlow · Keras · FastAPI · Supabase · React · Tailwind · NASA POWER · BPS · IBM Skillsbuild
- Subtle: "Open data. Open methods. Tertutup hanya: bagaimana cara mengubahnya jadi keputusan."
- **Effort: 0.5 day**

### 8.9 Section 8 — Vision (~100vh) — Phase 2 Teaser

- Header: "Yang Sedang Kami Bangun"
- Two large cards side-by-side:
  - **Plant Disease Detection** — mockup screenshot upload UI, badge "Coming Soon", caption "Foto daun → diagnosis dalam 2 detik"
  - **AI Assistant** — mockup chat UI, badge "Coming Soon", caption "Tanya seperti ke pakar pertanian"
- Background: blurred dashboard preview, opacity 0.3
- Subtle: "Phase 2 · Diharapkan akhir 2026"
- **Effort: 0.5 day**

### 8.10 Section 9 — Team (~100vh)

- Header: "Tim di Balik Agrolytics"
- 5 cards (dari project.txt):
  - Muhammad Rahman — MLOps & Deployment Specialist
  - Muhammad Husain Ali Ridha — AI Engineer
  - Siti Fitria Putri Hans — AI Engineer
  - Muhammad Rakha Djauhari — Project Manager & QA
  - M. Rohid Rivaldi — Front-End & AI Integration + MLOps
- Card: avatar (circle, gold ring) + name + role + LinkedIn icon (optional)
- Bottom: IBM Skillsbuild logo + "Capstone Project · Tim Pijak"
- **Effort: 0.5 day**

### 8.11 Section 10 — Footer

- 4 columns
  - **Agrolytics**: tentang, visi, kontak
  - **Sumber Data**: BPS, NASA POWER (with link)
  - **Hukum**: Syarat Layanan, Privasi, Disclaimer
  - **Sosial**: GitHub, Email, X (kalau ada)
- Bottom: "© 2026 Tim Pijak · Capstone IBM Skillsbuild"
- Background: deep emerald + thin gold separator top
- **Effort: 0.25 day**

### 8.12 Total Landing Effort

~8.25 person-days untuk 1 frontend dev. Realistic dalam **week 2–3** kalau
dashboard parallel-track.

### 8.13 Anti "Vibecoded" Checklist

1. Real interactive component (Leaflet section #5) — not just animations
2. Custom typography pairing (Instrument Serif + IBM Plex Mono)
3. Hand-curated content & copy Indonesia (bukan lorem ipsum)
4. Real data citations (NASA POWER, BPS) — dengan link sumber
5. Reduced-motion mode handled (accessibility = real product)
6. Asset bukan stock generic (drone Kalimantan + sketsa SVG custom)
7. Floating header micro-interaction (opacity scrub) — touch yang mahal

## 9. Dashboard Modules

Per modul: layout, primary data, components used, interactions, edge cases, effort.

### 9.1 Layout Shell (Semua Dashboard Pages)

```
┌──────────────────────────────────────────────────────────────┐
│ Topbar: logo · global filter chip · search · theme toggle ·  │
│         notifikasi (Phase 2) · avatar dropdown               │
├──────────┬───────────────────────────────────────────────────┤
│          │                                                   │
│ Sidebar  │  PAGE CONTENT (each module below)                 │
│ ─────    │                                                   │
│ Overview │                                                   │
│ Forecast │                                                   │
│ Map      │                                                   │
│ Histori  │                                                   │
│ Laporan  │                                                   │
│ ─────    │                                                   │
│ Plant Dx │                                                   │
│ Asisten  │                                                   │
│ ─────    │                                                   │
│ [Admin   │                                                   │
│  divider │                                                   │
│  if role │                                                   │
│  =admin] │                                                   │
│ Users    │                                                   │
│ Ingest   │                                                   │
│ ─────    │                                                   │
│ Setting  │                                                   │
└──────────┴───────────────────────────────────────────────────┘
```

- Sidebar: collapsible (mini icons-only mode), persist via localStorage
- Topbar: global filter chip menampilkan "Tahun: 2025 · Region: Semua Kalimantan"
- Active nav indicator: gold left-border 2px + emerald-100 text

### 9.2 Module 1 — Overview (`/app/overview`)

**Purpose**: dashboard home, snapshot semua data utama.

**KPI cards (4)**:
1. Avg yield Kalimantan 2025 (ton/ha) + ▲▼ vs 2024
2. Total produksi padi 2025 (juta ton) + delta
3. Top region by yield + nama kabupaten
4. Cuaca anomali count (kabupaten dengan rainfall <X% normal)

**Components**: `KPICardGrid`, `KPICard`, `MapPreviewCard`, `TopRegionsCard`,
`ForecastSnippet`, `WeatherAlertBanner`.

**Data sources**: `regions`, `production_history`, `predictions`, `weather_history`,
`cluster_assignments` — semua via TanStack Query.

**Edge cases**:
- New user (no data fetched yet): skeleton states, masing-masing card punya loading shimmer
- No weather alert: banner hidden, tidak collapse layout
- Filter global → semua KPI re-compute, mini map re-render

**Effort: 1 day**

### 9.3 Module 2 — Forecast (`/app/forecast`)

**Purpose**: prediksi produktivitas padi LSTM + baseline comparison.

**Layout**:
- Sidebar config: Region cascade, Horizon (1y|3y|5y), Models multiselect
- Main chart: Line chart LSTM (gold) + XGBoost (emerald) + RF (cyan) + Linear (slate)
- Confidence band LSTM + Tooltip on hover
- Below chart: Model comparison table (MAE, RMSE, R² per model)

**Components**: `ForecastChart`, `HorizonSelector`, `ModelMultiSelect`,
`ConfidenceBand`, `ModelMetricsTable`.

**Interactions**:
- Click legend toggles model line visibility (Chart.js native)
- Hover chart point → tooltip "Tahun 2026 · LSTM · 4.7 ton/ha · CI 95%: [4.3, 5.1]"
- "Custom Forecast" button: Phase 1 disabled with tooltip

**Edge cases**:
- Region tidak ada prediksi: empty state "Belum ada prediksi untuk wilayah ini"
- Hanya 1 model aktif: hide comparison table, show single-model card
- All models off: chart kosong + helper "Pilih minimal 1 model"

**Effort: 1.5 days**

### 9.4 Module 3 — Geospatial Map (`/app/map`)

**Purpose**: peta Kalimantan interactive dengan choropleth + cluster + popup.

**Layout**:
- Topbar overlay: Layer toggle (Yield/Cluster/Production), Year selector, Reset view
- Leaflet map (full width, ~80vh) dengan choropleth coloring
- Hover region: tooltip
- Click region: side panel slide-in (right 30%) dengan KPIs, mini chart, weather summary, "Buat Laporan" btn

**Components**: `KalimantanMap`, `ChoroplethLayer`, `ClusterLegend`,
`RegionPopup`, `LayerToggle`, `MapLegend`.

**Data sources**:
- `public/geojson/kalimantan-kabupaten.geojson` — 56 polygon features
- `regions` join `production_history` (year filter) → choropleth color
- `cluster_assignments` → cluster layer color

**Performance**:
- GeoJSON simplification: target <500KB
- Lazy load Leaflet bundle (code-split)
- Memoize choropleth color calc per year

**Effort: 2 days**

### 9.5 Module 4 — Historical Analytics (`/app/historical`)

**Purpose**: deep-dive multi-year comparison (B2 multi-year overlay).

**Layout**:
- Filter row (sticky top): Provinsi, Kabupaten (multi-max-5), Tahun (chips),
  Metric (Production/Yield/Area), Reset, Export PNG
- Main chart: line overlay multi-year × multi-region
- Comparison table (synchronized): rows = year, cols = selected regions, cells = value + delta

**Components**: `RegionCascadeFilter`, `YearMultiSelect`, `MetricSwitch`,
`HistoricalChart`, `ComparisonTable`.

**Interactions**:
- Add/remove year chip → chart re-render with line add/remove animation
- Add/remove region → same
- Switch metric: chart Y-axis updates
- Export PNG: html2canvas snapshot chart only

**Edge cases**:
- 5 region × 8 year = 40 lines → too noisy. Limit total lines = 15 (validate UI).
- Missing data points: line interpolated dengan "?" annotation
- No data selected: empty state "Pilih region dan tahun"

**Effort: 1.5 days**

### 9.6 Module 5 — Reports (`/app/reports`)

**Purpose**: generate PDF per-region + per-year (A1).

**Layout**: 2-step wizard.
- Step 1: Konfigurasi (region, tahun, checkboxes untuk content)
- Step 2: Pratinjau & Export (A4 page preview + "Unduh PDF" button)

**PDF generation**: client-side hybrid `jsPDF` + `html2canvas`.
- Render hidden div berukuran A4 (210×297mm @ 96dpi = 794×1123px)
- 1 div per "page" dengan styling custom
- `html2canvas(div)` → canvas → `pdf.addImage(canvas, ...)`
- Total ~5 pages = 5–8s generate time

**Recommendation auto-generate**: Template-based berdasarkan cluster.

**Components**: `ReportConfigForm`, `ReportPreview`, `PDFPage`, `ExportPDFButton`.

**Effort: 2 days**

### 9.7 Module 6 & 7 — Phase 2 Placeholders

**`/app/plant-detection`** — `PlantDetectionComingPage.tsx`
- Centered hero: "Deteksi Penyakit Tanaman dengan AI"
- Mockup screenshot upload UI
- Badge: "Diharapkan akhir 2026"
- CTA: "Daftar untuk early access"

**`/app/assistant`** — `AssistantComingPage.tsx`
- Mockup chat UI
- Same pattern early access signup

**Effort: 0.5 day total**

### 9.8 Module 8 — User Management (`/app/admin/users`) [Admin only]

**Layout**:
- Header: "Manajemen Pengguna" + "Total: 142"
- Search, Role filter, Status filter, Export CSV
- DataTable: Avatar, Name, Email, Role, Status, Login, Action

**Per-row dropdown actions**:
- "Promote ke Admin" / "Demote ke User"
- "Suspend Akun" / "Aktifkan Akun"
- "Lihat Audit" → expand row dengan log entries

**Confirm dialogs** untuk semua destructive actions. Self-demote disabled.

**Components**: `UserTable`, `UserActionMenu`, `ConfirmDialog`, `AuditExpandRow`.

**Effort: 1 day**

### 9.9 Module 9 — Data Ingestion Log (`/app/admin/ingestion`) [Admin only]

**Layout**:
- Header: "Log Ingestion Data"
- 2 status cards: BPS Production, NASA POWER (last sync, status, rows, trigger button)
- Audit Log Table (action='data.ingest')

**Components**: `IngestionStatusGrid`, `AuditLogTable`.

**Effort: 0.5 day**

### 9.10 Module 10 — Settings (`/app/settings`)

**Tabs**:
- **Profil**: full_name, avatar_url upload, email (read-only)
- **Tampilan**: theme switch (sync ke `profiles.preferred_theme`)
- **Keamanan**: ganti password, sessions list (Phase 2)
- **Notifikasi**: email pref (Phase 2 placeholder)

**Effort: 0.5 day**

### 9.11 Total Dashboard Effort

| Module | Effort (days) |
|---|---|
| Overview | 1 |
| Forecast | 1.5 |
| Geospatial Map | 2 |
| Historical | 1.5 |
| Reports | 2 |
| Phase 2 placeholders | 0.5 |
| User Management | 1 |
| Ingestion Log | 0.5 |
| Settings | 0.5 |
| **Subtotal modules** | **10.5** |
| Layout shell + sidebar + topbar | 1 |
| Auth pages (login, register, callback) | 1 |
| **TOTAL DASHBOARD** | **~12.5** |

Plus landing **8.25** dari Section 8 = **~21 person-days frontend total** untuk 1 dev.

5 minggu × 5 hari kerja = 25 hari. **Margin 4 hari** untuk QA, polish, fix bugs,
deployment, demo prep. **Tight tapi feasible** kalau scope tidak melebar.

## 10. Design Tokens & Motion System

Single source of truth untuk semua nilai visual. Implementasi via CSS variables +
Tailwind theme extend.

### 10.1 Color Tokens

```typescript
// src/styles/theme.ts (semantic naming, not raw colors)
export const tokens = {
  // Brand
  brand: {
    emerald: { 400: '#34D399', 500: '#10B981', 600: '#059669', 700: '#047857' },
    gold:    { 400: '#E5C76B', 500: '#D4AF37', 600: '#B8860B' },
  },
  // Surface (dark default)
  dark: {
    bg:        '#0A1F1A',  // primary background
    surface:   '#0F2A23',  // cards, panels
    elevated:  '#143329',  // dialog, dropdown
    overlay:   'rgba(255,255,255,0.04)',  // glass tint
    border:    'rgba(255,255,255,0.08)',
    borderGold:'rgba(212,175,55,0.2)',
    text:      '#F1F5F2',
    textMuted: '#94A3B8',
    textSubtle:'#64748B',
  },
  // Surface (light variant)
  light: {
    bg:        '#FAFAF7',
    surface:   '#FFFFFF',
    elevated:  '#F1F5F2',
    overlay:   'rgba(0,0,0,0.04)',
    border:    'rgba(0,0,0,0.08)',
    borderGold:'rgba(184,134,11,0.3)',
    text:      '#0F1F1A',
    textMuted: '#475569',
    textSubtle:'#94A3B8',
  },
  // Semantic state
  state: {
    success: '#10B981',  // = emerald 500
    warning: '#F59E0B',  // amber
    danger:  '#EF4444',
    info:    '#3B82F6',
  },
  // Data viz palette (untuk chart consistency)
  chart: {
    primary:   '#D4AF37',  // gold (LSTM)
    secondary: '#10B981',  // emerald (XGBoost)
    tertiary:  '#06B6D4',  // cyan (RF)
    quaternary:'#94A3B8',  // slate (linear)
    cluster: { high: '#10B981', medium: '#D4AF37', low: '#EF4444' },
  },
} as const
```

### 10.2 CSS Variables (Theme Switch via data-attribute)

```css
/* src/styles/globals.css */
:root,
[data-theme="dark"] {
  --bg: #0A1F1A;
  --surface: #0F2A23;
  --elevated: #143329;
  --overlay: rgba(255,255,255,0.04);
  --border: rgba(255,255,255,0.08);
  --border-gold: rgba(212,175,55,0.2);
  --text: #F1F5F2;
  --text-muted: #94A3B8;
  --brand-emerald: #10B981;
  --brand-gold: #D4AF37;
}

[data-theme="light"] {
  --bg: #FAFAF7;
  --surface: #FFFFFF;
  --elevated: #F1F5F2;
  --overlay: rgba(0,0,0,0.04);
  --border: rgba(0,0,0,0.08);
  --border-gold: rgba(184,134,11,0.3);
  --text: #0F1F1A;
  --text-muted: #475569;
  --brand-emerald: #059669;
  --brand-gold: #B8860B;
}
```

Tailwind theme extend reads `var(--*)` so utilities auto-react ke theme switch
tanpa class swap.

### 10.3 Typography

```typescript
fonts: {
  display: ['"Instrument Serif"', 'Georgia', 'serif'],   // hero, headlines
  body:    ['Inter',              'system-ui', 'sans-serif'],
  mono:    ['"IBM Plex Mono"',    'JetBrains Mono', 'monospace'],
}

fontSize: {
  // Display scale (storytelling)
  'display-xl': ['96px', { lineHeight: '1.05', letterSpacing: '-0.03em' }],
  'display-lg': ['72px', { lineHeight: '1.08', letterSpacing: '-0.02em' }],
  'display-md': ['56px', { lineHeight: '1.1',  letterSpacing: '-0.02em' }],
  // UI scale
  'h1': ['36px', { lineHeight: '1.2' }],
  'h2': ['28px', { lineHeight: '1.25' }],
  'h3': ['22px', { lineHeight: '1.3' }],
  'body-lg': ['18px', { lineHeight: '1.6' }],
  'body':    ['15px', { lineHeight: '1.6' }],
  'body-sm': ['13px', { lineHeight: '1.5' }],
  'caption': ['12px', { lineHeight: '1.4' }],
  // Mono (numbers/data)
  'data-xl': ['48px', { lineHeight: '1', letterSpacing: '-0.02em' }],
  'data':    ['16px', { lineHeight: '1.3' }],
}
```

Loading: Instrument Serif & IBM Plex Mono via `<link rel="preconnect">` +
`font-display: swap`. Inter pakai `@fontsource-variable/inter`.

### 10.4 Spacing Scale

```
0  - 0
1  - 4px
2  - 8px
3  - 12px
4  - 16px
5  - 20px
6  - 24px
8  - 32px
10 - 40px
12 - 48px
16 - 64px
20 - 80px
24 - 96px
```

Tailwind default. **Aturan**: section vertical padding `py-20` mobile, `py-24`
desktop. Card padding `p-6`. Inline gap `gap-3` atau `gap-4`.

### 10.5 Border Radius

```
sm:   6px    (badges, chips)
md:   10px   (inputs, small cards)
lg:   14px   (cards, panels)
xl:   20px   (hero buttons, big cards)
2xl:  28px   (floating header pill)
full: 9999px (avatars, pills)
```

### 10.6 Shadow & Glow

```css
--shadow-card:      0 4px 24px rgba(0,0,0,0.20);
--shadow-elevated:  0 8px 40px rgba(0,0,0,0.30);
--shadow-floating:  0 20px 60px rgba(0,0,0,0.40);
--glow-emerald:     0 0 40px rgba(16,185,129,0.15);
--glow-gold:        0 0 32px rgba(212,175,55,0.18);
```

CTA primary hover: `box-shadow: var(--glow-gold)`. Active card: `var(--glow-emerald)`.

### 10.7 Glassmorphism Recipe

```css
.glass {
  background: rgba(15, 42, 35, 0.5);          /* surface @50% */
  backdrop-filter: blur(20px) saturate(140%);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-card), inset 0 1px 0 rgba(255,255,255,0.05);
}
.glass-gold {
  border: 1px solid var(--border-gold);
  box-shadow: var(--shadow-card), 0 0 0 1px rgba(212,175,55,0.1) inset;
}
```

Light theme: tint pakai `rgba(255,255,255,0.7)` instead.

### 10.8 Motion System — Easing

```typescript
easing: {
  // Standard: smooth in/out, default semua transition
  standard:    'cubic-bezier(0.4, 0, 0.2, 1)',
  // Decelerate: enter (fade-in, slide-in)
  decelerate:  'cubic-bezier(0, 0, 0.2, 1)',
  // Accelerate: exit
  accelerate:  'cubic-bezier(0.4, 0, 1, 1)',
  // Cinematic (landing only): heavy ease-out untuk parallax
  cinematic:   'cubic-bezier(0.16, 1, 0.3, 1)',
  // Spring-like (Framer Motion default)
  spring:      { type: 'spring', stiffness: 260, damping: 20 },
}
```

### 10.9 Motion System — Duration

```typescript
duration: {
  instant:  '50ms',    // hover bg color
  fast:     '150ms',   // hover scale, shadow
  normal:   '300ms',   // page transitions, dialog
  slow:     '500ms',   // section reveal, layer fade
  cinematic:'1200ms',  // hero frame sequence individual frame transition
}
```

### 10.10 Reduced Motion

```typescript
// Top-level guard
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

// di ScrollPin / FrameSequence / ParallaxLayer
if (prefersReducedMotion) {
  // skip GSAP timeline, render static layout
  return <StaticFallback />
}
```

### 10.11 Scroll Mechanics

**Lenis config**:
```typescript
new Lenis({
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  smoothWheel: true,
  smoothTouch: false,  // mobile native scroll
  wheelMultiplier: 1,
})
```

**GSAP ScrollTrigger** integration: `lenis.on('scroll', ScrollTrigger.update)` +
`gsap.ticker.add((time) => lenis.raf(time * 1000))`.

### 10.12 Frame Sequence Component

```tsx
// public/frames/hero/frame-001.jpg ... frame-031.jpg (31 frames)
// Pre-load semua via JS Image() + cache di state
// Canvas draw current frame based on scroll progress

<FrameSequence
  framesPath="/frames/hero/"
  framePrefix="frame-"
  frameCount={31}
  frameExtension="jpg"
  scrollTrigger={{ start: 'top top', end: 'bottom top', scrub: 1 }}
/>
```

Performance:
- Pre-decode di mount via `await Promise.all(images.map(decode()))`
- Canvas dimension: `window.innerWidth × window.innerHeight × devicePixelRatio` (capped 2x)
- Convert source JPG ke WebP build-time pakai `sharp` (~40% size reduction)

### 10.13 Layout Grid

```
Container max-width:
- landing: 1280px (max content width, gutters auto)
- dashboard: 1440px (full bleed sidebar 240px + content)

Grid columns: 12 (Tailwind default)
Section vertical padding: 80px mobile / 120px desktop
```

### 10.14 Iconography

**Library**: `lucide-react` (consistent stroke 1.5px, matches modern SaaS aesthetic)

Custom icons (kalau perlu):
- Logo Agrolytics (gold serif "A" dengan emerald leaf accent)
- Cluster pin variants (high/medium/low — colored circles)
- Disabled untuk Phase 2 features (clock badge)

### 10.15 Component Token Usage (Contoh)

**Button variants**:
```tsx
// Primary CTA
className="bg-[var(--brand-gold)] text-black font-medium px-6 py-3 rounded-xl
           hover:shadow-[var(--glow-gold)] transition-all duration-fast ease-standard"

// Ghost
className="border border-[var(--border-gold)] text-[var(--text)] px-6 py-3 rounded-xl
           hover:bg-[var(--overlay)] transition-colors"

// Disabled (Phase 2 placeholders)
className="bg-[var(--surface)] text-[var(--text-muted)] cursor-not-allowed opacity-60"
```

**Card glass**:
```tsx
<div className="glass-gold rounded-lg p-6">{children}</div>
```

### 10.16 Key Decisions

1. **CSS variables, bukan Tailwind theme swap** — theme switch jadi single
   attribute change `[data-theme]`, no rebuild, no hydration mismatch.
2. **Semantic naming** (`--bg`, `--text`) bukan raw color — easier audit.
3. **Display scale terpisah dari UI scale** — Instrument Serif untuk hero/section
   header, Inter untuk UI. Tidak campur.
4. **Reduced motion respected dari awal** — accessibility = real product.
5. **Frame sequence pre-decode** — jangan stream-load saat scroll, atau janky.

## 11. Technical Roadmap & 5-Week Timeline

### 11.1 Reality Check Tim (dari project.txt)

| Role | Count | Effective FE bandwidth |
|---|---|---|
| AI Engineer (Husain + Fitria) | 2 | 0 (sibuk full LSTM/baseline/clustering) |
| MLOps (Rahman) | 1 | 0 |
| Front-End + AI Integration + MLOps double duty (Rohid) | 1 | **partial** (split FE/MLOps) |
| PM & QA (Rakha) | 1 | 0 (manage + test only) |

**Critical finding**: Cuma **1 frontend dev efektif** (Rohid), dan dia juga
di-double duty MLOps. Dari Section 8+9 estimate **~21 person-days** Frontend
total. Dengan 5 minggu × 5 hari = 25 hari, **margin 4 hari**, tapi Rohid bukan
full-time FE → realistis margin **negative** kalau scope tidak dibagi atau
di-prioritize.

**Mitigasi**:
- Husain/Fitria selesai EDA + baseline minggu 2–3 → kalau cepat, bisa bantu seed
  data + integrasi
- PM (Rakha) bantu QA paralel — tidak nambah FE bandwidth
- **PRIORITY ORDER** scope kalau time crunch (lihat below)

### 11.2 5-Week Timeline (Revised)

#### Minggu 1 — Foundation & Setup

- **Frontend (Rohid)**: scaffold Vite project, Tailwind config, design tokens,
  routing skeleton, Supabase client setup, env config, shadcn primitives copy,
  basic layout shell (sidebar+topbar)
- **AI (Husain+Fitria)**: dataset validation, EDA tahap awal NASA POWER + BPS
- **MLOps (Rahman)**: GitHub repo + branching policy, GitHub Actions CI skeleton
  (lint+typecheck), Supabase project provision, schema migration `0001_init` +
  `0002_rls` apply
- **PM (Rakha)**: finalize design doc, Jira board setup, daily standup ritme

**Milestone M1**: repo running locally (`pnpm dev`), Supabase schema deployed,
dummy seed loaded, login page working with Supabase Auth.

#### Minggu 2 — Auth Flow & Landing Foundation

- **Frontend**:
  - Auth pages (login, register, forgot, callback) + Turnstile + Google OAuth
  - RequireAuth/RequireAdmin guards
  - Landing sections 1–3 (Floating Header, Hero parallax, Problem)
  - Lenis + GSAP setup, FrameSequence component
- **AI**: pipeline preprocessing, sliding window, baseline model training
- **MLOps**: FastAPI scaffold (Phase 2 prep), endpoint blueprint, Supabase
  Storage buckets

**Milestone M2**: signup → login → /app/overview placeholder works end-to-end.
Landing hero scroll cinematic functional.

#### Minggu 3 — Landing Continued + Dashboard Core

- **Frontend**:
  - Landing sections 4–7 (Insight, Live Map Leaflet, Solution, Tech)
  - Overview page (KPI cards, mini map)
  - Forecast page (chart + filters)
  - GeoJSON Kalimantan kabupaten simplified, integrate ke Live Map
- **AI**: LSTM training + tuning, K-means clustering elbow method
- **MLOps**: Cloudflare R2 setup (Phase 2 prep), backend API endpoint stubs

**Milestone M3**: Landing page 7/10 sections live. Dashboard 2/5 user modules
functional. Live Map landing menampilkan 56 kabupaten via real data Supabase.

#### Minggu 4 — Dashboard Complete + Admin + Reports

- **Frontend**:
  - Geospatial Map page (full)
  - Historical Analytics (multi-year overlay)
  - Reports (jsPDF + html2canvas)
  - User Management + Ingestion Log (admin)
  - Settings page
  - Phase 2 placeholders
  - Landing sections 8–10 (Vision, Team, Footer)
- **AI**: model evaluation + comparative analysis + export artifacts (.h5, .joblib)
- **MLOps**: API integration (kalau timeline cocok untuk Phase 2 partial),
  CI/CD untuk staging deploy
- **PM/QA**: smoke testing semua flows, MCP Chrome DevTools / Playwright run,
  bug triage

**Milestone M4**: Full app functional, semua module siap demo, code freeze
approaching.

#### Minggu 5 — Polish, Deploy, Demo

- **Frontend**: bug fixes, theme switcher polish, accessibility (reduced motion
  verified), Chrome browser testing
- **All**: deploy ke Vercel production (`agrolytics.my.id`), env vars secured,
  analytics setup (optional)
- **PM**: pitch deck finalize, video demo recording, gladi presentasi
- **AI**: technical documentation final
- **MLOps**: Capacitor PWA conversion (PWA manifest + service worker minimal)

**Milestone M5**: Live di `agrolytics.my.id`, video demo selesai, pitch deck
ready, dokumen final.

### 11.3 Priority Order (Kalau Time Crunch)

**P0 — Wajib ada di demo (cannot skip)**:
1. Auth flow (login/register/Google/Turnstile)
2. Overview dashboard (4 KPI + mini map)
3. Geospatial Map page (full Leaflet + cluster + popup)
4. Forecast page (chart 4 model overlay)
5. Landing: Hero + Live Map + Solution + Team + Footer (5 dari 10 sections)
6. Theme switcher
7. Production deploy

**P1 — Sangat diingingkan (skip kalau benar-benar tertinggal)**:
1. Historical Analytics page
2. Reports / PDF export
3. Admin pages
4. Landing: Problem + Insight + Tech + Vision sections (5 sisa)

**P2 — Nice-to-have (cut tanpa ragu)**:
1. Settings page advanced (notifikasi, sessions)
2. Audit log expand row
3. PWA install prompt
4. Lottie animations

### 11.4 CI/CD Strategy

```yaml
# .github/workflows/ci.yml
- on: pull_request, push to main
- jobs:
  lint:        eslint + prettier check
  typecheck:   tsc --noEmit
  test-unit:   vitest run
  build:       vite build (verify production build sukses)
  test-e2e:    playwright (smoke only) — optional, manual trigger

# Deploy
- Vercel auto-deploy on push to main → production
- PR preview deploys → review URL per PR
- Phase 2: Railway auto-deploy via Railway GitHub integration
```

### 11.5 Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| FE bandwidth tipis (1 dev double duty) | High | High | Strict P0/P1 priority, defer P2, PM bantu testing |
| GeoJSON Kalimantan tidak tersedia simplified | Medium | Medium | Backup: pakai default Indonesia GeoJSON + filter, atau mapshaper online |
| Supabase free tier limit | Low | Low | Storage <500MB, project size <500MB, fine untuk capstone |
| ML hand-off tidak siap minggu 4 | High | Low | Phase 1 design memang tidak bergantung ML — seed dummy realistic |
| Landing cinematic terlalu heavy untuk 1 dev | Medium | High | Cut sections P1 kalau time crunch. Hero + Live Map + Solution + Team + Footer = 5 sections → tetap impressive |
| Cloudflare Turnstile setup blocker | Low | Medium | Fallback: skip captcha sementara, deploy tanpa, tambah saat ada waktu |
| Theme switcher hydration flash | Medium | Low | Read localStorage di `<head>` script before React hydrates → set `data-theme` early |

### 11.6 Success Criteria (untuk demo Minggu 5)

✓ Live di `agrolytics.my.id` dengan HTTPS  
✓ Landing page scroll smooth, hero frame sequence functional  
✓ Live Map landing menampilkan 56 kabupaten dengan hover/click  
✓ Login/register works (email + Google + Turnstile)  
✓ Dashboard Overview, Forecast, Map, Historical all functional dengan data Supabase  
✓ Reports page generate PDF download successfully  
✓ Admin role dapat suspend user, lihat audit log  
✓ Theme switcher persisted  
✓ Reduced motion accessibility verified  
✓ Chrome desktop testing — no console errors  
✓ Pitch deck dengan video demo siap presentasi

### 11.7 Post-Capstone Phase 2 Roadmap (Informational)

**Minggu 1–2 (Post-capstone)**:
- Railway FastAPI deployment + LSTM inference integration
- Swap mock predictions → real model output
- Forecast custom job queue (B3 hybrid)

**Minggu 3–4**:
- Plant Disease Detection: upload UI + TensorFlow CNN inference
- AI Assistant: LLM integration (Claude API atau open-source)

**Minggu 5+**:
- Capacitor APK build + mobile testing
- Real-time data ingestion (BPS API polling, NASA POWER scheduled)
- Advanced analytics (anomaly detection, forecasting confidence intervals)

## 12. Open Questions & References

### 12.1 Open Questions (untuk clarification post-design)

1. **GeoJSON Kalimantan source**: Apakah tim sudah punya shapefile Kalimantan
   kabupaten/kota dari QGIS? Kalau belum, backup: download dari
   `https://github.com/datasets/geo-countries` atau `opendata.go.id`.

2. **Hero frame sequence asset**: 31 frames sudah ada di `hero_parralax/` folder.
   Perlu convert JPG → WebP build-time via `sharp` untuk save bandwidth?

3. **Supabase project**: Sudah provision di `mawewomqcdnsqnxmkjlq.supabase.co`?
   Perlu setup RLS policies + seed data sebelum minggu 1 selesai?

4. **Cloudflare Turnstile**: Sudah ada account Cloudflare + site key? Atau setup
   saat minggu 2?

5. **Google OAuth**: Sudah setup Google Cloud Console project + OAuth credentials?
   Atau setup saat minggu 2?

6. **Domain `agrolytics.my.id`**: Sudah registered + DNS pointing ke Vercel?
   Atau pakai `*.vercel.app` subdomain dulu?

7. **IBM Skillsbuild branding**: Perlu logo IBM di landing page + footer? Atau
   cukup di pitch deck?

8. **PWA vs Capacitor**: Phase 1 PWA manifest + service worker minimal. Capacitor
   APK build masuk Phase 2 backlog?

9. **Data seed**: Tim AI Engineer akan provide CSV files BPS + NASA POWER? Atau
   saya generate dummy realistic via script?

10. **ML artifacts hand-off**: Saat minggu 4 selesai, tim AI akan provide `.h5`
    + `MinMaxScaler.joblib` + input/output schema docs?

### 12.2 References & Resources

#### Documentation
- [Supabase Auth](https://supabase.com/docs/guides/auth)
- [Supabase RLS](https://supabase.com/docs/guides/auth/row-level-security)
- [React Router v6](https://reactrouter.com/en/main)
- [TanStack Query](https://tanstack.com/query/latest)
- [Zustand](https://github.com/pmndrs/zustand)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Leaflet.js](https://leafletjs.com/reference.html)
- [Chart.js](https://www.chartjs.org/docs/latest/)
- [GSAP ScrollTrigger](https://gsap.com/docs/v3/Plugins/ScrollTrigger/)
- [Lenis](https://github.com/darkroom-labs/lenis)
- [Framer Motion](https://www.framer.com/motion/)
- [jsPDF](https://github.com/parallax/jsPDF)
- [html2canvas](https://html2canvas.hertzen.com/)

#### Data Sources
- [NASA POWER](https://power.larc.nasa.gov/) — meteorologi data
- [BPS (Badan Pusat Statistik)](https://www.bps.go.id/) — produksi padi historis
- [QGIS](https://www.qgis.org/) — shapefile processing

#### Design References
- [Vercel Design System](https://vercel.com/design)
- [Linear App](https://linear.app/) — SaaS UI inspiration
- [Figma](https://www.figma.com/) — design tool

#### Deployment & Infrastructure
- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/)

### 12.3 Glossary

| Term | Definition |
|---|---|
| **LSTM** | Long Short-Term Memory — deep learning model untuk time series prediction |
| **K-Means** | Unsupervised clustering algorithm untuk segmentasi wilayah |
| **RLS** | Row Level Security — Supabase policy untuk data access control |
| **Choropleth** | Peta dengan warna berdasarkan nilai data per region |
| **GeoJSON** | Format file untuk geographic data (polygon, point, line) |
| **Glassmorphism** | UI design dengan semi-transparent glass effect + blur |
| **Parallax** | Visual effect dimana background bergerak lebih lambat dari foreground |
| **Frame sequence** | Animasi dengan menampilkan frame-by-frame dari image sequence |
| **Service layer** | Abstraction layer untuk business logic + data fetching |
| **TanStack Query** | Library untuk async state management + caching |
| **Zustand** | Lightweight state management library |
| **Vercel rewrite** | URL rewrite rule untuk proxy request ke backend |
| **PWA** | Progressive Web App — web app yang bisa diinstall seperti native app |

### 12.4 Document History

| Date | Version | Author | Changes |
|---|---|---|---|
| 2026-05-29 | 1.0 | Claude Code | Initial design doc complete, all 12 sections |

### 12.5 Approval Sign-off

- **Design approved by**: M. Rohid Rivaldi (Front-End Lead)
- **Date approved**: 2026-05-29
- **Status**: Ready for implementation planning

---

## Appendix A — File Checklist (Pre-implementation)

Sebelum minggu 1 dimulai, pastikan:

- [ ] GitHub repo initialized + `.gitignore` + `README.md`
- [ ] Supabase project provisioned + schema migrations applied
- [ ] Vercel project linked + environment variables configured
- [ ] `hero_parralax/` folder renamed/moved ke `public/frames/hero/`
- [ ] GeoJSON Kalimantan kabupaten tersedia di `public/geojson/`
- [ ] Cloudflare Turnstile site key configured
- [ ] Google OAuth credentials setup
- [ ] Domain `agrolytics.my.id` DNS pointing ke Vercel (atau use `*.vercel.app`)
- [ ] Figma design file shared dengan tim
- [ ] Jira board setup dengan epics + stories
- [ ] Daily standup schedule confirmed (time + platform)

## Appendix B — Deployment Checklist (Minggu 5)

Sebelum production deploy:

- [ ] All P0 features tested + working
- [ ] Console errors cleared (Chrome DevTools)
- [ ] Accessibility audit passed (reduced motion, keyboard nav, color contrast)
- [ ] Performance audit passed (Lighthouse >80 semua kategori)
- [ ] Environment variables secured (no secrets di code)
- [ ] HTTPS certificate valid
- [ ] Analytics setup (optional: Vercel Analytics atau Plausible)
- [ ] Error tracking setup (optional: Sentry)
- [ ] Backup + disaster recovery plan documented
- [ ] Pitch deck finalized
- [ ] Video demo recorded
- [ ] Team ready untuk presentasi

---

**End of Design Document**

Dokumen ini adalah blueprint lengkap untuk implementasi Agrolytics Phase 1.
Setiap section dirancang untuk actionable — tim dapat langsung mulai coding
berdasarkan spec ini tanpa ambiguitas.

Untuk pertanyaan atau clarification, hubungi PM (Muhammad Rakha Djauhari) atau
FE Lead (M. Rohid Rivaldi).
