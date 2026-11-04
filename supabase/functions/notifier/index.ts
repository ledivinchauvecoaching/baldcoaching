// Fonction Supabase « notifier » : envoie une notification push quand
//  - le coach commente une séance, programme une séance ou fixe des objectifs (→ le client) ;
//  - un client envoie son bilan de la semaine (→ son coach).
// Appelée par un « Database Webhook » sur la table carnet_docs (INSERT et UPDATE).
// Secrets à définir (Edge Functions › Secrets) : VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY.
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
webpush.setVapidDetails("https://baldcoachingapp.netlify.app", Deno.env.get("VAPID_PUBLIC_KEY")!, Deno.env.get("VAPID_PRIVATE_KEY")!);

async function envoyer(userId: string, msg: { title: string; body: string; url: string; tag: string }) {
  const { data: subs } = await sb.from("abonnements_push").select("endpoint,p256dh,auth").eq("user_id", userId);
  for (const s of subs ?? []) {
    try {
      await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify(msg), { TTL: 86400 });
    } catch (e) {
      const code = (e as { statusCode?: number }).statusCode;
      if (code === 404 || code === 410) await sb.from("abonnements_push").delete().eq("endpoint", s.endpoint);
    }
  }
}

Deno.serve(async (req) => {
  let p: any; try { p = await req.json(); } catch { return new Response("ignoré", { status: 200 }); }
  const r = p?.record; if (!r || p.table !== "carnet_docs") return new Response("ignoré");
  const old = p.old_record;
  const col = r.collection, doc = r.doc_id, data = r.data ?? {};
  let cible: string | null = null, msg: any = null;
  if (col === "commentaires" && JSON.stringify(old?.data) !== JSON.stringify(data)) {
    cible = r.user_id; msg = { title: "💬 Ton coach a commenté ta séance", body: String(data.texte ?? "").slice(0, 140), url: "/#seances", tag: "commentaire" };
  } else if (col === "prevues" && data.coach && p.type === "INSERT") {
    cible = r.user_id; msg = { title: "📅 Nouvelle séance programmée", body: `${data.titre ?? data.type ?? "Séance"} · ${data.date ?? ""}`, url: "/#programme", tag: "programme" };
  } else if (col === "reglages" && doc === "coach") {
    cible = r.user_id; msg = { title: "🎯 Nouveaux objectifs nutrition", body: data?.cibles?.kcal ? `${data.cibles.kcal} kcal par jour` : "Ton coach a mis à jour tes objectifs", url: "/#nutrition", tag: "objectifs" };
  } else if (col === "bilans" && p.type === "INSERT") {
    const { data: lien } = await sb.from("coaching").select("coach_id,client_nom,client_email").eq("client_id", r.user_id).eq("actif", true).maybeSingle();
    if (lien) { cible = lien.coach_id; msg = { title: "📝 Bilan de la semaine reçu", body: `${lien.client_nom ?? lien.client_email ?? "Un client"} a envoyé son bilan`, url: "/#clients", tag: "bilan-" + r.user_id }; }
  }
  if (cible && msg) await envoyer(cible, msg);
  return new Response("ok");
});
