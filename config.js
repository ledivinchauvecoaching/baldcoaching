/* Configuration de la version hébergée (Netlify + Supabase).
   Remplis ces deux valeurs depuis Supabase > Project Settings > API.
   - supabaseUrl     : "Project URL", par ex. https://abcdefgh.supabase.co
   - supabaseAnonKey : la clé "anon public"
   La clé anon est publique par conception : ce sont les règles RLS (supabase/schema.sql)
   qui protègent les données. Ne mets JAMAIS la clé "service_role" ici. */
window.BALD_CONFIG = {
  supabaseUrl: "",
  supabaseAnonKey: ""
};
