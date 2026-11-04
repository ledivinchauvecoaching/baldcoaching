-- =====================================================================
-- Carnet d'entraînement @bald.coaching : OBJECTIFS NUTRITION FIXÉS PAR LE COACH (migration n°4)
-- À coller dans Supabase > SQL Editor > New query > Run, APRÈS 03. Peut être relancé.
--
-- Le coach peut écrire UN document chez son client : reglages/coach (calories,
-- protéines, lipides, repas par jour). Le client le lit mais ne peut pas le modifier.
-- =====================================================================

drop policy if exists "ajouter ses donnees"   on public.carnet_docs;
drop policy if exists "modifier ses donnees"  on public.carnet_docs;
drop policy if exists "supprimer ses donnees" on public.carnet_docs;

-- Chez soi : tout, sauf le document réservé au coach.
-- Chez un client coaché : séances prévues, commentaires et reglages/coach.
create policy "ajouter ses donnees" on public.carnet_docs for insert to authenticated
  with check (
    ((select auth.uid()) = user_id and public.est_membre((select auth.uid()))
       and not (collection = 'reglages' and doc_id = 'coach'))
    or ((collection in ('prevues','commentaires') or (collection = 'reglages' and doc_id = 'coach'))
       and public.coache((select auth.uid()), user_id)));

create policy "modifier ses donnees" on public.carnet_docs for update to authenticated
  using (
    ((select auth.uid()) = user_id and public.est_membre((select auth.uid()))
       and not (collection = 'reglages' and doc_id = 'coach'))
    or ((collection in ('prevues','commentaires') or (collection = 'reglages' and doc_id = 'coach'))
       and public.coache((select auth.uid()), user_id)))
  with check (
    ((select auth.uid()) = user_id and public.est_membre((select auth.uid()))
       and not (collection = 'reglages' and doc_id = 'coach'))
    or ((collection in ('prevues','commentaires') or (collection = 'reglages' and doc_id = 'coach'))
       and public.coache((select auth.uid()), user_id)));

create policy "supprimer ses donnees" on public.carnet_docs for delete to authenticated
  using (
    ((select auth.uid()) = user_id and not (collection = 'reglages' and doc_id = 'coach'))
    or ((collection in ('prevues','commentaires') or (collection = 'reglages' and doc_id = 'coach'))
       and public.coache((select auth.uid()), user_id)));
