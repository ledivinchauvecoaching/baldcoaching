"""Retrouve la page source (carnet.html) à partir de index.html, pour les tests automatiques."""
import sys
idx=open(sys.argv[1],encoding='utf-8').read()
i=idx.index('<title>');sep='\n</head>\n<body>\n';j=idx.index(sep)
src=idx[i:j]+idx[j+len(sep):]
src=src[:src.rindex('\n</body>\n</html>\n')]
open(sys.argv[2],'w',encoding='utf-8').write(src)
