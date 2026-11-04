"""Test des vidéos de démonstration : python3 tests/videos.py"""
from playwright.sync_api import sync_playwright
import subprocess,time,json,datetime,os
D='/tmp/claude-0/site';os.makedirs(D,exist_ok=True)
subprocess.run(['python3','/home/claude/tests/construire_site.py',D+'/index.html'],check=True)
open(D+'/config.js','w').write('window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock"};')
M=open('/home/claude/baldcoaching/tests/mock-supabase.js').read().replace('window.BALD_CONFIG=','window.__ignore=')
today=datetime.date.today().isoformat()
plan={"date":today,"type":"Musculation","titre":"TEST","createdAt":1,"exercices":[
  {"nom":"Hack squats","sets":[{"charge":None,"reps":10}],"video":"https://www.instagram.com/reel/abc/"},
  {"nom":"Leg extension (machine)","sets":[{"charge":None,"reps":12}],"video":"javascript:alert(document.domain)"}]}
db=[{"user_id":"u","collection":"prevues","doc_id":"p1","data":plan,"updated_at":"x"}]
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
srv=subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2)
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:(errs.append('DIALOG '+d.message),d.dismiss()))
    pg.add_init_script(M+";localStorage.setItem('bald-install',JSON.stringify({fait:true}));localStorage.setItem('mock-session',JSON.stringify({user:{id:'u',email:'a@b.fr',user_metadata:{}}}));if(!localStorage.getItem('mock-db'))localStorage.setItem('mock-db',"+json.dumps(json.dumps(db))+")")
    pg.goto('http://127.0.0.1:8765/#programme');pg.wait_for_timeout(1200)
    pg.locator('[data-ptog]').first.click();pg.wait_for_timeout(200)
    ok("programme : lien vidéo dans le détail",pg.locator('#plans .vdemo').count()==1)
    pg.goto('http://127.0.0.1:8765/#seances');pg.wait_for_timeout(900);(pg.locator('[data-sd]:visible').first.click() if pg.locator('[data-sd]:visible').count() else None);pg.wait_for_timeout(600)
    a=pg.locator('#exRows .vdemo')
    ok("séance : bouton « ▶ Voir la démo »",a.count()==1 and a.first.get_attribute('href').startswith('https://www.instagram.com/') and a.first.get_attribute('target')=='_blank')
    pg.locator('#exRows .g-cur').screenshot(path='/home/claude/rendus/v60-video-demo.png')
    ok("lien « javascript: » ignoré",pg.locator('a[href^="javascript"]').count()==0)
    b.close()
finally:srv.terminate()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",errs or "aucune")
