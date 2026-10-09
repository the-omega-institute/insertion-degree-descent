#!/usr/bin/env python3
"""Regenerate the exact structured binary sample without running its audit."""
from pathlib import Path
import argparse
import hashlib
import json


def generate(bound=22):
    pairs = set()
    for period in range(2, 5):
        for bits in range(1, (1 << period) - 1):
            block = ''.join(str((bits >> i) & 1) for i in range(period))
            for m in range(3, 13):
                for n in range(3, 13):
                    if m + n > bound:
                        continue
                    for phase in range(period):
                        u = ''.join(block[i % period] for i in range(m))
                        v = ''.join(block[(i + phase) % period] for i in range(n))
                        pairs.add((u, v))
                        if m + n <= 18:
                            for i in range(m):
                                pairs.add((u[:i] + str(1-int(u[i])) + u[i+1:], v))
                            for i in range(n):
                                pairs.add((u, v[:i] + str(1-int(v[i])) + v[i+1:]))
    ordered = sorted(pairs, key=lambda pair: (len(pair[0])+len(pair[1]), pair))
    return ''.join(u+'\t'+v+'\n' for u, v in ordered).encode('ascii')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('runs/factor22-pairs.tsv'))
    args = parser.parse_args()
    data = generate()
    assert data == Path('inputs/factor22-pairs.tsv').read_bytes()
    assert len(data.splitlines()) == 70710
    digest = hashlib.sha256(data).hexdigest()
    assert digest == '40bc4f135e39eea3e9e8ee404709ac0f90f5cdb62e69e5e963906b6af5167b7a'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    result = dict(status='PASS', pairs=70710, sha256=digest,
                  byte_identical_to_archived_input=True)
    Path('results/structured-input-verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
