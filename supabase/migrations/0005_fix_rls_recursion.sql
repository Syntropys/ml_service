-- ──────────────────────────────────────────────────────────────────
-- Migration 0005 — Fix RLS Infinite Recursion
-- ──────────────────────────────────────────────────────────────────
-- Problem: admin policies (FOR ALL) on every table queried public.profiles
-- to check role = 'admin'. But profiles itself has an admin policy that
-- queries profiles → infinite recursion → Postgres aborts with 500 on
-- ALL reads (even anon public-read on regions/clusters for the landing map).
--
-- Fix: is_admin() with SECURITY DEFINER bypasses RLS internally (runs as
-- function owner), breaking the recursion. Rewrite every admin policy to
-- call it instead of an inline EXISTS subquery on profiles.
-- ──────────────────────────────────────────────────────────────────

create or replace function public.is_admin()
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from public.profiles where id = auth.uid() and role = 'admin'
  );
$$;

grant execute on function public.is_admin to authenticated, anon;

-- profiles
drop policy if exists "profiles_admin_all" on public.profiles;
create policy "profiles_admin_all" on public.profiles
  for all using (public.is_admin());

-- regions
drop policy if exists "regions_admin_write" on public.regions;
create policy "regions_admin_write" on public.regions
  for all using (public.is_admin());

-- production_history
drop policy if exists "production_admin_write" on public.production_history;
create policy "production_admin_write" on public.production_history
  for all using (public.is_admin());

-- weather_history
drop policy if exists "weather_admin_write" on public.weather_history;
create policy "weather_admin_write" on public.weather_history
  for all using (public.is_admin());

-- cluster_assignments
drop policy if exists "cluster_admin_write" on public.cluster_assignments;
create policy "cluster_admin_write" on public.cluster_assignments
  for all using (public.is_admin());

-- predictions
drop policy if exists "predictions_admin_write" on public.predictions;
create policy "predictions_admin_write" on public.predictions
  for all using (public.is_admin());

-- audit_log
drop policy if exists "audit_admin_read" on public.audit_log;
create policy "audit_admin_read" on public.audit_log
  for select using (public.is_admin());
