#!/usr/bin/env python3
"""Check completed ranges, sums, input combinatorics and manuscript totals.

This checks archive consistency; it does not rerun the large searches.
"""
from pathlib import Path
from math import comb
import json


def rows(name):
    return [json.loads(line) for line in (Path('logs')/name).read_text().splitlines()
            if line.startswith('{')]


def symbolic(names, lengths, degree=None, expected=None):
    data = [row for name in names for row in rows(name)]
    assert [row['length'] for row in data] == list(lengths)
    for row in data:
        r = degree or row.get('degree', 3)
        assert row['masks'] == comb(row['length']+1, 2*r)
    total = {key: sum(row[key] for row in data) for key in ('masks','nodes','bad')}
    if expected is not None:
        assert tuple(total[k] for k in ('masks','nodes','bad')) == expected
    return total


def main():
    report = {}
    summary = json.loads(Path('results/SUMMARY.json').read_text())
    expected = {
        'binary_full': (1835012, 415262716),
        'ternary_full8': (63972, 726198),
        'ternary_modulo_renaming': (1395066, 135331916),
        'four_modulo_renaming': (508982, 24145502),
    }
    for key, totals in expected.items():
        data = summary[key]
        assert (data['pairs'],data['higher']) == totals
        assert data['rules']['first_mask_any']['failed'] == 0
        assert data['rules']['last_mask_any']['failed'] == 0
    # Input counts are checked separately from the output-count sums.
    for names, q, modulo, bound in (
        (['binary13.log','binary14.log','binary15.log','binary16.log'],2,False,16),
        (['ternary8.log'],3,False,8),
        (['quaternary8.log','quaternary10.log'],4,True,10),
    ):
        data = [row for name in names for row in rows(name)]
        assert [x['length'] for x in data] == list(range(2,bound+1))
        stirling=[1]+[0]*q
        pattern_counts={}
        for length in range(1,bound+1):
            stirling=[0]+[k*stirling[k]+stirling[k-1] for k in range(1,q+1)]
            pattern_counts[length]=sum(stirling)
        for row in data:
            length=row['length']
            assert row['pairs'] == (length-1)*(pattern_counts[length] if modulo else q**length)
    report['numerical_domains'] = {k:dict(pairs=v[0],higher=v[1]) for k,v in expected.items()}
    total16={'masks':0,'nodes':0,'bad':0}
    for degree in range(3,9):
        total=symbolic([f'symbolic{degree}-16.log'],range(2*degree-1,17),degree)
        for key in total16: total16[key]+=total[key]
    assert tuple(total16.values()) == (121670,2306288203,0)
    report['first_all_degrees_through16']=total16
    data17=[x for x in rows('symbolic3-30.log') if x['length']==17]
    data17 += [x for r in range(4,10) for x in rows(f'memo{r}-17.log')]
    assert sorted(x['degree'] for x in data17) == list(range(3,10))
    total17={key:sum(x[key] for x in data17) for key in total16}
    assert tuple(total17.values()) == (127858,6254062825,0)
    report['first_all_degrees_exact17']=total17
    for name,r,length,totals in (
        ('memo4-18.log',4,18,(75582,279632995,1)),
        ('memo5-18.log',5,18,(92378,8962639586,0)),
        ('last4-19.log',4,19,(125970,532910127,0)),
        ('last4-20.log',4,20,(203490,1212060756,1)),
    ):
        report[name]=symbolic([name],[length],r,totals)
    report['first_degree3_through30']=symbolic(['symbolic3-16.log','symbolic3-30.log'],
        range(5,31),3,(3365856,139406910,0))
    report['arbitrary_degree3_through26']=symbolic(['symbolic3-26.log'],
        range(5,27),3,(1184040,69396022,305))
    report['arbitrary_degree3_through30']=symbolic(['fresh3-30.log'],
        range(5,31),3,(3365856,266866735,1512))
    earlier=rows('symbolic3-26.log'); current=rows('fresh3-30.log')
    for a,b in zip(earlier,current):
        assert all(a[k]==b[k] for k in ('length','masks','nodes','bad','total_masks','total_nodes','total_bad'))
    def witnesses(name):
        return [json.loads(line) for line in (Path('certificates')/name).read_text().splitlines()]
    a=witnesses('symbolic3-26-bad.jsonl');b=witnesses('fresh3-30-bad.jsonl')
    normalized=lambda x:(x['u'],x['v'],x['w'],x['mask'],tuple(x['cuts']))
    assert sorted(map(normalized,a))==sorted(normalized(x) for x in b if len(x['w'])<=26)
    assert len(a)==305 and len(b)==1512
    assert len({normalized(x)[:4] for x in a})==221
    assert len({normalized(x)[:4] for x in b})==896
    c=json.loads(Path('results/coarsening-summary.json').read_text())
    assert (c['instances'],c['coarsenings'],c['degree_three_coarsenings']) == (221,8110169,6702697)
    assert c['degree_counts']=={'1':1407472,'2':0,'3':6702697}
    report['full_identifications']=c
    structured=rows('structured-audit.log')[-1]
    assert structured['complete'] is True
    assert tuple(structured[k] for k in ('pairs','outputs','higher','degree_three_outputs',
            'degree_three_minimum_masks','bad_degree_three_masks')) == (70710,20001166,19443384,8861068,33306824,0)
    first=rows('factor22.log')[-1]
    assert tuple(first[k] for k in ('pairs','outputs','higher','bad_first','bad_last')) == (70710,20001166,19443384,0,0)
    report['structured']=structured
    report['status']='PASS'
    Path('results/archive-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','checks':len(report),'scope':'archive ranges, arithmetic, input combinatorics and leaf matching'},indent=2))


if __name__=='__main__': main()
