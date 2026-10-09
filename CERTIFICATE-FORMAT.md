# Certificate formats

All text uses UTF-8; the actual words and masks are ASCII. JSONL has one JSON
object per line, no header. Sources are ordered. A mask labels each output
position U or V, has the same length as the word, and projects to exactly u and
v in order. A run is a maximal nonempty U block. Source-grid degree minimization
uses a fictitious initial V label. Intervals and witness cuts are zero-based,
half-open; the prefix dataset explicitly uses one-based position fields.

## Symbolic surviving partitions

In `fresh3-30-bad.jsonl` and `symbolic3-26-bad.jsonl`, fields are:

| Field | Meaning |
| --- | --- |
| `u`, `v`, `w` | Source words and emitted original word after imposed equalities |
| `mask` | Selected original three-run source-position mask |
| `cuts` | Four integers c for witnesses `V^c U^|u| V^(|v|-c)` of successors 1L,1R,2L,2R |
| `left_equal`, `right_equal` | Recorded equality of the two original successors on each side; informational, not a replacement for checking witnesses |

Equal letters in concatenated `uv` encode the full equality partition of the
initial distinct source-position variables. Class names A,B,... follow first
occurrence. Thus the row retains the surviving partition as well as its
witnesses; no external union-find state is required. A row denotes every
further identification of these classes. Distinct witness tuples can encode
the same source/output/mask instance. Deduplicate those instances by the four
fields `(u,v,w,mask)`, retaining every tuple when comparing generation counts.

`memo4-18-bad.jsonl` and `last4-20-bad.jsonl` additionally contain `degree` and
`witness_indices`. Reconstruct the lower-mask list by increasing integers
1 <= b < 2^L with exactly |u| set bits and at most degree-2 U-runs, excluding the
all-U mask. Position zero is the least significant bit; a set bit is U.
`witness_indices` index that list from zero, in separator order, left before
right. This is the exact list used by the respective C++ engine. The same
letter partition in `uv` records the leaf equalities. Proper coarsening of a
two-class partition is unary.

`independent-leaves.jsonl` stores `length`, `m`, `mask`, `classes`, and `cuts`.
`classes` is the normalized integer equality pattern of concatenated sources,
split after m positions. Re-emitting with `mask` reconstructs w. These rows are
compared with the production rows after class-name normalization.

## Repair and identification certificates

`period-certificates.jsonl` expands the degree-three leaves with the primitive
period, local a,P,b,Q,c factors, outer contexts, `shifted_mask`, and four
`shifted_successors`. Each successor contains `move`, `bounds`, `word`,
`transported` mask and checked `degree`. `bounds=[lo,mid,hi]` rotates adjacent
blocks in the original word as `w[:lo]+w[mid:hi]+w[lo:mid]+w[hi:]`.

`period-instances.tsv` has no header and five tab-separated columns:
`u`, `v`, `w`, original mask, shifted mask. It contains the 221 distinct
length-twenty-six instances consumed by the complete coarsening enumerator.

`identification-audit30.jsonl` and `identification-audit26.jsonl` have one row per
distinct instance. `shifted` is the repaired mask. Each `cut_pruning` entry is
`[move_index,cut,original_degree_after_imposing_cut]`, with move indices 0 and 3
for 1L and 2R. Impose the least equalities between the shifted successor z and
`v[:cut]+u+v[cut:]`; the resulting original degree must be at most two. These
entries are rechecked by recomputing the equalities and degree, not trusted as
assertions. Lower original masks survive all further identifications, giving
the all-coarsening conclusion for each leaf. `independent_certificates.py`
implements this check separately.

## Numerical and explicit finite evidence

Numerical `*-witnesses.jsonl` rows contain u,v,w, degree, the selected mask,
the failed choice rule and its successor moves. They are illustrative witnesses;
the execution counters and coverage come from the corresponding completed logs.
The structured audit's empty survivor file is paired with its `complete: true`
final row.

`results/small-verification.json` retains complete feasible masks, run counts,
first/last minimizers, each exchanged word and transported mask, every minimum
successor mask, and contiguous-u deletion remainders. This is sufficient to
check each displayed finite example without a manuscript file.

`inputs/prefix168.json` is an array of the source/output triples used for the
profile comparison. `failed_position`, `successful_positions` and
`exact_positions` are one-based original-word positions. `successful_profile`
and `ordinary_profile` are existential flags over the specified positions and
proper-prefix cutoffs, rechecked by both included profile implementations.
