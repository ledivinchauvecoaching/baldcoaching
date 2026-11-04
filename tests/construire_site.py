"""Fabrique index.html (page complète pour Netlify) à partir de carnet.html."""
import sys
src=open('/home/claude/carnet.html',encoding='utf-8').read()
head='<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover">\n'
i=src.index('</style>')+len('</style>')
out=head+src[:i]+'\n</head>\n<body>\n'+src[i:]+'\n</body>\n</html>\n'
open(sys.argv[1],'w',encoding='utf-8').write(out)
