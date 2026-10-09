#!/usr/bin/env python3
"""Compare the documented finite reruns with completed archived outputs."""
from pathlib import Path
import json


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()
            if line.startswith('{')]


def comparable(row):
    return {k:v for k,v in row.items() if k not in ('elapsed','elapsed_seconds')}


def compare(actual, expected, limit=None):
    a=rows(actual); b=rows(expected)
    if limit is not None: b=[x for x in b if x['length']<=limit]
    assert [comparable(x) for x in a] == [comparable(x) for x in b], (actual,expected)
    return dict(status='PASS',rows=len(a))


def main():
    report={}
    for actual,expected,limit in (
        ('runs/independent-symbolic20.log','logs/independent-symbolic20.log',None),
        ('runs/smoke-binary6.log','logs/binary13.log',6),
        ('runs/smoke-first3.log','logs/symbolic3-16.log',9),
        ('runs/smoke-memo3.log','logs/memo3-9.log',None),
        ('runs/smoke-last3.log','logs/last3-9.log',None),
        ('runs/smoke-arbitrary3.log','logs/symbolic3-26.log',20),
        ('runs/smoke-fresh3.log','logs/fresh3-30.log',20),
    ):
        report[actual]=compare(actual,expected,limit)
    structured=rows('runs/structured-audit.log')[-1]
    assert comparable(structured)==comparable(rows('logs/structured-audit.log')[-1])
    report['structured']=dict(status='PASS',pairs=structured['pairs'],outputs=structured['outputs'],
                              degree_three_minimum_masks=structured['degree_three_minimum_masks'])
    a=json.loads(Path('runs/coarsening-summary.json').read_text())
    b=json.loads(Path('results/coarsening-summary.json').read_text())
    assert comparable(a)==comparable(b)
    report['coarsenings']=dict(status='PASS',combinations=a['coarsenings'])
    normalize=lambda x:(tuple(x['classes']),x['m'],x['mask'],tuple(x['cuts']))
    a=rows('runs/independent-leaves.jsonl');b=rows('certificates/independent-leaves.jsonl')
    assert sorted(map(normalize,a))==sorted(map(normalize,b))
    report['independent_leaves']=dict(status='PASS',tuples=len(a))
    for name in ('smoke-arbitrary3','smoke-fresh3'):
        normalize=lambda x:(x['u'],x['v'],x['w'],x['mask'],tuple(x['cuts']))
        a=rows(f'runs/{name}-bad.jsonl'); b=rows('certificates/fresh3-30-bad.jsonl')
        b=[x for x in b if len(x['w'])<=20]
        assert sorted(map(normalize,a))==sorted(map(normalize,b))
        report[name+'_leaves']=dict(status='PASS',tuples=len(a))
    report['status']='PASS'
    Path('results/revision-runs.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
