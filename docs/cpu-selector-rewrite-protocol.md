# Bounded rewrite-source development screen

Recorded before any rewrite-source proof outcomes. This tests whether equality
and iff patterns that match goal/context subexpressions complement the existing
whole-conclusion index. It is a generic signature-only source; neither index
reads proof bodies or fits a model. No individual failed goals guided the design.

Use selector `fab11ad748b77910d0edfe5575acce074da1a145`, including the tested
application-head traversal correction and caller-filter state restoration. Measure
full-library costs of the corrected rewrite index and combined modes before proof
trials; earlier single-index timings are not combined-mode measurements.

The completed matched-warmup pilot selects CPU native order (16/34 versus 13/34)
and neural Jev premise reranking (14/34 versus 13/34), following the predeclared
highest on-time verified coverage, then total goal-time rule. The choice comes
from development data and does not establish optimal guidance on unseen goals.

| Method | Premise sources | Jev premise reranking |
|---|---|---|
| `RewriteStudy.cpuControl` | Public sparse + conclusion patterns | No |
| `RewriteStudy.cpuRewrites` | Public sparse + conclusion + rewrite patterns | No |
| `RewriteStudy.signatureOnly` | Conclusion + rewrite patterns | No |
| `RewriteStudy.neuralControl` | Warmed neural + conclusion patterns | Yes |
| `RewriteStudy.neuralRewrites` | Warmed neural + conclusion + rewrite patterns | Yes |

Every arm retains Jev proof-state guidance, identical Mathlib tactics, six seconds
per goal, three shared Jev calls, 100 retrieved names, eight injected premises,
and the same premise-refresh policy. Controls and their rewrite variants use
identical search configurations. The signature-only ablation uses CPU settings.
This compares complete selector configurations; CPU/neural differences include
their development-selected premise guidance, so do not attribute every difference
solely to retrieval quality.

Use flat reciprocal-rank fusion (offset 16, pool factor 2, maximum pool 256).
The rewrite source visits at most 256 distinct expressions with at most 64
pattern queries, depth eight, and eight propositional hypotheses after the goal.
It uses 10,000 query heartbeats and weights forward matches twice as much as
backward matches. Each premise receives its strongest weighted match. These
parameters are fixed before collection and shared by both rewrite variants.

Give every method independent mutable conclusion/rewrite caches copied from fixed
`True` warmup bases. Initialization of both indexes stays outside goal timing;
query-specific lazy expansion stays inside. Immutable preparation and imported
statement data may be shared; report warmup costs and order-dependent attribution.
Start fresh CPU neural services, warming imported and earlier current-file
statements outside goal timing in both neural arms. Goal embeddings stay timed.

Re-admit all **34 original pilot locations and owners**, without changing source
sites or goals. All 188 broad-cohort owners remain excluded from the fitted sparse
statistics. Keep the **122 reserved evaluation locations untouched**. Do not use
this exposed pilot to claim final superiority. A promising candidate must pass a
larger matched development comparison before reserved evaluation.

Run **170 trials**, at most **510 Jev requests** and **5,000,000 reported input
tokens**, with two threads and serial modules. Enclose services, Lean workers,
and independent replay in one aggregate **16,000,000,000-byte, zero-swap cgroup**.
Run no other heavy work concurrently. Preserve errors, late results, and budget
blocking. Replay every claimed proof against its original source context; publish
all methods, paired declaration-grouped uncertainty, retrieval/goal/warmup costs,
actual premise/state calls, usage, memory events, and provenance. No selective
retry or goal-specific tuning.

After preparing the public sparse artifact and configuring the pinned CPU neural
endpoint (see the neural integration documentation), run:

```sh
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-rewrites-v1.json \
  --methods JevHammerBenchmark.RewriteStudy.cpuControl \
    JevHammerBenchmark.RewriteStudy.cpuRewrites \
    JevHammerBenchmark.RewriteStudy.signatureOnly \
    JevHammerBenchmark.RewriteStudy.neuralControl \
    JevHammerBenchmark.RewriteStudy.neuralRewrites \
  --config '{}' \
  --max-requests 510 --max-input-tokens 5000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-rewrites-v1
```
