-- ──────────────────────────────────────────────────────────────────
-- Migration 0004 — Triggers & RPC Functions
-- ──────────────────────────────────────────────────────────────────

-- Auto-update updated_at on profiles
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_profiles_updated_at
  before update on public.profiles
  for each row
  execute function public.set_updated_at();

-- ──────────────────────────────────────────────────────────────────
-- Auto-create profile on auth.users INSERT
-- ──────────────────────────────────────────────────────────────────
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name, role, status)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', ''),
    'user',
    'active'
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute function public.handle_new_user();

-- ──────────────────────────────────────────────────────────────────
-- RPC: admin_set_user_role (with audit log + self-demote prevention)
-- ──────────────────────────────────────────────────────────────────
create or replace function public.admin_set_user_role(
  target_user uuid,
  new_role text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  actor uuid := auth.uid();
  actor_role text;
begin
  if actor is null then
    raise exception 'unauthorized: not authenticated';
  end if;

  select role into actor_role from public.profiles where id = actor;
  if actor_role is null or actor_role <> 'admin' then
    raise exception 'unauthorized: admin role required';
  end if;

  if new_role not in ('admin','user') then
    raise exception 'invalid role: %', new_role;
  end if;

  if target_user = actor and new_role <> 'admin' then
    raise exception 'cannot demote self';
  end if;

  update public.profiles set role = new_role where id = target_user;

  insert into public.audit_log (actor_id, action, entity_type, entity_id, metadata)
  values (
    actor,
    'user.set_role',
    'profile',
    target_user,
    jsonb_build_object('new_role', new_role)
  );
end;
$$;

-- ──────────────────────────────────────────────────────────────────
-- RPC: admin_set_user_status (suspend/activate)
-- ──────────────────────────────────────────────────────────────────
create or replace function public.admin_set_user_status(
  target_user uuid,
  new_status text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  actor uuid := auth.uid();
  actor_role text;
begin
  if actor is null then
    raise exception 'unauthorized: not authenticated';
  end if;

  select role into actor_role from public.profiles where id = actor;
  if actor_role is null or actor_role <> 'admin' then
    raise exception 'unauthorized: admin role required';
  end if;

  if new_status not in ('active','suspended') then
    raise exception 'invalid status: %', new_status;
  end if;

  if target_user = actor and new_status = 'suspended' then
    raise exception 'cannot suspend self';
  end if;

  update public.profiles set status = new_status where id = target_user;

  insert into public.audit_log (actor_id, action, entity_type, entity_id, metadata)
  values (
    actor,
    'user.set_status',
    'profile',
    target_user,
    jsonb_build_object('new_status', new_status)
  );
end;
$$;

-- Grant execute on RPC functions to authenticated users (still gated by SECURITY DEFINER + role check)
grant execute on function public.admin_set_user_role to authenticated;
grant execute on function public.admin_set_user_status to authenticated;
