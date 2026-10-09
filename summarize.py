"""Combine completed exact-length logs without double counting."""
import json
from pathlib import Path


def rows(tag):
    path=Path('logs')/(tag+'.log')
    return [json.loads(line) for line in path.read_text().splitlines() if line.startswith('{')] if path.exists() else []


def domain(tags):
    combined=[row for tag in tags for row in rows(tag)]
    assert len({x['length'] for x in combined})==len(combined)
    out=dict(lengths=sorted(x['length'] for x in combined))
    for key in ['pairs','outputs','higher','masks']:
        out[key]=sum(x[key] for x in combined)
    names={k for x in combined for k in x['rules']}
    out['rules']={name:{key:sum(x['rules'].get(name,{}).get(key,0) for x in combined)
                        for key in ['tested','failed']} for name in sorted(names)}
    return out


def main():
    binary=domain(['binary13','binary14','binary15']+(['binary16'] if rows('binary16') else []))
    ternary_full=domain(['ternary8'])
    lower=dict(ternary_full)
    # q=3 has six injective renamings for both 2- and 3-letter patterns;
    # the one-letter pattern has three. All higher-degree cases use >=2.
    lower['pairs']=(lower['pairs']+3*28)//6
    lower['outputs']=(lower['outputs']+3*28)//6
    lower['masks']=(lower['masks']+3*494)//6
    lower['higher']//=6
    lower['rules']={name:{key:value//6 for key,value in data.items()} for name,data in lower['rules'].items()}
    extension=domain(['ternary10','ternary12'])
    ternary=dict(lengths=lower['lengths']+extension['lengths'])
    for key in ['pairs','outputs','higher','masks']:ternary[key]=lower[key]+extension[key]
    ternary['rules']={name:{key:lower['rules'][name][key]+extension['rules'][name][key]
                          for key in ['tested','failed']} for name in lower['rules']}
    four=domain(['quaternary8','quaternary10'])
    symbolic={}
    for degree in range(3,9):
        tag=f'symbolic{degree}-16'
        if (Path('logs')/(tag+'.log')).exists():
            rr=rows(tag)
            if rr:symbolic[str(degree)]=rr[-1]
    symbolic_totals={key:sum(x['total_'+key] for x in symbolic.values())
                     for key in ['masks','nodes','bad']}
    degree3=rows('symbolic3-30')[-1]
    degree3_combined={key:symbolic['3']['total_'+key]+degree3['total_'+key]
                      for key in ['masks','nodes','bad']}
    fixed={tag:rows(tag) for length in [17,18] for degree in range(4,10)
           for tag in [f'memo{degree}-{length}'] if rows(tag)}
    exact17=[x for x in rows('symbolic3-30') if x['length']==17]
    exact17 += [x for degree in range(4,10) for x in rows(f'memo{degree}-17')]
    degree17={key:sum(x[key] for x in exact17) for key in ['masks','nodes','bad']}
    degree17['completed_degrees']=sorted(x['degree'] for x in exact17)
    last_extensions={tag:rows(tag) for tag in ['last4-18','last4-19','last4-20'] if rows(tag)}
    result=dict(binary_full=binary,ternary_full8=ternary_full,
                ternary_modulo_renaming=ternary,four_modulo_renaming=four,
                symbolic_first_mask=symbolic,
                symbolic_all_degrees16_totals=symbolic_totals,
                symbolic_all_degrees17_extension=degree17,
                symbolic_first_mask_degree3_through30=degree3_combined,
                symbolic_arbitrary_degree3_through26=rows('symbolic3-26')[-1],
                symbolic_completed_fixed_length=fixed,
                symbolic_last_degree4_length18=rows('last4-18'),
                symbolic_last_degree4_completed=last_extensions,
                structured_factor22=rows('factor22')[-1],
                independent_verification=json.loads(Path('results/verification.json').read_text()),
                independent_symbolic_verification=json.loads(Path('results/verification-symbolic.json').read_text()),
                independent_example_verification=json.loads(Path('results/verification-examples.json').read_text()),
                independent_last_verification=json.loads(Path('results/verification-last.json').read_text()),
                extension_status={tag:json.loads((Path('results')/(tag+'.json')).read_text())
                                  for tag in ['extension-jobs','extension17-jobs','last-extension-jobs'] if (Path('results')/(tag+'.json')).exists()})
    Path('results/SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
    for key in ['binary_full','ternary_full8','ternary_modulo_renaming','four_modulo_renaming']:
        x=result[key]
        print(key,{k:v for k,v in x.items() if k!='rules'})
    print('symbolic', {k:(v['length'],v['total_nodes'],v['total_bad']) for k,v in symbolic.items()})


if __name__=='__main__':main()
