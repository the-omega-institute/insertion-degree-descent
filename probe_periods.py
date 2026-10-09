#!/usr/bin/env python3
"""Reproduce the exploratory general-border scan; no universal proof claimed."""
from pathlib import Path
from collections import Counter
from itertools import product
import json
import time
from core import primitive,degree,shift_middle_left,exchanges


def main():
    started=time.monotonic();counts=Counter();failures=[];total=0
    for length in range(3,9):
        for bits in product('AB',repeat=length):
            T=''.join(bits)
            if primitive(T)!=T:continue
            for bsize in range(1,length):
                b=T[:bsize]
                if not T.endswith(b):continue
                for h,j,k,ell in product(range(1,4),repeat=4):
                    a=(T*h)[:-bsize];c=(T*j)[bsize:]
                    u=a+b+c;v=T*(k+ell);w=a+T*k+b+T*ell+c
                    M='U'*len(a)+'V'*(length*k)+'U'*len(b)+'V'*(length*ell)+'U'*len(c)
                    total+=1;d=degree(u,v,w);counts[d]+=1
                    if d!=3:continue
                    N=shift_middle_left(w,M);ds=[degree(u,v,z['word']) for z in exchanges(w,N)]
                    if ds[0]!=2:
                        failures.append(dict(T=T,b=b,h=h,j=j,k=k,ell=ell,
                                             u=u,v=v,w=w,M=M,N=N,degrees=ds))
    result=dict(domain='primitive binary T lengths 3..8; every proper nonempty border b; h,j,k,ell in 1..3',
                total=total,degree_counts=dict(counts),failures=failures,
                elapsed_seconds=time.monotonic()-started)
    Path('results/general-period-probe.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='failures'},indent=2))


if __name__=='__main__':
    main()
