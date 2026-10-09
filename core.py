"""Exact word/mask operations; no imports from the archived search programs."""
from itertools import combinations
import re


def runs(mask):
    return sum(q == 'U' and (i == 0 or mask[i-1] != 'U')
               for i, q in enumerate(mask))


def projections(word, mask):
    return tuple(''.join(c for c, q in zip(word, mask) if q == s)
                 for s in 'UV')


def degree(u, v, word):
    """Minimum number of U-runs via sparse, layered source-grid DP."""
    if len(word) != len(u) + len(v):
        return float('inf')
    dp = {(0, 0, 'V'): 0}
    for c in word:
        nxt = {}
        for (i, j, q), cost in dp.items():
            if i < len(u) and u[i] == c:
                s = (i+1, j, 'U')
                nxt[s] = min(nxt.get(s, float('inf')), cost + (q != 'U'))
            if j < len(v) and v[j] == c:
                s = (i, j+1, 'V')
                nxt[s] = min(nxt.get(s, float('inf')), cost)
        dp = nxt
    return min((c for (i, j, q), c in dp.items()
                if i == len(u) and j == len(v)), default=float('inf'))


def all_masks(u, v, word):
    """Independent position-combination enumeration for finite certificates."""
    if len(word) != len(u) + len(v):
        return []
    out = []
    for pp in combinations(range(len(word)), len(u)):
        if ''.join(word[i] for i in pp) != u:
            continue
        selected = set(pp)
        if ''.join(c for i, c in enumerate(word) if i not in selected) != v:
            continue
        out.append(''.join('U' if i in selected else 'V'
                           for i in range(len(word))))
    return out


def blocks(word, mask):
    return [(m[0][0], word[m.start():m.end()], m.start(), m.end())
            for m in re.finditer('U+|V+', mask)]


def exchanges(word, mask):
    bb = blocks(word, mask)
    number = 0
    for k in range(1, len(bb)-1):
        if bb[k][0] != 'V':
            continue
        number += 1
        for side, lo, mid, hi in (
                ('L', bb[k-1][2], bb[k][2], bb[k][3]),
                ('R', bb[k][2], bb[k][3], bb[k+1][3])):
            yield dict(move=f'{number}{side}', bounds=[lo, mid, hi],
                       word=word[:lo]+word[mid:hi]+word[lo:mid]+word[hi:],
                       transported=mask[:lo]+mask[mid:hi]+mask[lo:mid]+mask[hi:])


def primitive(word):
    assert word
    return next(word[:k] for k in range(1, len(word)+1)
                if len(word) % k == 0 and word[:k]*(len(word)//k) == word)


def shift_middle_left(word, mask):
    bb = blocks(word, mask)
    s = next(i for i, b in enumerate(bb) if b[0] == 'U')
    assert [b[0] for b in bb[s:s+5]] == list('UVUVU')
    a, p, b, q, c = [x[1] for x in bb[s:s+5]]
    assert len(p) > len(b) and p.endswith(b)
    pos = bb[s+2][2]
    k = len(b)
    shifted = mask[:pos-k]+'U'*k+'V'*k+mask[pos+k:]
    assert projections(word, shifted) == projections(word, mask)
    assert runs(shifted) == runs(mask) == 3
    return shifted
