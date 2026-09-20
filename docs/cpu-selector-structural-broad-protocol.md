# Structural retrieval: full development comparison

The 34-location pilot motivates a larger check of public-catalog sparse retrieval
and its fusion with structural signatures. This protocol is fixed before any
trial of these methods on the full development partition. It is still development
evidence, not the reserved evaluation used for the research acceptance target.

Use all **134 locations from 99 declarations across 34 modules** in the existing
development partition. Re-admit exactly those locations and original goals under
the current imports; do not resample. The 34 pilot locations are included, so
this is not an independent test of the pilot's selection decision. The 122
reserved evaluation locations remain unused. All 188 cohort owners remain
excluded from fitted sparse statistics.

Compare four methods with the existing implementation, selector
`b8b0a954ee12a776cd5d248d69f1f343e9ef0c22`:

| Method | Premise retrieval |
|---|---|
| `Research.publicTarget` | Public-catalog target-weighted sparse |
| `Research.structuralPublic` | Sparse plus structural reciprocal-rank fusion |
| `Research.neuralWarm` | Warmed LeanHammer-style neural reference |
| `Research.structuralNeural` | Neural plus the same structural fusion |

Keep the pilot's exact tactics, six-second goal limit, three-call Jev budget,
100-candidate retrieval, and `guidePremises := false`. Every method uses Jev for
proof-state selection. Structural queries use 10,000 heartbeats; fusion keeps
rank offset 16, pool factor 2, maximum pool 256. Do not include the newly drafted
rewrite-pattern mode or change parameters during this comparison.

Use a fresh CPU neural deployment with the published immutable model/corpus
pins and validated float32 embeddings. Initialize structural trees with fixed
`True` only. Each structural method gets an independent mutable cache copied
from that base, so goal-specific lazy refinement cannot warm another method.
Imported/current-file neural statement warmup is outside goal timing; goal
embeddings and actual structural query refinement are timed. Record startup
separately; attribution of shared immutable preparation is order-dependent.

Run all services, Lean workers, and independent replay inside one shared
**16,000,000,000-byte, zero-swap cgroup**, with two threads and serial modules.
No other heavy job may overlap. The fixed **536 trials** permit at most **1,608
Jev requests** and **16,000,000 reported input tokens**. Keep API errors, late
proofs, and budget blocking in the denominators; retry no trials selectively.
Independently replay every successful proof before reporting verified coverage.

Publish all four arms, paired gains/losses, declaration-grouped bootstrap
intervals, elapsed/retrieval/startup costs, API usage/errors, memory peak and
events. Compare the CPU candidates with both neural arms, rather than choosing a
weaker reference. Any promotion toward reserved evaluation must consider both
coverage and measured cost. A development win alone does not complete the goal.

With the matching prepared public index and fresh neural endpoint configured:

```sh
python -m jevhammer_benchmark run \
  --dataset datasets/mathlib-broad-v1/research-structural-v1.json \
  --methods JevHammerBenchmark.Research.publicTarget \
    JevHammerBenchmark.Research.structuralPublic \
    JevHammerBenchmark.Research.neuralWarm \
    JevHammerBenchmark.Research.structuralNeural \
  --config '{"guidePremises": false}' \
  --max-requests 1608 --max-input-tokens 16000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-structural-broad-v1
```
