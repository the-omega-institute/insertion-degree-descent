#!/usr/bin/env python3
"""Reconstruct the prefix-profile statistics from literal binary inputs.
Uses only the review's own functions, never imports the manuscript verifier.
"""
from collections import Counter, defaultdict
from itertools import combinations, product
from pathlib import Path
import json
import math
from independent_core import count_runs, emit


def profile(u, v, prefix):
    costs = {(0, 0, 'V'): 0}
    for letter in prefix:
        updated = {}
        for (i, j, last), cost in costs.items():
            if i < len(u) and u[i] == letter:
                key = (i + 1, j, 'U')
                updated[key] = min(updated.get(key, math.inf), cost + (last == 'V'))
            if j < len(v) and v[j] == letter:
                key = (i, j + 1, 'V')
                updated[key] = min(updated.get(key, math.inf), cost)
        costs = updated
    return costs


counts = Counter()
for size in (8, 9):
    for m in range(1, size):
        labelings = []
        for picked in combinations(range(size), m):
            marked = set(picked)
            mask = ''.join('U' if i in marked else 'V' for i in range(size))
            labelings.append((mask, count_runs(mask)))
        for symbols in product('01', repeat=size):
            u, v = ''.join(symbols[:m]), ''.join(symbols[m:])
            groups = defaultdict(list)
            for mask, run_count in labelings:
                groups[emit(u, v, mask)].append((mask, run_count))
            minima = {word: min(cost for _, cost in values) for word, values in groups.items()}
            for word, values in groups.items():
                if minima[word] != 3:
                    continue
                candidates = set()
                for mask, cost in values:
                    if cost != 3:
                        continue
                    for position in range(size - 1):
                        if word[position] == word[position + 1]:
                            continue
                        if mask[position] != mask[position + 1]:
                            swapped_mask = mask[:position] + mask[position:position + 2][::-1] + mask[position + 2:]
                            if count_runs(swapped_mask) == 2:
                                candidates.add(position)
                neighbors = {i: word[:i] + word[i:i + 2][::-1] + word[i + 2:]
                             for i in range(size - 1) if word[i] != word[i + 1]}
                bad = [i for i in candidates if minima[neighbors[i]] == 1]
                if not bad:
                    continue
                assert len(bad) == 1
                counts['failed_triples'] += 1
                successful = [i for i in candidates if minima[neighbors[i]] == 2]
                ordinary = [i for i, neighbor in neighbors.items() if minima.get(neighbor) == 2]
                profiles = [profile(u, v, word[:cut]) for cut in range(size)]
                def certified(position):
                    for cut in range(position + 2, size):
                        old = profiles[cut]
                        new = profile(u, v, neighbors[position][:cut])
                        if all(new.get(state, math.inf) >= old.get(state, math.inf) - 1
                               for state in old.keys() | new.keys()):
                            return True
                    return False
                if successful:
                    counts['with_successful_candidate'] += 1
                    counts['successful_profile'] += any(map(certified, successful))
                else:
                    counts['without_successful_candidate'] += 1
                    counts['ordinary_profile_without_candidate'] += any(map(certified, ordinary))
assert counts == dict(failed_triples=168, with_successful_candidate=116,
                      successful_profile=94, without_successful_candidate=52,
                      ordinary_profile_without_candidate=52), counts
Path('results/independent-profile-results.json').write_text(json.dumps(dict(status='PASS', counts=dict(counts)), indent=2) + '\n')
print(json.dumps(dict(status='PASS', counts=dict(counts)), indent=2))
