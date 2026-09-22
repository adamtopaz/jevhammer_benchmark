# Available-premise sensitivity study

Protocol specified before follow-up proof trials, 2026-09-22.

The original CPU selector excluded evaluated owners from fitted statistics,
but used other Mathlib statements, including later/downstream declarations.
This follow-up measures a stricter preparation policy without tuning the tactic
or inspecting individual failed goals. It is a sensitivity study on previously
exposed goals, not a new unseen confirmation.

## Strict preparation

For each source module, build the sparse index from **only imported Mathlib
signatures in the safe preceding-command environment**. Never load the original
full-library artifact in this arm. Exclude every owner in the original 1,212-owner
holdout, including named children, from IDF and mean-length fitting. Public
definitions/constructors remain candidate-only. No proof bodies are inspected.
All imported postings and their deterministic sampling are built only from these
available signatures, so unavailable catalog rows cannot affect the query.

Earlier current-file premises remain available through the existing selector's
live-signature supplementation. They do not contribute to the imports-only fit.
The index is initialized once per module, outside the goal clock, and its time,
counts and identity are recorded in warmup.jsonl. This is a deliberately
conservative subset of the statements available before each tested theorem;
it does not refit statistics on the growing current-file prefix.

The conclusion matcher, target/context weights (4/1), pivoted length penalty,
rank fusion, tactic collection, depth, beam and request budgets remain unchanged.
The neural selector and Jev remain third-party pretrained models with unknown
training overlap; this study cannot certify their training as uncontaminated.

## Comparisons and sampling

Reuse the original 1,024 locations and goal texts. Re-admit the complete source
modules under the added method, verifying every selected location and goal is
unchanged. Never drop a source/proof failure based on follow-up results. Keep
one goal location per owner and retain all 131 modules/17 areas.

Compare strict CPU, original CPU, neural/conclusion JevHammer and full LeanHammer.
Primary comparison: strict CPU minus original CPU. Secondary comparisons: strict
CPU minus each neural comparator. Each method attempts each location once.
Retain unsuccessful and late trials; independently kernel-replay all successes.
No selective retries, optional stopping, or tuning after collection starts.

Assign whole modules to four batches by round-robin after sorting by SHA-256 of
`jevbench-available-premises-v1:MODULE`. Counterbalance order with a four-treatment
Williams design: strict/cpu/full/neural; cpu/neural/strict/full;
neural/full/cpu/strict; full/strict/neural/cpu. Every method occupies each position
once and every ordered pair of adjacent methods occurs once.

Use the original six-second end-to-end goal deadline, 200,000 outer heartbeats,
eight Lean workers, two CPU embedding threads, and one aggregate **16 GB,
zero-swap** cgroup. Each Jev arm permits three calls and 35,000 reported input
tokens per selected location. Start fresh local neural services for each arm;
initialization is outside goal timing and reported separately. Local disk caches
persist. Hold all model, Mathlib, solver and tactic pins fixed.

Report paired counts and stratified module-bootstrap 95% intervals using the
existing analysis implementation (20,000 draws). The original CPU arm controls
for changing Jev responses and timing; paired differences still have run noise.
Do not interpret an insignificant difference as equivalence. Publish all trial
records, costs, preparation measurements, source/configuration hashes and
resource events, together with portable reproduction instructions.
