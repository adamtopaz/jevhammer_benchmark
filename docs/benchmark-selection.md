# How the confirmation problems were selected

The [1,024-goal confirmation](full-leanhammer-confirmation-v1.md) tests finishing
at actual intermediate proof states. A location can contain several open goals;
success must close all of them. This is not complete theorem synthesis from the
surrounding declaration's original statement.

## Module selection

The source is Mathlib `db584cd6d46c92f209a44c0f1c829460d327499d`, using Lean
4.33.0. The 17 areas are Algebra, Analysis, CategoryTheory, Combinatorics,
Computability, Data, Dynamics, FieldTheory, Geometry, LinearAlgebra, MeasureTheory,
NumberTheory, Order, Probability, RingTheory, SetTheory and Topology.

Before any new proof outcomes, the planner excluded the harness's complete
import closure, all modules/owners in recorded earlier benchmark runs and the
prior-exposure manifest, and the entire older 256-location cohort, including its
122 reserved locations. Testing already-imported modules would expose their
completed declarations to the tactic.

Remaining source files had to contain 3,000–30,000 bytes, at least 12 lexical
`by` tokens, and neither `deprecated_module` nor `assert_not_exists`. These are
cost/compatibility filters; lexical tokens are not eligible-goal counts. Within
each area, candidates were sorted by SHA-256 of
`jevbench-full-confirmation-v1:MODULE`; the first eight were selected, giving
136 modules. This is deterministic, stratified sampling, not a uniform random
sample of all Mathlib.

The [recipe](../datasets/full-leanhammer-confirmation-v1/recipe.json) includes
every candidate queue, source checksum, filter and seed. The
[exclusions](../datasets/full-leanhammer-confirmation-v1/exclusions.json) list
blocked names and exposure-input checksums. The implementation is
[`plan_leanhammer_cohort.py`](../scripts/plan_leanhammer_cohort.py). Only module
and owner identities, never success/failure outcomes, enter its exclusion step.

## Proof-state discovery and sampling

Discovery elaborates original source with Mathlib's tactic-analysis hook. It
records states before tactic nodes with source positions and nonempty goals,
skipping nodes marked as possibly failing. Records contain module, byte range,
owning declaration, goal/context text, goal count and a goal fingerprint.
Duplicate location identifiers are removed.

Eligibility requires a real owner that survives elaboration and an environment
saved before the enclosing command. The owner itself must not already exist
there. All constants in the goals, local types and local-definition values must
be available in that preceding-command environment. Anonymous `example`s and
states depending on unavailable generated declarations are ineligible. Earlier
current-file declarations remain available. Search and replay use the saved
environment, not the completed theorem's environment. See
[`Hook.lean`](../JevHammerBenchmark/Hook.lean).

Discovery makes no tested-tactic calls or Jev requests. Five entire modules
failed original-source elaboration after the harness imports were added:
`Combinatorics.SimpleGraph.Extremal.Turan`, `Computability.Language`,
`Computability.Reduce`, `NumberTheory.NumberField.Units.Regulator`, and
`Order.BourbakiWitt` (under `Mathlib`). All five were excluded before site
sampling or proof trials, without replacement. Diagnostics and hashes were
retained; no source proofs were patched. This leaves 131 modules across all
17 areas, with 14,424 discovered locations and 14,038 eligible before owner
capping. Compatibility exclusions are an additional population limitation.

Within each module, locations are sorted by SHA-256 of `20260921:SITE_ID`.
The sampler visits modules in sorted name order and takes one location per
module per round, skipping owners already selected, until it has exactly 1,024
locations from 1,024 distinct declarations. Thus a long proof cannot contribute
many nearby states. See `select_sites` in [`cli.py`](../jevhammer_benchmark/cli.py).

The frozen [dataset](../datasets/full-leanhammer-confirmation-v1/dataset.json)
contains every location and goal text; the
[summary](../datasets/full-leanhammer-confirmation-v1/summary.json) gives area
counts. Both were committed before the first proof trial.

## Holdouts, batches and analysis

CPU preparation excluded all 1,024 evaluation owners plus 188 earlier cohort
owners, including resolved named children. The recipe uses public statement
features and IDF statistics, not proof bodies. Lean validates compiled statement
identities and all 1,212 explicit owner exclusions before evaluation. Available
premises can be selected at runtime subject to availability and caller filters.
This is a fitted-owner holdout; third-party neural training overlap is unknown.
It does not exclude related or downstream declarations from statement statistics.
The original CPU catalog also contains unavailable statements, filtered at query
time. Consequently this is not a dependency-isolated or chronological holdout.
The [available-premise follow-up](available-premises-protocol.md) removes that
exposure from the CPU fit and imported postings.

Modules are sorted by SHA-256 of `jevbench-full-confirmation-order-v1:MODULE`
and distributed round-robin into six batches, keeping whole modules together.
Each permutation of `(cpu, full, neural)` is used once. Batch sizes are 169,
176, 169, 174, 178 and 158. The [schedule](../datasets/full-leanhammer-confirmation-v1/schedule.json)
records method order, dataset identities and request budgets.

Every method attempts every location once. A counted proof must arrive within
six seconds end to end and independently kernel-replay against the original
source goal. Late proofs are replayed but excluded from on-time coverage. Once
collection starts, failed trials cannot be dropped, goals cannot be replaced,
and the sample cannot grow based on results. All 3,072 trials completed in the
published study. API/ranking failures remain in the scores.

The primary contrast is CPU JevHammer minus full LeanHammer. Its 95% interval
resamples whole modules within subject areas, retaining paired outcomes, using
20,000 resamples and seed 20260921. The other contrasts are secondary. The
[protocol](full-leanhammer-confirmation-protocol.md) describes sensitivity tests;
the [report](full-leanhammer-confirmation-v1.md) gives counts and limitations.
Once these public outcomes inform development, this cohort is no longer unseen
validation for that work.
