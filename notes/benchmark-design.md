# Public JevHammer benchmark design

Status: agreed requirements and proposed implementation, recorded 2026-09-18.

## Repository responsibilities

| Repository | Responsibility | Dependencies |
|---|---|---|
| `jevpilot` | Typed Jev client | Lean |
| `jevhammer` | Configurable proof search with Jev state guidance | Lean and JevPilot |
| `jevhammer_benchmark` | Source-location sampling, method registration, execution, proof verification, and reports | Mathlib and JevHammer; optional selector/comparator integrations |
| `jevselector` | Generic selector artifact preparation and CPU premise selection | Lean; JevPilot if used; other dependencies justified by the selected implementation |

The benchmark may use Mathlib-specific datasets and tactic presets. The selector
preparation API must not require Mathlib or the benchmark package. A benchmark
adapter should be able to consume `jevselector` without creating a dependency
cycle. The benchmark's sampling machinery should keep project/module inputs
explicit so it can later be reused beyond Mathlib.

Public code must not depend on sibling research worktrees, private absolute
paths, a particular password-store entry, or uncommitted setup scripts. Separate
optional neural-service and external-solver setup from the default installation.
Check licensing and attribution before copying research code or redistributing
third-party models, corpora, or binaries. Preserve the original research evidence.

## What defines a benchmark method

A named method consists of:

- A compiled `Lean.LibrarySuggestions.Selector` and its configuration/artifacts.
- A compiled `JevHammer.TacticSet`, including all five phases: `close`, `prepare`,
  `finish`, `steps`, and `cleanup`.
- A `JevHammer.Config`, including budgets, optional premise reranking, and refresh.
- Jev model/client settings and any explicitly configured decision cache.
- Required imports and optional runtime services.

Use the existing generic interfaces; avoid adding a new hardcoded dispatch
branch to the runner for each experiment. Function-valued selectors and tactic
generators cannot be identified adequately by a JSON configuration alone: record
their declaration names, defining source hashes/revisions, resolved dependencies,
and configuration. Record artifact hashes too. Two methods with different imports
or registered rules need those differences visible in the run manifest.

The default benchmark preset should preserve JevHammer's current collection.
Mathlib extensions can supply richer collections separately. Importing more
tactics must not silently redefine what an existing named method means.

For selector comparisons, hold the tactic collection, Jev state heuristic,
premise-reranking policy, budgets, source environment, and timing policy fixed.
For comparisons of complete pipelines, identify every changed component. Keep
Jev state guidance enabled in every JevHammer arm, including neural-selector
and deterministic-selector arms. Record whether a trial actually reached a
state-ranking decision or closed in the cheap prefix.

## Dataset and source-location contract

Benchmark intermediate tactic locations from actual source elaboration, using
the goal list, local context, environment, and shared metavariable state at that
location. Do not load the completed target module to reconstruct its earlier
goals. Later declarations, the target theorem itself, and benchmark helper
declarations must not become candidate premises through instrumentation.

Each dataset manifest should identify:

- Project, Lean toolchain, dependency revisions, and source content hashes.
- Module, owning declaration, source location, and expected goal fingerprint.
- Eligibility rules, deterministic sampling seed, and selected location IDs.
- Declaration-level development/confirmation/test partitions and exclusions.
- The treatment of generated helpers and other declarations owned by a theorem.

Reject changed or ambiguous source matches. Reuse the same frozen locations for
all methods. Restore the complete initial state between attempts, including
assignments shared by multiple goals. Report source-discovery or eligibility
failures before collection; do not silently change the sample afterward.

Multiple locations from the same theorem belong to the same partition. Final
confirmation must not share training proofs or development declarations with the
candidate's development runs. The old 1,024-site cohort remains useful for paired
regression checks; repeated tuning on it would not constitute a new unseen test.

## Timing, resources, and proof verification

The main outcome is a complete, independently checked proof within the stated
end-to-end goal budget. Timed work includes premise retrieval, Jev requests,
tactic execution, and proof construction/checking. Report compilation, artifact
loading, and declared one-time warmup separately; also provide cold-start results
where they matter. Do not give one method unreported goal-dependent warmup.

Search wall budgets are soft; record actual elapsed time and successful-but-late
proofs separately. Preserve unsuccessful, errored, timed-out, interrupted, and
resource-limited trials with explicit statuses and denominator rules. API
failures and deterministic fallbacks remain part of the measured pipeline.

Save proof certificates that can be verified against the allowed source
environment without Jev or premise-service access. Verification must reject
admissions, unresolved expression metavariables, and unavailable declarations.
Preserve shared witness assignments when a tactic solves multiple goals. A
successful elaboration log alone is not an independently replayed proof.

All related local processes share the 24 GB, zero-swap scope; no second heavy
run may escape that aggregate limit. Report peak memory, swap configuration,
worker counts, and OOM/resource events. The absolute user limit remains 32 GB.

## Reports and reusable artifacts

Produce versioned machine-readable manifests, per-trial records, certificates,
and aggregate reports. At minimum report:

- Deadline coverage, raw verified coverage, and paired gains/losses.
- Timing distributions for complete trials and separately for successes.
- Retrieval latency, artifact load time, preparation time, artifact size, and RAM.
- Premise counts, state/premise Jev calls, failures, fallback use, and reported tokens.
- Errors, censorship, late proofs, replay failures, and memory-limit events.
- Declaration-cluster uncertainty and repeated-run variation where appropriate.

Distinguish measured token usage from a complete billing ledger; failed requests
may have unknown usage. Distinguish fresh model runs from decision-cache replay.
Cached requests need exact input/model identities, recorded response provenance,
and an explicit latency policy. Report actual wall time separately from any
charged cached latency. Never silently overwrite a completed run or its ledger.

Keep large run outputs and caches outside the source tree by default. Provide
small public fixtures and commands for discovery, execution, offline replay,
and report regeneration. Offline CI should not require API credentials or a
large neural service. Live runs require explicit configuration of credentials,
resource limits, and usage budgets.

## Historical reference to reproduce

The previous selected method was `neural_search_jev`, exposed by
`jev_neural_live`: neural premise retrieval, Jev premise reranking, and Jev-guided
adaptive proof-state search. It used Aesop and the matching Mathlib tactic
environment as well as core Lean automation. It did not invoke LeanHammer's
proof engines.

| Budget and cohort | Selected method | Full LeanHammer |
|---|---:|---:|
| Six seconds, 1,024 held-out locations | 459 (44.8%) | 350 (34.2%) |
| Twenty seconds, fixed 256-location subset | 127 (49.6%) | 91 (35.5%) |

On the same 256-site subset, the selected method solved 114 within six seconds.
Do not compare the twenty-second subset percentage directly with the full
1,024-site six-second percentage as if only the budget changed.

Historical pins/settings:

- Lean 4.33.0.
- Mathlib `db584cd6d46c92f209a44c0f1c829460d327499d`.
- LeanHammer `21886b7ffbdf32017655a9d6e699f98779046533` and its pinned local CPU
  neural-selector model/corpus, ordinary fallback, and retrieval exclusions.
- Jev `jev-1.13.0`; premise reranking enabled.
- Practical: 6,000 ms, depth 3, 12 nodes, 3 shared Jev calls, 24 candidates,
  100 premises, beam width 4, premise prefix size 8, and one changed-goal refresh.
- 15,000 heartbeats per tactic attempt; 200,000 outer heartbeats for practical
  runs; eight Lean workers and synchronous elaboration.
- Extended: 20,000 ms, depth 5, 64 nodes, 8 calls, 666,667 outer heartbeats.

The research checkout retains the detailed protocol, selector deployment pins,
source archives, resource events, and repeat results in `notes/finisher-results.md`,
`notes/final-evaluation-design.md`, and their linked artifacts. These are migration
inputs, not runtime dependencies of the public benchmark repository.

The new JevHammer package has implementation changes, including configurable
generators and budgeted preparation. Build and test the baseline adapter under
the new harness, then run matched comparisons before attaching old scores to
the new package. Preserve the frozen old implementation for diagnosing migration
differences. Historical scores are reference evidence, not guarantees of exact
counts from a fresh model run.
