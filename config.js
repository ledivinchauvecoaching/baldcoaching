/* Configuration de la version hébergée (Netlify + Supabase).
   - supabaseUrl     : "Project URL" du projet Supabase
   - supabaseAnonKey : la clé publique ("Publishable key", sb_publishable_…)
   Cette clé est publique par conception : ce sont les règles RLS (supabase/schema.sql)
   qui protègent les données. Ne mets JAMAIS la clé secrète (sb_secret_… / service_role) ici. */
window.BALD_CONFIG = {
  supabaseUrl: "https://eeuyskeovxjviqslbpth.supabase.co",
  supabaseAnonKey: "sb_publishable_h5C-AqX7CDaqdN4N3014eA_wiGNgnGg"
};
