#!/usr/bin/env python3
"""Independent finite checks for Hughes v3; Python standard library only.

Matching masks are found by testing every U-position combination against both
source projections. No producer or previous audit module is imported.
Run: python3 check_small.py [--tex path/to/paper.tex]
"""
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import platform
import re
import time


def runs(mask):
    return sum(q == 'U' and (i == 0 or mask[i-1] == 'V')
               for i, q in enumerate(mask))


@lru_cache(maxsize=None)
def masks(u, v, w):
    if len(w) != len(u) + len(v):
        return ()
    found = []
    for positions in combinations(range(len(w)), len(u)):
        if ''.join(w[i] for i in positions) != u:
            continue
        selected = set(positions)
        if ''.join(c for i, c in enumerate(w) if i not in selected) != v:
            continue
        found.append(''.join('U' if i in selected else 'V'
                             for i in range(len(w))))
    return tuple(sorted(found))


def degree(u, v, w):
    mm = masks(u, v, w)
    return min(map(runs, mm), default=float('inf'))


def exchanges(w, mask):
    blocks = []
    for match in re.finditer(r'U+|V+', mask):
        blocks.append((match.start(), match.end(), match[0][0]))
    separator = 0
    for k, (a, b, q) in enumerate(blocks):
        if q != 'V' or k == 0 or k == len(blocks)-1:
            continue
        separator += 1
        for direction, lo, mid, hi in (
                ('L', blocks[k-1][0], a, b),
                ('R', a, b, blocks[k+1][1])):
            z = w[:lo] + w[mid:hi] + w[lo:mid] + w[hi:]
            transported = (mask[:lo] + mask[mid:hi] +
                           mask[lo:mid] + mask[hi:])
            yield dict(separator=separator, direction=direction, bounds=[lo,mid,hi],
                       separator_length=b-a, word=z, transported=transported)


def case(u, v, w, selected=None):
    mm = masks(u, v, w)
    d = degree(u, v, w)
    minima = [x for x in mm if runs(x) == d]
    chosen = selected or minima[0]
    assert chosen in minima, (u, v, w, chosen)
    moves = []
    for move in exchanges(w, chosen):
        z = move['word']
        move['degree'] = degree(u, v, z)
        move['minimum_masks'] = [x for x in masks(u, v, z)
                                 if runs(x) == move['degree']]
        move['all_masks'] = list(masks(u, v, z))
        move['contiguous_u_remainders'] = [
            z[:i]+z[i+len(u):] for i in range(len(v)+1)
            if z[i:i+len(u)] == u]
        assert move['transported'] in masks(u, v, z)
        assert runs(move['transported']) == d-1
        moves.append(move)
    return dict(u=u, v=v, w=w, degree=d, masks=list(mm),
                mask_runs=[runs(x) for x in mm], first=minima[0], last=minima[-1],
                selected=chosen, moves=moves)


def emit(u, v, mask):
    i = j = 0
    output = []
    for q in mask:
        if q == 'U':
            output.append(u[i]); i += 1
        else:
            output.append(v[j]); j += 1
    return ''.join(output)


def transfer(u, v, segment, start):
    """Literal DP on (i,j,previous_label), including an empty segment."""
    dp = {start: 0}
    for letter in segment:
        nxt = {}
        for (i,j,p), cost in dp.items():
            if i < len(u) and u[i] == letter:
                target = (i+1,j,'U')
                nxt[target] = min(nxt.get(target, float('inf')), cost+(p=='V'))
            if j < len(v) and v[j] == letter:
                target = (i,j+1,'V')
                nxt[target] = min(nxt.get(target, float('inf')), cost)
        dp = nxt
    return dp


def constrained_dp(u, v, z, bounds):
    lo, mid, hi = bounds
    # In z the exchanged B precedes A: the B-end is lo+(hi-mid).
    t1 = lo + hi-mid
    answer = float('inf')
    for s0, f in transfer(u,v,z[:lo],(0,0,'V')).items():
        for s1, tb in transfer(u,v,z[lo:t1],s0).items():
            for s2, ta in transfer(u,v,z[t1:hi],s1).items():
                bu, au = u[s0[0]:s1[0]], u[s1[0]:s2[0]]
                bv, av = v[s0[1]:s1[1]], v[s1[1]:s2[1]]
                if au+bu == bu+au and av+bv == bv+av:
                    continue
                for end, g in transfer(u,v,z[hi:],s2).items():
                    if end[:2] == (len(u),len(v)):
                        answer = min(answer, f+tb+ta+g)
    return answer


def check_core(bound=6):
    totals = Counter()
    for length in range(2,bound+1):
        for m in range(1,length):
            for letters in product('01', repeat=length):
                u = ''.join(letters[:m]); v = ''.join(letters[m:])
                outputs = defaultdict(list)
                for positions in combinations(range(length),m):
                    selected = set(positions)
                    mm = ''.join('U' if t in selected else 'V' for t in range(length))
                    outputs[emit(u,v,mm)].append(mm)
                for w, original_masks in outputs.items():
                    assert set(original_masks) == set(masks(u,v,w))
                    d = min(map(runs,original_masks))
                    assert degree(u,v,w) == d
                    for source, other, reverse in [(u,v,False),(v,u,True)]:
                        if len(set(source)) != 1:
                            continue
                        a = source[0]
                        source_gaps = re.split('[^'+re.escape(a)+']',other)
                        output_gaps = re.split('[^'+re.escape(a)+']',w)
                        assert len(source_gaps) == len(output_gaps)
                        inserted = [len(x)-len(y) for x,y in zip(output_gaps,source_gaps)]
                        assert all(x>=0 for x in inserted) and sum(inserted)==len(source)
                        expected = (1+sum(x>0 for x in inserted[1:-1]) if reverse
                                    else sum(x>0 for x in inserted))
                        assert d == expected
                        totals['unary_gap_formula_checks'] += 1
                    end = transfer(u,v,w,(0,0,'V'))
                    assert min(c for s,c in end.items()
                               if s[:2] == (len(u),len(v))) == d
                    totals['outputs'] += 1
                    for mm in original_masks:
                        if runs(mm) != d or d == 1:
                            continue
                        for move in exchanges(w,mm):
                            lo,mid,hi = move['bounds']; z = move['word']
                            commuting, noncommuting = [], []
                            for nn in masks(u,v,z):
                                pull = nn[:lo]+nn[lo+hi-mid:hi]+nn[lo:lo+hi-mid]+nn[hi:]
                                au = ''.join(c for c,q in zip(z[lo+hi-mid:hi],nn[lo+hi-mid:hi]) if q=='U')
                                bu = ''.join(c for c,q in zip(z[lo:lo+hi-mid],nn[lo:lo+hi-mid]) if q=='U')
                                av = ''.join(c for c,q in zip(z[lo+hi-mid:hi],nn[lo+hi-mid:hi]) if q=='V')
                                bv = ''.join(c for c,q in zip(z[lo:lo+hi-mid],nn[lo:lo+hi-mid]) if q=='V')
                                commutes = au+bu == bu+au and av+bv == bv+av
                                assert (pull in original_masks) == commutes
                                assert abs(runs(pull)-runs(nn)) <= 1
                                (commuting if commutes else noncommuting).append(runs(nn))
                                totals['alternative_masks'] += 1
                            c = min(commuting,default=float('inf'))
                            b = min(noncommuting,default=float('inf'))
                            assert c == d-1 and degree(u,v,z) == min(d-1,b)
                            assert constrained_dp(u,v,z,move['bounds']) == b
                            totals['criterion_and_constrained_dp_exchanges'] += 1
                            if len(set(u)) == 1 or len(set(v)) == 1:
                                assert degree(u,v,z) == d-1
                                totals['unary_exchanges'] += 1
    # Empty prefixes/suffixes/transfer segments are exercised above; explicitly
    # check that the empty segment preserves every state with cost zero.
    for i in range(3):
        for j in range(3):
            for p in 'UV':
                assert transfer('01','10','',(i,j,p)) == {(i,j,p):0}
    totals['empty_segment_states'] = 18
    distribution = Counter()
    for ell,a,alpha,b,beta,t in product([0,1],repeat=6):
        diff=(1-ell)*(a-b)+(1-alpha)*(b-t)+(1-beta)*(t-a)
        assert diff in [-1,0,1]
        distribution[diff] += 1
    assert distribution == {-1:12,0:40,1:12}
    totals['boundary_assignments'] = sum(distribution.values())
    return dict(totals)


def verify_tex_tables(tex, data):
    checked = Counter()
    words = lambda line: re.findall(r'\\ttw\{([^{}]*)\}',
                    re.sub(r'\\hspace\{[^{}]*\}', '', line))
    def lines(label):
        start = tex.index('\\label{'+label+'}')
        end = tex.index('\\end{table}',start)
        return tex[start:end].splitlines()
    u,v,w = '01010','01010101','0010110011010'
    for line in lines('tab:masks'):
        entries = words(line)
        for mm in entries:
            if set(mm) <= {'U','V'}:
                assert mm in masks(u,v,w)
                match = re.search(re.escape(mm)+r'\}&(\d)',line)
                assert match and runs(mm)==int(match[1])
                checked['table1_masks'] += 1
    specs = [('tab:successors','01010','01010101'),
             ('tab:firstfailure','ABAABAABAAB','ABABAAB'),
             ('tab:lastfailure','ABABABBABAB','ABABABBAB')]
    for label,u,v in specs:
        for line in lines(label):
            entries = words(line)
            if len(entries)<2 or set(entries[1]) - {'U','V'}:
                continue
            z, mm = entries[:2]
            assert mm in masks(u,v,z) and runs(mm)==2 and degree(u,v,z)==2
            if label=='tab:successors':
                remainders = [z[:i]+z[i+len(u):] for i in range(len(v)+1)
                              if z[i:i+len(u)]==u]
                assert remainders == entries[2:]
                checked['table2_remainders'] += len(remainders)
            checked[label+'_witness_rows'] += 1
    for label,keys in [('tab:lastcert',['last','last_exact_successor']),
                       ('tab:packedcert',['packed','packed_exact_successor'])]:
        literal = []
        for line in lines(label):
            literal += [(mm,int(n)) for mm,n in
                        re.findall(r'\\ttw\{([UV]+)\}\s*&\s*(\d+)',line)]
        expected = [(mm,n) for key in keys
                    for mm,n in zip(data[key]['masks'],data[key]['mask_runs'])]
        assert literal == expected, label
        checked[label+'_complete_mask_entries'] = len(literal)
    for line in lines('tab:packedmoves'):
        entries = words(line)
        if len(entries)==2:
            z,mm = entries
            assert mm in masks('ABBAABBA','ABBABABBA',z)
            assert degree('ABBAABBA','ABBABABBA',z)==runs(mm)==2
            checked['packed_successor_rows'] += 1
    rule_tex = '\n'.join(lines('tab:rules'))
    for c in data['rules'].values():
        exact = next(x for x in c['moves'] if x['degree']==2)
        for token in [c['u'],c['v'],c['w'],c['first'],exact['word'],exact['minimum_masks'][0]]:
            assert r'\ttw{'+token+'}' in rule_tex
        assert not exact['contiguous_u_remainders']
        checked['separator_rule_rows'] += 1
    return dict(checked)


def check_prefix_counts():
    """Reconstruct the 168 failed adjacent candidates from binary masks."""
    failed = []
    for length in [8,9]:
        for m in range(1,length):
            label_masks = []
            for positions in combinations(range(length),m):
                selected = set(positions)
                mm = ''.join('U' if t in selected else 'V' for t in range(length))
                label_masks.append((mm,runs(mm)))
            for letters in product('01',repeat=length):
                u,v = ''.join(letters[:m]),''.join(letters[m:])
                grouped = defaultdict(list)
                for mm,r in label_masks:
                    grouped[emit(u,v,mm)].append((mm,r))
                degrees = {w:min(r for mm,r in arr) for w,arr in grouped.items()}
                for w,arr in grouped.items():
                    if degrees[w]!=3:
                        continue
                    candidate_positions = set()
                    for mm,r in arr:
                        if r!=3:
                            continue
                        for i in range(length-1):
                            if w[i]==w[i+1] or mm[i]==mm[i+1]:
                                continue
                            changed=mm[:i]+mm[i+1]+mm[i]+mm[i+2:]
                            if runs(changed)==2:
                                candidate_positions.add(i)
                    def swapped(i):
                        return w[:i]+w[i+1]+w[i]+w[i+2:]
                    failures = [i for i in candidate_positions if degrees[swapped(i)]==1]
                    if not failures:
                        continue
                    assert len(failures)==1
                    assert set(masks(u,v,w))=={mm for mm,r in arr}
                    successful = [i for i in candidate_positions if degrees[swapped(i)]==2]
                    exact = [i for i in range(length-1) if w[i]!=w[i+1]
                             and swapped(i) in degrees and degrees[swapped(i)]==2]
                    def profile_certified(i):
                        z=swapped(i)
                        for cut in range(i+2,length):
                            old=transfer(u,v,w[:cut],(0,0,'V'))
                            new=transfer(u,v,z[:cut],(0,0,'V'))
                            if all(new.get(s,float('inf')) >= old.get(s,float('inf'))-1
                                   for s in old.keys() | new.keys()):
                                return True
                        return False
                    failed.append(dict(u=u,v=v,w=w,failed_position=failures[0]+1,
                                       successful_positions=[i+1 for i in successful],
                                       exact_positions=[i+1 for i in exact],
                                       successful_profile=any(profile_certified(i) for i in successful),
                                       ordinary_profile=any(profile_certified(i) for i in exact)))
    counts = dict(failed_triples=len(failed),
                  with_successful_candidate=sum(bool(x['successful_positions']) for x in failed),
                  successful_profile=sum(x['successful_profile'] for x in failed),
                  without_successful_candidate=sum(not x['successful_positions'] for x in failed),
                  ordinary_profile_without_candidate=sum(x['ordinary_profile'] for x in failed
                                                         if not x['successful_positions']))
    assert counts == dict(failed_triples=168,with_successful_candidate=116,
                          successful_profile=94,without_successful_candidate=52,
                          ordinary_profile_without_candidate=52), counts
    return dict(counts=counts,triples=failed)


def main():
    start = time.monotonic()
    result = {'method':'all U-position combinations; both projections checked',
              'python':platform.python_version(),
              'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    result['proposition5'] = case('01010','01010101','0010110011010','UVVVVUVUUVVVU')
    assert len(result['proposition5']['masks'])==16
    assert result['proposition5']['degree']==4
    assert [x['degree'] for x in result['proposition5']['moves']]==[2]*6
    result['proposition5_first'] = case('01010','01010101','0010110011010')
    assert any(x['degree']==3 for x in result['proposition5_first']['moves'])
    result['rules'] = {}
    inputs = dict(First=('011001','1001','0101011001'),
                  Last=('01201','012','01201021'),
                  Shortest=('0011001','0011','00110010101'),
                  Longest=('0101010','010','0100110010'))
    for rule, args in inputs.items():
        c = case(*args); assert c['degree']==3
        sizes = {x['separator']:x['separator_length'] for x in c['moves']}
        if rule=='First': chosen=[min(sizes)]
        elif rule=='Last': chosen=[max(sizes)]
        elif rule=='Shortest': chosen=[i for i,n in sizes.items() if n==min(sizes.values())]
        else: chosen=[i for i,n in sizes.items() if n==max(sizes.values())]
        assert all(x['degree']==1 for x in c['moves'] if x['separator'] in chosen)
        assert any(x['degree']==2 for x in c['moves'])
        c['selected_separators']=chosen
        result['rules'][rule]=c
    result['proposition7'] = case('ABAABAABAAB','ABABAAB','ABABAAABABABAAABAB')
    c = result['proposition7']; assert c['degree']==4 and len(c['masks'])==36
    assert Counter(c['mask_runs'])=={4:16,5:16,6:4}
    assert c['first']=='UUVVVUUUUVUUUUVUVV'
    assert [x['degree'] for x in c['moves']]==[2]*6
    prefixes = ['UUVVUUVUUV','UUVVUVUUUV','UUVVVUUUUV','VVUUUUVUUV','VVUUUVUUUV','VVUUVUUUUV']
    suffixes = ['UUUUVUVV','UUUVUUVV','UUUVVVUU','UUVUUUVV','UUVUVVUU','UUVVUVUU']
    assert set(c['masks'])=={p+s for p in prefixes for s in suffixes}
    assert degree(c['u'],c['v'],'ABABAAABAABABAABAB')==3
    result['proposition7_other'] = case(c['u'],c['v'],c['w'],'UUVVVUUUUVUUUVUUVV')
    result['last'] = case('ABABABBABAB','ABABABBAB','ABABABBABAABBABABABB',
                          'UUUUUUUVVVUUVVVUVVVU')
    c = result['last']; assert len(c['masks'])==8 and Counter(c['mask_runs'])=={5:6,4:2}
    assert [x['degree'] for x in c['moves']]==[2]*6
    result['last_first'] = case(c['u'],c['v'],c['w'])
    assert sum(x['degree']==3 for x in result['last_first']['moves'])==1
    result['last_exact_successor'] = case(c['u'],c['v'],'ABABABBABAABBABBAABB')
    assert result['last_exact_successor']['degree']==3
    result['packed'] = case('ABBAABBA','ABBABABBA','ABBABABABABABABBA','VVVUUVUUVUUVUUVVV')
    c = result['packed']; assert len(c['masks'])==8 and c['mask_runs']==[4]*8
    assert [x['degree'] for x in c['moves']]==[2]*6
    # Whole-factor shifts forbidden in the stated mask, including leading V.
    blocks = [(m[0][0],c['w'][m.start():m.end()]) for m in re.finditer(r'U+|V+',c['selected'])]
    for (q,p),(qq,b) in zip(blocks,blocks[1:]):
        if q=='V' and qq=='U':
            assert not (len(p)>len(b) and p.endswith(b))
            assert not (len(b)>len(p) and b.startswith(p))
    result['packed_first'] = case(c['u'],c['v'],c['w'])
    assert any(x['word']=='ABABBABABABABABBA' and x['degree']==3
               for x in result['packed_first']['moves'])
    result['packed_exact_successor'] = case(c['u'],c['v'],'ABABBABABABABABBA')
    assert result['packed_exact_successor']['degree']==3
    # Check the fresh terminal-letter reduction directly for every original mask.
    assert masks(c['u'],c['v']+'C',c['w']+'C')==tuple(mm+'V' for mm in c['masks'])
    result['both_ends'] = case('01201Y34534','201XZ345','02101201XYZ34534354')
    c = result['both_ends']; assert c['degree']==7 and c['first']=='UVUVVUUUVUVUUUVVUVU'
    assert [x['degree'] for x in c['moves']]==[5,5]+[6]*8+[5,5]
    result['left_gadget']=case('01201','201','02101201')
    result['right_gadget']=case('34534','345','34534354')
    result['family'] = []
    for k in range(2,5):
        for ell in range(2,5):
            u,v,w='ABABA','ABA'*(k+ell),'AB'+'ABA'*k+'A'+'ABA'*ell+'BA'
            c=case(u,v,w,'UU'+'V'*(3*k)+'U'+'V'*(3*ell)+'UU')
            assert len(c['masks'])==12 and c['mask_runs']==[3]*12
            assert [x['word'] for x in c['moves']]==[v+u,v+u,u+v,u+v]
            assert [x['degree'] for x in c['moves']]==[1]*4
            assert c['first']=='UU'+'V'*(3*k-1)+'U'+'V'*(3*ell-1)+'UU'+'VV'
            z='ABA'*(k-1)+'ABABAA'+'ABA'*ell+'BA'
            assert degree(u,v,z)==2
            result['family'].append(dict(k=k,ell=ell,masks=c['masks'],first=c['first'],exact=z))
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--tex', type=Path, help='Optional external manuscript for literal table validation')
    args = parser.parse_args()
    result['literal_tables'] = (verify_tex_tables(args.tex.read_text(), result)
                                if args.tex else {'external_tex_check': 'not requested'})
    result['core_binary_through6'] = check_core()
    result['prefix_profile'] = check_prefix_counts()
    result['elapsed_seconds'] = round(time.monotonic()-start,3)
    Path('results').mkdir(exist_ok=True)
    Path('results/small-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PASS','literal_tables':result['literal_tables'],
                      'core':result['core_binary_through6'],
                      'prefix_profile':result['prefix_profile']['counts'],
                      'elapsed_seconds':result['elapsed_seconds']},indent=2))


if __name__=='__main__':
    main()
