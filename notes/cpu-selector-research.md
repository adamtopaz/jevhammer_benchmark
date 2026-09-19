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

## Proof-neighbor screen, frozen before outcomes

The next model transfers direct proof dependencies from the 32 most similar
eligible training statements. Preparation excludes all cohort owners before
reading any example proof, omits recursively hidden helper dependencies, and
fits dependency-frequency weights only on eligible examples. Its complete
fixed recipe is in jevselector's `notes/experiment-02.md`.

After measuring full-library preparation and query costs, compare
`Research.neighbors`, `Research.proofHybrid`, `Research.target`, and
`Research.neuralWarm` at the same 34 development locations. Target-weighted
retrieval replaces sparse as the inexpensive reference because it had the
highest CPU-selector coverage in the first screen. The two new methods use
direct dependency votes and fusion with original sparse retrieval, respectively.
No candidate has access to excluded owners' proof bodies, and every returned
premise is checked against the real environment and caller filter.

Re-admit identical locations and goals under the updated sources; use a fresh
neural service deployment. Keep the same tactic configuration, six-second limit,
three-call budget, and Jev proof-state guidance without premise reranking.
Allow at most 408 requests and 4,000,000 reported input tokens. Run all local
services and Lean processes together in one 16 GB zero-swap cgroup; independently
replay all successes. Dependency/index caches are shared across compatible
methods within each module process, so per-method initialization is ordered and
must be reported separately. No reserved evaluation data will be inspected.

## Learned premise-usage screen, frozen before outcomes

The next model aggregates statement symbols across all eligible proofs using each
premise. It fits smoothed sparse likelihood profiles with mass 20 and retains each
label's 64 strongest feature corrections, preserving full normalization. The
formulation and pruning policy are fixed in jevselector's experiment-04 note.
This fitting pass reuses the exact excluded statement/dependency artifacts and
does not inspect additional proof bodies. Runtime lookup uses only CPU postings.

After preparation and query-cost checks, compare `Research.usage`,
`Research.target`, and `Research.neuralWarm` at the same 34 development locations,
re-admitted under the new sources. Keep identical six-second budgets, tactics,
three-call limits, and Jev state guidance without premise reranking. Start fresh
neural services and retain the same catalog warmup policy. Permit at most 306
requests and 3,000,000 reported input tokens in a shared 16 GB zero-swap scope.
Independently replay every success and publish all failures. The reserved
evaluation split remains untouched. Do not combine structural features or Jev
premise reranking into this first usage-model screen.

The first usage query preflight exposed a generic feature-key serialization bug:
printed hygienic names need not parse as identifiers. The corrected selector
keeps feature keys as opaque strings. This changes sparse query behavior as well,
so re-admit and rerun target retrieval under the same fixed revision as usage.
The failed preflight attempted no proof goals and made no model calls. Existing
artifact bytes and training exclusions remain unchanged; preserve the failed log
and report the reader revision with the successful profile and benchmark.
