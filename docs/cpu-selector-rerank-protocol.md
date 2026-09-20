# Matched-warmup premise reranking check

Frozen after the completed 134-location development comparison, before this
experiment's proof outcomes. The earlier neural-reranking reference warmed only
imported statements; its non-reranked follow-up reused the service cache. That
comparison cannot establish the strongest configuration under the later, improved
warmup policy. This experiment checks premise reranking with matched warmup.

The predeclared selection rule chooses highest full-development verified coverage,
then lower retrieval time for ties, separately among CPU and neural sources.
It selects **public sparse + structural fusion (63/134)** and **neural + structural
fusion (64/134)**. Both use selector `b8b0a95`; the newly implemented rewrite mode
is not included. Preserve the frozen rank-fusion parameters and search settings.

| Method | Source | Jev premise reranking |
|---|---|---|
| `RerankStudy.cpuNative` | Public sparse + structural | No |
| `RerankStudy.cpuReranked` | Public sparse + structural | Yes |
| `RerankStudy.neuralNative` | Warmed neural + structural | No |
| `RerankStudy.neuralReranked` | Warmed neural + structural | Yes |

All four retain Jev proof-state guidance, the same Mathlib tactic set, six seconds
per goal, **three shared Jev calls**, 100 retrieved names, eight injected premises,
and the unchanged refresh policy. Premise ranking consumes the shared call/time
budget. A native configuration check ensures that only `guidePremises` differs
among search configurations; do not override it globally in the driver. Verify
the actual premise/state call counts in the final evidence.

Use the existing **34-location / 34-owner development pilot**, re-admitting every
original goal under the new adapter import. No resampling or per-goal tuning.
All 188 broad-cohort owners remain excluded from fitted sparse statistics. The
122 reserved evaluation locations stay untouched. This is an exposed development
ablation, not the final acceptance test.

Start fresh CPU neural services with the published pinned model/corpus and
float32 validation. Warm imported and earlier current-file statement embeddings
outside the goal clock for both neural arms; actual goal embeddings stay timed.
The service caches statement embeddings, not goal embeddings (audited upstream
`retrieve.py`). Give all four methods independent mutable structural caches copied
from the same fixed-`True` base. Shared immutable initialization is reported
separately; method-by-method startup attribution is order-dependent.

Run **136 trials**, capped at **408 Jev requests** and **4,000,000 reported input
tokens**, in one aggregate **16,000,000,000-byte, zero-swap cgroup** containing both
services and all Lean workers. Use two threads and serial source modules. Run no
other heavy work concurrently. Keep all errors, late proofs, and budget blocking;
independently replay every claimed success before reporting coverage. Publish
paired counts/intervals, retrieval/goal/startup costs, request kinds and usage,
rank failures, memory events, and any interruption. Do not selectively retry.

After preparing the public index and configuring a fresh neural endpoint:

```sh
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-rerank-v1.json \
  --methods JevHammerBenchmark.RerankStudy.cpuNative \
    JevHammerBenchmark.RerankStudy.cpuReranked \
    JevHammerBenchmark.RerankStudy.neuralNative \
    JevHammerBenchmark.RerankStudy.neuralReranked \
  --config '{}' \
  --max-requests 408 --max-input-tokens 4000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-rerank-v1
```
