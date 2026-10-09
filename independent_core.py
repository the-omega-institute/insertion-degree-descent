"""Independent review operations; no production modules imported."""
from itertools import groupby
import math

def count_runs(mask):
    return sum(q == 'U' and (t == 0 or mask[t - 1] == 'V')
               for t, q in enumerate(mask))


def project(word, mask):
    assert len(word) == len(mask)
    return tuple(''.join(c for c, q in zip(word, mask) if q == source)
                 for source in 'UV')


def emit(u, v, mask):
    readers = {'U': iter(u), 'V': iter(v)}
    return ''.join(next(readers[q]) for q in mask)


def enumerate_feasible(u, v, word):
    result = []
    def visit(i, j, labels):
        if i + j == len(word):
            if i == len(u) and j == len(v):
                result.append(labels)
            return
        letter = word[i + j]
        if i < len(u) and u[i] == letter:
            visit(i + 1, j, labels + 'U')
        if j < len(v) and v[j] == letter:
            visit(i, j + 1, labels + 'V')
    visit(0, 0, '')
    return result


def degree(u, v, word):
    states = {(0, 'V'): 0}
    for t, letter in enumerate(word):
        following = {}
        for (i, last), cost in states.items():
            j = t - i
            candidates = []
            if i < len(u) and u[i] == letter:
                candidates.append(((i + 1, 'U'), cost + (last != 'U')))
            if j < len(v) and v[j] == letter:
                candidates.append(((i, 'V'), cost))
            for key, new_cost in candidates:
                following[key] = min(following.get(key, math.inf), new_cost)
        states = following
    return min((cost for (i, last), cost in states.items()
                if i == len(u) and len(word) - i == len(v)), default=math.inf)


def block_ranges(mask):
    bounds = []
    offset = 0
    for source, labels in groupby(mask):
        size = len(list(labels))
        bounds.append((source, offset, offset + size))
        offset += size
    return bounds


def all_exchanges(word, mask):
    bounds = block_ranges(mask)
    answer = []
    for t in range(1, len(bounds) - 1):
        if [bounds[s][0] for s in (t - 1, t, t + 1)] != ['U', 'V', 'U']:
            continue
        for first in (t - 1, t):
            lo, mid, hi = bounds[first][1], bounds[first][2], bounds[first + 1][2]
            z = word[:lo] + word[mid:hi] + word[lo:mid] + word[hi:]
            new = mask[:lo] + mask[mid:hi] + mask[lo:mid] + mask[hi:]
            answer.append((z, new, (lo, mid, hi)))
    return answer


def shift_middle(word, mask):
    ublocks = [entry for entry in block_ranges(mask) if entry[0] == 'U']
    assert len(ublocks) == 3
    _, start, end = ublocks[1]
    size = end - start
    assert word[start - size:start] == word[start:end]
    assert mask[start - size:start] == 'V' * size
    shifted = mask[:start - size] + 'U' * size + 'V' * size + mask[end:]
    assert project(word, shifted) == project(word, mask)
    assert count_runs(shifted) == 3
    return shifted


