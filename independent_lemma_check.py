#!/usr/bin/env python3
"""Exhaust every binary labeling and block boundary through length nine."""
from itertools import product
from pathlib import Path
import hashlib
import json
from independent_core import count_runs

checks = 0
for length in range(2, 10):
    for labels in product('VU', repeat=length):
        mask = ''.join(labels)
        for lo in range(length - 1):
            for mid in range(lo + 1, length):
                for hi in range(mid + 1, length + 1):
                    exchanged = mask[:lo] + mask[mid:hi] + mask[lo:mid] + mask[hi:]
                    difference = count_runs(mask) - count_runs(exchanged)
                    assert abs(difference) <= 1
                    ell = int(lo > 0 and mask[lo - 1] == 'U')
                    a, alpha = int(mask[lo] == 'U'), int(mask[mid - 1] == 'U')
                    b, beta = int(mask[mid] == 'U'), int(mask[hi - 1] == 'U')
                    tail = int(hi < length and mask[hi] == 'U')
                    assert difference == ((1 - ell) * (a - b)
                                          + (1 - alpha) * (b - tail)
                                          + (1 - beta) * (tail - a))
                    checks += 1

result = dict(status='PASS', binary_labelings_and_block_boundaries_through9=checks)
Path('results/independent-lemma-results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
