-- =====================================================================
-- Carnet d'entraînement @bald.coaching : BILAN HEBDOMADAIRE + PHOTOS (migration n°5)
-- À coller dans Supabase > SQL Editor > New query > Run, APRÈS 04. Peut être relancé.
--
-- * nouvelle collection « bilans » (un bilan par semaine, écrit par le client,
--   lu par son coach grâce aux règles déjà en place) ;
-- * espace de stockage PRIVÉ « photos » : chaque client range ses photos dans
--   un dossier à son identifiant ; lui seul peut les déposer, lui et son coach
--   peuvent les voir (liens temporaires). Rien n'est public.
-- =====================================================================

alter table public.carnet_docs drop constraint if exists carnet_docs_collection_check;
alter table public.carnet_docs add constraint carnet_docs_collection_check
  check (collection in ('seances','objectifs','prevues','tracking','reglages','commentaires','bilans'));

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('photos', 'photos', false, 5242880, array['image/jpeg','image/webp','image/png'])
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

-- Le dossier (1er niveau du chemin) doit être l'identifiant d'un compte.
create or replace function public.dossier_photo(nom text) returns uuid
language sql immutable as $$
  select case when split_part(nom,'/',1) ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
              then split_part(nom,'/',1)::uuid end
$$;

drop policy if exists "photos : voir"      on storage.objects;
drop policy if exists "photos : deposer"   on storage.objects;
drop policy if exists "photos : remplacer" on storage.objects;
drop policy if exists "photos : supprimer" on storage.objects;

create policy "photos : voir" on storage.objects for select to authenticated
  using (bucket_id = 'photos' and (
    public.dossier_photo(name) = (select auth.uid())
    or public.coache((select auth.uid()), public.dossier_photo(name))));

create policy "photos : deposer" on storage.objects for insert to authenticated
  with check (bucket_id = 'photos' and public.dossier_photo(name) = (select auth.uid())
    and public.est_membre((select auth.uid())));

create policy "photos : remplacer" on storage.objects for update to authenticated
  using (bucket_id = 'photos' and public.dossier_photo(name) = (select auth.uid()))
  with check (bucket_id = 'photos' and public.dossier_photo(name) = (select auth.uid())
    and public.est_membre((select auth.uid())));

create policy "photos : supprimer" on storage.objects for delete to authenticated
  using (bucket_id = 'photos' and public.dossier_photo(name) = (select auth.uid()));
