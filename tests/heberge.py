"""Test de la version hébergée (Netlify + Supabase simulé) : python3 tests/heberge.py"""
from playwright.sync_api import sync_playwright
import subprocess,os,shutil,time,json,sys
D='/tmp/claude-0/site';shutil.rmtree(D,ignore_errors=True);os.makedirs(D)
subprocess.run(['python3','/home/claude/tests/construire_site.py',D+'/index.html'],check=True)
open(D+'/config.js','w').write('window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock-anon"};')
MOCK=open('/home/claude/depot/tests/mock-supabase.js').read()
srv=subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U='http://127.0.0.1:8765/'
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
def login(pg,uid,mail):
    pg.evaluate(f"localStorage.setItem('mock-session',JSON.stringify({{user:{{id:'{uid}',email:'{mail}'}}}}))");pg.reload();pg.wait_for_timeout(700)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True);ctx.add_init_script(MOCK.replace('window.BALD_CONFIG=','window.__ignore='))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(U);pg.wait_for_timeout(700)
    ok("écran de connexion sans session",pg.is_visible('#login'))
    pg.screenshot(path='/home/claude/rendus/v39-connexion-mobile.png')
    pg.fill('#loginEmail','client@exemple.fr');pg.click('#loginSend');pg.wait_for_timeout(300)
    ok("lien magique demandé",'Lien envoyé' in pg.inner_text('#loginMsg') and pg.evaluate("localStorage.getItem('mock-last-otp')")=='"client@exemple.fr"')
    pg.click('#loginDemo');pg.wait_for_timeout(400)
    ok("mode découverte sans compte",pg.is_hidden('#login') and 'découverte' in pg.inner_text('#banner').lower())
    # utilisateur A
    pg.evaluate("sessionStorage.removeItem('bald-demo')");login(pg,'user-A','a@exemple.fr')
    ok("connecté : application ouverte",pg.is_hidden('#login'))
    ok("connecté : e-mail affiché",'a@exemple.fr' in pg.inner_text('#acct') or pg.is_visible('#logout'))
    ok("carnet vide au départ",pg.locator('#onb').is_visible())
    pg.evaluate("location.hash='#tracking'");pg.wait_for_timeout(200)
    pg.locator('#tTable .tcell[data-k="poids"]:not([disabled])').last.click();pg.fill('#tEditVal','81,4');pg.click('#tEditSave');pg.wait_for_timeout(300)
    pg.evaluate("location.hash='#seances'");pg.wait_for_timeout(300);pg.click('#horsProg');pg.fill('#sDuree','45');pg.fill('#sNotes','Séance de A');pg.click('#sessionForm button[type=submit]');pg.wait_for_timeout(400)
    pg.evaluate("location.hash='#accueil'");pg.wait_for_timeout(200);pg.click('#newGoalBox summary') if not pg.evaluate("document.querySelector('#newGoalBox').open") else None
    pg.fill('#gTitre','Objectif de A');pg.click('#goalForm .btn');pg.wait_for_timeout(300)
    n=len(pg.evaluate("JSON.parse(localStorage.getItem('mock-db')||'[]')"));ok("données écrites dans Supabase",n>=3,f"{n} lignes")
    pg.reload();pg.wait_for_timeout(800)
    ok("données retrouvées après rechargement",'Objectif de A' in pg.inner_text('#goals'))
    pg.evaluate("location.hash='#seances'");pg.wait_for_timeout(300);ok("séance retrouvée",'Séance de A' in pg.inner_text('#journal'))
    pg.evaluate("location.hash='#tracking'");pg.wait_for_timeout(300);ok("pesée retrouvée",'81,4' in pg.inner_text('#tTable'))
    # sauvegarde JSON
    pg.evaluate("location.hash='#bilan'");pg.wait_for_timeout(300);pg.click('#expBtn')
    with pg.expect_download() as dl:pg.click('#jsonExp')
    path='/tmp/claude-0/backup-A.json';dl.value.save_as(path);B=json.load(open(path))
    ok("sauvegarde JSON complète",B['format']=='bald-carnet' and len(B['seances'])==1 and len(B['objectifs'])==1 and any(v.get('poids')==81.4 for v in B['tracking'].values()),f"{len(B['seances'])} séance, {len(B['objectifs'])} objectif, {len(B['tracking'])} jour")
    # déconnexion
    pg.click('#logout');pg.wait_for_timeout(700);ok("déconnexion : retour à la connexion",pg.is_visible('#login'))
    # utilisateur B : cloisonnement puis import
    pg.evaluate("location.hash='#accueil'");login(pg,'user-B','b@exemple.fr')
    ok("B ne voit pas les données de A",'Objectif de A' not in pg.inner_text('#goals') and 'Séance de A' not in pg.inner_text('body'))
    pg.evaluate("location.hash='#bilan'");pg.wait_for_timeout(300);pg.click('#expBtn')
    pg.set_input_files('#jsonImp',path);pg.wait_for_timeout(300)
    ok("import : résumé avant confirmation",'1 séance' in pg.inner_text('#impBox'))
    pg.screenshot(path='/home/claude/rendus/v39-import-mobile.png')
    pg.click('#impGo');pg.wait_for_timeout(1200)
    ok("import terminé",'terminé' in pg.inner_text('#impProg'),pg.inner_text('#impProg'))
    pg.evaluate("location.hash='#accueil'");pg.reload();pg.wait_for_timeout(800)
    ok("données importées chez B",'Objectif de A' in pg.inner_text('#goals'))
    rows=pg.evaluate("JSON.parse(localStorage.getItem('mock-db'))");ok("lignes de B bien à B",all(r['user_id'] in ('user-A','user-B') for r in rows) and sum(r['user_id']=='user-B' for r in rows)>=3)
    pg.screenshot(path='/home/claude/rendus/v39-connecte-mobile.png')
    # fichier faux
    open('/tmp/claude-0/faux.json','w').write('{"bonjour":1}');pg.evaluate("location.hash='#bilan'");pg.wait_for_timeout(200);pg.click('#expBtn') if pg.is_hidden('#expPanel') else None
    pg.set_input_files('#jsonImp','/tmp/claude-0/faux.json');pg.wait_for_timeout(200);ok("fichier invalide refusé","pas une sauvegarde" in pg.inner_text('#impBox'))
    # lien des pas pointe vers le site
    pg.evaluate("location.hash='#tracking'");pg.wait_for_timeout(200);ok("lien des pas adapté au site",pg.inner_text('#stepUrl').startswith(U),pg.inner_text('#stepUrl'))
    d=b.new_page(viewport={'width':1280,'height':900});d.add_init_script(MOCK.replace('window.BALD_CONFIG=','window.__ignore='));d.goto(U);d.wait_for_timeout(600);d.screenshot(path='/home/claude/rendus/v39-connexion-bureau.png')
    b.close()
finally:
  srv.terminate()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",[e for e in errs if 'favicon' not in e and '404' not in e] or "aucune")
