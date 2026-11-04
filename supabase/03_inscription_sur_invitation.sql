-- =====================================================================
-- Carnet d'entraînement @bald.coaching : INSCRIPTION SUR INVITATION (migration n°3)
-- À coller dans Supabase > SQL Editor > New query > Run, APRÈS 02_espace_coach.sql.
-- Peut être relancé sans risque.
--
-- Effet : un compte (Google ou lien e-mail) ne peut être CRÉÉ que si son adresse
-- e-mail a une invitation en cours. Les comptes existants ne changent pas.
-- Ensuite : Authentication > Auth Hooks > « Before User Created » >
--           Postgres > schéma public > fonction hook_inscription_sur_invitation.
-- =====================================================================

-- 0) Ces tables restent fermées aux comptes (aucun droit accordé) ; seules les fonctions
--    ci-dessous, exécutées par leur propriétaire, peuvent les lire. Sans « force », le
--    propriétaire n'est pas bloqué par ses propres règles.
alter table public.app_roles   no force row level security;
alter table public.coaching    no force row level security;
alter table public.invitations no force row level security;

-- 1) L'invitation porte l'adresse e-mail du client
alter table public.invitations add column if not exists email text;
create index if not exists invitations_email_idx on public.invitations (lower(email));

-- 2) Création d'invitation : prénom + e-mail obligatoire
drop function if exists public.creer_invitation(text);
create or replace function public.creer_invitation(p_note text, p_email text) returns json
language plpgsql volatile security definer set search_path = public as $$
declare me uuid := auth.uid(); t text; e text := lower(trim(p_email));
begin
  if not public.est_coach(me) then raise exception 'reserve au coach' using errcode = '42501'; end if;
  if e is null or e !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then raise exception 'email invalide' using errcode = '22023'; end if;
  t := replace(gen_random_uuid()::text,'-','') || replace(gen_random_uuid()::text,'-','');
  insert into public.invitations(token, coach_id, note, email) values (t, me, left(nullif(trim(p_note),''),80), e);
  return (select json_build_object('token',token,'note',note,'email',email,'expire_le',expire_le) from public.invitations where token = t);
end $$;

create or replace function public.mes_invitations() returns setof json
language sql stable security definer set search_path = public as $$
  select json_build_object('token',token,'note',note,'email',email,'cree_le',cree_le,'expire_le',expire_le)
  from public.invitations
  where coach_id = auth.uid() and public.est_coach(auth.uid()) and utilise_par is null and expire_le > now()
  order by cree_le desc
$$;

-- 3) Accepter : le lien ne marche que pour l'adresse invitée
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
  if inv.email is not null and lower(u.email) <> lower(inv.email) then
    return json_build_object('ok',false,'raison','autre_email'); end if;
  insert into public.coaching(client_id, coach_id, client_email, client_nom)
    values (me, inv.coach_id, u.email, coalesce(nullif(u.nom,''), inv.note))
    on conflict (client_id) do update set coach_id = excluded.coach_id, actif = true,
      client_email = excluded.client_email, client_nom = coalesce(excluded.client_nom, public.coaching.client_nom);
  update public.invitations set utilise_par = me, utilise_le = now() where token = p_token;
  return json_build_object('ok',true);
end $$;

-- 4) Le crochet d'inscription (appelé par Supabase Auth AVANT de créer un compte)
create or replace function public.hook_inscription_sur_invitation(event jsonb) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare e text := lower(trim(event->'user'->>'email'));
begin
  if e is not null and exists(
    select 1 from public.invitations
    where lower(email) = e and utilise_par is null and expire_le > now()) then
    return '{}'::jsonb;
  end if;
  return jsonb_build_object('error', jsonb_build_object(
    'http_code', 403,
    'message', 'Inscription reservee aux clients de bald.coaching : demande ton lien d''invitation a ton coach.'));
end $$;

revoke execute on function public.hook_inscription_sur_invitation(jsonb) from public, anon, authenticated;
do $$ begin
  grant execute on function public.hook_inscription_sur_invitation(jsonb) to supabase_auth_admin;
exception when undefined_object then null; end $$;

revoke execute on function public.creer_invitation(text,text) from public, anon;
grant execute on function public.creer_invitation(text,text) to authenticated;
