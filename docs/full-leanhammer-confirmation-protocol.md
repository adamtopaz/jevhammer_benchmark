# Full LeanHammer confirmation study

Protocol fixed on 2026-09-21, before new goal discovery or proof trials. The
34-location development pilot selected CPU/conclusion JevHammer as the primary
candidate. This study compares that unchanged method against full LeanHammer
on **1,024 new locations from 1,024 distinct declarations**. Neural/conclusion
JevHammer is a prespecified secondary comparator. No tuning or manual
failed-goal analysis is permitted during collection.

## Population and sampling

Use the pilot's pinned Lean 4.33.0, Mathlib, JevHammer, JevSelector, neural
model/corpus and full LeanHammer revisions, through the unchanged optional
`integrations/leanhammer` project. Exclude the complete import closure of that
harness, the prior-exposure manifest, all modules/owners with recorded public
trials, and the entire older 256-location cohort. Its 122 reserved goals remain
untouched. Publish exclusion inputs and hashes.

Use the same 17 subject areas as `mathlib-broad-v1`. Within each area, consider
source files of 3,000–30,000 bytes with at least 12 lexical `by` tokens and no
`deprecated_module` or `assert_not_exists`. Sort eligible modules by SHA-256 of
`jevbench-full-confirmation-v1:MODULE` and take the first eight per area (136
modules). These size filters limit elaboration cost; this is a stratified,
size-filtered sample, not a uniform sample of all Mathlib.

Discover locations without invoking any tested tactic. Sample 1,024 eligible
locations with seed 20260921, equal module turns, and a strict cap of one per
owning declaration. If fewer than 1,024 owners are available, extend each area's
module list in the same hash order before any proof trials. Discovery errors
are retained and must be resolved or documented before the final cohort is
frozen; no proof outcomes may influence eligibility. Never admit a partially
elaborated module as successful discovery.

Prepare the identical public-constant sparse/IDF artifact recipe on Mathlib,
excluding all new evaluation owners and all 188 earlier cohort owners (including
named children). No proof bodies are used by this recipe. Structural retrieval
continues to use available signatures only. Verify all holdouts before trials.
Third-party neural training overlap remains unknown.

## Methods, budgets and order

Reuse `LeanHammerComparison.cpu`, `.neural`, and `.full` without changing their
tactics or settings. Both JevHammer methods use Jev `jev-1.13.0` for state
guidance, depth 3, 12 nodes, beam 4, 24 successor candidates, 100 retrieved
premises, 8/16 finishing prefixes, at most one premise refresh and three Jev
calls. No premise reranking or deferred guidance. Individual tactic attempts
receive 15,000 heartbeats; the complete invocation gets 200,000.

Full LeanHammer retains all engines and default parallelism, upstream neural
selection with its ordinary recorded Sine fallback, the default five-second
internal solver timeout, and 200,000 heartbeats for its complete invocation.
It makes no Jev calls. All methods use eight Lean workers, synchronous
elaboration, the same source goals, and an observed **six-second end-to-end
deadline** including retrieval and certificate creation. Initialization is
outside goal timing and reported separately. Replay all late proofs as well.

Assign modules to six batches by round-robin after sorting their module hashes
with seed `jevbench-full-confirmation-order-v1`. Run the six lexicographically
ordered permutations of `(cpu, full, neural)`, one per batch. Each method/module
uses a separate Lean process. Start fresh neural service processes for each arm
of each batch; persistent model/corpus disk caches are disclosed. Every arm
uses two embedding threads. This counterbalances order without allowing the
CPU artifact cache to coexist inside full LeanHammer's Lean process.

Collect exactly **3,072 trials**, without optional stopping, adaptive extension,
selective retries or result-dependent configuration changes. Each Jev arm has
at most three requests and 35,000 reported input tokens per selected location,
aggregated within its batch. Across the study these permit at most **6,144 Jev
requests and 71,680,000 reported input tokens**. Failed/unknown calls remain in
the accounting; one call may cross the token threshold. Budget blocks and
infrastructure failures remain visible and cannot be silently dropped.

All preparation, services, solvers, Lean processes and replay share a maximum
**16,000,000,000 bytes of RAM and zero swap**, with one heavy job at a time.
Record memory peaks/events and stop owned services after every arm. Freeze the
final dataset, artifact hash, schedule and exporter before proof collection.

## Outcomes and analysis

Primary outcome: on-time independently replayed proof at each location.
Primary contrast: CPU/conclusion JevHammer minus full LeanHammer. Report counts,
rates, paired gains/losses, absolute percentage-point difference and costs.
The two remaining pairwise contrasts are secondary and explicitly labeled.

The main uncertainty interval is a paired **module bootstrap stratified by
subject area**, 20,000 resamples, seed 20260921, percentile 2.5%/97.5%. Resample
whole modules within each area, retaining all their paired location outcomes;
compute each resample's difference divided by its resampled location count.
Also report declaration/location bootstrap intervals and the exact two-sided
McNemar p-value on discordant pairs. The latter assumes independent pairs and
is a sensitivity analysis, since same-module goals can be correlated (see
[NIST's assumptions](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/mcnemar.htm)).
Do not base a superiority claim solely on the unclustered p-value. A positive
primary result requires the primary module-bootstrap interval to exclude zero;
report effect size regardless. Secondary tests are exploratory, not additional
confirmatory claims, and their two McNemar p-values receive Holm adjustment.

Sample-size planning uses no new outcomes. Under a rough independent-pair
approximation, 1,024 pairs with 25% discordance give about 89% power for a
five-percentage-point difference at two-sided 5%. Correlation and a different
discordance rate can reduce that power. This target improves precision; it
does not guarantee significance, equivalence or a particular winner.

Publish all trials, independent replay counts, late successes, ranking/API
failures, neural fallbacks/unavailable suggestions, time, warmup, tokens,
resource measurements, pins and evidence hashes. Treat incomplete collection
as incomplete evidence. Do not pool the earlier pilot into confirmation counts.
Single-run Jev variability and the sampled population limit generalization.
