# What the existing results say about Jev

The current modular system's original 1,024-goal comparisons measure **whole
finishing tactics**, not the marginal benefit of Jev. On their own, they do not
establish that Jev beats the same search using fixed or random state ordering.
The [completed 256-goal state-only ablation](guidance-ablation-v1.md) now finds
107 solves with Jev, 103 with fixed order, and 99/106/102 with random ordering.
It supports a small gain over the specified random average, conditional on these
seeds and this run, but remains inconclusive against fixed order.
The original monolithic experiments did include no-Jev controls with positive
results; see [the historical audit](historical-guidance.md). Those changed both
premise and state guidance and do not answer the current state-only question.

Most successful attempts finish before requesting any ranking:

| Study and JevHammer configuration | On-time solves | No Jev state-ranking attempt | After a ranking attempt |
|---|---:|---:|---:|
| Original confirmation, CPU | 450 | 361 (80.2%) | 89 |
| Original confirmation, neural premises | 469 | 373 (79.5%) | 96 |
| Available-premise follow-up, strict CPU | 438 | 353 (80.6%) | 85 |
| Available-premise follow-up, original CPU | 448 | 361 (80.6%) | 87 |
| Available-premise follow-up, neural premises | 466 | 373 (80.0%) | 93 |

The final column does **not** count proofs attributable to Jev. Some or all might
also be found by an unguided search. It even includes successes where every
ranking attempt failed: respectively 2, 4, 2, 1 and 3 in the rows above. The
search falls back to candidate order when ranking fails. No-call successes can
include early beam expansion as well as the initial tactic portfolio.

The recorded `winner` names the closing tactic or successful branch path. It
does not establish that the model's ordering was necessary, or that the closing
tactic would have succeeded without the preceding transformations. Neither
winner breakdowns nor the occurrence of a model call supply a counterfactual.

Comparing JevHammer with full LeanHammer also changes the tactic portfolio,
search strategy and, in CPU arms, premise selection. A higher whole-tactic score
therefore cannot be attributed specifically to Jev. The original modular-system
evidence supports the reported package/configuration comparisons. The new matched
ablation measures a much smaller difference between state-ranking policies.

These counts come from all published trial rows and recorded independent replay
flags, without choosing individual examples. Recompute them with Python alone:

```sh
python3 scripts/audit_guidance_usage.py --check docs/guidance-usage-audit.json
```

See the [machine-readable audit](guidance-usage-audit.json). The completed
[first-pass ablation](guidance-ablation-v1.md) changes only state-ranking decisions;
premise refresh and search budgets are identical. Setting `maxCalls` to zero
would also disable refresh in the pinned search and is not an adequate control.
