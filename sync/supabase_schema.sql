-- Run in your own Supabase project SQL Editor. Do not expose service_role keys.
create table if not exists public.thaiword_progress (
  user_id uuid primary key references auth.users(id) on delete cascade,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
alter table public.thaiword_progress enable row level security;
revoke all on public.thaiword_progress from anon;
grant select, insert, update on public.thaiword_progress to authenticated;
drop policy if exists "ThaiWord owner select" on public.thaiword_progress;
drop policy if exists "ThaiWord owner insert" on public.thaiword_progress;
drop policy if exists "ThaiWord owner update" on public.thaiword_progress;
create policy "ThaiWord owner select" on public.thaiword_progress for select to authenticated using ((select auth.uid())=user_id);
create policy "ThaiWord owner insert" on public.thaiword_progress for insert to authenticated with check ((select auth.uid())=user_id);
create policy "ThaiWord owner update" on public.thaiword_progress for update to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
