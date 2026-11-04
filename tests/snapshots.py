"""Captures déterministes de chaque écran : python3 tests/snapshots.py <dossier>"""
from playwright.sync_api import sync_playwright
import sys,shutil;shutil.copy("/home/claude/config.claude.js","/tmp/claude-0/config.js"),os
out=sys.argv[1];os.makedirs(out,exist_ok=True)
head='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font:14px system-ui}[hidden]{display:none!important}*{transition:none!important;animation:none!important;caret-color:transparent!important}</style></head><body>'
open('/tmp/claude-0/snap.html','w').write(head+open('/home/claude/carnet.html').read()+'</body></html>')
FIX="Math.random=()=>0.42;const _D=Date;Date.now=()=>new _D('2026-11-04T10:00:00').getTime();"
VIEWS=['accueil','tracking','programme','seances','nutrition','bilan','suggestion']
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    for tag,w,h,dpr,mode in [('d',1280,900,1,'light'),('m',390,844,1,'dark')]:
        ctx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr);ctx.add_init_script(FIX)
        pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('file:///tmp/claude-0/snap.html');pg.wait_for_timeout(500);pg.click(f'.theme-sw [data-th="{mode}"]');pg.wait_for_timeout(100)
        for v in VIEWS:
            pg.evaluate(f"location.hash='#{v}'");pg.wait_for_timeout(250);pg.evaluate("scrollTo(0,0)");pg.wait_for_timeout(50)
            pg.screenshot(path=f'{out}/{tag}-{v}.png',full_page=True)
        # états interactifs
        pg.evaluate("location.hash='#programme'");pg.wait_for_timeout(200)
        if tag=='m':pg.click('#goPlan');pg.wait_for_timeout(200)
        pg.click('#pN0');pg.wait_for_timeout(150);pg.screenshot(path=f'{out}/{tag}-picker.png',full_page=True);pg.keyboard.press('Escape')
        pg.evaluate("location.hash='#nutrition'");pg.wait_for_timeout(200)
        pg.locator('#nTable .tcell[data-k="glucides"]:not([disabled])').last.click();pg.wait_for_timeout(200);pg.screenshot(path=f'{out}/{tag}-macros.png',full_page=True)
        pg.evaluate("location.hash='#tracking'");pg.wait_for_timeout(200)
        pg.locator('#tTable .tcell[data-k="eau"]:not([disabled])').last.click();pg.wait_for_timeout(200);pg.screenshot(path=f'{out}/{tag}-trackedit.png',full_page=True)
        pg.evaluate("location.hash='#seances'");pg.wait_for_timeout(200);pg.click('#horsProg');pg.wait_for_timeout(200);pg.screenshot(path=f'{out}/{tag}-horsprog.png',full_page=True)
        pg.evaluate("location.hash='#bilan'");pg.wait_for_timeout(200)
        for k in ['tonnage','poids']:pg.click(f'[data-ind="{k}"]');pg.wait_for_timeout(100)
        pg.screenshot(path=f'{out}/{tag}-bilan-graph.png',full_page=True)
        ctx.close()
    b.close()
print(len(os.listdir(out)),'captures',errs or 'sans erreur')
