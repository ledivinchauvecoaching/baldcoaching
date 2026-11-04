\pset tuples_only on
\set ON_ERROR_STOP 0
insert into auth.users values ('00000000-0000-0000-0000-00000000c0ac','coach@x.fr','{}'),('00000000-0000-0000-0000-0000000000a1','paul@x.fr','{"full_name":"Paul"}'),('00000000-0000-0000-0000-0000000000b2','autre@x.fr','{}');
insert into public.app_roles values ('00000000-0000-0000-0000-00000000c0ac','coach');
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-00000000c0ac',false);
\echo H01 invitation sans e-mail (attendu ERREUR)
select public.creer_invitation('Paul',null);
\echo H02 invitation e-mail invalide (attendu ERREUR)
select public.creer_invitation('Paul','pas-un-mail');
select (public.creer_invitation('Paul','Paul@X.fr')->>'token') as tok \gset
reset role; set role supabase_auth_admin;
\echo H03 inscription paul@x.fr invite (attendu {})
select public.hook_inscription_sur_invitation('{"user":{"email":"paul@x.fr"}}');
\echo H04 inscription inconnu (attendu 403)
select public.hook_inscription_sur_invitation('{"user":{"email":"pirate@x.fr"}}')->'error'->>'http_code';
\echo H05 inscription sans email (attendu 403)
select public.hook_inscription_sur_invitation('{"user":{}}')->'error'->>'http_code';
reset role; set role authenticated;
\echo H06 authenticated appelle le crochet (attendu ERREUR permission)
select public.hook_inscription_sur_invitation('{"user":{"email":"x@x.fr"}}');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-0000000000b2',false);
\echo H07 autre compte avec le lien de Paul (attendu autre_email)
select public.accepter_invitation(:'tok');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-0000000000a1',false);
\echo H08 Paul accepte (attendu ok)
select public.accepter_invitation(:'tok');
reset role; set role supabase_auth_admin;
\echo H09 invitation utilisee : plus d inscription possible (attendu 403)
select public.hook_inscription_sur_invitation('{"user":{"email":"paul@x.fr"}}')->'error'->>'http_code';
