"""Inspect canonical block descent and the exact commutation obstruction.

python3 canonical.py 01010 01010101 0010110011010

U precedes V. Dynamic programming selects the first minimum mask and
computes the two constrained minima for every candidate exchange.
"""
import argparse
import json


def optimal(u,v,w,interval=None,commuting=None):
    """Return (degree, first minimum mask), or None if infeasible.

    interval=(lo,mid,hi) is the new order B,A. With a commutation filter,
    remember source consumption at lo and mid, test at hi, and collapse
    those extra coordinates before the common suffix.
    """
    if len(w)!=len(u)+len(v):return None
    states={(0,'V',-1,-1):(0,'')}
    def put(table,key,value):
        if key not in table or value<table[key]:table[key]=value
    for t in range(len(w)+1):
        if interval:
            lo,mid,hi=interval
            if t in (lo,mid):
                marked={}
                for (i,last,i0,i1),value in states.items():
                    put(marked,(i,last,i if t==lo else i0,i if t==mid else i1),value)
                states=marked
            if t==hi:
                filtered={}
                for (i,last,i0,i1),value in states.items():
                    j0,j1,j2=lo-i0,mid-i1,hi-i
                    bu,au=u[i0:i1],u[i1:i]
                    bv,av=v[j0:j1],v[j1:j2]
                    agrees=bu+au==au+bu and bv+av==av+bv
                    if agrees==commuting:put(filtered,(i,last,-1,-1),value)
                states=filtered
        if t==len(w):break
        new={}
        for (i,last,i0,i1),(cost,mask) in states.items():
            j=t-i
            if i<len(u) and u[i]==w[t]:
                put(new,(i+1,'U',i0,i1),(cost+(last=='V'),mask+'U'))
            if j<len(v) and v[j]==w[t]:
                put(new,(i,'V',i0,i1),(cost,mask+'V'))
        states=new
    values=[value for (i,_,_,_),value in states.items() if i==len(u)]
    return min(values) if values else None


def exchanges(w,mask):
    boundaries=[0]+[p for p in range(1,len(w)) if mask[p]!=mask[p-1]]+[len(w)]
    for k in range(1,len(boundaries)-2):
        a,b=boundaries[k],boundaries[k+1]
        if mask[a]!='V':continue
        l,h=boundaries[k-1],boundaries[k+2]
        for lo,cut,hi,side in [(l,a,b,'left'),(a,b,h,'right')]:
            z=w[:lo]+w[cut:hi]+w[lo:cut]+w[hi:]
            moved=mask[:lo]+mask[cut:hi]+mask[lo:cut]+mask[hi:]
            yield dict(word=z,begin=lo,cut=cut,end=hi,mid=lo+hi-cut,
                       separator=a,side=side,exchanged_mask=moved)


def factors(u,v,mask,lo,mid,hi):
    i0=mask[:lo].count('U');i1=mask[:mid].count('U');i2=mask[:hi].count('U')
    j0,j1,j2=lo-i0,mid-i1,hi-i2
    bu,au=u[i0:i1],u[i1:i2];bv,av=v[j0:j1],v[j1:j2]
    return dict(u_boundaries=[i0,i1,i2],v_boundaries=[j0,j1,j2],
                B_U=bu,A_U=au,B_V=bv,A_V=av,
                U_commutes=bu+au==au+bu,V_commutes=bv+av==av+bv)


def inspect(u,v,w,selected_mask=None):
    minimum=optimal(u,v,w)
    if minimum is None:raise ValueError('The word is not a shuffle of these sources.')
    r,first=minimum
    mask=first if selected_mask is None else selected_mask
    if selected_mask is not None:
        if len(mask)!=len(w) or set(mask)-{'U','V'}:
            raise ValueError('The supplied mask must label every position U or V.')
        pu=''.join(c for c,q in zip(w,mask) if q=='U')
        pv=''.join(c for c,q in zip(w,mask) if q=='V')
        runs=sum(q=='U' and (p==0 or mask[p-1]=='V') for p,q in enumerate(mask))
        if (pu,pv)!=(u,v) or runs!=r:
            raise ValueError('The supplied labeling is not a minimum mask for these sources.')
    candidates=[]
    for item in exchanges(w,mask):
        z=item['word'];interval=(item['begin'],item['mid'],item['end'])
        cc=optimal(u,v,z,interval,True)
        bb=optimal(u,v,z,interval,False)
        ordinary=optimal(u,v,z)
        assert cc is not None and cc[0]==r-1
        assert ordinary[0]==min(cc[0],bb[0] if bb else float('inf'))
        item['degree']=ordinary[0]
        item['exact']=ordinary[0]==r-1
        item['commuting_minimum']=dict(degree=cc[0],mask=cc[1])
        item['noncommuting_minimum']=None if bb is None else dict(
            degree=bb[0],mask=bb[1],factors=factors(u,v,bb[1],*interval))
        candidates.append(item)
    exact=next((x for x in candidates if x['exact']),None)
    return dict(u=u,v=v,w=w,degree=r,first_minimum_mask=first,selected_minimum_mask=mask,
                chosen_exchange=exact,candidates=candidates,
                status='degree_one' if r==1 else 'exact_predecessor' if exact else
                       'first_mask_failure' if mask==first else 'selected_mask_failure',
                index_convention='zero-based, half-open')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('u');p.add_argument('v');p.add_argument('w')
    p.add_argument('--mask',help='Inspect this minimum mask instead of the first one.')
    args=p.parse_args()
    if not args.u or not args.v:p.error('Both source words must be nonempty.')
    print(json.dumps(inspect(args.u,args.v,args.w,args.mask),indent=2))
