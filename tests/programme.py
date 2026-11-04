"""Test de l'onglet Programme (fiches résumées, détail, semaine type) : python3 tests/programme.py"""
from playwright.sync_api import sync_playwright
import subprocess,time,json,datetime,os,shutil
D='/tmp/claude-0/site';os.makedirs(D,exist_ok=True)
subprocess.run(['python3','/home/claude/tests/construire_site.py',D+'/index.html'],check=True)
open(D+'/config.js','w').write('window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock"};')
M=open('/home/claude/baldcoaching/tests/mock-supabase.js').read().replace('window.BALD_CONFIG=','window.__ignore=')
mods=json.load(open('/home/claude/baldcoaching/tests/modeles-exemple.json'));up=mods[4]
today=datetime.date.today().isoformat()
plan={"date":today,"type":"Musculation","titre":"UPPER","notes":"","createdAt":1,"exercices":[{**e,"ref":[]} for e in up['exercices']]}
past={"date":(datetime.date.today()-datetime.timedelta(days=7)).isoformat(),"type":"Musculation","duree":60,"rpe":7,"notes":"","createdAt":1,"exercices":[{"nom":e['nom'],"sets":[{"charge":20+i*2,"reps":10} for i in range(len(e['sets']))],"repos":e['repos']} for e in up['exercices']]}
db=[{"user_id":"u","collection":"prevues","doc_id":"p1","data":plan,"updated_at":"x"},{"user_id":"u","collection":"seances","doc_id":"s0","data":past,"updated_at":"x"},
    {"user_id":"u","collection":"reglages","doc_id":"tracking","data":{"cibles":{"pas":10000},"habitudes":[],"modeles":mods,"semaine":{"1":"mx1","2":"mx2","4":"mx3","5":"mx4"},"semaineDepuis":"2026-11-01"},"updated_at":"x"}]
srv=subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(M+";localStorage.setItem('bald-install',JSON.stringify({fait:true}));localStorage.setItem('mock-session',JSON.stringify({user:{id:'u',email:'a@b.fr',user_metadata:{given_name:'Alex'}}}));localStorage.setItem('mock-db',"+json.dumps(json.dumps(db))+")")
    pg.goto('http://127.0.0.1:8765/#programme');pg.wait_for_timeout(1300)
    ok("semaine type en clair",'QUADS MOLLETS' in pg.inner_text('#wkSum') and 'Repos' in pg.inner_text('#wkSum'))
    ok("séances groupées par semaine",pg.locator('#plans .p-week').count()>=2)
    ok("fiches résumées (pas de tableau par défaut)",pg.locator('#plans .ptable').count()==0 and pg.locator('#plans .p-sum').count()>=3)
    n0=pg.locator('#plans .plan').count()
    ok("7 prochains jours puis « Voir la suite »",pg.locator('#plMore').count()==1,f"{n0} fiches")
    pg.locator('[data-ptog]').first.click();pg.wait_for_timeout(300)
    ok("détail exercice par exercice à la demande",pg.locator('#plans .plan').first.locator('.ptable').count()==1 and pg.locator('#plans .plan').first.locator('td[data-l="Repère"]').count()>=5)
    pg.locator('#plans .plan').first.screenshot(path='/home/claude/rendus/v57-prog-detail.png')
    pg.click('#plMore');pg.wait_for_timeout(300);ok("« Voir la suite » affiche tout",pg.locator('#plans .plan').count()>n0)
    ok("bouton « Faire » seulement le jour même",pg.locator('#plans .plan').first.locator('[data-start]').count()==1 and pg.locator('#plans .plan').nth(1).locator('[data-start]').count()==0)
    b.close()
finally:srv.terminate()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",errs or "aucune")
