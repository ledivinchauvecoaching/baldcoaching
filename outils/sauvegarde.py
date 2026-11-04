"""Sauvegarde complète de la base Supabase (lancée par GitHub Actions).
Lit SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY dans l'environnement, écrit sauvegarde.json.
La clé service ne quitte jamais GitHub : elle est stockée dans les « secrets » du dépôt."""
import os,json,re,sys,urllib.request,datetime
url=os.environ.get("SUPABASE_URL") or re.search(r'supabaseUrl:\s*"([^"]+)"',open("config.js").read()).group(1)
key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
if not key:sys.exit("Secret SUPABASE_SERVICE_ROLE_KEY manquant : ajoute-le dans GitHub › Settings › Secrets and variables › Actions.")
def get(table,select="*"):
    out=[];start=0
    while True:
        req=urllib.request.Request(f"{url}/rest/v1/{table}?select={select}",headers={"apikey":key,"Authorization":"Bearer "+key,"Range-Unit":"items","Range":f"{start}-{start+999}"})
        try:
            with urllib.request.urlopen(req,timeout=60) as r:rows=json.load(r)
        except urllib.error.HTTPError as e:
            if e.code==404 and table!="carnet_docs":return None
            raise
        out+=rows
        if len(rows)<1000:return out
        start+=1000
data={"format":"bald-sauvegarde","version":1,"date":datetime.datetime.utcnow().isoformat()+"Z"}
for t in ["carnet_docs","coaching","invitations","app_roles"]:data[t]=get(t)
json.dump(data,open("sauvegarde.json","w"),ensure_ascii=False)
print("Sauvegarde :",{k:(len(v) if isinstance(v,list) else v) for k,v in data.items() if k not in("format","version")})
