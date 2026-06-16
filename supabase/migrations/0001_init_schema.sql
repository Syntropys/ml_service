-- ──────────────────────────────────────────────────────────────────
-- Migration 0001 — Initial Schema
-- Agrolytics Phase 1 baseline tables
-- ──────────────────────────────────────────────────────────────────

create extension if not exists "pgcrypto";

-- ──────────────────────────────────────────────────────────────────
-- profiles (extends auth.users 1:1)
-- ──────────────────────────────────────────────────────────────────
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  full_name text,
  avatar_url text,
  role text not null default 'user' check (role in ('admin','user')),
  status text not null default 'active' check (status in ('active','suspended')),
  preferred_theme text not null default 'dark' check (preferred_theme in ('dark','light')),
  last_login_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ──────────────────────────────────────────────────────────────────
-- regions (master 56 kabupaten/kota Kalimantan)
-- ──────────────────────────────────────────────────────────────────
create table public.regions (
  id uuid primary key default gen_random_uuid(),
  bps_code text unique not null,
  name text not null,
  province text not null,
  province_code text,
  centroid_lat numeric(9,6),
  centroid_lng numeric(9,6),
  area_km2 numeric,
  geojson_id text,
  created_at timestamptz not null default now()
);

-- ──────────────────────────────────────────────────────────────────
-- production_history (BPS 2018–2025)
-- ──────────────────────────────────────────────────────────────────
create table public.production_history (
  id uuid primary key default gen_random_uuid(),
  region_id uuid not null references public.regions(id) on delete cascade,
  year int not null check (year between 2015 and 2030),
  month int check (month between 1 and 12),
  production_ton numeric not null,
  area_harvest_ha numeric,
  yield_ton_ha numeric,
  source text not null default 'BPS',
  created_at timestamptz not null default now(),
  unique (region_id, year, month)
);

-- ──────────────────────────────────────────────────────────────────
-- weather_history (NASA POWER bulanan)
-- ──────────────────────────────────────────────────────────────────
create table public.weather_history (
  id uuid primary key default gen_random_uuid(),
  region_id uuid not null references public.regions(id) on delete cascade,
  year int not null check (year between 2015 and 2030),
  month int not null check (month between 1 and 12),
  rainfall_mm numeric,
  temp_avg_c numeric,
  temp_min_c numeric,
  temp_max_c numeric,
  humidity_pct numeric,
  solar_radiation numeric,
  source text not null default 'NASA_POWER',
  created_at timestamptz not null default now(),
  unique (region_id, year, month)
);

-- ──────────────────────────────────────────────────────────────────
-- predictions (model output, Phase 1 dummy seed)
-- ──────────────────────────────────────────────────────────────────
create table public.predictions (
  id uuid primary key default gen_random_uuid(),
  region_id uuid not null references public.regions(id) on delete cascade,
  target_year int not null,
  target_month int check (target_month between 1 and 12),
  predicted_yield numeric not null,
  predicted_prod_ton numeric,
  confidence_lower numeric,
  confidence_upper numeric,
  model_name text not null check (model_name in ('lstm','xgboost','random_forest','linear')),
  model_version text not null default 'v1-dummy',
  computed_at timestamptz not null default now(),
  is_baseline boolean not null default false
);

-- ──────────────────────────────────────────────────────────────────
-- cluster_assignments (K-Means hasil)
-- ──────────────────────────────────────────────────────────────────
create table public.cluster_assignments (
  id uuid primary key default gen_random_uuid(),
  region_id uuid not null references public.regions(id) on delete cascade,
  cluster_label int not null check (cluster_label in (0,1,2)),
  cluster_name text,
  reference_year int not null,
  computed_at timestamptz not null default now(),
  unique (region_id, reference_year)
);

-- ──────────────────────────────────────────────────────────────────
-- audit_log (admin actions)
-- ──────────────────────────────────────────────────────────────────
create table public.audit_log (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid references public.profiles(id) on delete set null,
  action text not null,
  entity_type text,
  entity_id uuid,
  metadata jsonb,
  ip_address inet,
  user_agent text,
  created_at timestamptz not null default now()
);

comment on table public.profiles is 'Extends auth.users with role, status, theme preference';
comment on table public.regions is 'Master 56 kabupaten/kota Kalimantan dari BPS';
comment on table public.production_history is 'Produksi padi historis (BPS) per region per tahun/bulan';
comment on table public.weather_history is 'Cuaca historis (NASA POWER) per region bulanan';
comment on table public.predictions is 'Output model prediksi produktivitas (LSTM + 3 baseline)';
comment on table public.cluster_assignments is 'Hasil K-Means clustering 3 kategori (high/medium/low)';
comment on table public.audit_log is 'Log admin actions; INSERT only via RPC functions';
