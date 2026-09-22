# CPU selector versus neural premise selection

The fresh [1,024-goal confirmation](full-leanhammer-confirmation-v1.md) found
**CPU/conclusion JevHammer 450/1,024 (43.95%)**, **neural/conclusion JevHammer
469/1,024 (45.80%)**, and **full LeanHammer 372/1,024 (36.33%)**. Every counted
proof was produced within six seconds and independently replayed. Both JevHammer
arms use Jev for proof-state selection.

CPU JevHammer exceeded full LeanHammer by **7.62 percentage points**, with a
prespecified stratified module-bootstrap 95% interval of **+5.34 to +9.91**.
However, the secondary comparison favored neural over CPU by 1.86 points
(95% interval +0.29 to +3.47). **The objective of CPU-selector superiority over
the neural approach remains unmet.** CPU retrieval was faster: 190.369 seconds
in aggregate versus 577.650 for neural/conclusion, while total goal times were
3,143.744 and 3,271.963 seconds. The CPU artifact took 92.16 seconds to prepare.

This confirmation covers 1,024 distinct held-out owners in 131 modules across
17 subject areas, with six counterbalanced method orders. Five source-incompatible
modules were excluded before outcomes. All jobs respected the 16 GB, zero-swap
cap; it recorded memory pressure during the final full LeanHammer arm, without
OOM kills. The report publishes all trials, uncertainty, usage and limitations.
No methods were tuned on this cohort. Earlier evidence below remains separate.

A separate [full LeanHammer pilot](full-leanhammer-pilot-v1.md), completed on
2026-09-21, compares complete tactics on 34 exposed development locations:
CPU/conclusion JevHammer 16/34, neural/conclusion JevHammer 13/34, and full
LeanHammer 12/34. All 41 successful proofs replayed. CPU gained six locations
and lost two versus full LeanHammer; its 95% interval includes zero. This pilot
does not change the broader selector-comparison conclusion below.

The earlier broader selector comparison uses 134 development locations from 99
declarations, matched tactics and search budgets, and independent proof replay:

| Premise selection | On-time verified proofs |
|---|---:|
| Prepared sparse CPU | 57/134 (42.5%) |
| CPU sparse + conclusion matching | 63/134 (47.0%) |
| Neural | 63/134 (47.0%) |
| Neural + conclusion matching | 64/134 (47.8%) |

CPU versus neural gained seven locations and lost seven. CPU versus neural
fusion gained five and lost six; its declaration-bootstrap 95% interval is
−5.51 to +4.32 percentage points. Neither comparison establishes superiority
or statistical equivalence. All 247 successful trial proofs replayed.

CPU retrieval totaled 26.698 seconds, versus 54.893 for neural and 62.836 for
neural fusion. Initialization was outside the goal clock and reported
separately. Faster retrieval did not produce a comparable end-to-end speedup:
total goal times were 414.761, 403.897, and 417.450 seconds, respectively.
See [configurations, costs, and paired results](cpu-selector-structural-broad-v1.json).

The latest [34-location signature-graph experiment](cpu-selector-graph-v1.json)
completed 136 trials, with all 58 successful proofs independently replayed.
CPU control solved 16, Jev-guided graph 14, neural native 13, and neural reranked
15. The graph variant gained none and lost two versus CPU, so it is not promoted.
CPU's 16–15 lead over the stronger neural arm has a 95% interval including zero.
This repeatedly exposed pilot is useful for development, not final superiority
claims. The subsequent [destination-preview screen](cpu-selector-graph-preview-v1.json)
completed all 170 trials and independently replayed all 71 successes. CPU solved
16/34, original graph and preview graph each 14/34, neural native 13/34, and
neural reranked 14/34. Previews changed traversal directions substantially but
gained one and lost one against the original graph. They fail the promotion rule.
Their [native CPU profile](cpu-selector-profile-graph-v6.json) preserves all 384
fixed-direction rankings, at roughly 243–248 ms median and 383–387 ms p95,
excluding real Jev latency. This exceeds the provisional 200 ms p95 target.

The next scheduling hypothesis tries base-selected premises before spending
calls on premise guidance, under the same goal clock and call limit. It applies
equally to CPU and neural methods and has no proof-quality result yet.

All 122 older reserved evaluation locations remain unused for proof trials.
The new confirmation cohort now supplies a separate held-out reference; future
development must not treat it as unseen validation after tuning on its results.
Third-party neural training overlap is unknown; local preparation excluded all
cohort owners. Local workloads use a 16 GB, zero-swap limit.
