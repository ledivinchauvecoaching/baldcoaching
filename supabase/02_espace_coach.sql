-- =====================================================================
-- Carnet d'entraînement @bald.coaching : ESPACE COACH (migration n°2)
-- À coller une seule fois dans Supabase > SQL Editor > New query > Run,
-- APRÈS schema.sql. Peut être relancé sans risque.
--
-- Règles :
--   * un seul coach (rôle dans app_roles) ;
--   * l'appli est réservée au coach et à ses clients (invitation) ;
--   * le coach LIT tout le carnet de ses clients actifs ;
--   * le coach ÉCRIT seulement leurs séances prévues et des commentaires ;
--   * un client ne voit jamais les données d'un autre client.
-- =====================================================================

-- 1) Nouvelle collection : commentaires du coach sur les séances
alter table public.carnet_docs drop constraint if exists carnet_docs_collection_check;
alter table public.carnet_docs add constraint carnet_docs_collection_check
  check (collection in ('seances','objectifs','prevues','tracking','reglages','commentaires'));

-- 2) Rôles (le coach)
create table if not exists public.app_roles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role    text not null check (role in ('coach'))
);

-- 3) Lien coach ↔ client
create table if not exists public.coaching (
  client_id    uuid primary key references auth.users(id) on delete cascade,
  coach_id     uuid not null references auth.users(id) on delete cascade,
  client_email text,
  client_nom   text,
  depuis       timestamptz not null default now(),
  actif        boolean not null default true
);

-- 4) Invitations (lien à usage unique, valable 14 jours)
create table if not exists public.invitations (
  token      text primary key,
  coach_id   uuid not null references auth.users(id) on delete cascade,
  note       text check (char_length(note) <= 80),
  cree_le    timestamptz not null default now(),
  expire_le  timestamptz not null default now() + interval '14 days',
  utilise_par uuid references auth.users(id) on delete set null,
  utilise_le timestamptz
);

-- Ces 3 tables ne sont accessibles QUE par les fonctions ci-dessous.
alter table public.app_roles   enable row level security;
alter table public.coaching    enable row level security;
alter table public.invitations enable row level security;
alter table public.app_roles   force row level security;
alter table public.coaching    force row level security;
alter table public.invitations force row level security;
revoke all on public.app_roles, public.coaching, public.invitations from anon, authenticated;

-- 5) Fonctions d'aide (utilisées par les règles de sécurité)
create or replace function public.est_coach(u uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.app_roles where user_id = u and role = 'coach')
$$;

create or replace function public.est_membre(u uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select public.est_coach(u) or exists(select 1 from public.coaching where client_id = u and actif)
$$;

create or replace function public.coache(coach uuid, client uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select public.est_coach(coach) and exists(
    select 1 from public.coaching where client_id = client and coach_id = coach and actif)
$$;

-- 6) Règles du carnet
drop policy if exists "lire ses donnees"      on public.carnet_docs;
drop policy if exists "ajouter ses donnees"   on public.carnet_docs;
drop policy if exists "modifier ses donnees"  on public.carnet_docs;
drop policy if exists "supprimer ses donnees" on public.carnet_docs;

-- Lire : ses propres lignes (toujours, même sans abonnement : export RGPD),
--        ou celles d'un client que l'on coache.
create policy "lire ses donnees" on public.carnet_docs for select to authenticated
  using ((select auth.uid()) = user_id or public.coache((select auth.uid()), user_id));

-- Ajouter : chez soi si membre ; chez un client coaché seulement prévues + commentaires.
create policy "ajouter ses donnees" on public.carnet_docs for insert to authenticated
  with check (
    ((select auth.uid()) = user_id and public.est_membre((select auth.uid())))
    or (collection in ('prevues','commentaires') and public.coache((select auth.uid()), user_id)));

create policy "modifier ses donnees" on public.carnet_docs for update to authenticated
  using (
    ((select auth.uid()) = user_id and public.est_membre((select auth.uid())))
    or (collection in ('prevues','commentaires') and public.coache((select auth.uid()), user_id)))
  with check (
    ((select auth.uid()) = user_id and public.est_membre((select auth.uid())))
    or (collection in ('prevues','commentaires') and public.coache((select auth.uid()), user_id)));

create policy "supprimer ses donnees" on public.carnet_docs for delete to authenticated
  using (
    (select auth.uid()) = user_id
    or (collection in ('prevues','commentaires') and public.coache((select auth.uid()), user_id)));

-- 7) Fonctions appelées par l'appli
create or replace function public.mon_statut() returns json
language plpgsql stable security definer set search_path = public as $$
declare me uuid := auth.uid(); c record;
begin
  if me is null then return json_build_object('role','aucun'); end if;
  if public.est_coach(me) then return json_build_object('role','coach'); end if;
  select * into c from public.coaching where client_id = me;
  if found and c.actif then return json_build_object('role','client','depuis',c.depuis); end if;
  if found then return json_build_object('role','suspendu'); end if;
  return json_build_object('role','aucun');
end $$;

create or replace function public.creer_invitation(p_note text default null) returns json
language plpgsql volatile security definer set search_path = public as $$
declare me uuid := auth.uid(); t text;
begin
  if not public.est_coach(me) then raise exception 'reserve au coach' using errcode = '42501'; end if;
  t := replace(gen_random_uuid()::text,'-','') || replace(gen_random_uuid()::text,'-','');
  insert into public.invitations(token, coach_id, note) values (t, me, left(nullif(trim(p_note),''),80));
  return (select json_build_object('token',token,'note',note,'expire_le',expire_le) from public.invitations where token = t);
end $$;

create or replace function public.mes_invitations() returns setof json
language sql stable security definer set search_path = public as $$
  select json_build_object('token',token,'note',note,'cree_le',cree_le,'expire_le',expire_le)
  from public.invitations
  where coach_id = auth.uid() and public.est_coach(auth.uid()) and utilise_par is null and expire_le > now()
  order by cree_le desc
$$;

create or replace function public.annuler_invitation(p_token text) returns void
language sql volatile security definer set search_path = public as $$
  delete from public.invitations where token = p_token and coach_id = auth.uid() and utilise_par is null
$$;

create or replace function public.accepter_invitation(p_token text) returns json
language plpgsql volatile security definer set search_path = public as $$
declare me uuid := auth.uid(); inv record; u record;
begin
  if me is null then raise exception 'non connecte' using errcode = '42501'; end if;
  if public.est_coach(me) then return json_build_object('ok',false,'raison','coach'); end if;
  select * into inv from public.invitations where token = p_token for update;
  if not found or inv.utilise_par is not null or inv.expire_le < now() then
    return json_build_object('ok',false,'raison','invalide'); end if;
  select email, coalesce(raw_user_meta_data->>'full_name', raw_user_meta_data->>'name', '') as nom
    into u from auth.users where id = me;
  insert into public.coaching(client_id, coach_id, client_email, client_nom)
    values (me, inv.coach_id, u.email, nullif(u.nom,''))
    on conflict (client_id) do update set coach_id = excluded.coach_id, actif = true,
      client_email = excluded.client_email, client_nom = coalesce(excluded.client_nom, public.coaching.client_nom);
  update public.invitations set utilise_par = me, utilise_le = now() where token = p_token;
  return json_build_object('ok',true);
end $$;

create or replace function public.mes_clients() returns setof json
language sql stable security definer set search_path = public as $$
  select json_build_object('id',client_id,'email',client_email,'nom',client_nom,'depuis',depuis,'actif',actif)
  from public.coaching
  where coach_id = auth.uid() and public.est_coach(auth.uid())
  order by actif desc, coalesce(client_nom, client_email)
$$;

create or replace function public.changer_client(p_client uuid, p_actif boolean) returns void
language sql volatile security definer set search_path = public as $$
  update public.coaching set actif = p_actif
  where client_id = p_client and coach_id = auth.uid() and public.est_coach(auth.uid())
$$;

-- Personne d'autre que les comptes connectés ne peut appeler ces fonctions.
revoke execute on function public.est_coach(uuid), public.est_membre(uuid), public.coache(uuid,uuid),
  public.mon_statut(), public.creer_invitation(text), public.mes_invitations(), public.annuler_invitation(text),
  public.accepter_invitation(text), public.mes_clients(), public.changer_client(uuid,boolean) from public, anon;
grant execute on function public.est_coach(uuid), public.est_membre(uuid), public.coache(uuid,uuid),
  public.mon_statut(), public.creer_invitation(text), public.mes_invitations(), public.annuler_invitation(text),
  public.accepter_invitation(text), public.mes_clients(), public.changer_client(uuid,boolean) to authenticated;

-- 8) TOI = COACH. Remplace l'adresse par celle de ton compte dans l'appli, puis exécute.
--    (Supabase > Authentication > Users pour la retrouver.)
insert into public.app_roles(user_id, role)
  select id, 'coach' from auth.users where email = 'TON_EMAIL_ICI'
  on conflict (user_id) do nothing;

-- Vérification : doit afficher une ligne avec ton e-mail.
select u.email, r.role from public.app_roles r join auth.users u on u.id = r.user_id;
