# Carnet d'entraînement @bald.coaching

Application de suivi (séances, programme, tracking, nutrition, bilan) : une seule page `index.html`, hébergée sur **Netlify**, données dans **Supabase**.

## Mise en place (une seule fois)

1. **Supabase** : crée un projet, ouvre *SQL Editor*, colle le contenu de `supabase/schema.sql` et exécute.
   - *Authentication › Providers* : active **Email** (lien magique) et, si souhaité, **Google**.
   - *Authentication › URL Configuration* : mets l'adresse Netlify du site dans *Site URL* et *Redirect URLs*.
2. **config.js** : renseigne `supabaseUrl` et `supabaseAnonKey` (*Project Settings › API*).
   La clé *anon* est publique par conception : la sécurité vient des règles RLS du fichier SQL.
   **Ne mets jamais la clé `service_role` dans ce dépôt.**
3. **Netlify** : *Add new site › Import from GitHub*, choisis ce dépôt. Aucun build : le dossier publié est la racine (voir `netlify.toml`).

## Espace coach (migration n°2)

1. Supabase › SQL Editor : colle `supabase/02_espace_coach.sql`, remplace `TON_EMAIL_ICI` par l'adresse de ton compte (celle affichée dans le menu du compte de l'appli), puis **Run**. La dernière requête doit afficher ton e-mail avec le rôle `coach`.
2. Dans l'appli : menu du compte › **Mes clients** › « Créer le lien », puis envoie le lien en DM.
3. Règles : l'appli est réservée au coach et à ses clients ; le coach lit tout le carnet d'un client actif et n'écrit que ses séances prévues et des commentaires ; un client ne voit jamais un autre client ; un client « en pause » garde l'accès en lecture à ses données.

4. **Inscription sur invitation** : colle `supabase/03_inscription_sur_invitation.sql` et **Run**, puis *Authentication › Auth Hooks › Before User Created* : type **Postgres**, schéma `public`, fonction `hook_inscription_sur_invitation`. Un nouveau compte (Google ou lien e-mail) n'est alors créé que si son adresse a une invitation en cours ; le lien d'invitation ne fonctionne que pour cette adresse.

Tant que ce script n'est pas exécuté, l'appli fonctionne comme avant (chacun son carnet, sans espace coach).

## Développement

- Chaque modification passe par une branche → Netlify crée une *deploy preview* → validation → fusion dans `main` → mise en ligne.
- Tests (Python + Playwright) :
  - `python3 tests/coach.py` : espace coach (invitation, accès réservé, vue coach, programmation, commentaires, cloisonnement) ;
  - `tests/sql/` : règles de sécurité testées sur un vrai PostgreSQL (`supabase_min.sql` imite Supabase, puis `test_rls.sql` tente 34 contournements) ;
  - `python3 tests/heberge.py` : version hébergée avec un faux Supabase (connexion, cloisonnement entre comptes, sauvegarde/import) ;
  - `python3 tests/regression.py` : parcours fonctionnels ;
  - `python3 tests/securite.py` : injections, export CSV, liens piégés ;
  - `python3 tests/snapshots.py` puis `tests/compare.py` : comparaison visuelle avant/après.

## Sécurité

- Table unique `carnet_docs`, RLS activé et forcé : chaque compte ne lit et n'écrit que ses lignes.
- Le temps réel n'écoute que les insertions et mises à jour (les suppressions Supabase ne sont pas filtrées par RLS).
- En-têtes de sécurité (CSP, anti-iframe, HSTS…) dans `netlify.toml` ; `/tests` et `/supabase` ne sont pas servis.
- Sauvegarde : *Bilan › Exporter mes données › Exporter tout mon carnet (JSON)*.
