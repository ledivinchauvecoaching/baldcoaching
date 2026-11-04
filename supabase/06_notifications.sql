-- =====================================================================
-- Carnet d'entraînement @bald.coaching : NOTIFICATIONS PUSH (migration n°6)
-- À coller dans Supabase > SQL Editor > New query > Run, APRÈS 05. Peut être relancé.
-- Chaque appareil qui accepte les notifications enregistre ici son « adresse » push.
-- Seul son propriétaire la voit ; la fonction « notifier » (clé service) les lit pour envoyer.
-- =====================================================================
create table if not exists public.abonnements_push (
  endpoint text primary key check (endpoint like 'https://%' and char_length(endpoint) < 1000),
  user_id  uuid not null default auth.uid() references auth.users(id) on delete cascade,
  p256dh   text not null check (char_length(p256dh) < 200),
  auth     text not null check (char_length(auth) < 100),
  cree_le  timestamptz not null default now()
);
alter table public.abonnements_push enable row level security;
revoke all on public.abonnements_push from anon;
grant select, insert, update, delete on public.abonnements_push to authenticated;
drop policy if exists "push : les siens" on public.abonnements_push;
create policy "push : les siens" on public.abonnements_push for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
