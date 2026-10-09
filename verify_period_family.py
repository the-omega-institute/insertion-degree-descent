#!/usr/bin/env python3
"""Finite checks of the unbounded family theorem, including nonminimum masks."""
from itertools import product
from pathlib import Path
from collections import Counter
import json
import time
from core import degree, all_masks, runs, projections, exchanges, shift_middle_left


def main():
    start = time.monotonic()
    counts = Counter()
    exact, finite = 0, 0
    for C in ('B', 'BB', 'BC', 'BCB'):
        domain = range(1,7) if C == 'B' else range(1,4)
        T = 'A'+C+'A'
        for h,j,k,ell in product(domain, repeat=4):
            a=T*(h-1)+'A'+C
            c=C+'A'+T*(j-1)
            u=a+'A'+c;v=T*(k+ell);w=a+T*k+'A'+T*ell+c
            M='U'*len(a)+'V'*(len(T)*k)+'U'+'V'*(len(T)*ell)+'U'*len(c)
            assert projections(w,M)==(u,v)
            assert [z['word'] for z in exchanges(w,M)]==[v+u,v+u,u+v,u+v]
            N=shift_middle_left(w,M)
            z=next(exchanges(w,N))
            expected=T*(k-1)+'A'+C+T*h+'A'+T*ell+C+'A'+T*(j-1)
            assert z['word']==expected and projections(z['word'],z['transported'])==(u,v)
            assert runs(z['transported'])==degree(u,v,expected)==2
            old=degree(u,v,w);counts[C,old]+=1
            exact+=old==3
            if C=='B' and len(w)<=17:
                assert degree(u,v,expected)==min(map(runs,all_masks(u,v,expected)))
                finite+=1
    result=dict(status='PASS',cases=sum(counts.values()),
                cases_where_original_degree_three=exact,
                degree_counts={str(k):v for k,v in counts.items()},
                all_periodic_repaired_outputs_have_degree_two=True,
                independent_position_combination_checks=finite,
                elapsed_seconds=round(time.monotonic()-start,3))
    Path('results/period-family-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
