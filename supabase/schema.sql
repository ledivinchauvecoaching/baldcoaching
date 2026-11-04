-- =====================================================================
-- Carnet d'entraînement @bald.coaching : schéma Supabase
-- À coller une seule fois dans Supabase > SQL Editor > New query > Run
-- =====================================================================

-- Une seule table : chaque ligne est un document (séance, objectif,
-- séance prévue, jour de suivi ou réglages) appartenant à UN utilisateur.
create table if not exists public.carnet_docs (
  user_id    uuid        not null default auth.uid() references auth.users(id) on delete cascade,
  collection text        not null check (collection in ('seances','objectifs','prevues','tracking','reglages')),
  doc_id     text        not null check (char_length(doc_id) between 1 and 200),
  data       jsonb       not null check (pg_column_size(data) < 262144),
  updated_at timestamptz not null default now(),
  primary key (user_id, collection, doc_id)
);

-- Cloisonnement : chacun ne voit et ne modifie QUE ses propres lignes.
alter table public.carnet_docs enable row level security;
alter table public.carnet_docs force row level security;

drop policy if exists "lire ses donnees"      on public.carnet_docs;
drop policy if exists "ajouter ses donnees"   on public.carnet_docs;
drop policy if exists "modifier ses donnees"  on public.carnet_docs;
drop policy if exists "supprimer ses donnees" on public.carnet_docs;

create policy "lire ses donnees"      on public.carnet_docs for select to authenticated using ((select auth.uid()) = user_id);
create policy "ajouter ses donnees"   on public.carnet_docs for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "modifier ses donnees"  on public.carnet_docs for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "supprimer ses donnees" on public.carnet_docs for delete to authenticated using ((select auth.uid()) = user_id);

-- Les visiteurs non connectés n'ont aucun accès.
revoke all on public.carnet_docs from anon;
grant select, insert, update, delete on public.carnet_docs to authenticated;

-- Synchronisation en direct entre appareils (ajouts et modifications).
do $$ begin
  alter publication supabase_realtime add table public.carnet_docs;
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------
-- Vérification (facultatif) : doit renvoyer "true" pour les 4 lignes RLS
-- select relname, relrowsecurity, relforcerowsecurity from pg_class where relname = 'carnet_docs';
-- ---------------------------------------------------------------------
