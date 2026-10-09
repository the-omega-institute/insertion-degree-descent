#!/usr/bin/env python3
"""Check all possible further identifications by imposing each one-run witness.

For every original bad partition and each proposed contiguous-u cut in each
shifted successor, impose the least extra letter equalities making that cut a
valid one-run mask. If the resulting original word has degree <=2, that pruning
witness persists under every further identification. Thus no coarsening can
retain degree three and make that successor degree one. This independently
checks the finite reduction without enumerating Bell-many alphabet partitions.
"""
import argparse
from pathlib import Path
from collections import Counter
import hashlib
import json
import time
from core import degree, runs, projections, blocks, exchanges, primitive, shift_middle_left


def force_cut(u,v,w,z,cut):
    parent={c:c for c in u+v}
    def root(c):
        while parent[c]!=c:
            parent[c]=parent[parent[c]];c=parent[c]
        return c
    for a,b in zip(z,v[:cut]+u+v[cut:]):
        parent[root(a)]=root(b)
    alphabet=sorted(set(u+v));names={}
    for c in alphabet:
        r=root(c)
        if r not in names:names[r]=chr(65+len(names))
    translation=str.maketrans({c:names[root(c)] for c in alphabet})
    return [s.translate(translation) for s in (u,v,w,z)]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('--output',type=Path,default=Path('results/identification-audit.json'))
    args=parser.parse_args();start=time.monotonic()
    rows=[json.loads(s) for s in args.input.read_text().splitlines()]
    unique={(x['u'],x['v'],x['w'],x['mask']):x for x in rows}
    vectors=Counter();shapes=Counter();attempts=0;certificates=[]
    for x in unique.values():
        u,v,w,M=(x[k] for k in ('u','v','w','mask'))
        assert degree(u,v,w)==runs(M)==3 and projections(w,M)==(u,v)
        original=list(exchanges(w,M))
        assert [degree(u,v,z['word']) for z in original]==[1]*4
        for z,cut in zip(original,x['cuts']):
            assert z['word']==v[:cut]+u+v[cut:]
        bb=blocks(w,M);s=next(i for i,b in enumerate(bb) if b[0]=='U')
        a,P,b,Q,c=[z[1] for z in bb[s:s+5]];T=primitive(P)
        assert all(len(z)%len(T)==0 and z==T*(len(z)//len(T)) for z in (P,Q,a+b,b+c))
        assert len(b)<len(T)
        N=shift_middle_left(w,M);new=list(exchanges(w,N))
        ds=tuple(degree(u,v,z['word']) for z in new);vectors[ds]+=1
        assert ds==(2,1,1,2)
        shapes[len(T),len(b)]+=1
        entries=[]
        for e in (0,3):
            for cut in range(len(v)+1):
                uu,vv,ww,zz=force_cut(u,v,w,new[e]['word'],cut)
                assert zz==vv[:cut]+uu+vv[cut:]
                old=degree(uu,vv,ww)
                assert old<=2, (x,e,cut,uu,vv,ww)
                attempts+=1;entries.append([e,cut,old])
        certificates.append(dict(u=u,v=v,w=w,mask=M,period=T,
                                 shifted=N,cut_pruning=entries))
    output=dict(status='PASS',input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                witness_tuples=len(rows),distinct_source_output_mask_instances=len(unique),
                maximum_length=max(len(x['w']) for x in rows),
                coarsening_witness_cuts_checked=attempts,
                shifted_degree_vectors={str(k):v for k,v in vectors.items()},
                period_and_middle_run_lengths={str(k):v for k,v in shapes.items()},
                elapsed_seconds=round(time.monotonic()-start,3))
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    args.output.with_suffix('.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in certificates))
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    main()
