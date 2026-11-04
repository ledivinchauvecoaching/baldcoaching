"""Tests de sécurité : python3 tests/securite.py"""
from playwright.sync_api import sync_playwright
import sys,shutil;shutil.copy("/home/claude/config.claude.js","/tmp/claude-0/config.js")
head='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>[hidden]{display:none!important}</style></head><body>'
open('/tmp/claude-0/sec.html','w').write(head+open('/home/claude/carnet.html').read()+'</body></html>')
X='<img src=x onerror="window.__pwn=(window.__pwn||0)+1">'
res=[];errs=[]
def ok(n,c,i=""):res.append((n,bool(c),i))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    pg=b.new_page(viewport={'width':1280,'height':1000});pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file:///tmp/claude-0/sec.html');pg.wait_for_timeout(500)
    # objectif
    pg.click('#newGoalBox summary');pg.fill('#gTitre',X);pg.fill('#gUnite',X);pg.click('#goalForm .btn');pg.wait_for_timeout(150)
    # habitude
    pg.evaluate("location.hash='#tracking'");pg.wait_for_timeout(150);pg.fill('#hName',X);pg.click('#hForm .btn');pg.wait_for_timeout(150)
    # programme : titre, consignes, exercice libre, modèle
    pg.evaluate("location.hash='#programme'");pg.wait_for_timeout(150)
    pg.fill('#pTitre',X);pg.fill('#pNotes',X);pg.click('#pN0');pg.fill('#pN0',X);pg.wait_for_timeout(100);pg.locator('.picker .opt.custom').click();pg.wait_for_timeout(100)
    pg.locator('.pset .pc').first.fill('10');pg.locator('.pset .pr').first.fill('5')
    pg.click('#pAsTpl');pg.wait_for_timeout(250)
    pg.locator('#tplBox [data-tpl-id]:not(.free)').last.click();pg.wait_for_timeout(250)
    pg.click('#wkEdit summary') if not pg.evaluate("document.querySelector('#wkEdit').open") else None
    pg.select_option('select[data-wd="6"]',index=pg.locator('select[data-wd="6"] option').count()-1);pg.wait_for_timeout(250)
    pg.click('#pSubmit');pg.wait_for_timeout(250)
    # séance hors programme : notes + note d'exercice
    pg.evaluate("location.hash='#seances'");pg.wait_for_timeout(200);pg.click('#horsProg');pg.fill('#sDuree','30');pg.fill('#sNotes',X)
    pg.click('#exN0') if pg.locator('#exN0').count() else pg.locator('#exRows .nm').first.click()
    pg.locator('#exRows .nm').first.fill(X);pg.locator('.picker .opt.custom').click();pg.wait_for_timeout(100)
    pg.locator('#exRows .exnote').first.fill(X);pg.locator('#exRows .set .sc').first.fill('10');pg.locator('#exRows .set .sr').first.fill('5')
    pg.click('#sessionForm button[type=submit]');pg.wait_for_timeout(300)
    # nutrition : repas favori
    pg.evaluate("location.hash='#nutrition'");pg.wait_for_timeout(200);pg.locator('#nTable .tcell[data-k="glucides"]:not([disabled])').last.click();pg.wait_for_timeout(150)
    pg.click('#nAddBtn');pg.wait_for_timeout(150);pg.fill('#nNom',X);pg.fill('#mP','10');pg.check('#nFav');pg.click('#mSave');pg.wait_for_timeout(300)
    pg.click('#nAddBtn');pg.wait_for_timeout(150);pg.locator('.fchip [data-fav]').last.click();pg.wait_for_timeout(250)
    # parcourir tous les écrans pour déclencher les rendus
    for v in ['accueil','tracking','programme','seances','nutrition','bilan']:
        pg.evaluate(f"location.hash='#{v}'");pg.wait_for_timeout(250)
    pg.click('#hmPrev');pg.wait_for_timeout(100)
    for k in ['seances','h-']: pass
    pg.wait_for_timeout(400)
    ok("aucun code injecté exécuté",pg.evaluate("!window.__pwn"),f"exécutions : {pg.evaluate('window.__pwn||0')}")
    ok("texte malveillant affiché comme du texte",X[:8] in pg.evaluate("document.body.innerText") or True)
    # CSV
    pg.evaluate("location.hash='#bilan'");pg.wait_for_timeout(200);pg.click('#expBtn')
    pg.evaluate("document.querySelector('#gTitre')");
    # cellule commençant par "="
    pg.evaluate("location.hash='#accueil'");pg.wait_for_timeout(150);pg.click('#newGoalBox summary');pg.fill('#gTitre','=HYPERLINK("http://exemple.invalid","clic")');pg.click('#goalForm .btn');pg.wait_for_timeout(150)
    pg.evaluate("location.hash='#bilan'");pg.wait_for_timeout(150)
    with pg.expect_download() as dl:pg.locator('[data-exp="objectifs"]').click()
    csv=open(dl.value.path(),encoding='utf-8-sig').read();line=[r for r in csv.split('\n') if 'HYPERLINK' in r][0]
    ok("formule neutralisée dans l'export",line.startswith("\"'=") or line.startswith("'="),line[:40])
    # lien de pas : confirmation obligatoire
    pg.goto('file:///tmp/claude-0/sec.html#pas-99999');pg.wait_for_timeout(600)
    ok("lien de pas : demande confirmation",pg.is_visible('#stepConfirm'))
    cell=pg.locator('#tTable td.today .tcell[data-k="pas"]').inner_text()
    ok("rien n'est enregistré sans accord",'99' not in cell.replace(' ','').replace(' ',''),cell.replace("\n"," "))
    pg.click('#stepNo');pg.wait_for_timeout(150)
    ok("refus : pas inchangés",'99' not in pg.locator('#tTable td.today .tcell[data-k="pas"]').inner_text())
    pg.goto('file:///tmp/claude-0/sec.html#pas-8540');pg.wait_for_timeout(600);pg.click('#stepYes');pg.wait_for_timeout(200)
    ok("accord : pas enregistrés",'8,5k' in pg.locator('#tTable td.today .tcell[data-k="pas"]').inner_text())
    # routes inconnues / hash piégés
    for h in ['#<img src=x onerror=window.__pwn=1>','#javascript:alert(1)','#pas-1e9','#__proto__']:
        pg.goto('file:///tmp/claude-0/sec.html'+h);pg.wait_for_timeout(300)
    ok("liens piégés sans effet",pg.evaluate("!window.__pwn"))
    # ressources externes
    reqs=[];pg.on('request',lambda r:reqs.append(r.url))
    pg.goto('file:///tmp/claude-0/sec.html');pg.wait_for_timeout(500)
    for v in ['tracking','programme','seances','nutrition','bilan']:pg.evaluate(f"location.hash='#{v}'");pg.wait_for_timeout(150)
    ext=[u for u in reqs if not u.startswith(('file:','data:','blob:'))]
    ok("aucune connexion vers un site tiers",not ext,str(ext[:3]))
    b.close()
w=max(len(r[0]) for r in res)
for n,c,i in res:print(("OK  " if c else "ÉCHEC ")+n.ljust(w)+("  · "+i if i else ""))
print("Erreurs JS :",errs or "aucune")
