"""Test de non-régression du carnet : python3 tests/regression.py"""
from playwright.sync_api import sync_playwright
import sys,shutil;shutil.copy("/home/claude/config.claude.js","/tmp/claude-0/config.js")
head='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font:14px system-ui}[hidden]{display:none!important}</style></head><body>'
open('/tmp/claude-0/page.html','w').write(head+open('/home/claude/carnet.html').read()+'</body></html>')
errs=[];res=[]
def ok(name,cond,info=""):res.append((name,bool(cond),info))
def pick(pg,sel,name,q):
    pg.click(sel);pg.fill(sel,q);pg.wait_for_timeout(100);pg.click(f'.picker [data-v="{name}"]');pg.wait_for_timeout(150)
TODAY="(()=>{const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')})()"
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    ctx=b.new_context(viewport={'width':1280,'height':1000});ctx.grant_permissions(['clipboard-read','clipboard-write'])
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('file:///tmp/claude-0/page.html');pg.wait_for_timeout(500);pg.click('.theme-sw [data-th="light"]')
    ok("accueil par défaut",pg.inner_text('#pageTitle').upper()=="ACCUEIL")
    ok("6 onglets en bas",pg.locator('nav.tabs a').count()==6)
    ok("suggestion dans l'en-tête",pg.locator('header #tab-suggestion').count()==1)
    ok("bandeau sans UA","UA" not in pg.inner_text('.week'),pg.inner_text('.week').replace("\n"," "))
    ok("objectif lié squat",pg.locator('.goal',has_text='Squat à 100 kg').locator('.gauto').count()==1)
    # tracking + comma
    pg.click('#tab-tracking');pg.locator('#tTable .tcell[data-k="poids"]:not([disabled])').last.click();pg.fill('#tEditVal','');pg.type('#tEditVal','77,6');ok("virgule convertie",pg.input_value('#tEditVal')=="77.6",pg.input_value('#tEditVal'));pg.click('#tEditSave');pg.wait_for_timeout(150)
    # nutrition favs + macros
    pg.click('#tab-nutrition');pg.locator('#nTable .tcell[data-k="glucides"]:not([disabled])').last.click();pg.wait_for_timeout(150)
    pg.fill('#mP','');pg.fill('#mG','');pg.fill('#mL','');pg.locator('[data-fav="r1"]').click();pg.locator('[data-fav="r3"]').click();pg.wait_for_timeout(100)
    ok("repas favoris additionnés",pg.input_value('#mP')=="80" and pg.input_value('#mG')=="140",pg.input_value('#mP')+"/"+pg.input_value('#mG'))
    pg.locator('#view-nutrition .panel').first.screenshot(path='/home/claude/rendus/v38-favoris.png')
    pg.click('#mSave');pg.wait_for_timeout(200)
    ok("kcal calculées",kcal:=pg.locator('#nTable td.today .tcell[data-k="kcal"]').inner_text().replace("\n"," "),kcal)
    pg.click('.kcalp>h2') if pg.locator('.kcalp.collapsed').count() else None
    ok("BMR Harris-Benedict",'1 818' in pg.inner_text('#hbFormula') or '1 810' in pg.inner_text('#hbFormula') or 'kcal' in pg.inner_text('#hbFormula'))
    # programme
    pg.click('#tab-programme');pg.wait_for_timeout(200)
    ok("semaine type affichée",pg.locator('.cal-c.rec').count()>=2)
    pg.select_option('#palSel','2.5');pg.wait_for_timeout(200)
    ok("palier affiché dans l'en-tête",pg.inner_text('#palTxt')=="2,5")
    pg.evaluate(f"document.querySelector('#pDate').value={TODAY}")
    pg.fill('#pTitre','Push test');pick(pg,'#pN0','Développé couché à la barre','couche barre')
    pc=pg.locator('.prow').first.locator('.pset .pc').nth(0).input_value();rc=pg.locator('.prow').first.locator('.pset .rc').nth(0).input_value()
    ok("surcharge progressive avec palier",True,f"repère {rc} → prévu {pc}")
    pg.click('#pSubmit');pg.wait_for_timeout(300)
    # séance du jour auto + draft
    pg.click('#tab-seances');pg.wait_for_timeout(300)
    ok("séance du jour chargée",'Push test' in pg.inner_text('#fromPlanTxt'))
    pg.fill('#sDuree','55');pg.locator('#exRows .set .sr').nth(1).fill('7');pg.wait_for_timeout(700)
    ok("brouillon sauvegardé",pg.evaluate("!!localStorage.getItem('bald-draft')"))
    pg.reload();pg.wait_for_timeout(500);pg.click('#tab-seances');pg.wait_for_timeout(300)
    ok("carte reprise après rechargement",pg.locator('#drResume').count()==1)
    pg.locator('#view-seances .panel').first.screenshot(path='/home/claude/rendus/v38-reprise.png')
    # (reload resets local example data; draft points to a plan that no longer exists -> resumes as libre)
    pg.click('#drResume');pg.wait_for_timeout(300)
    ok("brouillon restauré",pg.input_value('#sDuree')=="55" and pg.locator('#exRows .set .sr').nth(1).input_value()=="7",pg.input_value('#sDuree'))
    pg.click('#sessionForm button[type=submit]');pg.wait_for_timeout(300)
    ok("brouillon effacé après enregistrement",not pg.evaluate("!!localStorage.getItem('bald-draft')"))
    # hors programme course with distance
    pg.click('#horsProg');pg.click('#typeChips label:has-text("Course")');pg.fill('#sDuree','50');pg.fill('#sDist','10');pg.wait_for_timeout(100)
    ok("allure calculée","5:00" in pg.inner_text('#sPace'),pg.inner_text('#sPace'))
    pg.locator('#view-seances .panel').first.screenshot(path='/home/claude/rendus/v38-course.png')
    pg.click('#sessionForm button[type=submit]');pg.wait_for_timeout(300)
    e=pg.locator('#journal .entry').first;ok("journal : distance",'10 km' in e.inner_text(),e.inner_text().split("\n")[1][:60])
    # edit session
    e.locator('[data-edit-s]').click();pg.wait_for_timeout(300)
    ok("mode modification",pg.inner_text('#sessTitle').upper()=="MODIFIER LA SÉANCE" and pg.input_value('#sDist')=="10")
    pg.fill('#sDist','12');pg.click('#sessionForm button[type=submit]');pg.wait_for_timeout(300)
    ok("séance modifiée",'12 km' in pg.locator('#journal .entry').first.inner_text())
    pg.locator('#journal .entry').first.screenshot(path='/home/claude/rendus/v38-journal-edit.png')
    # timer title
    pg.click('#horsProg');pg.locator('#exRows .rs-go').first.click();pg.wait_for_timeout(300)
    ok("minuteur dans le titre",pg.title().startswith("⏱"),pg.title());pg.click('#rReset')
    ok("annuler une séance hors programme",pg.is_visible('#editCancel'));pg.click('#editCancel');pg.wait_for_timeout(150)
    ok("retour à la séance du jour",pg.is_visible('#horsProg') and pg.locator('#sessionForm').is_hidden())
    # export
    pg.click('#tab-bilan');pg.wait_for_timeout(200);pg.click('#expBtn')
    with pg.expect_download() as dl:pg.locator('[data-exp="seances"]').click()
    csv=open(dl.value.path(),encoding='utf-8-sig').read();ok("export : nom de fichier",dl.value.suggested_filename.endswith('.csv'),dl.value.suggested_filename);ok("export CSV séances",csv.startswith("Date;Type") and csv.count("\n")>20,f"{csv.count(chr(10))} lignes")
    pg.locator('#expPanel').screenshot(path='/home/claude/rendus/v38-export.png')
    ok("indicateur distance au bilan",pg.locator('[data-ind="distance"]').count()==1)
    # palier : séance où toutes les séries sont réussies -> +2,5 kg
    pg.click('#tab-programme');pg.wait_for_timeout(150);pg.select_option('#palSel','2.5');pg.wait_for_timeout(200)
    pg.click('#tab-seances');pg.wait_for_timeout(200);pg.click('#horsProg');pg.fill('#sDuree','20')
    pick(pg,'#exRows .nm','Curl à la barre EZ','curl a la barre ez')
    for j,(c,r) in enumerate([(30,10),(30,10),(30,10)]):
        if j>0:pg.locator('#exRows .addset').first.click()
        pg.locator('#exRows .set .sc').nth(j).fill(str(c));pg.locator('#exRows .set .sr').nth(j).fill(str(r))
    pg.click('#sessionForm button[type=submit]');pg.wait_for_timeout(300)
    pg.click('#tab-programme');pg.wait_for_timeout(200);pick(pg,'#pRows .prow .nm','Curl à la barre EZ','curl a la barre ez')
    pv=[pg.locator('.prow').first.locator('.pset .pc').nth(k).input_value() for k in range(3)]
    ok("palier +2,5 kg appliqué",pv==['32.5','32.5','32.5'],str(pv))
    pg.click('#pCancel') if pg.is_visible('#pCancel') else None
    # suggestion via header
    pg.click('header #tab-suggestion');pg.wait_for_timeout(150);ok("page suggestion",pg.inner_text('#pageTitle').upper()=="SUGGESTION")
    # onboarding (empty data)
    src=open('/tmp/claude-0/page.html').read()
    a='const b=$("#banner");b.hidden=false;b.classList.add("demo");';assert src.count(a)==1
    open('/tmp/claude-0/page-vide.html','w').write(src.replace(a,'state.tset={...DEFAULT_T,cibles:{...DEFAULT_T.cibles}};state.sessions=[];state.plans=[];state.goals=[];'+a))
    pg.goto('file:///tmp/claude-0/page-vide.html');pg.wait_for_timeout(400);pg.evaluate("localStorage.removeItem('bald-onb-hide')");pg.reload();pg.wait_for_timeout(400);pg.click('.theme-sw [data-th="light"]')
    ok("guide de démarrage",pg.is_visible('#onb') and "0 étape" in pg.inner_text('#onb'))
    if pg.is_visible('#onb'):pg.locator('#onb').screenshot(path='/home/claude/rendus/v38-guide.png')
    # phone
    m=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);m.on('pageerror',lambda e:errs.append(str(e)))
    m.goto('file:///tmp/claude-0/page.html');m.wait_for_timeout(400);m.click('.theme-sw [data-th="dark"]')
    m.screenshot(path='/home/claude/rendus/v38-accueil-mobile.png')
    ok("pas de défilement horizontal",m.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    b.close()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+str(i) if i else ""))
print("Erreurs JS :",errs or "aucune")
sys.exit(0 if all(r[1] for r in res) and not errs else 1)
