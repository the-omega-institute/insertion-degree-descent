#!/usr/bin/env python3
"""Independent review checker of every supplied leaf and identification cut.
This does not establish generation completeness above length twenty.
"""
from collections import Counter
from pathlib import Path
import json, math
from independent_core import project, count_runs, emit, enumerate_feasible, degree, block_ranges, all_exchanges, shift_middle
HERE = Path(__file__).resolve().parent
REPORT = {}
def normalize(word):
    names = {}
    return tuple(names.setdefault(c, len(names)) for c in word)


def check_symbolic_and_certificates():
    fresh = [json.loads(row) for row in (HERE / 'logs/independent-symbolic20.log').read_text().splitlines()]
    archived = [json.loads(row) for row in (HERE / 'logs/fresh3-30.log').read_text().splitlines()]
    assert [x['length'] for x in fresh] == list(range(5,21))
    assert [x['length'] for x in archived] == list(range(5,31))
    for actual, expected in zip(fresh, archived):
        for field in ('length', 'masks', 'nodes', 'pruned', 'bad', 'total_masks', 'total_nodes', 'total_bad'):
            assert actual[field] == expected[field], (field, actual, expected)
        assert actual['masks'] == math.comb(actual['length'] + 1, 6)
    leaves = [json.loads(row) for row in (HERE / 'certificates/independent-leaves.jsonl').read_text().splitlines()]
    author_rows = [json.loads(row) for row in (HERE / 'certificates/fresh3-30-bad.jsonl').read_text().splitlines()]
    ours = set()
    for row in leaves:
        m = row['m']
        source = ''.join(chr(65 + root) for root in row['classes'])
        u, v = source[:m], source[m:]
        w = emit(u, v, row['mask'])
        ours.add((normalize(source), m, row['mask'], tuple(row['cuts'])))
        masks = enumerate_feasible(u, v, w)
        assert min(map(count_runs, masks)) == 3
        N = shift_middle(w, row['mask'])
        assert [min(map(count_runs, enumerate_feasible(u, v, z)))
                for z, _, _ in all_exchanges(w, N)] == [2, 1, 1, 2]
    expected = {(normalize(row['u'] + row['v']), len(row['u']), row['mask'], tuple(row['cuts']))
                for row in author_rows if len(row['w']) <= 20}
    assert ours == expected and len(ours) == 12
    # Check the cut choices in every tuple, including duplicate instances
    # recorded with different witness choices.
    for row in author_rows:
        u, v, w, mask = (row[key] for key in ('u', 'v', 'w', 'mask'))
        assert project(w, mask) == (u, v) and count_runs(mask) == 3
        moves = all_exchanges(w, mask)
        assert len(moves) == len(row['cuts']) == 4
        for (z, _, _), cut in zip(moves, row['cuts']):
            assert 0 <= cut <= len(v)
            assert z == v[:cut] + u + v[cut:]
    instances = {(row['u'], row['v'], row['w'], row['mask']): row for row in author_rows}
    witness_cuts = 0
    vectors = Counter()
    # Independently check every supplied leaf, and the finite coarsening
    # argument by checking every one-run cut of the two proposed exact moves.
    for (u, v, w, mask), row in instances.items():
        assert project(w, mask) == (u, v) and count_runs(mask) == degree(u, v, w) == 3
        old = all_exchanges(w, mask)
        for (z, _, _), cut in zip(old, row['cuts']):
            assert z == v[:cut] + u + v[cut:]
        inner = [w[start:end] for _, start, end in block_ranges(mask)]
        first = next(t for t, entry in enumerate(block_ranges(mask)) if entry[0] == 'U')
        a, P, b, Q, c = inner[first:first + 5]
        roots = [P[:size] for size in range(1, len(P) + 1)
                 if len(P) % size == 0 and P[:size] * (len(P) // size) == P]
        T = roots[0]
        assert all(len(factor) % len(T) == 0 and T * (len(factor) // len(T)) == factor
                   for factor in (P, Q, a + b, b + c))
        assert len(b) < len(T)
        shifted = all_exchanges(w, shift_middle(w, mask))
        ds = tuple(degree(u, v, z) for z, _, _ in shifted)
        assert ds == (2, 1, 1, 2)
        vectors[ds] += 1
        alphabet = sorted(set(u + v))
        for move in (0, 3):
            z = shifted[move][0]
            for cut in range(len(v) + 1):
                relation = {c: c for c in alphabet}
                def root(c):
                    while relation[c] != c:
                        c = relation[c]
                    return c
                template = v[:cut] + u + v[cut:]
                for left, right in zip(z, template):
                    relation[root(left)] = root(right)
                uu, vv, ww, zz = (''.join(root(c) for c in word) for word in (u, v, w, z))
                assert zz == vv[:cut] + uu + vv[cut:]
                assert degree(uu, vv, ww) <= 2
                witness_cuts += 1
    assert len(author_rows) == 1512 and len(instances) == 896 and witness_cuts == 41244
    REPORT['symbolic_through20'] = dict(final_counts=fresh[-1], independently_generated_leaves=len(leaves),
                                       exact_leaf_match=True, brute_force_shift_checks=len(leaves))
    REPORT['all_supplied30_certificates'] = dict(rows=len(author_rows), distinct_instances=len(instances),
                                                vectors={str(key):value for key,value in vectors.items()},
                                                lower_witnesses=4 * len(author_rows),
                                                coarsening_cuts=witness_cuts)


if __name__ == '__main__':
    check_symbolic_and_certificates()
    REPORT['status'] = 'PASS'
    (HERE/'results/independent-certificates.json').write_text(json.dumps(REPORT,indent=2)+'\n')
    print(json.dumps(REPORT,indent=2))
