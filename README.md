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

## Développement

- Chaque modification passe par une branche → Netlify crée une *deploy preview* → validation → fusion dans `main` → mise en ligne.
- Tests (Python + Playwright) :
  - `python3 tests/heberge.py` : version hébergée avec un faux Supabase (connexion, cloisonnement entre comptes, sauvegarde/import) ;
  - `python3 tests/regression.py` : parcours fonctionnels ;
  - `python3 tests/securite.py` : injections, export CSV, liens piégés ;
  - `python3 tests/snapshots.py` puis `tests/compare.py` : comparaison visuelle avant/après.

## Sécurité

- Table unique `carnet_docs`, RLS activé et forcé : chaque compte ne lit et n'écrit que ses lignes.
- Le temps réel n'écoute que les insertions et mises à jour (les suppressions Supabase ne sont pas filtrées par RLS).
- En-têtes de sécurité (CSP, anti-iframe, HSTS…) dans `netlify.toml` ; `/tests` et `/supabase` ne sont pas servis.
- Sauvegarde : *Bilan › Exporter mes données › Exporter tout mon carnet (JSON)*.
