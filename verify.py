"""Independent position-combination enumeration and mathematical checks."""
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
import time


def masks(u,v):
    out=defaultdict(list)
    length=len(u)+len(v)
    for positions in itertools.combinations(range(length),len(u)):
        us=set(positions)
        it,jt=iter(u),iter(v)
        word=''.join(next(it) if p in us else next(jt) for p in range(length))
        label=''.join('U' if p in us else 'V' for p in range(length))
        out[word].append((label,len(positions)-sum(b==a+1 for a,b in zip(positions,positions[1:]))))
    return out


def degree(u,v,w):
    """Dense grid recurrence, with an independent previous-source state."""
    m,n=len(u),len(v)
    inf=m+n+1
    dp=[[[inf,inf] for j in range(n+1)] for i in range(m+1)]
    dp[0][0][0]=0
    for i in range(m+1):
        for j in range(n+1):
            t=i+j
            if t==m+n:continue
            if i<m and u[i]==w[t]:
                dp[i+1][j][1]=min(dp[i+1][j][1],dp[i][j][1],dp[i][j][0]+1)
            if j<n and v[j]==w[t]:
                dp[i][j+1][0]=min(dp[i][j+1][0],*dp[i][j])
    return min(dp[m][n])


def moves(w,label):
    starts=[0]+[p for p in range(1,len(label)) if label[p]!=label[p-1]]+[len(label)]
    for k in range(1,len(starts)-2):
        a,b=starts[k],starts[k+1]
        if label[a]!='V':continue
        l,h=starts[k-1],starts[k+2]
        for lo,cut,hi in [(l,a,b),(a,b,h)]:
            yield lo,cut,hi,w[:lo]+w[cut:hi]+w[lo:cut]+w[hi:]


def projection(w,label,source):
    return ''.join(c for c,q in zip(w,label) if q==source)


def count_runs(label):
    return sum(q=='U' and (p==0 or label[p-1]=='V') for p,q in enumerate(label))


def main():
    started=time.monotonic();counts=Counter()
    for flags in itertools.product([0,1],repeat=6):
        l,a,A,b,B,r=flags
        delta=(1-l)*(a-b)+(1-A)*(b-r)+(1-B)*(r-a)
        assert delta in [-1,0,1]
        counts['boundary_assignments']+=1
    for length in range(2,9):
        for split in range(1,length):
            for letters in itertools.product('01',repeat=length):
                u,v=''.join(letters[:split]),''.join(letters[split:])
                classes=masks(u,v)
                ds={w:min(r for _,r in rows) for w,rows in classes.items()}
                counts['pairs']+=1;counts['outputs']+=len(ds)
                for w,rows in classes.items():
                    assert degree(u,v,w)==ds[w]
                    counts['dp_checks']+=1
                    r=ds[w]
                    if r<=1:continue
                    for label,q in rows:
                        if q!=r:continue
                        for lo,cut,hi,z in moves(w,label):
                            blen=hi-cut
                            c,b=99,99
                            for nn,k in classes[z]:
                                first=projection(z[lo:lo+blen],nn[lo:lo+blen],'U')
                                second=projection(z[lo+blen:hi],nn[lo+blen:hi],'U')
                                firstv=projection(z[lo:lo+blen],nn[lo:lo+blen],'V')
                                secondv=projection(z[lo+blen:hi],nn[lo+blen:hi],'V')
                                commuting=first+second==second+first and firstv+secondv==secondv+firstv
                                pulled=nn[:lo]+nn[lo+blen:hi]+nn[lo:lo+blen]+nn[hi:]
                                valid=projection(w,pulled,'U')==u and projection(w,pulled,'V')==v
                                assert commuting==valid
                                assert abs(count_runs(pulled)-k)<=1
                                if commuting:c=min(c,k)
                                else:b=min(b,k)
                                counts['transport_checks']+=1
                            assert c==r-1
                            assert ds[z]==min(r-1,b)
                            counts['block_criterion_checks']+=1
    unary_pairs=set()
    for length in range(2,12):
        for m in range(1,length):
            n=length-m
            for a in '01':
                for vv in itertools.product('01',repeat=n):unary_pairs.add((a*m,''.join(vv)))
                for uu in itertools.product('01',repeat=m):unary_pairs.add((''.join(uu),a*n))
    for u,v in sorted(unary_pairs,key=lambda p:(len(p[0])+len(p[1]),p)):
        classes=masks(u,v);ds={w:min(r for _,r in rows) for w,rows in classes.items()}
        counts['unary_pairs']+=1
        for w,rows in classes.items():
            r=ds[w]
            if r<=1:continue
            for label,q in rows:
                if q!=r:continue
                for _,_,_,z in moves(w,label):
                    assert ds[z]==r-1,(u,v,w,label,z,r,ds[z])
                    counts['unary_move_checks']+=1
    for tag in ['binary13','ternary8','quaternary8','binary14','binary15','binary16','ternary10','quaternary10','ternary12']:
        path=Path('certificates')/(tag+'-witnesses.jsonl')
        if not path.exists():continue
        for line in path.read_text().splitlines():
            x=json.loads(line);u,v,w=x['u'],x['v'],x['w'];r=x['degree']
            cc=masks(u,v);ds={z:min(k for _,k in rows) for z,rows in cc.items()}
            assert ds[w]==r
            minimum=sorted(label for label,k in cc[w] if k==r)
            if x['rule'].startswith('first_mask'):assert x['mask']==minimum[0]
            if x['rule'].startswith('last_mask'):assert x['mask']==minimum[-1]
            chosen=[]
            for z in x['moves']:
                assert ds[z['word']]==z['degree']
                if z['chosen']:chosen.append(z['degree'])
                counts['witness_move_checks']+=1
            assert chosen and r-1 not in chosen
            counts['rule_witnesses']+=1
    for line in Path('certificates/symbolic3-20-bad.jsonl').read_text().splitlines():
        x=json.loads(line);u,v,w=x['u'],x['v'],x['w']
        cc=masks(u,v);ds={z:min(k for _,k in rows) for z,rows in cc.items()}
        assert ds[w]==3
        assert all(ds[z]==1 for _,_,_,z in moves(w,x['mask']))
        first=min(label for label,k in cc[w] if k==3)
        assert any(ds[z]==2 for _,_,_,z in moves(w,first))
        counts['symbolic_bad_masks_verified']+=1
    for k in range(2,11):
        for h in range(2,11):
            u='ABABA';v='ABA'*(k+h);w='AB'+'ABA'*k+'A'+'ABA'*h+'BA'
            label='UU'+'V'*(3*k)+'U'+'V'*(3*h)+'UU'
            assert degree(u,v,w)==3
            mm=list(moves(w,label))
            assert [z for _,_,_,z in mm]==[v+u,v+u,u+v,u+v]
            first='UU'+'V'*(3*k-1)+'U'+'V'*(3*h-1)+'UU'+'VV'
            z=next(moves(w,first))[3]
            assert z=='ABA'*(k-1)+'ABABAA'+'ABA'*h+'BA'
            assert degree(u,v,z)==2
            counts['infinite_family_instances']+=1
            if k+h<=6:
                cc=masks(u,v)
                assert len(cc[w])==12 and {r for _,r in cc[w]}=={3}
                assert min(label for label,r in cc[w])==first
                counts['family_complete_mask_lists']+=1
    result=dict(counts=counts,elapsed_seconds=round(time.monotonic()-started,3))
    Path('results/verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
