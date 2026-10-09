"""Independently enumerate all masks and verify the new obstruction examples."""
import json
from itertools import groupby, combinations
from pathlib import Path
from verify import masks, moves, degree, count_runs
from canonical import inspect, optimal


def verify_case(u, v, w, selected=None):
    classes = masks(u, v)
    rows = classes[w]
    r = min(k for _, k in rows)
    minimum = sorted(m for m, k in rows if k == r)
    assert degree(u, v, w) == r
    chosen = minimum[0] if selected is None else selected
    assert chosen in minimum
    report = inspect(u, v, w, chosen)
    assert report['first_minimum_mask'] == minimum[0]
    for move in report['candidates']:
        z = move['word']
        d = min(k for _, k in classes[z])
        assert d == degree(u, v, z) == move['degree']
        lo, mid, hi = move['begin'], move['mid'], move['end']
        constrained = {True: [], False: []}
        for m, k in classes[z]:
            def projected(source, start, end):
                return ''.join(c for c, q in zip(z[start:end], m[start:end]) if q == source)
            commuting = all(projected(q, lo, mid) + projected(q, mid, hi)
                            == projected(q, mid, hi) + projected(q, lo, mid)
                            for q in 'UV')
            constrained[commuting].append(k)
        assert min(constrained[True]) == move['commuting_minimum']['degree'] == r - 1
        noncommuting = move['noncommuting_minimum']
        assert (min(constrained[False]) if constrained[False] else None) == (
            noncommuting['degree'] if noncommuting else None)
    exact = []
    for m in minimum:
        for lo, cut, hi, z in moves(w, m):
            d = min(k for _, k in classes[z])
            assert d == degree(u, v, z)
            if d == r - 1:
                exact.append(dict(source_mask=m, begin=lo, cut=cut, end=hi, word=z))
    return dict(u=u, v=v, w=w, degree=r, total_masks=len(rows),
                minimum_masks=minimum, selected_mask=chosen,
                selected_degrees=[x['degree'] for x in report['candidates']],
                exact_moves=len(exact))


def main():
    first = verify_case('ABAABAABAAB', 'ABABAAB', 'ABABAAABABABAAABAB')
    assert first['degree'] == 4 and first['total_masks'] == 36
    assert len(first['minimum_masks']) == 16 and first['selected_degrees'] == [2] * 6
    assert first['exact_moves'] == 24
    last = verify_case('ABABABBABAB', 'ABABABBAB', 'ABABABBABAABBABABABB',
                       'UUUUUUUVVVUUVVVUVVVU')
    assert last['degree'] == 4 and last['total_masks'] == 8
    assert len(last['minimum_masks']) == 2
    assert last['selected_mask'] == last['minimum_masks'][-1]
    assert last['selected_degrees'] == [2]*6 and last['exact_moves'] == 1
    for q in range(1, 41):
        u, v, w = first['u'], first['v'] + 'A'*q, first['w'] + 'A'*q
        m = first['selected_mask'] + 'V'*q
        assert optimal(u, v, w) == (4, m)
        assert all(degree(u, v, z) == 2 for _, _, _, z in moves(w, m))
    packed = verify_case('ABBAABBA', 'ABBABABBA', 'ABBABABABABABABBA',
                         'VVVUUVUUVUUVUUVVV')
    assert packed['degree'] == 4 and packed['total_masks'] == 8
    assert len(packed['minimum_masks']) == 8 and packed['selected_degrees'] == [2] * 6
    w, m = packed['w'], packed['selected_mask']
    boundaries = [0] + [i for i in range(1, len(m)) if m[i] != m[i-1]] + [len(m)]
    for h in range(len(boundaries)-2):
        a, b, c = boundaries[h:h+3]
        if m[a] != 'V':
            continue
        p, q = w[a:b], w[b:c]
        assert not (len(p) > len(q) and p.endswith(q))
        assert not (h == 0 and p == q)
        assert not (h > 0 and len(p) < len(q) and q.startswith(p))
    ends = verify_case('01201Y34534', '201XZ345', '02101201XYZ34534354')
    assert ends['degree'] == 7
    assert ends['selected_degrees'] == [5,5,6,6,6,6,6,6,6,6,5,5]
    family_branches = 0
    for line in Path('certificates/symbolic3-26-bad.jsonl').read_text().splitlines():
        x = json.loads(line)
        u, v, w, m = x['u'], x['v'], x['w'], x['mask']
        assert count_runs(m) == degree(u, v, w) == 3
        moved = [z for _, _, _, z in moves(w, m)]
        assert all(degree(u, v, z) == 1 for z in moved)
        assert moved[0] == moved[1] and moved[2] == moved[3]
        blocks = [(label, ''.join(c for c, _ in letters))
                  for label, letters in groupby(zip(w, m), key=lambda t: t[1])]
        start = next(i for i, (label, _) in enumerate(blocks) if label == 'U')
        a, p, b, q, c = [word for _, word in blocks[start:start+5]]
        assert all(s+t == t+s for s, t in combinations([p, q, a+b, b+c], 2))
        family_branches += 1
    assert family_branches == 305
    result = dict(first_mask=first, last_mask=last, whole_factor_shift=packed, both_end_separators=ends,
                  degree_three_bad_branches_dp_checked=family_branches,
                  degree_three_period_observations_checked=family_branches,
                  binary_first_mask_padding_instances=40)
    Path('results/verification-examples.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
