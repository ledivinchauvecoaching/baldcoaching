"""Test de l'espace coach (faux Supabase en mode coach) : python3 tests/coach.py"""
from playwright.sync_api import sync_playwright
import subprocess,time,json,os,shutil,datetime
D='/tmp/claude-0/site';shutil.rmtree(D,ignore_errors=True);os.makedirs(D)
subprocess.run(['python3','/home/claude/tests/construire_site.py',D+'/index.html'],check=True)
open(D+'/config.js','w').write('window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock"};')
M=open('/home/claude/baldcoaching/tests/mock-supabase.js').read().replace('window.BALD_CONFIG=','window.__ignore=')
mods=json.load(open('/tmp/claude-0/modeles.json'))
COACH={"id":"coach","email":"jeremy@x.fr","user_metadata":{"given_name":"Jérémy"}}
PAUL={"id":"paul","email":"paul@x.fr","user_metadata":{"full_name":"Paul Martin","given_name":"Paul"}}
LEA={"id":"lea","email":"lea@x.fr","user_metadata":{"full_name":"Léa Dubois"}}
INTRUS={"id":"intrus","email":"intrus@x.fr","user_metadata":{}}
today=datetime.date.today().isoformat()
seed=[{"user_id":"coach","collection":"reglages","doc_id":"tracking","data":{"cibles":{"pas":10000},"habitudes":[],"modeles":mods},"updated_at":"x"}]
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
srv=subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U='http://127.0.0.1:8765/'
def as_user(pg,u,path=''):
    pg.evaluate("u=>localStorage.setItem('mock-session',JSON.stringify({user:u}))",u);pg.goto(U+path);pg.reload();pg.wait_for_timeout(900)
db=lambda pg:pg.evaluate("JSON.parse(localStorage.getItem('mock-db')||'[]')")
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)
    ctx.add_init_script(M);pg=ctx.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U);pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mock-roles',JSON.stringify(['coach']));localStorage.setItem('mock-db',s)}",json.dumps(seed))
    # intrus sans invitation
    as_user(pg,INTRUS)
    ok("sans invitation : écran « réservé aux clients »",pg.is_visible('#reserve') and 'réservée aux clients' in pg.inner_text('#reserveTxt'))
    pg.screenshot(path='/home/claude/rendus/v50-reserve.png')
    # coach
    as_user(pg,COACH,'#clients')
    ok("coach : page Mes clients",pg.is_visible('#view-clients') and 'MES CLIENTS' in pg.inner_text('#pageTitle').upper())
    pg.click('#acctBtn');pg.wait_for_timeout(150);ok("coach : « Mes clients » dans le menu du compte",pg.is_visible('#acctClients'));pg.click('#acctBtn')
    pg.fill('#invNote','Paul');pg.click('#invGo');pg.wait_for_timeout(500)
    link=pg.inner_text('#invNew code');ok("lien d'invitation créé",'?invite=' in link,link[-30:])
    pg.screenshot(path='/home/claude/rendus/v50-clients-invitation.png',full_page=True)
    ok("invitation en attente listée",'Paul' in pg.inner_text('#invList'))
    pg.fill('#invNote','Léa');pg.click('#invGo');pg.wait_for_timeout(500);linkL=pg.inner_text('#invNew code')
    # Paul : ouvre le lien sans être connecté
    pg.evaluate("localStorage.removeItem('mock-session')");pg.goto(link);pg.wait_for_timeout(800)
    ok("lien ouvert : invitation mémorisée, adresse nettoyée",pg.evaluate("localStorage.getItem('bald-invite')") and 'invite=' not in pg.url)
    ok("écran de connexion « tu es invité(e) »",pg.is_visible('#login') and 'invité' in pg.inner_text('#loginIntro'))
    pg.screenshot(path='/home/claude/rendus/v50-connexion-invite.png')
    as_user(pg,PAUL)
    ok("Paul connecté : accès au carnet",pg.is_hidden('#reserve') and pg.is_hidden('#login'))
    ok("invitation consommée",pg.evaluate("localStorage.getItem('bald-invite')") is None)
    pg.click('#acctBtn');pg.wait_for_timeout(150);ok("Paul : « Suivi par @bald.coaching »",pg.is_visible('#acctCoach'));pg.click('#acctBtn')
    # Paul enregistre une séance
    pg.evaluate("location.hash='#seances'");pg.wait_for_timeout(400);pg.click('#horsProg');pg.fill('#sDuree','50');pg.fill('#sNotes','Séance de Paul');pg.click('#sessionForm button[type=submit]');pg.wait_for_timeout(500)
    sid=[r for r in db(pg) if r['user_id']=='paul' and r['collection']=='seances'][0]['doc_id']
    # intrus réutilise le lien de Paul
    pg.evaluate("localStorage.removeItem('mock-session')");pg.goto(link);pg.wait_for_timeout(500);pg.evaluate("u=>localStorage.setItem('mock-session',JSON.stringify({user:u}))",INTRUS);pg.reload();pg.wait_for_timeout(900)
    ok("lien de Paul réutilisé par un autre : refusé",pg.is_visible('#reserve') and "n'est plus valable" in pg.inner_text('#reserveMsg'))
    # Léa rejoint et ne voit rien de Paul
    pg.evaluate("localStorage.removeItem('mock-session')");pg.goto(linkL);pg.wait_for_timeout(500);as_user(pg,LEA,'#seances')
    ok("Léa ne voit pas la séance de Paul",'Séance de Paul' not in pg.inner_text('body'))
    ok("Léa n'a pas accès à Mes clients",(as_user(pg,LEA,'#clients') or True) and pg.is_hidden('#view-clients'))
    r=pg.evaluate("async()=>{const sb=supabase.createClient();const a=await sb.from('carnet_docs').upsert({user_id:'paul',collection:'prevues',doc_id:'pirate',data:{titre:'pirate'}});const b=await sb.from('carnet_docs').select('doc_id,data').eq('user_id','paul');return [a.error&&a.error.message,b.data.length]}")
    ok("Léa ne peut ni écrire ni lire chez Paul (attaque directe)",r[0] and r[1]==0,str(r))
    # coach ouvre le carnet de Paul
    as_user(pg,COACH,'#clients');pg.wait_for_timeout(300)
    ok("coach voit 2 clients",pg.locator('#clList .clcard').count()==2)
    pg.locator('[data-cl-open]').first.click();pg.wait_for_timeout(900)
    ok("vue coach : bandeau « Carnet de Paul »",pg.is_visible('#coachBar') and 'Paul' in pg.inner_text('#coachBar'),pg.inner_text('#coachBar'))
    pg.evaluate("location.hash='#seances'");pg.wait_for_timeout(500)
    ok("vue coach : séance de Paul visible",'Séance de Paul' in pg.inner_text('#journal'))
    ok("vue coach : saisie de séance masquée",pg.is_hidden('#horsProg'))
    pg.click(f'[data-com-add="{sid}"]');pg.wait_for_timeout(200);pg.fill('#journal .ccom textarea','Belle séance, monte de 2,5 kg la prochaine fois !');pg.click('#journal .ccom .btn');pg.wait_for_timeout(500)
    ok("commentaire enregistré chez Paul",any(r['user_id']=='paul' and r['collection']=='commentaires' for r in db(pg)))
    pg.locator('#journal .entry').first.scroll_into_view_if_needed();pg.screenshot(path='/home/claude/rendus/v50-vue-coach-journal.png')
    # programmer depuis les modèles du coach
    pg.evaluate("location.hash='#programme'");pg.wait_for_timeout(500);pg.click('#planFormTitle');pg.wait_for_timeout(200)
    opts=pg.evaluate("[...document.querySelectorAll('#tplSel option')].map(o=>o.text)")
    ok("modèles du coach proposés",any('UPPER' in o for o in opts),str(len(opts)))
    pg.select_option('#tplSel',label='UPPER · 9 exercices');pg.wait_for_timeout(300);pg.fill('#pDate',today);pg.click('#planForm button[type=submit]');pg.wait_for_timeout(600)
    pp=[r for r in db(pg) if r['user_id']=='paul' and r['collection']=='prevues']
    ok("séance programmée dans le carnet de Paul",len(pp)==1 and pp[0]['data'].get('coach') and pp[0]['data'].get('titre')=='UPPER')
    pg.screenshot(path='/home/claude/rendus/v50-vue-coach-programme.png')
    # écriture interdite : tracking de Paul
    n0=len(db(pg));pg.evaluate("location.hash='#tracking'");pg.wait_for_timeout(300)
    r=pg.evaluate("async()=>{const sb=supabase.createClient();const a=await sb.from('carnet_docs').upsert({user_id:'paul',collection:'seances',doc_id:'faux',data:{}});return a.error&&a.error.message}")
    ok("coach ne peut pas modifier les séances de Paul",bool(r))
    pg.click('#coachBack');pg.wait_for_timeout(800)
    ok("retour au carnet du coach",pg.is_hidden('#coachBar') and 'Séance de Paul' not in pg.inner_text('body'))
    # Paul voit le commentaire et la séance programmée
    as_user(pg,PAUL,'#seances');pg.wait_for_timeout(300)
    ok("Paul voit le commentaire du coach",'monte de 2,5 kg' in pg.inner_text('#journal'))
    ok("Paul a la séance UPPER du coach aujourd'hui",'UPPER' in pg.inner_text('body'))
    pg.evaluate("location.hash='#programme'");pg.wait_for_timeout(400);ok("Programme : étiquette « Par ton coach »",'PAR TON COACH' in pg.inner_text('#view-programme').upper())
    pg.locator('.tag-coach').first.scroll_into_view_if_needed();pg.screenshot(path='/home/claude/rendus/v50-client-programme.png')
    pg.evaluate("location.hash='#seances'");pg.wait_for_timeout(400)
    pg.locator('#journal .ccom').first.scroll_into_view_if_needed();pg.screenshot(path='/home/claude/rendus/v50-client-commentaire.png')
    # coach met Paul en pause
    as_user(pg,COACH,'#clients');pg.wait_for_timeout(300);bt=pg.locator('[data-cl-off]').first;bt.click();pg.wait_for_timeout(150);bt.click();pg.wait_for_timeout(500)
    as_user(pg,PAUL)
    ok("Paul en pause : écran dédié + lecture seule possible",pg.is_visible('#reserve') and pg.is_visible('#reserveRead'))
    pg.click('#reserveRead');pg.wait_for_timeout(800);pg.evaluate("location.hash='#seances'");pg.wait_for_timeout(300)
    ok("Paul en pause garde l'accès à ses données",'Séance de Paul' in pg.inner_text('#journal'))
    b.close()
finally:srv.terminate()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",errs or "aucune")
