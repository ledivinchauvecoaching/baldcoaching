\pset tuples_only on
\set ON_ERROR_STOP 0
insert into auth.users values ('00000000-0000-0000-0000-0000000000a1','paul@x.fr','{}'),('00000000-0000-0000-0000-0000000000b2','lea@x.fr','{}');
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-0000000000a1',false);
\echo N01 Paul enregistre son appareil (attendu INSERT 0 1)
insert into public.abonnements_push(endpoint,p256dh,auth) values ('https://push.exemple/abc','k','a');
\echo N02 Paul enregistre un appareil au nom de Lea (attendu ERREUR)
insert into public.abonnements_push(endpoint,user_id,p256dh,auth) values ('https://push.exemple/x','00000000-0000-0000-0000-0000000000b2','k','a');
\echo N03 adresse non https (attendu ERREUR)
insert into public.abonnements_push(endpoint,p256dh,auth) values ('http://x','k','a');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-0000000000b2',false);
\echo N04 Lea voit les appareils de Paul (attendu 0)
select count(*) from public.abonnements_push;
\echo N05 Lea supprime l appareil de Paul (attendu DELETE 0)
delete from public.abonnements_push;
