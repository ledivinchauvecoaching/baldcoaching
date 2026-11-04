"""Vérifie la sortie des tests SQL : chaque ligne « … (attendu X) » doit être suivie d'un résultat contenant X.
Usage : psql … -f test.sql 2>&1 | python3 outils/verifier_sql.py"""
import sys,re
L=[l.rstrip("\n") for l in sys.stdin];ko=0;n=0
norm=lambda t:re.sub(r"[^0-9a-zà-ü]","",t.lower())
for i,l in enumerate(L):
    m=re.search(r"\(attendu ([^)]*)\)",l)
    if not m or "," in m.group(1):continue
    exp=m.group(1).strip();nxt=next((x for x in L[i+1:] if x.strip()),"")
    good=("ERROR" in nxt) if exp.startswith("ERREUR") else (norm(exp.split(" puis")[0]) in norm(nxt) and "ERROR" not in nxt)
    n+=1
    if not good:ko+=1;print("ÉCHEC",l.strip(),"→",nxt.strip())
print(f"{n-ko}/{n} vérifications SQL réussies");sys.exit(1 if ko else 0)
