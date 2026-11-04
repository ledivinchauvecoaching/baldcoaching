import sys,os
from PIL import Image,ImageChops
a,b=sys.argv[1],sys.argv[2];diff=0
for f in sorted(os.listdir(a)):
    A=Image.open(f'{a}/{f}').convert('RGB');B=Image.open(f'{b}/{f}').convert('RGB')
    if A.size!=B.size:print('TAILLE ',f,A.size,B.size);diff+=1;continue
    bb=ImageChops.difference(A,B).getbbox()
    if bb:print('DIFF   ',f,bb);diff+=1
print('identiques' if not diff else f'{diff} écran(s) différent(s)')
