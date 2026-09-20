# CPU selector versus neural premise selection

The current CPU selector is competitive with the pinned LeanHammer-style
neural premise selector, but **superiority has not been established**. These
comparisons substitute premise selectors inside JevHammer, with Jev proof-state
guidance in every arm. They do not compare against the full LeanHammer tactic.

The strongest broader comparison uses 134 development locations from 99
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

All 122 reserved evaluation locations remain unused for proof trials. A
substantial improvement still needs to be demonstrated there after development
selection. Third-party neural training overlap is unknown; local preparation
excluded all cohort owners. Local workloads use a 16 GB, zero-swap limit.
