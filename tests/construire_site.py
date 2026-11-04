"""Fabrique index.html (page complète pour Netlify) à partir de carnet.html."""
import sys
src=open('/home/claude/carnet.html',encoding='utf-8').read()
head='<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover">\n'
head+='<link rel="manifest" href="/manifest.webmanifest">\n<link rel="icon" href="/favicon.ico" sizes="any">\n<link rel="icon" type="image/png" href="/favicon.png">\n<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
head+='<meta name="theme-color" content="#2A1A0E">\n<meta name="application-name" content="BaldCoaching">\n<meta name="apple-mobile-web-app-title" content="BaldCoaching">\n<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-status-bar-style" content="black">\n'
i=src.index('</style>')+len('</style>')
out=head+src[:i]+'\n</head>\n<body>\n'+src[i:]+'\n</body>\n</html>\n'
open(sys.argv[1],'w',encoding='utf-8').write(out)
