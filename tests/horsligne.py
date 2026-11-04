"""Test du mode hors-ligne : python3 tests/horsligne.py"""
from playwright.sync_api import sync_playwright
import subprocess,time,os,shutil,json
D='/tmp/claude-0/site';shutil.rmtree(D,ignore_errors=True);os.makedirs(D)
subprocess.run(['python3','/home/claude/tests/construire_site.py',D+'/index.html'],check=True)
for f in ['sw.js','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png','favicon.png']:shutil.copy('/home/claude/baldcoaching/'+f,D+'/'+f)
M=open('/home/claude/baldcoaching/tests/mock-supabase.js').read()
# le faux Supabase est servi comme fichier : il doit fonctionner hors connexion grâce au cache
open(D+'/config.js','w').write(M)
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
srv=subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U='http://localhost:8765/'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(viewport={'width':390,'height':844})
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U);pg.evaluate("localStorage.setItem('bald-install',JSON.stringify({fait:true}));localStorage.setItem('mock-session',JSON.stringify({user:{id:'u',email:'a@b.fr',user_metadata:{}}}))")
    pg.goto(U+'#nutrition');pg.reload();pg.wait_for_timeout(2500)
    ok("service worker actif",pg.evaluate("navigator.serviceWorker.controller!==null")or (pg.reload() or pg.wait_for_timeout(1500) or pg.evaluate("navigator.serviceWorker.controller!==null")))
    pg.click('#nAddBtn');pg.fill('#mP','30');pg.click('#mSave');pg.wait_for_timeout(500)
    ok("en ligne : repas envoyé",any(r['collection']=='tracking' for r in pg.evaluate("JSON.parse(localStorage.getItem('mock-db')||'[]')")))
    # coupure réseau
    ctx.set_offline(True);pg.evaluate("localStorage.setItem('mock-offline','1')");pg.wait_for_timeout(200)
    pg.click('#nAddBtn');pg.fill('#nNom','Collation hors ligne');pg.fill('#mP','25');pg.click('#mSave');pg.wait_for_timeout(500)
    ok("hors ligne : saisie gardée et affichée",'Collation hors ligne' in pg.inner_text('#nDay'))
    ok("hors ligne : bandeau « en attente »",pg.is_visible('#netBar') and 'attente' in pg.inner_text('#netBar'),pg.inner_text('#netBar'))
    pg.screenshot(path='/home/claude/rendus/v58-hors-ligne.png')
    q=pg.evaluate("JSON.parse(localStorage.getItem('bald-file-u')||'[]').length");ok("file d'attente",q==1,str(q))
    pg.reload();pg.wait_for_timeout(2500)
    ok("hors ligne : l'appli se rouvre (rechargement)",pg.is_visible('#view-nutrition') and pg.is_hidden('#login'))
    ok("hors ligne : données retrouvées après rechargement",'Collation hors ligne' in pg.inner_text('#nDay'),pg.inner_text('#nDay')[:80].replace('\n',' '))
    # retour du réseau
    pg.evaluate("localStorage.removeItem('mock-offline')");ctx.set_offline(False);pg.wait_for_timeout(2500)
    db=pg.evaluate("JSON.parse(localStorage.getItem('mock-db')||'[]')")
    ok("retour réseau : saisie envoyée",any('Collation hors ligne' in json.dumps(r['data']) for r in db))
    ok("retour réseau : file vide, bandeau masqué",pg.evaluate("JSON.parse(localStorage.getItem('bald-file-u')||'[]').length")==0 and pg.is_hidden('#netBar'))
    b.close()
finally:srv.terminate()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",[e for e in errs if 'Failed to fetch' not in e] or "aucune")
