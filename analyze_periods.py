#!/usr/bin/env python3
"""Audit every archived degree-three witness and every alphabet coarsening.

Outputs and evidence are written only in this task directory. A branch is a
four-witness tuple, not a distinct source/output/mask instance.
"""
from collections import Counter
from itertools import product
from pathlib import Path
import hashlib
import json
import time
from core import degree, all_masks, runs, projections, blocks, exchanges, primitive, shift_middle_left

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT/'certificates'


def partitions(n):
    def visit(row, largest):
        if len(row) == n:
            yield tuple(row)
        else:
            for q in range(largest+2):
                yield from visit(row+[q], max(q, largest))
    yield from visit([0], 0)


def inspect(x):
    u, v, w, m = (x[k] for k in ('u', 'v', 'w', 'mask'))
    assert projections(w, m) == (u, v)
    assert degree(u, v, w) == runs(m) == 3
    original = list(exchanges(w, m))
    assert len(original) == 4
    assert [degree(u, v, z['word']) for z in original] == [1]*4
    for z, cut in zip(original, x['cuts']):
        assert z['word'][cut:cut+len(u)] == u
        assert z['word'][:cut]+z['word'][cut+len(u):] == v
    bb = blocks(w, m)
    s = next(i for i, z in enumerate(bb) if z[0] == 'U')
    a, p, b, q, c = [z[1] for z in bb[s:s+5]]
    t = primitive(p)
    assert all(z == t*(len(z)//len(t)) for z in (p, q, a+b, b+c))
    assert len(b) < len(t)
    shifted = shift_middle_left(w, m)
    successors = list(exchanges(w, shifted))
    degrees = [degree(u, v, z['word']) for z in successors]
    assert degrees == [2, 1, 1, 2], (x, shifted, degrees)
    return dict(u=u, v=v, w=w, mask=m, cuts=x['cuts'], period=t,
                blocks=dict(a=a, P=p, b=b, Q=q, c=c),
                left_context=w[:bb[s][2]], right_context=w[bb[s+4][3]:],
                shifted_mask=shifted, shifted_successors=[
                    dict(**z, degree=d) for z, d in zip(successors, degrees)])


def main():
    started = time.monotonic()
    src = ARCHIVE/'symbolic3-26-bad.jsonl'
    rows = [inspect(json.loads(line)) for line in src.read_text().splitlines()]
    assert len(rows) == 305
    unique = {(r['u'], r['v'], r['w'], r['mask']): r for r in rows}
    finite_checks = 0
    for u, v, w, m in unique:
        if len(w) <= 20:
            mm = all_masks(u, v, w)
            assert min(map(runs, mm)) == 3
            assert rows and unique[u,v,w,m]['shifted_mask'] in mm
            for z in exchanges(w, unique[u,v,w,m]['shifted_mask']):
                assert degree(u,v,z['word']) == min(map(runs, all_masks(u,v,z['word'])))
            finite_checks += 1
    (ROOT/'certificates/period-certificates.jsonl').write_text(''.join(
        json.dumps(r, sort_keys=True)+'\n' for r in rows))
    (ROOT/'certificates/period-instances.tsv').write_text(''.join(
        '\t'.join((r['u'],r['v'],r['w'],r['mask'],r['shifted_mask']))+'\n'
        for r in unique.values()))
    summary = dict(status='PASS', archived_witness_tuples=len(rows),
                   distinct_source_output_mask_instances=len(unique),
                   archive_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                   shifted_degree_vector=[2,1,1,2],
                   position_combination_cross_checks=finite_checks,
                   maximum_recorded_length=max(len(r['w']) for r in rows),
                   elapsed_seconds=round(time.monotonic()-started,3))
    (ROOT/'results/period-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
