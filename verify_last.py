"""Audit the last-minimum-mask engine against explicit source paths."""
import json
import subprocess
from pathlib import Path
from verify_symbolic import audit


def main():
    results = []
    for r in [3, 4, 5]:
        tag = f'runs/last{r}-9'
        with Path(tag + '.log').open('w') as out:
            subprocess.run(['./bin/symbolic_last', '9', str(r), str(2*r-1), tag],
                           stdout=out, check=True)
        for line in Path(tag + '.log').read_text().splitlines():
            data = json.loads(line)
            result = audit(data['length'], r, True, True)
            assert result == {key: data[key] for key in result}, (data, result)
            results.append(dict(length=data['length'], degree=r, **result))
    Path('results/verification-last.json').write_text(json.dumps(dict(rows=results), indent=2) + '\n')
    print('Last-mask explicit-path checks passed:', len(results), 'length/degree domains.')


if __name__ == '__main__':
    main()
