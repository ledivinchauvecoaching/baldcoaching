\pset tuples_only on
\set ON_ERROR_STOP 0
insert into auth.users values ('00000000-0000-0000-0000-00000000c0ac','coach@x.fr','{}'),('00000000-0000-0000-0000-0000000000a1','paul@x.fr','{}'),('00000000-0000-0000-0000-0000000000b2','lea@x.fr','{}');
insert into public.app_roles values ('00000000-0000-0000-0000-00000000c0ac','coach');
insert into public.coaching(client_id,coach_id) values ('00000000-0000-0000-0000-0000000000a1','00000000-0000-0000-0000-00000000c0ac'),('00000000-0000-0000-0000-0000000000b2','00000000-0000-0000-0000-00000000c0ac');
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-0000000000a1',false);
\echo P01 Paul depose dans son dossier (attendu INSERT 0 1)
insert into storage.objects(bucket_id,name) values ('photos','00000000-0000-0000-0000-0000000000a1/2026-11-02-face.jpg');
\echo P02 Paul depose dans le dossier de Lea (attendu ERREUR)
insert into storage.objects(bucket_id,name) values ('photos','00000000-0000-0000-0000-0000000000b2/pirate.jpg');
\echo P03 Paul depose hors dossier (attendu ERREUR)
insert into storage.objects(bucket_id,name) values ('photos','racine.jpg');
\echo P04 Paul ecrit un bilan (attendu INSERT 0 1)
insert into public.carnet_docs(user_id,collection,doc_id,data) values ('00000000-0000-0000-0000-0000000000a1','bilans','2026-11-02','{"energie":4}');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-0000000000b2',false);
\echo P05 Lea voit les photos de Paul (attendu 0)
select count(*) from storage.objects where bucket_id='photos';
\echo P06 Lea lit le bilan de Paul (attendu 0)
select count(*) from public.carnet_docs where collection='bilans';
\echo P07 Lea supprime la photo de Paul (attendu DELETE 0)
delete from storage.objects;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-00000000c0ac',false);
\echo P08 coach voit la photo de Paul (attendu 1)
select count(*) from storage.objects where bucket_id='photos';
\echo P09 coach lit le bilan de Paul (attendu 1)
select count(*) from public.carnet_docs where collection='bilans';
\echo P10 coach supprime la photo de Paul (attendu DELETE 0)
delete from storage.objects;
\echo P11 coach modifie le bilan de Paul (attendu UPDATE 0)
update public.carnet_docs set data='{}' where collection='bilans';
