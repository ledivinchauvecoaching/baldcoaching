\set ON_ERROR_STOP 0
\pset tuples_only on
insert into auth.users values
 ('00000000-0000-0000-0000-00000000c0ac','coach@x.fr','{"full_name":"Jérémy Coach"}'),
 ('00000000-0000-0000-0000-0000000000a1','paul@x.fr','{"full_name":"Paul Client"}'),
 ('00000000-0000-0000-0000-0000000000b2','lea@x.fr','{"full_name":"Léa Cliente"}'),
 ('00000000-0000-0000-0000-0000000000e3','intrus@x.fr','{}');
insert into public.app_roles values ('00000000-0000-0000-0000-00000000c0ac','coach');
create or replace function pg_temp.as_user(u text) returns void language plpgsql as $$ begin perform set_config('request.jwt.claim.sub',u,false); end $$;
-- helpers
\set C '00000000-0000-0000-0000-00000000c0ac'
\set P '00000000-0000-0000-0000-0000000000a1'
\set L '00000000-0000-0000-0000-0000000000b2'
\set I '00000000-0000-0000-0000-0000000000e3'
set role authenticated;
-- intrus (non membre) : ne peut rien écrire
select pg_temp.as_user(:'I');
\echo T01 intrus statut (attendu aucun)
select public.mon_statut();
\echo T02 intrus insert (attendu ERREUR)
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'I','seances','s1','{}');
\echo T03 intrus cree invitation (attendu ERREUR)
select public.creer_invitation('x','x@x.fr');
\echo T04 intrus lit coaching direct (attendu ERREUR permission)
select * from public.coaching;
-- coach
select pg_temp.as_user(:'C');
\echo T05 coach statut (attendu coach)
select public.mon_statut();
\echo T06 coach ecrit chez lui (attendu INSERT 0 1)
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'C','reglages','tracking','{"modeles":[1]}');
select (public.creer_invitation('Paul','paul@x.fr')->>'token') as tok \gset
select (public.creer_invitation('Léa','lea@x.fr')->>'token') as tok2 \gset
\echo T07 coach liste invitations (attendu 2)
select count(*) from public.mes_invitations();
-- Paul accepte
select pg_temp.as_user(:'P');
\echo T08 Paul token bidon (attendu invalide)
select public.accepter_invitation('nimportequoi');
\echo T09 Paul accepte (attendu ok true)
select public.accepter_invitation(:'tok');
\echo T10 Paul statut client
select public.mon_statut()->>'role';
\echo T11 Paul ecrit chez lui (attendu INSERT 0 1)
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'P','seances','s1','{"notes":"Paul"}');
-- intrus reutilise token Paul
select pg_temp.as_user(:'I');
\echo T12 intrus reutilise le token de Paul (attendu invalide)
select public.accepter_invitation(:'tok');
-- Léa accepte
select pg_temp.as_user(:'L');
select public.accepter_invitation(:'tok2');
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'L','seances','s1','{"notes":"Lea"}');
\echo T13 Lea voit Paul ? (attendu 0)
select count(*) from public.carnet_docs where user_id=:'P';
\echo T14 Lea ecrit chez Paul (attendu ERREUR)
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'P','prevues','p9','{}');
\echo T15 Lea modifie Paul (attendu UPDATE 0)
update public.carnet_docs set data='{"pirate":1}' where user_id=:'P';
\echo T16 Lea liste clients (attendu 0)
select count(*) from public.mes_clients();
\echo T17 Lea lit les donnees du coach (attendu 0)
select count(*) from public.carnet_docs where user_id=:'C';
-- coach chez Paul
select pg_temp.as_user(:'C');
\echo T18 coach lit seances de Paul (attendu 1)
select count(*) from public.carnet_docs where user_id=:'P' and collection='seances';
\echo T19 coach programme chez Paul (attendu INSERT 0 1)
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'P','prevues','p1','{"titre":"UPPER"}');
\echo T20 coach commente chez Paul (attendu INSERT 0 1)
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'P','commentaires','s1','{"texte":"Bravo"}');
\echo T21 coach modifie seance de Paul (attendu UPDATE 0)
update public.carnet_docs set data='{"x":1}' where user_id=:'P' and collection='seances';
\echo T22 coach ecrit reglages de Paul (attendu ERREUR)
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'P','reglages','tracking','{}');
\echo T23 coach supprime seance de Paul (attendu DELETE 0)
delete from public.carnet_docs where user_id=:'P' and collection='seances';
\echo T24 coach liste clients (attendu 2)
select count(*) from public.mes_clients();
-- coach retire Paul
select public.changer_client(:'P',false);
\echo T25 coach ne lit plus Paul (attendu 0)
select count(*) from public.carnet_docs where user_id=:'P';
select pg_temp.as_user(:'P');
\echo T26 Paul suspendu statut
select public.mon_statut()->>'role';
\echo T27 Paul suspendu lit encore ses donnees (attendu 3)
select count(*) from public.carnet_docs where user_id=:'P';
\echo T28 Paul suspendu ecrit (attendu ERREUR)
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'P','seances','s2','{}');
\echo T29 Paul supprime commentaire coach chez lui (attendu DELETE 1)
delete from public.carnet_docs where user_id=:'P' and collection='commentaires';
\echo T30 Paul appelle changer_client pour se reactiver (attendu void, puis statut suspendu)
select public.changer_client(:'P',true);
select public.mon_statut()->>'role';
\echo T31 Paul se declare coach (attendu ERREUR)
insert into public.app_roles values (:'P','coach');
\echo T32 collection inconnue (attendu ERREUR)
reset role; set role authenticated; select pg_temp.as_user(:'L');
insert into public.carnet_docs(user_id,collection,doc_id,data) values (:'L','hack','x','{}');
-- anon
reset role; set role anon; select pg_temp.as_user('');
\echo T33 anon lit (attendu ERREUR)
select count(*) from public.carnet_docs;
\echo T34 anon mon_statut (attendu ERREUR)
select public.mon_statut();
