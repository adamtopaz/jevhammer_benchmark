# CPU selector research: baseline protocol

Frozen before collection, 2026-09-19, branch `research/cpu-selector`.
The selector research plan is in jevselector's branch of the same name under
`notes/cpu-selector-research.md`.

The first run compares `Prepared.sparse` with `Neural.neural` on the existing
34-site `datasets/sparse-jev-v1/dataset.json` development pilot. This compares
their existing configurations: plain sparse retrieval versus neural retrieval
with Jev premise reranking. Both retain Jev proof-state guidance, the identical
Mathlib tactic set, six-second budgets, and three shared Jev calls. A second
matched run sets `guidePremises` to false for both methods to measure the neural
selector without premise reranking. All other configuration remains unchanged.
Neither run touches the reserved evaluation partition.

Each run is limited to 204 Jev requests and 4,000,000 reported input tokens.
All attempts, including ranking errors and unsuccessful proofs, are retained.
There are no retries. Every success is replayed independently. Compare paired
locations and report total goal time, selector warmup, retrieval time, API usage,
and ranking failures. The external neural model's training overlap is unknown.

Use the historical CPU model/corpus pins from
`integrations/neural/provenance.example.json`, with deployment and embedding
validation provenance recorded separately for the actual endpoint. CPU service
and benchmark MUST share one **16,000,000,000-byte, zero-swap cgroup**, with two
Lean and embedding threads. This tighter user limit overrides older 24 GB
examples. No independent heavy build or extraction may run alongside collection.

The current public adapter does not provide Sine fallback on neural failure.
Diagnose service/compatibility failures before interpreting incomplete results.
Changes to methods or dependencies require dataset re-admission with identical
selected locations and observed goals, not silently changing fingerprints.
