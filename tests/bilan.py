"""Test du bilan hebdomadaire avec photos : python3 tests/bilan.py"""
from playwright.sync_api import sync_playwright
import subprocess,time,json,os,shutil
D='/tmp/claude-0/site';os.makedirs(D,exist_ok=True)
subprocess.run(['python3','/home/claude/tests/construire_site.py',D+'/index.html'],check=True)
open(D+'/config.js','w').write('window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock"};')
M=open('/home/claude/baldcoaching/tests/mock-supabase.js').read().replace('window.BALD_CONFIG=','window.__ignore=')
PHOTO='/tmp/claude-0/photo-test.jpg'
COACH={"id":"coach","email":"j@x.fr","user_metadata":{"given_name":"Jérémy"}};PAUL={"id":"paul","email":"paul@x.fr","user_metadata":{"full_name":"Paul Martin"}};LEA={"id":"lea","email":"lea@x.fr","user_metadata":{}}
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
srv=subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'],cwd=D,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U='http://127.0.0.1:8765/'
def as_user(pg,u,path=''):pg.evaluate("u=>localStorage.setItem('mock-session',JSON.stringify({user:u}))",u);pg.goto(U+path);pg.reload();pg.wait_for_timeout(1000)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2);ctx.add_init_script(M)
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U);pg.evaluate("()=>{localStorage.clear();localStorage.setItem('bald-install',JSON.stringify({fait:true}));localStorage.setItem('mock-roles',JSON.stringify(['coach']));localStorage.setItem('mock-coaching',JSON.stringify([{client_id:'paul',coach_id:'coach',client_email:'paul@x.fr',client_nom:'Paul Martin',depuis:new Date().toISOString(),actif:true},{client_id:'lea',coach_id:'coach',client_email:'lea@x.fr',client_nom:'Léa',depuis:new Date().toISOString(),actif:true}]))}")
    as_user(pg,PAUL,'#tracking')
    if pg.evaluate("document.querySelector('#bilPanel').classList.contains('collapsed')"):pg.click('#bilPanel > h2')
    ok("Paul : formulaire de bilan",pg.is_visible('#bilForm'))
    pg.fill('#bilPoids','80,4');pg.click('[data-bk="energie"][data-bv="4"]');pg.click('[data-bk="sommeil"][data-bv="3"]');pg.click('[data-bk="faim"][data-bv="2"]');pg.click('[data-bk="stress"][data-bv="2"]');pg.click('[data-bk="motivation"][data-bv="5"]')
    pg.fill('#bilTxt','4 séances faites, genou OK.');pg.set_input_files('[data-ph="face"]',PHOTO);pg.wait_for_timeout(800)
    pg.locator('#bilPanel').screenshot(path='/home/claude/rendus/v62-bilan-formulaire.png')
    pg.click('#bilSend');pg.wait_for_timeout(1500)
    rows=[r for r in pg.evaluate("JSON.parse(localStorage.getItem('mock-db')||'[]')") if r['collection']=='bilans']
    ok("bilan enregistré",len(rows)==1 and rows[0]['data']['energie']==4 and rows[0]['data']['photos'].get('face','').startswith('paul/'),json.dumps(rows[0]['data']['photos']) if rows else '')
    f=pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('mock-files')||'{}'))");ok("photo compressée et rangée dans le dossier de Paul",len(f)==1 and f[0].startswith('photos/paul/'),str(f))
    sz=pg.evaluate("Object.values(JSON.parse(localStorage.getItem('mock-files')))[0].length");ok("photo allégée (< 400 ko)",sz<400*1024*1.37,f"{round(sz/1.37/1024)} ko")
    pg.wait_for_timeout(500);ok("historique avec miniature",pg.locator('#bilHist img[src^="data:image"]').count()==1)
    pg.locator('#bilPanel').screenshot(path='/home/claude/rendus/v62-bilan-envoye.png')
    # Léa ne voit pas la photo de Paul
    as_user(pg,LEA,'#tracking')
    r=pg.evaluate("async()=>{const sb=supabase.createClient();const a=await sb.storage.from('photos').createSignedUrl(Object.keys(JSON.parse(localStorage.getItem('mock-files')))[0].slice(7),60);const c=await sb.storage.from('photos').upload('paul/pirate.jpg',new Blob(['x']));return [!!(a.data&&a.data.signedUrl),!!c.error]}")
    ok("Léa ne peut ni voir ni déposer chez Paul",r==[False,True],str(r))
    # coach
    as_user(pg,COACH,'#clients');pg.wait_for_timeout(800)
    ok("tableau de bord : bilan reçu",'reçu' in pg.inner_text('[data-res="paul"]'),pg.inner_text('[data-res="paul"]').replace('\n',' ')[:120])
    pg.locator('[data-cl-open="paul"]').click();pg.wait_for_timeout(900);pg.evaluate("location.hash='#tracking'");pg.wait_for_timeout(700)
    if pg.evaluate("document.querySelector('#bilPanel').classList.contains('collapsed')"):pg.click('#bilPanel > h2')
    pg.wait_for_timeout(500)
    ok("vue coach : bilan et photo visibles",'Bilan reçu' in pg.inner_text('#bilBody') and pg.locator('#bilHist img[src^="data:image"]').count()==1 and pg.is_hidden('#bilForm') if pg.locator('#bilForm').count() else 'Bilan reçu' in pg.inner_text('#bilBody'))
    pg.locator('#bilPanel').screenshot(path='/home/claude/rendus/v62-bilan-coach.png')
    b.close()
finally:srv.terminate()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",errs or "aucune")
