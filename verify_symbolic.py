"""Independent explicit-path audit of symbolic pruning and constrained DP."""
import itertools
import json
from collections import Counter
from pathlib import Path
import time
from verify import masks, moves, projection
from canonical import inspect, factors


def paths(length,m):
    out=[]
    for pp in itertools.combinations(range(length),m):
        positions=set(pp);i=0;j=m;perm=[];label=''
        for t in range(length):
            if t in positions:perm.append(i);i+=1;label+='U'
            else:perm.append(j);j+=1;label+='V'
        r=m-sum(b==a+1 for a,b in zip(pp,pp[1:]))
        out.append((r,label,perm))
    return sorted(out)


def audit(length,r,memo=False,last=False):
    counts=Counter()
    for m in range(r,length):
        pp=paths(length,m)
        alts=[perm for k,label,perm in pp if k<=r-2]
        if not alts:continue
        originals=[(label,perm) for k,label,perm in pp if k==r]
        for label,original in originals:
            mm=[z for _,_,_,z in moves(original,label)]
            seen=[set() for _ in range(len(mm)+1)]
            counts['masks']+=1
            def branch(depth,parent):
                if depth==len(mm):counts['bad']+=1;return
                for alt in alts:
                    eq=parent.copy()
                    def root(i):
                        while eq[i]!=i:i=eq[i]
                        return i
                    for i,j in zip(mm[depth],alt):eq[root(i)]=root(j)
                    roots=[root(i) for i in range(length)]
                    word=[roots[i] for i in original]
                    counts['nodes']+=1
                    if memo:
                        names={};signature=tuple(names.setdefault(x,len(names)) for x in roots)
                        if signature in seen[depth+1]:counts['duplicates']+=1;continue
                        seen[depth+1].add(signature)
                    valid=[(k,ll) for k,ll,perm in pp if [roots[i] for i in perm]==word]
                    best=min(valid)
                    if last:best=(best[0],max(ll for k,ll in valid if k==best[0]))
                    if best[0]<r:counts['pruned_low']+=1;continue
                    if (best[1]>label if last else best[1]<label):
                        counts['pruned_later' if last else 'pruned_earlier']+=1;continue
                    branch(depth+1,eq)
            branch(0,list(range(length)))
    for key in ['masks','nodes','pruned_low','pruned_later' if last else 'pruned_earlier','bad']:counts[key]+=0
    if memo:counts['duplicates']+=0
    return dict(counts)


def main():
    start=time.monotonic();counts=Counter();symbolic=[];memo_results=[]
    for r in [3,4,5]:
        data={x['length']:x for x in map(json.loads,Path(f'logs/symbolic{r}-16.log').read_text().splitlines())}
        for length in range(2*r-1,10):
            result=audit(length,r)
            assert result=={key:data[length][key] for key in result},(length,r,result,data[length])
            symbolic.append(dict(length=length,degree=r,**result))
    for r in [3,4,5]:
        data={x['length']:x for x in map(json.loads,Path(f'logs/memo{r}-9.log').read_text().splitlines())}
        for length in range(2*r-1,10):
            result=audit(length,r,True)
            assert result=={key:data[length][key] for key in result},(length,r,result,data[length])
            memo_results.append(dict(length=length,degree=r,**result))
    for length in range(2,7):
        for m in range(1,length):
            for letters in itertools.product('01',repeat=length):
                u,v=''.join(letters[:m]),''.join(letters[m:]);cc=masks(u,v)
                for w,rows in cc.items():
                    r=min(q for _,q in rows);first=min(label for label,q in rows if q==r)
                    result=inspect(u,v,w)
                    assert result['degree']==r and result['first_minimum_mask']==first
                    counts['canonical_masks']+=1
                    for z in result['candidates']:
                        cmin,bmin=None,None
                        for label,q in cc[z['word']]:
                            ff=factors(u,v,label,z['begin'],z['mid'],z['end'])
                            cm=ff['U_commutes'] and ff['V_commutes']
                            old=cmin if cm else bmin
                            val=(q,label)
                            if old is None or val<old:
                                if cm:cmin=val
                                else:bmin=val
                        assert (z['commuting_minimum']['degree'],z['commuting_minimum']['mask'])==cmin
                        reported=z['noncommuting_minimum']
                        assert (None if reported is None else (reported['degree'],reported['mask']))==bmin
                        counts['constrained_minima']+=2
    result=dict(counts=counts,symbolic=symbolic,symbolic_memo=memo_results,elapsed_seconds=round(time.monotonic()-start,3))
    Path('results/verification-symbolic.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
