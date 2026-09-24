# Current-system proof-state guidance ablation

Specified before new proof trials, 2026-09-24. This is a **256-goal first pass**,
not a new unseen evaluation: the parent 1,024-goal cohort has published outcomes.
No failed-goal inspection, tactic tuning, selective retries, or optional stopping.

## Intervention

Run `LeanHammerComparison.strict`, the current available-imports CPU
sparse/conclusion configuration, five times per goal:

1. Fresh Jev state ranking, with its real latency charged.
2. Fixed candidate order.
3. Random order, seed 17.
4. Random order, seed 29.
5. Random order, seed 43.

Random order is a Fisher–Yates permutation using the pinned Lean PRNG and a
private stream seeded from the experiment seed and source-site identifier.
Every candidate appears once in each permutation. Existing ancestor/sibling
deduplication is identical in all arms. There is no new global visited-state
filter. Method names and execution order do not enter the random seed.

Change **only the ranking policy**. The same CPU premise selector, imports-only
fit, full 1,212-owner holdout, tactics, candidate generation, and proof checks
apply to all arms. Premise ranking is disabled. Every ranking decision, including
fixed/random, consumes one of the same three slots: `maxCalls := 0` would also
disable premise refresh and is not an appropriate control. Ranking failures in
the Jev arm retain the ordinary fixed-order fallback and count toward its result.

Keep the six-second goal deadline, 200,000 outer heartbeats, 15,000 tactic
heartbeats, depth 3, 12 nodes, beam width 4, 24 successors, 100 retrieved premises,
8/16 premise prefixes, and one premise refresh. Eight Lean threads, one arm at a
time, in one aggregate **16,000,000,000-byte RAM, zero-swap** cgroup. Initializing
the selector is outside the goal clock and reported separately. Independent
offline kernel replay is required for every successful proof, including late
proofs; late successes do not count toward coverage.

No neural premise service runs in any arm. The Jev arm uses the hosted model;
fixed/random use no model or API credential. Fresh Jev requests have no decision
cache. The study permits at most 768 Jev requests and an aggregate 8,960,000
reported-input-token stop, allocated per batch at three requests and 35,000
tokens per goal. One response may cross a batch token threshold; unknown usage
is reported. These are stopping limits, not prepaid usage or guaranteed costs.

## Selection and execution order

Read only the parent dataset's source metadata, not its result rows. Within each
of its 17 top-level Mathlib areas, sort modules by SHA-256 of
`jevbench-state-guidance-v1:MODULE`. Visit one module from each area, in sorted
area order, then the next module from each area, until 256 sites are selected.
Within modules sort sites by SHA-256 of `jevbench-state-guidance-v1:SITE`; truncate
only the boundary module. This selects **256 distinct owners in 33 modules and
all 17 areas**. It is a deterministic area-spanning cluster subsample, not a
uniform sample of Mathlib goals. Retain the exact original goal text and source
bytes. Re-admit all selected sites under the updated benchmark dependency before
proof trials; failed admission stops the study rather than replacing a module.

Sort selected modules by the same hash, then assign them round-robin to ten
batches. For treatments `[jev, fixed, random17, random29, random43]`, use the five
cyclic relabelings of index order `[0, 1, 4, 2, 3]` (add 0 through 4 modulo 5),
then their reversals. Each arm
occupies each position twice and every ordered adjacent pair occurs twice.
Whole modules remain in one batch; site counts per batch can differ. Run all
50 batch/arm combinations, including unsuccessful and late trials.

Freeze the protocol, admitted dataset, schedule, dependency pins, and code in
Git before the first trial. Record fingerprints, per-decision permutations,
request accounting, failures, warmup provenance, and resource events. A failed
arm stops collection and retains its evidence; no automatic restart/retry.

## Analysis

Co-primary comparisons are Jev minus fixed, and Jev minus the **mean of the three
prespecified random runs**. Never select the best or worst random seed as the
primary comparator or treat the three outcomes at one goal as independent goals.
Report paired gains/losses for binary comparisons and mean solve differences.

Use 20,000 paired bootstrap draws of whole modules within Mathlib area, seed
20260924, retaining all methods/seeds for each sampled module. Report 95%
intervals descriptively and 97.5% intervals for the two co-primary comparisons
(Bonferroni familywise 95% coverage). The random-average interval is conditional
on these three seeds; it does not estimate all possible model/random-run
variability. With only 33 modules, including two single-module strata, uncertainty
is approximate and conditional on this sample. A larger independent evaluation
would be needed for a broad superiority claim. An inconclusive first pass does
not establish equivalence.

Also report each random seed, costs, latency, no-ranking versus after-ranking
solves, failures, and all replay/resource checks. A model call preceding a proof
is not itself evidence of contribution; use matched outcome differences.
Historical combined-guidance ablations are context, not pooled observations.
