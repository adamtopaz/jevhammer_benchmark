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

## First candidate screen, frozen before outcomes

Use the same 34 source locations with the new selector dependency and
`JevHammerBenchmark.Research` import, after offline re-admission checks every
selected location and goal. Compare `Prepared.sparse`, `Research.target`,
`Research.ensemble`, and `Research.neuralWarm`. All four retain Jev state guidance
and disable premise reranking. Search/tactic defaults remain identical.

The candidate parameters are fixed in jevselector's `notes/experiment-01.md`.
The neural reference warms both imported and earlier current-file statements
outside the goal clock, explicitly recorded as initialization, to avoid
disadvantaging it with a cold local-statement embedding cache. The goal itself
is still embedded at query time. This is a new initialization policy, not an
identical repeat of the baseline adapter. No target theorem/proof is available
to warmup or retrieval. Use a fresh service deployment for this screen.

The four-arm run allows 408 Jev requests and 4,000,000 reported input tokens,
under the same shared 16 GB zero-swap cap. Independently replay every success.
Publish all configurations and failures; do not select only a favorable arm.
