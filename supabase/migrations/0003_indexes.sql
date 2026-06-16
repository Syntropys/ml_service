-- ──────────────────────────────────────────────────────────────────
-- Migration 0003 — Composite Indexes for Hot Path Queries
-- ──────────────────────────────────────────────────────────────────

-- production_history: filter by region + year (Forecast page, Overview KPIs)
create index idx_production_region_year
  on public.production_history (region_id, year);

-- weather_history: filter by region + year + month (Historical chart)
create index idx_weather_region_yearmonth
  on public.weather_history (region_id, year, month);

-- predictions: filter by region + year + model (Forecast page main query)
create index idx_predictions_region_year_model
  on public.predictions (region_id, target_year, model_name);

-- predictions baseline lookup (Map choropleth)
create index idx_predictions_baseline
  on public.predictions (target_year, is_baseline)
  where is_baseline = true;

-- audit_log: list newest first (Admin Audit Log table)
create index idx_audit_created_desc
  on public.audit_log (created_at desc);

create index idx_audit_actor
  on public.audit_log (actor_id);

-- regions: filter by province (cascade dropdown UX)
create index idx_regions_province
  on public.regions (province, name);

-- profiles: filter by role + status (Admin User Management)
create index idx_profiles_role_status
  on public.profiles (role, status);
