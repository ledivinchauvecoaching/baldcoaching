"""Test du message « Installe l'appli » : python3 tests/installer.py"""
from playwright.sync_api import sync_playwright
import subprocess,time,os,shutil
D='/tmp/claude-0/site';os.makedirs(D,exist_ok=True)
subprocess.run(['python3','/home/claude/tests/construire_site.py',D+'/index.html'],check=True)
shutil.copy('/home/claude/baldcoaching/icon-192.png',D+'/icon-192.png')
open(D+'/config.js','w').write('window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock"};')
M=open('/home/claude/baldcoaching/tests/mock-supabase.js').read().replace('window.BALD_CONFIG=','window.__ignore=')
LOG=";localStorage.setItem('mock-session',JSON.stringify({user:{id:'u',email:'a@b.fr',user_metadata:{given_name:'Alex'}}}))"
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
srv=subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U='http://127.0.0.1:8765/'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    for name,dev in [('iphone',p.devices['iPhone 13']),('android',p.devices['Pixel 7'])]:
      ctx=b.new_context(**dev);ctx.add_init_script(M+LOG);pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.goto(U);pg.wait_for_timeout(2400)
      ok(f"{name} : message affiché au premier accès",pg.is_visible('#instBg'))
      t=pg.inner_text('#instBody')
      ok(f"{name} : bonnes instructions",("Sur l'écran d'accueil" in t) if name=='iphone' else ("Installer l'application" in t),t[:70].replace('\n',' '))
      pg.screenshot(path=f'/home/claude/rendus/v55-installer-{name}.png')
      pg.click('#instLater');pg.wait_for_timeout(200);ok(f"{name} : « Plus tard » ferme",pg.is_hidden('#instBg'))
      pg.reload();pg.wait_for_timeout(2400);ok(f"{name} : pas réaffiché tout de suite",pg.is_hidden('#instBg'))
      pg.click('#acctBtn');pg.wait_for_timeout(150);pg.click('#acctInstall');pg.wait_for_timeout(300)
      ok(f"{name} : rouvrable depuis le menu du compte",pg.is_visible('#instBg'))
      pg.click('#instDone');ctx.close()
    ctx=b.new_context(viewport={'width':1280,'height':800});ctx.add_init_script(M+LOG);pg=ctx.new_page();pg.goto(U);pg.wait_for_timeout(2400)
    ok("ordinateur : pas de message automatique",pg.is_hidden('#instBg'));ctx.close()
    ctx=b.new_context(**p.devices['iPhone 13']);ctx.add_init_script(M+";sessionStorage.setItem('bald-demo','1')");pg=ctx.new_page();pg.goto(U);pg.wait_for_timeout(2400)
    ok("sans compte (découverte) : pas de message",pg.is_hidden('#instBg'));ctx.close()
    b.close()
finally:srv.terminate()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",errs or "aucune")
