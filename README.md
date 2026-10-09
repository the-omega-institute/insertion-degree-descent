# Insertion-degree descent: reproduction package

This directory is a self-contained code and evidence package for the
block-exchange criterion, finite minimum-mask examples, periodic degree-three
repair, and bounded searches. It is prepared for the repository placeholder
<https://github.com/the-omega-institute/insertion-degree-descent>; that repository
has not been created by this task. There is no manuscript or correspondence in
this directory. All commands below run from this directory and use relative
paths.

`SHA256SUMS` identifies the exact distributed files. Verify it before running
commands with `shasum -a 256 -c SHA256SUMS`, or with
`sha256sum -c SHA256SUMS` on Linux. `PROVENANCE.json` records original source and
execution-output hashes. `adaptations.json` records the path changes made for
this package. C++ search and audit sources are unchanged; Python changes make
inputs and outputs local to this root and remove manuscript dependencies.

Requirements: Python 3.10 or later, a C++17 compiler (`c++`, Clang or GCC), and a
SHA-256 utility. Python checkers use the standard library. No command needs
Lean, a network connection, credentials, email, or git. Run one CPU-intensive
command at a time. The production numerical programs use 32-bit mask positions;
the archived domains remain inside their supported bounds. The symbolic
programs are intended for the documented lengths at most thirty.

## Files and verification scope

| Location | Content |
| --- | --- |
| Root `.cpp` files | Production numerical and symbolic searches, structured-sample audit, full coarsening audit, and independently implemented degree-three search |
| Root `.py` files | Independent mask/DP checks, certificate and identification checks, input generator, archive aggregation and consistency checks |
| `logs/` | Completed original executions and completed checks of this revision |
| `inputs/` | Exact structured ordered-pair list and the 168-case prefix dataset |
| `certificates/` | All surviving partitions/witness tuples, finite examples, period shifts, and identification-cut certificates |
| `results/` | Machine-readable summaries and completed verification results |

All required logs are included; none exceeds 50 MB. No checksum-only omission
is needed. An empty survivor file means the completed run has no survivors;
it is meaningful only together with its completed log. Completion is identified
by a row for every specified symbolic/numerical length, or `complete: true` for
the structured audit. Progress rows are not substitutes for completed ranges.

Generation of the arbitrary degree-three domain through length thirty is an
archived execution. An independent implementation regenerated every counter
and all twelve leaves through length twenty during review. Its checker verifies
all 1,512 archived tuples, 896 distinct instances, and 41,244 identification
cuts through thirty. This revision reran that checker and the independent
length-twenty generator. Leaf checking alone does not establish completeness
of generation above twenty. The completeness argument is the equality-partition
reduction in the manuscript; the archived completed generation supplies its
finite premises. Other higher-degree symbolic bounds also remain archived
executions, with small explicit-path cross-checks included.

## Build and practical checks

The build script compiles sequentially and creates `bin/` and `runs/`:

```sh
sh build.sh
python3 generate_structured_inputs.py
python3 check_small.py
python3 verify_period_family.py
python3 analyze_periods.py
python3 audit_identifications.py certificates/fresh3-30-bad.jsonl --output results/revision-identification30.json
python3 independent_certificates.py
python3 independent_profile_check.py
python3 independent_lemma_check.py
python3 summarize.py
python3 check_archive.py
```

`check_small.py` reconstructs the finite examples, unary formulas, constrained
exchange DP and prefix statistics from literal inputs. To compare the rendered
tables in a separately provided manuscript, optionally use
`python3 check_small.py --tex /path/to/paper.tex`. Its default run has no
manuscript dependency. `inputs/prefix168.json` contains its exact 168 triples.
The optional table check additionally verifies the 16 original masks in
Proposition 5, the 24 entries for the last-mask example and successor, the 29
entries for the packed example and successor, the separator-rule rows, and
the two-run successor witnesses.

The broader inherited checks are also runnable:

```sh
python3 verify.py
python3 verify_examples.py
python3 verify_symbolic.py
python3 verify_last.py
python3 canonical.py ABAABAABAAB ABABAAB ABABAAABABABAAABAB
python3 canonical.py ABAABAABAAB ABABAAB ABABAAABABABAAABAB --mask UUVVVUUUUVUUUVUUVV
```

`verify.py` compares position-combination grouping with a dense degree DP,
checks literal pull-backs and commutation, and tests unary exchanges.
`verify_symbolic.py` reconstructs small first-mask and memoized search trees
using explicit source paths. `verify_last.py` runs the small last-mask engine
and compares it to those explicit paths. `canonical.py` reports constrained
commuting/noncommuting minima for one selected mask. It does not presume that
the first mask has an exact exchange.

## Exact production commands and number map

Each command writes to `runs/` so the distributed logs and certificates remain
available. Elapsed times vary; compare counters and witness records, not timing
fields. `compare_revision_runs.py` checks the finite production reruns recorded
in `results/revision-runs.json`. The tables below map every numerical
experimental assertion in the manuscript to its producer and exact retained
output. Parameter bounds in theorem statements are mathematical hypotheses,
not execution counters.

To recreate the revision's finite production comparisons, run these commands
sequentially after the build:

```sh
./bin/independent_symbolic 20 runs/independent-leaves.jsonl > runs/independent-symbolic20.log
./bin/structured_audit inputs/factor22-pairs.tsv runs/structured > runs/structured-audit.log
./bin/coarsenings certificates/period-instances.tsv > runs/coarsening-summary.json
./bin/audit 2 6 runs/smoke-binary6 0 > runs/smoke-binary6.log
./bin/symbolic 9 3 5 runs/smoke-first3 > runs/smoke-first3.log
./bin/symbolic_memo 9 3 5 runs/smoke-memo3 > runs/smoke-memo3.log
./bin/symbolic_last 9 3 5 runs/smoke-last3 > runs/smoke-last3.log
./bin/symbolic3 20 5 runs/smoke-arbitrary3 > runs/smoke-arbitrary3.log
./bin/symbolic3_fresh 20 5 runs/smoke-fresh3 > runs/smoke-fresh3.log
python3 compare_revision_runs.py
```

The retained outputs have prefixes `logs/revision-` or `certificates/revision-`.
Comparisons check every non-timing counter and normalize independent partition
names. Generated binaries and scratch runs are not distributed; `build.sh`
creates those directories when needed.

### Numerical domains

```sh
./bin/audit 2 13 runs/binary13 0 > runs/binary13.log
./bin/audit 2 14 runs/binary14 0 14 > runs/binary14.log
./bin/audit 2 15 runs/binary15 0 15 > runs/binary15.log
./bin/audit 2 16 runs/binary16 0 16 > runs/binary16.log
./bin/audit 3 8 runs/ternary8 0 > runs/ternary8.log
./bin/audit 3 10 runs/ternary10 1 9 > runs/ternary10.log
./bin/audit 3 12 runs/ternary12 1 11 > runs/ternary12.log
./bin/audit 4 8 runs/quaternary8 1 > runs/quaternary8.log
./bin/audit 4 10 runs/quaternary10 1 9 > runs/quaternary10.log
```

Arguments are alphabet size, maximum combined length, output tag,
restricted-growth flag, and optional starting length. A restricted-growth
string for concatenated `uv` begins with `0`, and each later label is at most
one more than the largest earlier label. It represents one renaming class.
The two sources are nonempty and ordered. Every output is counted once within
its pair; identical words under different pairs are counted separately.

| Manuscript domain and totals | Producing logs | Aggregation and outcome |
| --- | --- | --- |
| Labeled binary through 16: 1,835,012 pairs; 415,262,716 higher-degree outputs | `logs/binary13.log`, `binary14.log`, `binary15.log`, `binary16.log` | `summarize.py` → `results/SUMMARY.json`, `binary_full`; first and last failure counts both zero |
| Labeled ternary through 8: 63,972 pairs; 726,198 higher-degree outputs | `logs/ternary8.log` | `ternary_full8`; both extrema pass |
| Ternary renaming classes through 12: 1,395,066 pairs; 135,331,916 higher-degree outputs | `logs/ternary8.log`, `ternary10.log`, `ternary12.log` | `ternary_modulo_renaming`; both extrema pass |
| Four-letter renaming classes through 10: 508,982 pairs; 24,145,502 higher-degree outputs | `logs/quaternary8.log`, `quaternary10.log` | `four_modulo_renaming`; both extrema pass |

The ternary labeled prefix through eight converts to renaming classes with six
injective renamings for two- or three-letter patterns and three for unary
patterns. All higher-degree outputs use at least two letters, so that counter
is divided by six. Pair/output counts need the unary correction: add three
times the 28 nonempty source-length splits through eight before dividing by
six. The source-mask correction uses 494 instead of 28. `summarize.py` applies
these corrections; `check_archive.py` verifies completed ranges, sums, extrema
outcomes, and the independent input combinatorics. Labeled pair counts at
length L are `(L-1) q^L`; renaming-class counts are `(L-1) sum S(L,j)` for
`1 <= j <= q`.

### Structured sample

The exact input is `inputs/factor22-pairs.tsv`, SHA-256
`40bc4f135e39eea3e9e8ee404709ac0f90f5cdb62e69e5e963906b6af5167b7a`.
Each ASCII row is `u`, a tab, `v`, and a newline. There is no header.

For periods p = 2, 3, 4, take all binary blocks of length p containing both
symbols; do not require the block to be primitive. For every m,n = 3..12 with
m+n <= 22, and every phase f = 0..p-1, repeat that block to make `u[i]=block[i
mod p]` and `v[i]=block[(i+f) mod p]`. If m+n <= 18, additionally flip each
single position of u while holding v fixed, and each single position of v
while holding u fixed. Do not perturb both sources together. Globally
deduplicate exact ordered pairs, then sort by `(m+n,u,v)`. The generator above
checks its output byte-for-byte against the distributed input and its hash.

```sh
./bin/targeted_factor runs/factor22 22 > runs/factor22.log
cmp runs/factor22-pairs.tsv inputs/factor22-pairs.tsv
./bin/structured_audit inputs/factor22-pairs.tsv runs/structured > runs/structured-audit.log
```

| Number or conclusion | Retained output and field |
| --- | --- |
| 70,710 pairs; 20,001,166 outputs; 19,443,384 higher-degree outputs; no first/last failure | Final row of `logs/factor22.log`: `pairs`, `outputs`, `higher`, `bad_first`, `bad_last` |
| 8,861,068 degree-three outputs; 33,306,824 degree-three minimum masks; zero all-failed degree-three masks | Completed row of `logs/structured-audit.log`: `degree_three_outputs`, `degree_three_minimum_masks`, `bad_degree_three_masks`; also `results/structured-summary.json` |
| Same counts reproduced by this revision | `results/revision-runs.json`, structured comparison; `logs/revision-structured-audit.log` |

`targeted_factor` checks extrema and some higher-degree strategies.
`structured_audit` checks every degree-three minimum mask of every grouped
output. Its survivor file `certificates/structured-bad-masks.jsonl` is empty.
This is a specified sample through length 22, not all binary pairs at that
length. The absence of bad degree-three masks makes a repair test vacuous on
this sample.

### Symbolic domains

```sh
./bin/symbolic 16 3 5 runs/symbolic3-16 > runs/symbolic3-16.log
./bin/symbolic 16 4 7 runs/symbolic4-16 > runs/symbolic4-16.log
./bin/symbolic 16 5 9 runs/symbolic5-16 > runs/symbolic5-16.log
./bin/symbolic 16 6 11 runs/symbolic6-16 > runs/symbolic6-16.log
./bin/symbolic 16 7 13 runs/symbolic7-16 > runs/symbolic7-16.log
./bin/symbolic 16 8 15 runs/symbolic8-16 > runs/symbolic8-16.log
./bin/symbolic 30 3 17 runs/symbolic3-30 > runs/symbolic3-30.log
./bin/symbolic_memo 17 4 17 runs/memo4-17 > runs/memo4-17.log
./bin/symbolic_memo 17 5 17 runs/memo5-17 > runs/memo5-17.log
./bin/symbolic_memo 17 6 17 runs/memo6-17 > runs/memo6-17.log
./bin/symbolic_memo 17 7 17 runs/memo7-17 > runs/memo7-17.log
./bin/symbolic_memo 17 8 17 runs/memo8-17 > runs/memo8-17.log
./bin/symbolic_memo 17 9 17 runs/memo9-17 > runs/memo9-17.log
./bin/symbolic_memo 18 4 18 runs/memo4-18 > runs/memo4-18.log
./bin/symbolic_memo 18 5 18 runs/memo5-18 > runs/memo5-18.log
./bin/symbolic_last 19 4 19 runs/last4-19 > runs/last4-19.log
./bin/symbolic_last 20 4 20 runs/last4-20 > runs/last4-20.log
./bin/symbolic3 26 5 runs/symbolic3-26 > runs/symbolic3-26.log
./bin/symbolic3_fresh 30 5 runs/fresh3-30 > runs/fresh3-30.log
```

First/last engines take maximum length, degree, starting length and output tag.
Arbitrary degree-three engines omit the degree argument. `symbolic3_fresh`
removes the old engine's 1,000-survivor output cap; it retains all 1,512 tuples
through thirty. The old length-twenty-six run has 305 tuples and is below that
cap. First/last masks and lower witnesses are ordered by source-position
integer, first position the least significant bit and U = 1. Arbitrary
degree-three witnesses use increasing contiguous-source cut order.

| Manuscript symbolic row | Retained log(s), fields `masks / nodes / bad` |
| --- | --- |
| All degrees through 16: 121,670 / 2,306,288,203 / 0 | Sum completed rows of `logs/symbolic3-16.log` through `symbolic8-16.log` |
| All degrees at 17: 127,858 / 6,254,062,825 / 0 | Length-17 row of `symbolic3-30.log` plus `memo4-17.log` through `memo9-17.log` |
| First, degree four at 18: 75,582 / 279,632,995 / 1 partition | `logs/memo4-18.log`; `certificates/memo4-18-bad.jsonl` |
| First, degree five at 18: 92,378 / 8,962,639,586 / 0 | `logs/memo5-18.log`; empty survivor file |
| Last, degree four at 19: 125,970 / 532,910,127 / 0 | `logs/last4-19.log`; empty survivor file |
| Last, degree four at 20: 203,490 / 1,212,060,756 / 1 partition | `logs/last4-20.log`; `certificates/last4-20-bad.jsonl` |
| First, degree three through 30: 3,365,856 / 139,406,910 / 0 | Disjoint ranges in `logs/symbolic3-16.log` and `symbolic3-30.log` |
| Arbitrary, degree three through 26: 1,184,040 / 69,396,022 / 305 tuples | `logs/symbolic3-26.log`; `certificates/symbolic3-26-bad.jsonl` |
| Arbitrary, degree three through 30: 3,365,856 / 266,866,735 / 1,512 tuples | `logs/fresh3-30.log`; `certificates/fresh3-30-bad.jsonl` |

`nodes` means attempted equality-branch extensions, including memoized
duplicates. A terminal leaf is counted per original mask. Nonmemoized arbitrary
leaves count witness tuples, which may share a partition or source/output/mask
instance. `check_archive.py` verifies the table, the completed ranges and the
independent mask count `binomial(L+1,2r)` at each length. The maximum possible
minimum degree is `min(|u|,|v|+1) <= floor((L+1)/2)`; degrees one and two need
no symbolic search. Forced-V suffix padding transfers exact-length results to
shorter lengths. The first-failure and unique-pattern conclusions use those
reductions, the archived zero-survivor ranges, and the two-class survivor
certificates; the proper unary coarsening has degree one.

The independent length-twenty generation is reproducible by:

```sh
./bin/independent_symbolic 20 runs/independent-leaves.jsonl > runs/independent-symbolic20.log
```

Its completed archive is `logs/independent-symbolic20.log` with leaves in
`certificates/independent-leaves.jsonl`. `independent_certificates.py` compares
every completed row and leaf against the production archive. There are twelve
tuples through twenty, no bad mask through sixteen, and first bad masks at
seventeen. This revision's rerun agrees, as recorded in `results/revision-runs.json`.

### Repair and identifications

```sh
python3 analyze_periods.py
python3 audit_identifications.py certificates/symbolic3-26-bad.jsonl --output results/identification-audit26.json
python3 audit_identifications.py certificates/fresh3-30-bad.jsonl --output results/identification-audit30.json
python3 independent_certificates.py
./bin/coarsenings certificates/period-instances.tsv > runs/coarsening-summary.json
```

| Number or conclusion | Producer and retained output |
| --- | --- |
| 305 tuples, 221 distinct instances through 26; twelve direct position-combination checks through 20; shifted vector `(2,1,1,2)` | `analyze_periods.py` → `results/period-summary.json`, `certificates/period-certificates.jsonl`, `certificates/period-instances.tsv` |
| 1,512 tuples, 896 distinct instances through 30; all four witnesses valid; periods ABA, ABCA, ABABA, ABCAB, ABCDA | `audit_identifications.py` → `results/identification-audit30.json` and sibling `.jsonl`; independent confirmation in `results/independent-certificates.json` |
| All 41,244 one-run cuts through 30 pass the coarsening reduction | Same audit; every imposed cut introduces an original mask of degree at most two; independent checker tests every cut separately |
| All 8,110,169 instance/identification combinations of the 221 instances; 6,702,697 retain degree three with vector `(2,1,1,2)`; 1,407,472 have degree one | `coarsenings.cpp` → `results/coarsening-summary.json`; regenerated result comparison in `results/revision-runs.json` |

Checking the imposed cuts covers every further alphabet identification, including
outer contexts: a lower original mask remains valid under further identification.
`independent_certificates.py` implements its own word operations and equivalence
relation check and imports no production Python module. Its direct feasible-mask
enumeration also checks all twelve small leaf repairs. This supplies independent
checks for surviving cases and for the identification argument, not just a
displayed representative.

### Finite examples and profile comparison

| Assertion in the manuscript | Producer and retained output |
| --- | --- |
| Proposition 5: 16 masks, eight minima, degree four; six degree-two moves with four distinct outputs and multiplicities 2,1,2,1 | `check_small.py` → `results/small-verification.json`, `proposition5`; complete masks and contiguous-deletion remainders retained |
| Proposition 6: twelve masks in each tested family instance, all of degree three; four degree-one moves, exact shifted exchange | Same output, `family`; all-parameter conclusion uses the written proof, not this finite check |
| Separator choices: four listed failures and exact alternatives | Same output, `rules`; sources, masks, separator lengths, all successors and their complete masks |
| Proposition 7: 36 masks, run histogram 4:16, 5:16, 6:4; six degree-two first-mask moves and a degree-three alternative | Same output, `proposition7`, `proposition7_other`; also `certificates/first-mask-counterexample-verified.json` |
| Last-mask example: eight original masks, histogram 4:2 and 5:6; six failed moves, five distinct outputs, 16 exact-successor masks | Same output, `last`, `last_first`, `last_exact_successor`; `certificates/last-mask-counterexample-verified.json` |
| Packed example: eight four-run masks; six degree-two moves; 21 exact-successor masks of minimum three | Same output, `packed`, `packed_first`, `packed_exact_successor`; inherited forced-suffix certificate also retained |
| Both-end gadget: degree seven; four end moves of degree five and eight other moves of degree six | Same output, `both_ends`, `left_gadget`, `right_gadget`; `certificates/both-end-separators-counterexample.json` |
| 2,338 binary outputs through six; 2,832 minimum-mask exchanges; empty-segment handling | Same output, `core_binary_through6`; `logs/revision-small.log` |
| 27,826 binary outputs through eight; 67,512 criterion exchanges; 213,608 alternative-mask transports; 1,354,880 unary exchanges through eleven | `verify.py` → `results/verification.json`; archived counts and independent implementations included |
| 168 failed triples, 116 with another successful candidate, 94 profile-certified, 22 missed, 52 without a successful candidate and 52 certified ordinary predecessors | `check_small.py` → `prefix_profile`, with every triple in `inputs/prefix168.json`; independent reconstruction via `independent_profile_check.py` → `results/independent-profile-results.json` |

For the 168-case comparison the domain is all nonempty labeled binary ordered
source pairs at combined lengths eight and nine, with degree-three outputs.
An eligible candidate swaps unequal adjacent letters at zero-based positions
i,i+1, assigned to different sources by some minimum mask, with a transported
two-run mask. Each of the 168 triples has exactly one failed eligible position,
whose output has degree one. Positions are deduplicated across masks within
the triple. The profile certificate requires some t with `i+2 <= t < |w|`,
and `F(w'[:t],state) >= F(w[:t],state)-1` at every source state. The suffix
after t is unchanged. Dataset position fields inherited from the original
checker are one-based; the cutoff definition and slice bounds are zero-based.

Theorem 8's h,j,k,ell hypotheses and deletion cases are proved in the manuscript.
`verify_period_family.py` supplements the proof with 1,539 finite parameter/word
cases: h,j,k,ell = 1..6 for S = B, and 1..3 for S = BB, BC, BCB. All repaired
degrees are two; 222 originals have degree three; fifteen cases also use direct
position-combination enumeration. These results are in
`results/period-family-verification.json`.

The optional `probe_periods.py` is exploratory: primitive binary periods of
lengths 3..8, every proper nonempty border, exponents 1..3. Its finite result
does not establish the open common-period classification or unbounded repair.
General existential descent and Singleton No-Gap remain open beyond the stated
bounded domains.
