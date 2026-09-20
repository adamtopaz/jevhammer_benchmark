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

The latest [34-location posting-cap experiment](cpu-selector-bayes-exact-protocol.md)
again gave the existing CPU control a small lead, 16 versus 15 for the
Jev-reranked neural control. Its 95% interval includes zero. None of the Bayes
variants beat the CPU control, so none is promoted. This repeatedly exposed
pilot is useful for development, not final superiority claims.

All 122 reserved evaluation locations remain unused for proof trials. A
substantial improvement still needs to be demonstrated there after development
selection. Third-party neural training overlap is unknown; local preparation
excluded all cohort owners. Local workloads use a 16 GB, zero-swap limit.
