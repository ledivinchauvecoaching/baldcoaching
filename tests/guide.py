"""Test du mode guidé en séance : python3 tests/guide.py"""
from playwright.sync_api import sync_playwright
import subprocess,time,json,datetime,os,shutil
D='/tmp/claude-0/site';shutil.rmtree(D,ignore_errors=True);os.makedirs(D)
subprocess.run(['python3','/home/claude/tests/construire_site.py',D+'/index.html'],check=True)
open(D+'/config.js','w').write('window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock"};')
M=open('/home/claude/depot/tests/mock-supabase.js').read().replace('window.BALD_CONFIG=','window.__ignore=')
mods=json.load(open('/tmp/claude-0/modeles.json'));up=[m for m in mods if m['nom']=='UPPER'][0]
today=datetime.date.today().isoformat()
plan={"date":today,"type":"Musculation","titre":"UPPER","notes":"","createdAt":1,"exercices":[{**e,"ref":[]} for e in up['exercices']]}
db=[{"user_id":"u","collection":"prevues","doc_id":"p1","data":plan,"updated_at":"x"}]
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
srv=subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
vis=lambda pg:pg.evaluate("[...document.querySelectorAll('#exRows>.exrow')].map(r=>r.className.match(/g-\\w+/)?.[0]||'-')")
rows=lambda pg:[r for r in pg.evaluate("JSON.parse(localStorage.getItem('mock-db'))") if r['collection']=='seances']
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2)
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(M+";if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');localStorage.setItem('mock-session',JSON.stringify({user:{id:'u',email:'a@b.fr'}}));localStorage.setItem('mock-db',"+json.dumps(json.dumps(db))+")}")
    pg.goto('http://127.0.0.1:8765/#seances');pg.wait_for_timeout(1000)
    pg.get_by_text('Commencer la séance').first.click();pg.wait_for_timeout(600)
    v=vis(pg);ok("1 exercice en cours + le suivant, le reste masqué",v[:2]==['g-cur','g-cur'] or (v[0]=='g-cur' and v[1]=='g-next'),str(v))
    ok("compteur affiché",'Exercice 1' in pg.inner_text('#guideTxt'),pg.inner_text('#guideTxt'))
    pg.locator('#exRows .g-cur').first.scroll_into_view_if_needed();pg.screenshot(path='/home/claude/rendus/v45-guide-1.png')
    # ex 1
    for i,inp in enumerate(pg.locator('#exRows .g-cur .sc').all()):inp.fill(str(10+i))
    pg.click('#exRows .g-val');pg.wait_for_timeout(500)
    R=rows(pg);ok("exercice validé = enregistré dans la séance",len(R)==1 and R[0]['data'].get('enCours') and len(R[0]['data']['exercices'])==1,str(len(R)))
    v=vis(pg);ok("passage au suivant",v[0]=='g-done' and v[1]=='g-cur',str(v))
    # ex2 then superset block (ex3+ex4)
    pg.click('#exRows .g-val');pg.wait_for_timeout(400)
    v=vis(pg);ok("superset affiché en bloc",v[2:4]==['g-cur','g-cur'] and 'superset' in pg.inner_text('#guideTxt'),str(v))
    ok("bouton « Valider le superset »",'superset' in pg.inner_text('#exRows .g-val').lower())
    pg.screenshot(path='/home/claude/rendus/v45-guide-superset.png')
    pg.reload();pg.wait_for_timeout(1000)
    if pg.locator('#drResume').count():pg.click('#drResume');pg.wait_for_timeout(500)
    v=vis(pg);ok("reprise après rechargement",v[:2]==['g-done','g-done'] and v[2]=='g-cur',str(v))
    pg.click('#exRows .g-sum >> nth=0');pg.wait_for_timeout(300);v=vis(pg);ok("« Modifier » rouvre un exercice validé",v[0]=='g-cur',str(v))
    pg.click('#exRows .g-val');pg.wait_for_timeout(300)
    n=0
    while pg.locator('#exRows .g-val').count() and n<10:pg.click('#exRows .g-val');pg.wait_for_timeout(300);n+=1
    ok("fin : tous validés",'Tous les exercices' in pg.inner_text('#guideTxt'))
    ok("durée remplie automatiquement",pg.input_value('#sDuree')!="",pg.input_value('#sDuree'))
    pg.screenshot(path='/home/claude/rendus/v45-guide-fin.png')
    pg.click('#sessionForm button[type=submit]');pg.wait_for_timeout(800)
    R=rows(pg);ok("une seule séance finale, plus « en cours »",len(R)==1 and not R[0]['data'].get('enCours') and len(R[0]['data']['exercices'])==9,f"{len(R)} séance(s)")
    ok("séance retirée du programme",not any(r['collection']=='prevues' for r in pg.evaluate("JSON.parse(localStorage.getItem('mock-db'))")))
    # annulation : supprime la séance en cours
    b.close()
finally:srv.terminate()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",errs or "aucune")
