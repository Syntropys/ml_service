-- ──────────────────────────────────────────────────────────────────
-- Migration 0002 — Row Level Security Policies
-- ──────────────────────────────────────────────────────────────────

-- Enable RLS on all tables
alter table public.profiles enable row level security;
alter table public.regions enable row level security;
alter table public.production_history enable row level security;
alter table public.weather_history enable row level security;
alter table public.predictions enable row level security;
alter table public.cluster_assignments enable row level security;
alter table public.audit_log enable row level security;

-- ──────────────────────────────────────────────────────────────────
-- profiles
-- ──────────────────────────────────────────────────────────────────
create policy "profiles_self_read" on public.profiles
  for select using (auth.uid() = id);

create policy "profiles_self_update" on public.profiles
  for update using (auth.uid() = id);

create policy "profiles_admin_all" on public.profiles
  for all using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );

-- ──────────────────────────────────────────────────────────────────
-- regions (public read; admin write)
-- ──────────────────────────────────────────────────────────────────
create policy "regions_public_read" on public.regions
  for select using (true);

create policy "regions_admin_write" on public.regions
  for all using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );

-- ──────────────────────────────────────────────────────────────────
-- production_history (public read; admin write)
-- ──────────────────────────────────────────────────────────────────
create policy "production_public_read" on public.production_history
  for select using (true);

create policy "production_admin_write" on public.production_history
  for all using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );

-- ──────────────────────────────────────────────────────────────────
-- weather_history (public read; admin write)
-- ──────────────────────────────────────────────────────────────────
create policy "weather_public_read" on public.weather_history
  for select using (true);

create policy "weather_admin_write" on public.weather_history
  for all using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );

-- ──────────────────────────────────────────────────────────────────
-- cluster_assignments (public read for landing Live Map; admin write)
-- ──────────────────────────────────────────────────────────────────
create policy "cluster_public_read" on public.cluster_assignments
  for select using (true);

create policy "cluster_admin_write" on public.cluster_assignments
  for all using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );

-- ──────────────────────────────────────────────────────────────────
-- predictions (auth-only read; admin write)
-- ──────────────────────────────────────────────────────────────────
create policy "predictions_auth_read" on public.predictions
  for select using (auth.uid() is not null);

create policy "predictions_admin_write" on public.predictions
  for all using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );

-- ──────────────────────────────────────────────────────────────────
-- audit_log (admin read-only; INSERT via RPC function only, no client write)
-- ──────────────────────────────────────────────────────────────────
create policy "audit_admin_read" on public.audit_log
  for select using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );
