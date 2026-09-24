# Current-system proof-state guidance ablation

Jev solved **107/256 goals**, fixed order **103/256**, and the three predetermined
random-order runs **99, 106, and 102/256**. Jev has a small measured advantage over
the average of these random runs, but **this first pass does not establish an
advantage over fixed order**. It does not justify attributing the earlier
whole-tactic improvement over LeanHammer entirely to Jev.

This is a fresh matched ablation of the current modular system, using the strict
CPU sparse/conclusion selector. Only proof-state ranking changes. Premise
selection, available-imports fitting, holdouts, tactics, search budgets, and proof
checks are identical. Neither neural premise services nor Jev premise reranking
are used. All 1,280 trials completed; all 518 raw successes were independently
kernel-replayed. One late random-seed-17 proof is retained but not counted.

## Coverage and paired differences

| Proof-state policy | On-time verified | Rate | Before any ranking | After a ranking decision |
|---|---:|---:|---:|---:|
| Fresh Jev | **107/256** | **41.80%** | 90 | 17 |
| Fixed candidate order | 103/256 | 40.23% | 90 | 13 |
| Random, seed 17 | 99/256 | 38.67% | 90 | 9 |
| Random, seed 29 | 106/256 | 41.41% | 90 | 16 |
| Random, seed 43 | 102/256 | 39.84% | 90 | 12 |

The three-seed mean is **102.33/256 (39.97%)**. The same 90 goals close before any
ranking in every arm. They comprise **84.1% of Jev's solves**, or **35.2% of all
256 goals**. The other 17 Jev solves are not 17 proofs attributable to Jev: fixed
and random ordering also close goals after making ranking decisions.

| Prespecified comparison | Difference | 95% interval, descriptive | 97.5% interval, co-primary |
|---|---:|---:|---:|
| Jev − fixed | +1.56 pp | [−0.39, +3.52] pp | **[−0.76, +3.80] pp** |
| Jev − mean of three random seeds | +1.82 pp | [+0.66, +2.98] pp | **[+0.52, +3.14] pp** |

Against fixed order, Jev gains **7** goals and loses **3**; 100 are solved by both.
Against individual random seeds it gains/loses 8/0, 5/4, and 7/2 respectively.
The best observed random seed is just one solve behind Jev. The random-average
comparison was chosen before collection; it does not pick a favorable seed or
treat repeated outcomes at one goal as independent problems.

Intervals use 20,000 paired whole-module bootstrap draws within Mathlib area,
seed 20260924. The two co-primary comparisons use 97.5% intervals for Bonferroni
familywise 95% coverage. The random-average interval is **conditional on these
three seeds and this one Jev run**; it does not measure variability across all
possible random seeds or repeated model calls. There are only 33 modules, mostly
two per area, and one single-module area. These approximate intervals describe
this small, previously exposed cohort, not a universal ranking of heuristics.

The evidence supports a modest gain against the specified random average under
this analysis. It remains inconclusive against the cheaper fixed-order policy.
Failure to distinguish Jev from fixed order does not establish equivalence.

## Timing, calls, and integrity

| Policy | Total goal seconds | Median goal ms | Ranking decisions | API attempts |
|---|---:|---:|---:|---:|
| Jev | 782.61 | 2,894.5 | 376 | 376 |
| Fixed | 695.33 | 2,007.0 | 393 | 0 |
| Random 17 | 739.90 | 2,451.5 | 395 | 0 |
| Random 29 | 718.37 | 2,252.0 | 384 | 0 |
| Random 43 | 720.12 | 2,285.5 | 387 | 0 |

Jev takes **12.6% more total goal time than fixed order** in this run. Its ranking
invocations account for 137.40 seconds, including request handling and failures.
The API reports **2,455,317 input tokens and 61,004 output tokens**; usage remains
unknown for 16 requests, so these are not complete billing totals.

All **31 ranking failures** are retained: 16 HTTP 400 responses and 15 responses
rejected by the client because ranking probabilities did not sum to one within
its tolerance. The normal fixed-order fallback handles them. There were no
automatic retries, budget-blocked trials, baseline API requests, or local ranking
failures. These results measure the deployed Jev policy, including its failures
and latency; they do not estimate a hypothetical error-free classifier.

All five policies reach their first ranking decision on the same **164 goals**.
At every one, the recorded state and candidate hashes match across all policies.
All source-module fitted-selector provenance also matches exactly across arms.
The exporter checks complete pairing, identical configurations, zero premise
ranking, fixed/random permutations, request accounting, and independent replay.

Selector initialization is outside the six-second goal clock and is reported
separately: about 105 seconds total per arm across 33 modules, with medians of
2.39–2.48 seconds per module. Collection plus replay took **93.93 minutes**.
Peak cgroup RAM was **2,181,558,272 bytes (2.18 GB)** under the 16,000,000,000-byte
cap, with zero swap and zero memory-limit/OOM events.

## Scope and reproduction

The 256 distinct-owner locations come from **33 modules and all 17 areas** of the
existing 1,024-goal cohort. Selection reads source metadata only: hash-order
modules within areas, visit areas round-robin, and truncate the boundary module
to reach 256 sites. Whole modules are assigned to ten counterbalanced batches.
All source states were re-admitted unchanged before trials. See the
[protocol](guidance-ablation-protocol.md) and [dataset notes](../datasets/guidance-ablation-v1/README.md).
This is a deterministic cluster subsample of previously exposed intermediate
goals, not a new unseen or uniform all-Mathlib benchmark. Jev pretraining overlap
remains unknown. No individual failed goals were used to tune this study.

Depth 3, beam width 4, 12 nodes, 24 successors, 100 retrieved premises, 8/16
premise prefixes, one refresh, three ranking slots, 15,000 tactic heartbeats,
200,000 outer heartbeats, and eight Lean threads are common to all arms. Fixed
and random decisions consume ranking slots too: setting `maxCalls := 0` would
also change premise refresh in this engine. Random permutations use independent
per-site seeded streams and the existing shared duplicate-state filtering.

- [Public report](guidance-ablation-v1.json), including full configurations,
  intervals, preparation records, deployment, and evidence hashes.
- [All 1,280 sanitized trial rows](guidance-ablation-v1-trials.jsonl).
- [All ranking decisions](guidance-ablation-v1-rankings.jsonl), including
  permutations, input hashes, elapsed time, and failure flags.
- [Selector preparation provenance](guidance-ablation-v1-preparation.json),
  stored once per module after checking that all five arms match.
- [Portable reproduction instructions](reproducing-guidance-ablation.md).
- [Historical combined premise/state ablations](historical-guidance.md), which
  are separate evidence and are not pooled with this experiment.

Check the public statistics without Lean or API access:

```sh
python3 scripts/analyze_guidance_ablation.py --check docs/guidance-ablation-v1.json
```

This recomputes coverage and uncertainty and checks public file hashes; it does
not perform another kernel replay. Raw certificates and full request/replay logs
are retained in the original run; a live reproduction generates fresh evidence.

The pre-trial freeze is `fee6c9bbdfc718e08586f66c44be519502077548`; the pinned
benchmark dependency is `fc5f5ea5aed665918f7cc4d84fd64408f8d0c2e2`. Lean 4.33,
Mathlib `db584cd6d46c92f209a44c0f1c829460d327499d`, JevHammer
`bf848e36e2f70f5ca745e0f88f6953279e7d00a6`, JevSelector
`397bef6d03d6ef4c7cda8ada8f3f92fb567863e1`, and model `jev-1.13.0` are recorded
in the public evidence. Publication fixes only a wording error about the number
of single-module areas, stores duplicate preparation provenance once per module,
and adds an analysis-source checksum and request-ledger reconciliation. All
numerical results match the original frozen analyzer exactly.
