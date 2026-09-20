# CPU selector research: development results

These exploratory comparisons belong to `research/cpu-selector`. The
[protocol](../notes/cpu-selector-research.md) was committed before collection.
The 122-site reserved evaluation partition has not been used.

## First neural reference: complete

On the fixed 34-site, 34-module development pilot, with six seconds per goal:

| Configuration | On-time verified | Total goal time |
|---|---:|---:|
| Prepared sparse + Jev state guidance | 13/34 | 120.289 s |
| Neural retrieval + Jev premise/state guidance | 11/34 | 160.954 s |

Sparse gained three locations and lost one. The declaration-bootstrap 95%
interval for sparse minus neural is **−5.9 to +17.6 percentage points**. This
small development result does not establish superiority. All 68 trials were
recorded and all 24 successful proofs independently replayed, with no late
successes or budget-blocked trials. The sparse arm had five ranking failures;
the neural arm had none. Failures remain included in the results.

Both used the same expanded Mathlib tactics and Jev proof-state guidance. The
neural arm additionally reranked premises, sharing the same three-call cap with
state guidance. This is a comparison of the two existing configurations. The
second pre-registered comparison disables premise reranking in both arms;
its separate results follow below.

The pinned CPU neural service and the benchmark shared one **16,000,000,000-byte,
zero-swap cgroup**. The measured peak was **11,343,564,800 bytes**, with no limit
or OOM events. This replaces the earlier 24 GB execution limit. Model, corpus,
deployment validation, request costs, configurations, and evidence hashes are
in the [machine-readable report](cpu-selector-neural-reranked-reference.json).
[Every trial](cpu-selector-neural-reranked-reference-trials.jsonl) is also published.

Neural initialization warms the imported catalog outside the goal clock. New
current-file statements can still require embedding during retrieval, and that
time is included. The service remains alive between the two configurations, so
the second run can benefit from its embedding cache. The external model's
training overlap is unknown. No new selector has been benchmarked at this stage,
and no result here reproduces or supersedes the historical 1,024-site evaluation.

## Neural retrieval without premise reranking: complete

| Configuration | On-time verified | Total goal time | Retrieval time |
|---|---:|---:|---:|
| Prepared sparse + Jev state guidance | 14/34 | 116.860 s | 4.669 s |
| Neural retrieval + Jev state guidance | 15/34 | 117.648 s | 10.788 s |

Neural gained one location and lost none against the concurrent sparse control.
The paired interval for neural minus sparse is **0.0 to +8.8 points**. All 68
trials were recorded and all 29 successes independently replayed. Neither arm
had late successes or budget-blocked trials. Sparse had two ranking failures;
neural had three. All failures are included. The run used 102 Jev requests,
535,487 reported input tokens, and 12,146 reported output tokens, with unknown
usage on four requests. The cumulative service/benchmark memory peak remained
11.34 GB, with no cgroup limit or OOM events.

The higher neural result does **not** isolate the effect of removing premise
reranking: this second run also reused the first run's service embedding cache,
and the fresh sparse control itself changed from 13 to 14 successes. Neural
retrieval's total time fell from 48.814 to 10.788 seconds across runs. Use the
15/34 configuration as the stronger observed reference for further experiments,
with matched fresh controls and explicit cache conditions.

[Second machine-readable report](cpu-selector-neural-retrieval-reference.json)
and [all second-run trials](cpu-selector-neural-retrieval-reference-trials.jsonl).
Across both runs there are 136 recorded trials and 53 independently replayed
successful trials, on the same 34 development locations. This is a baseline
milestone; no new-selector improvement has been demonstrated yet.

## First candidate CPU profiles

On 32 deterministic theorem-type queries from the full Mathlib catalog, repeated
three times per method, using the excluded artifact and two CPU threads:

| Method | Median query | p95 query | Cold index load |
|---|---:|---:|---:|
| Original sparse | 66.6 ms | 130.1 ms | 3.833 s |
| Target-weighted | 66.9 ms | 131.9 ms | 3.969 s |
| Reciprocal-rank fusion | 217.3 ms | 342.0 ms | 4.300 s |

Target weighting has similar measured cost to the default. Fusion is slower and
misses the provisional 200 ms p95 target; retain its proof-coverage experiment
to measure the tradeoff before deciding whether to optimize or reject it. These
are latency profiles, not proof results. No model calls were made. The shared
16 GB zero-swap scope peaked at 6.64 GB with no limit/OOM events.
[Machine-readable profiles](cpu-selector-profile-v1.json).

## Four-way candidate screen: complete

All four methods ran on the same 34 development locations, with Jev proof-state
guidance, no premise reranking, and identical six-second search/tactic settings.
The neural reference explicitly warmed the imported and earlier current-file
statement catalog outside the goal clock. This is the initialization policy
frozen for this screen, not an identical repeat of the earlier neural adapter.

| Method | On-time verified | Raw replayed | Total goal time | Retrieval time |
|---|---:|---:|---:|---:|
| Original sparse | 13/34 | 13 | 120.848 s | 4.797 s |
| Target-weighted | **14/34** | 14 | 119.546 s | 4.849 s |
| Reciprocal-rank fusion | 12/34 | 13 | 127.270 s | 10.286 s |
| Warmed neural reference | **14/34** | 14 | 121.770 s | 10.675 s |

Target weighting gained one location and lost none against its concurrent sparse
control. Against neural it gained one and lost one: equal coverage, different
solved sets. The paired 95% interval for target minus sparse is 0.0 to +8.8
percentage points, and for target minus neural it is −8.8 to +8.8 points. This is
a small development improvement over the matched sparse control, **not a
significant improvement over the neural reference**, nor a new best across the
different earlier runs (the earlier neural-only run solved 15).

All **136 expected trials** were recorded and **54 successful proofs independently
replayed**. Fusion's late proof is excluded from on-time coverage. There were no
module failures or budget-blocked trials. The methods had respectively 3, 6, 3,
and 1 ranking failures, all retained with fallback in the outcomes and timings.
The run used 215 Jev requests, 1,199,076 reported input tokens, and 27,354 reported
output tokens, with unavailable usage for eight HTTP errors. Peak combined RAM
was **9.47 GB**, below the 16 GB zero-swap cap, with no limit/OOM events.

Retain target weighting as a cheap candidate for broader testing. Fusion adds
latency without a coverage gain in this screen; do not promote it. Continue with
proof-neighbor transfer as the next substantive hypothesis. The reserved
evaluation partition remains untouched.

[Full configurations, costs, and evidence](cpu-selector-candidates-v1.json) and
[all per-location outcomes](cpu-selector-candidates-v1-trials.jsonl).

## Proof-neighbor preparation and CPU profiling

The new CPU model retrieves 32 similar eligible theorem statements and votes for
the public lemmas directly used by their proofs. Its optional fusion combines
these votes with original sparse retrieval. Exclusions are enforced before
reading examples and fitting label frequencies; private/helper bodies are not
recursively opened. Runtime suggestions must be available in the current Lean
environment. No neural training or Jev call is used for preparation or retrieval.

Preparing the dependency companion for the existing excluded Mathlib index took
**282.25 seconds**: **254,885 proofs**, **1,536,554 edges**, **145,736 labels**,
and a **65.17 MB** artifact. Peak memory was **8.01 GB** under the 16 GB zero-swap
cap, with no memory-limit/OOM events. This excludes the original statement-index
preparation cost. [Preparation measurements](cpu-selector-dependency-preparation-v1.json).

| Method | Median query | p95 query | Combined index/model load |
|---|---:|---:|---:|
| Direct proof-neighbor votes | 45.0 ms | 95.4 ms | 7.89 s |
| Sparse + proof-neighbor fusion | 164.5 ms | 278.1 ms | 6.35 s |

These use the same 32 deterministic theorem types and three repetitions as the
earlier CPU profiles. Direct voting meets the provisional 200 ms p95 target;
fusion misses it. The scope peaked at 2.81 GB with no memory events. These are
cost measurements only; the paired proof results are reported below.
[Query profile evidence](cpu-selector-profile-dependencies-v1.json).

## Proof-neighbor screen: complete, no coverage improvement

The four methods ran on the same re-admitted 34 development locations, with the
same tactics, six-second budgets, and Jev proof-state guidance. No premise
reranking was used. Both neural services started fresh, and the reference warmed
imported/earlier current-file statements outside the goal clock as before.

| Method | On-time verified | Total goal time | Retrieval time |
|---|---:|---:|---:|
| Target-weighted | 13/34 | 120.498 s | 5.668 s |
| Direct proof-neighbor votes | 12/34 | 138.081 s | 4.409 s |
| Sparse + proof-neighbor fusion | 12/34 | 126.539 s | 9.869 s |
| Warmed neural reference | **14/34** | 121.789 s | 10.428 s |

Direct voting gained one location and lost three against neural; its paired 95%
interval is −17.6 to +5.9 percentage points. Fusion gained none and lost two
(−14.7 to 0.0 points). Neither candidate improves coverage. Target weighting also
lost one net location against neural in this fresh run, underscoring that its
earlier tie was not evidence of superiority. Keep the dependency preparation and
retrieval APIs as experimental infrastructure; do not promote these configurations.

All **136 expected trials** were recorded, and **all 51 successful proofs
independently replayed**. There were no late proofs, module failures, or blocked
trials. All 15 ranking failures remain included: 4 target, 7 direct voting,
3 fusion, and 1 neural. The run made 226 Jev requests, with 1,230,897 reported
input tokens, 29,524 output tokens, and unknown usage for eight HTTP errors.
Combined peak RAM was **9.19 GB** under the shared 16 GB zero-swap limit, with
no limit/OOM events. The reserved evaluation partition remains untouched.

The next implementation aggregates premise-usage features across all eligible
examples instead of transferring from only 32 neighbors. Its CPU cost and proof
coverage have not yet been measured. Structural statement features remain another
documented hypothesis. The research objective is still open.

[Complete configurations and evidence](cpu-selector-neighbors-v1.json),
[all per-location outcomes](cpu-selector-neighbors-v1-trials.jsonl).

## Learned premise-usage model: preparation and query costs

The new model aggregates the statement features of all eligible proofs using
each premise. It fits sparse smoothed likelihood profiles by counting, with
smoothing mass 20 and at most 64 positive corrections per label. Fitting reuses
the excluded artifacts and takes **14.08 s**, producing **145,736 profiles** and
**4,971,407 feature edges** in **251.89 MB**. Peak RAM was **4.54 GB**, with no
limit/OOM events. Prior statement/proof extraction costs are separate.
[Fitting measurements](cpu-selector-usage-preparation-v1.json).

The first full-library profile failed before querying because printed hygienic
constant names were reparsed as identifiers and collapsed to anonymous. The
fixed reader preserves opaque feature strings in both usage and sparse lookup.
Its regression suite passes. The same artifact bytes can be reused, but the
matched target reference must also run under corrected selector `63c3d60`.

| Method | Median query | p95 query | Cold index/model load |
|---|---:|---:|---:|
| Learned usage profiles | **39.1 ms** | **74.1 ms** | 20.71 s |
| Corrected target-weighted retrieval | 66.8 ms | 132.1 ms | 2.66 s |

The profile uses 32 deterministic theorem types with three repetitions, without
proof attempts or model calls. Both warm costs meet the provisional target, but
usage loading is substantially slower. Peak scope memory was 5.01 GB with no
memory events. [Profile and failed-preflight evidence](cpu-selector-profile-usage-v1.json).
The next live three-arm screen compares usage, target, and warmed neural retrieval
at the same 34 development locations; no coverage result is available yet.

## Usage-model screen: complete, no coverage gain

All three methods used the corrected opaque-feature reader, identical tactics
and six-second budgets, and Jev proof-state guidance without premise reranking.
The neural service started fresh with the same catalog warmup policy as before.

| Method | On-time verified | Total goal time | Retrieval time |
|---|---:|---:|---:|
| Target-weighted | **14/34** | 116.184 s | 5.104 s |
| Learned usage profiles | 10/34 | 124.844 s | 2.431 s |
| Warmed neural reference | **14/34** | 120.631 s | 10.807 s |

Usage selection gained no location and lost four against each reference. Its
paired interval versus neural is −23.5 to −2.9 percentage points. Its successful
set is a subset of each reference's successful set in this pilot. Fast fitting
and lookup therefore did not translate into stronger proofs. Do not promote this
configuration or claim it improves coverage. Target and neural gained one and
lost one against each other, with paired interval −8.8 to +8.8 points.

All **102 trials** were recorded and **38 successful proofs independently
replayed**. There were no late proofs, blocked trials, or module failures. All
11 ranking errors remain included (5 target, 4 usage, 2 neural). The run used
171 Jev requests, 841,290 reported input tokens, 20,924 output tokens, and unknown
usage for eight HTTP errors. Combined peak memory was **11.42 GB** under the
shared 16 GB zero-swap cap, with no memory-limit/OOM events. No reserved
evaluation location was run.

The next implementation broadens the premise universe to public definitions and
constructors while keeping fitted statistics and proof owners theorem-only.
Its coverage is unmeasured. Structural retrieval and bounded applicability
reranking remain separate hypotheses. The research goal remains unfulfilled.

[Complete evidence](cpu-selector-usage-v1.json),
[all per-location outcomes](cpu-selector-usage-v1-trials.jsonl).

## Public catalogs and closure ranking: cost measured, proof screen pending

The public-constant catalog has **318,231 rows**, including **63,162 eligible
candidate-only constants**, while retaining **254,885 theorem training owners**.
Preparation took **232.66 s** and produced **183.78 MB**. Its public-label companion
contains **187,655 premises** and **5,249,157 direct edges**, taking **739.28 s**
and **129.56 MB**. Definition/helper bodies remain unopened. Exhaustive artifact
audits confirm unchanged original theorem rows, owners, exclusions, fitted
symbol weights, original dependency edges, and original label hashes/weights.
[Statement preparation](cpu-selector-public-catalog-preparation-v1.json),
[label preparation](cpu-selector-public-dependencies-preparation-v1.json).

`closingFirst` is a generic CPU wrapper: retrieve up to 100 names, probe the first
64 filtered candidates, and promote those that close by application plus local
assumptions or reflexivity. Probes have a 1,000-heartbeat limit and at most four
subgoals. It restores Lean state and returns only names; no model calls or training
are hidden in the wrapper. Native integration checks and 19 Python tests pass.

| Method | Median query | p95 query | Cold load |
|---|---:|---:|---:|
| Original target ranking | 65.62 ms | 128.19 ms | 2.39 s |
| Target + closure ranking | 105.90 ms | 216.91 ms | 2.48 s |
| Public-catalog target | 83.40 ms | 152.40 ms | 2.84 s |
| Public-label neighbors | 52.73 ms | 86.35 ms | 7.39 s |

Each profile has 32 deterministic statement types × 3 repetitions. The first
two use identical types; the public-catalog pair samples different types from
the expanded catalog, including non-theorems. These are latency profiles, not
source-goal proof measurements. Closure p95 slightly exceeds the provisional
200 ms target but is affordable enough for one proof screen; parameters remain
unchanged. The serial scope peaked at **3.85 GB** with no memory events under
the **16 GB, zero-swap cap**. [Profile evidence](cpu-selector-profile-public-closure-v1.json).

The [frozen six-arm screen](cpu-selector-public-closure-protocol.md) compares these
four methods with warmed neural retrieval and equally closure-ranked neural
retrieval, using the same 34 development goals, six-second limits, tactic sets,
and Jev proof-state guidance. Re-admission verifies unchanged source goals.
The reserved evaluation split remains untouched. No coverage improvement has
yet been established for either intervention.

## Public-catalog and closure screen: complete, small exploratory gain

All **204 trials** completed, and **all 82 successes independently replayed**.
There were no late successes, blocked trials, or module failures. Every arm used
the same six-second budget, Mathlib tactics, and Jev proof-state guidance, without
Jev premise reranking. Neural services started fresh with the frozen warmup policy.

| Method | On-time verified | Total goal time | Retrieval time |
|---|---:|---:|---:|
| Original target ranking | 14/34 | 118.923 s | 5.629 s |
| Public-catalog target | **15/34** | **113.456 s** | 5.399 s |
| Public-label neighbors | 12/34 | 124.376 s | 5.003 s |
| Target + closure ranking | 13/34 | 122.517 s | 7.838 s |
| Warmed neural reference | 14/34 | 120.244 s | 10.614 s |
| Neural + closure ranking | 14/34 | 122.997 s | 14.109 s |

The expanded catalog gained one location and lost none against the original
target selector. Against either neural arm it gained two and lost one, with a
paired declaration-bootstrap 95% interval of **−5.9 to +11.8 percentage points**.
This is a one-goal exploratory lead, not statistically established superiority.
Retain the expanded catalog as a promising CPU candidate for larger development
validation; do not claim the research objective is achieved.

Public-label voting still trails neural by two locations and has the slowest
preparation of these candidates. Closure ranking added cost and no coverage to
neural; it lost one location when applied to target retrieval. Neither is promoted
as an improved configuration. Candidate parameters were unchanged during the run.

All **23 ranking/API errors** remain in the results (3, 5, 5, 4, 1, 5 by arm).
The run made **326 Jev requests**, with **1,836,304 reported input tokens**,
**43,911 output tokens**, and unknown usage for **15** requests. Combined peak
memory was **12.85 GB**, with no memory events under the shared **16 GB zero-swap
cap**. Services stopped after replay. No reserved evaluation trial was run.

The next candidate uses Lean's signature discrimination tree as an additional
premise source; implementation is under validation. Its initialization and query
costs must be measured before proof evaluation. The significant-improvement goal
remains open.

[Complete configurations and evidence](cpu-selector-public-closure-v1.json),
[all per-location outcomes](cpu-selector-public-closure-v1-trials.jsonl).

## Structural signatures: CPU costs before the proof screen

The new signature index initializes from actual imported public types, without
proof values or fitted data. It uses Lean's lazy discrimination tree, includes
both directions of iff declarations, and ranks by pattern specificity. Updated
deny policies, actual availability, type hashes, state restoration, and independent
query caches have native regression coverage. All 19 Python tests and the native
artifact/selector integration checks pass.

| Method | Median query | p95 query | Structural initialization |
|---|---:|---:|---:|
| Public-catalog target | 78.36 ms | 144.66 ms | — |
| Structural signatures | **6.12 ms** | **91.65 ms** | 27.54 s |
| Public target + structural fusion | 159.67 ms | 289.05 ms | 27.56 s |

These use identical 32 public statement types × 3 repeats. Artifact loading was
2.77–2.93 s separately; pure structural selection uses the artifact only to choose
the profile queries. Structural initialization includes fixed `True` warmup;
actual-query lazy expansion remains timed. The serial scope peaked at **4.71 GB**
under the 16 GB zero-swap bound, without memory events. Fusion exceeds the
provisional 200 ms p95 target; its extra cost is explicit, not a quality claim.
[Complete CPU measurements](cpu-selector-profile-structural-v1.json).

The [frozen five-arm pilot](cpu-selector-structural-protocol.md) compares public
target, structural-only, their fusion, warmed neural, and the same structural
fusion applied to neural. Per-method mutable caches prevent cross-arm warming
on evaluation goals. The same 34 development goals are re-admitted; reserved
evaluation remains unused. These profiles alone establish no proof-coverage gain.

## Structural screen: two-goal CPU fusion lead

The frozen five-arm run completed all **170 trials** at the same 34 development
locations. All **70 successful proofs independently replayed**; none were late,
budget-blocked, or lost to a module failure. The selector revision was `b8b0a95`
and benchmark revision `debb49f`; no parameters changed during collection.

| Method | On-time verified | Total goal time | Retrieval time |
|---|---:|---:|---:|
| Public-catalog target | 15/34 | 112.113 s | 5.354 s |
| Structural signatures | 12/34 | 126.089 s | 0.666 s |
| Public target + structural | **16/34** | 116.620 s | 6.820 s |
| Warmed neural reference | 14/34 | 120.828 s | 10.321 s |
| Neural + structural | 13/34 | 126.641 s | 12.245 s |

CPU fusion gained one location and lost none against public target. Against
neural it gained **two and lost none**, an observed **+5.9 percentage points**
with paired declaration-bootstrap 95% interval **0 to +14.7 points**. Against
neural fusion it gained three and lost none, interval **0 to +17.6 points**.
All other arms' successes were subsets of CPU fusion in this run. This is a
promising exposed-pilot result, not established significant superiority. It
motivates the [134-location development comparison](cpu-selector-structural-broad-protocol.md)
with both neural references and unchanged implementation/search parameters.

Structural-only retrieval was inexpensive but weaker. Fusion's extra retrieval
cost over sparse was 1.466 seconds across the full run, including refreshes;
the separate full-library profile still exceeded the provisional 200 ms p95
target. Costs and initialization must accompany any coverage claim.

All **15 ranking/API failures** remain in the results (6, 3, 3, 1, 2 by arm).
The run made **244 Jev requests**, with **1,413,999 reported input tokens**,
**34,304 output tokens**, and **8** requests of unknown usage. Combined peak
memory was **11.82 GB**, with no memory events under the shared **16 GB zero-swap
cap**. CPU services stopped after replay. The 122 reserved evaluation locations
remain unused. No individual failures were analyzed to tune the selector.

[Complete configurations and evidence](cpu-selector-structural-v1.json),
[all per-location outcomes](cpu-selector-structural-v1-trials.jsonl).

## Full development: structural CPU fusion ties plain neural, trails neural fusion

The frozen comparison completed all **536 trials at 134 locations from 99
declarations**. All **247 successful proofs independently replayed**, none were
late or budget-blocked, and every source file re-elaborated during replay.
Benchmark `405f7fe` used the unchanged selector `b8b0a95`; all methods retained
Jev proof-state guidance, no premise reranking, and identical six-second budgets.

| Method | On-time verified | Total goal time | Retrieval time |
|---|---:|---:|---:|
| Public-catalog target | 57/134 (42.5%) | 424.942 s | 22.724 s |
| Public target + structural | **63/134 (47.0%)** | 414.761 s | 26.698 s |
| Warmed neural reference | **63/134 (47.0%)** | 403.897 s | 54.893 s |
| Neural + structural | **64/134 (47.8%)** | 417.450 s | 62.836 s |

CPU fusion gained seven locations and lost one against public sparse: **+4.5
percentage points**, with declaration-grouped paired bootstrap 95% interval
**+0.75 to +8.73 points**. Against plain neural it gained seven and lost seven,
interval **−5.15 to +5.60 points**. Against neural fusion it gained five and lost
six, interval **−5.51 to +4.32 points**. The pilot lead did not establish a larger
development advantage. CPU fusion is a measured improvement over sparse, with
roughly half the neural retrieval time, but it has not beaten the strongest
neural reference and does not satisfy the research goal.

The exploratory exposure breakdown reinforces that limitation:

| Development subset | Locations | Sparse | CPU fusion | Neural | Neural fusion |
|---|---:|---:|---:|---:|---:|
| Original selector-pilot locations | 34 | 15 | 16 | 14 | 13 |
| Other locations of pilot owners | 19 | 9 | 10 | 9 | 9 |
| Owners absent from selector pilot | 81 | 33 | 37 | 40 | 42 |

The last subset has 65 owners and still has earlier broad-baseline exposure;
it is not an untouched test set. Do not reinterpret these development strata as
independent significance tests. The 122 reserved evaluation locations remain
unused. No individual failed goals were analyzed to tune the selector.

The host execution environment changed after **92 complete four-method trial
groups (368 trials)** were recorded. The launcher and Lean workers had exited,
while the original two neural services remained live. Recovery preserved the
original records and all **410** prior request decisions, resumed only the 42
untouched goals in 11 modules, and joined the same original 16 GB cgroup with
the same neural-service processes and caches. No trial was retried and no usage
counter was reset. Retained logs had no panic/error markers; all 134 source
locations and successful certificates subsequently passed independent replay.
The interruption and before/after evidence are retained in the machine report.

All **32 ranking/API failures** remain included (9, 13, 5, 5 by arm). There were
**675 Jev requests**, **3,611,284 reported input tokens**, **96,696 output tokens**,
and **14** requests with unknown usage. Combined peak was **10.51 GB**, with no
memory events under the shared **16 GB, zero-swap bound**. Services stopped after
replay. This run used no Jev premise-ranking calls; state-ranking calls were
recorded in every arm.

Next, compare the selected CPU fusion and stronger neural fusion with and without
Jev premise reranking under matched current-file/imported catalog warmup. The
earlier reranking reference had a warmup/cache confound and cannot settle that
comparison. Bounded rewrite-pattern retrieval is a separate validated candidate
whose full-library cost is being measured before proof trials.

[Complete configurations, paired intervals, exposure breakdown, and recovery audit](cpu-selector-structural-broad-v1.json),
[all 536 per-location outcomes](cpu-selector-structural-broad-v1-trials.jsonl).

## Bounded rewrite retrieval: measured costs, no proof result yet

The validated rewrite mode indexes both sides of equality/iff signatures and
matches a bounded set of goal/context subexpressions. It reads no proof values,
fits no statistics, and calls no model. On identical 32 public statement types
with three repeats per method:

| Method | Median query | p95 query | Structural initialization |
|---|---:|---:|---:|
| Public sparse target | 78.65 ms | 142.45 ms | — |
| Rewrite patterns | **16.20 ms** | **92.18 ms** | 28.03 s |
| Public sparse + rewrite fusion | 179.97 ms | 299.02 ms | 28.00 s |

Initialization includes fixed `True` warmup. Actual-shape expansion stays in
query timing, and artifact loading is reported separately (2.78–2.92 s). The
shared serial scope peaked at **3.63 GB**, with no memory events under **16 GB,
zero swap**. Pure rewrite retrieval meets the provisional query-cost target;
fusion exceeds the 200 ms p95 target. These are latency measurements, not proof
coverage. An explicit import/plugin overlay used validated selector `ae41248`
(documentation revision `ed067b0`) without changing the proof benchmark's pin.
[Full profile and binary-artifact provenance](cpu-selector-profile-rewrites-v1.json).

## Matched-warmup premise reranking

All **136 trials** completed at the same 34 exposed development locations.
Every one of the **57 successful proofs independently replayed**. One proof in
the neural-reranked arm was late and is excluded from the on-time result.

| Method | On-time verified | Total goal time | Retrieval time | Reported input tokens |
|---|---:|---:|---:|---:|
| CPU fusion, native order | **16/34 (47.1%)** | 116.441 s | 6.728 s | 240,565 |
| CPU fusion, Jev reranked | 13/34 (38.2%) | 137.314 s | 6.532 s | 1,064,223 |
| Neural fusion, native order | 13/34 (38.2%) | 125.498 s | 11.889 s | 291,528 |
| Neural fusion, Jev reranked | **14/34 (41.2%)** | 139.348 s | 11.773 s | 1,118,159 |

Benchmark `2a5fffb` and selector `b8b0a95` used six seconds and three shared Jev
calls per goal, with Jev proof-state guidance in every arm. Both neural arms
warmed imported and earlier current-file statement embeddings outside the clock;
goal embeddings remained timed. Each method had independent mutable structural
query caches. Shared initialization and warmup costs are reported separately;
per-arm startup attribution is order-dependent.

Native CPU order gained three and lost none against CPU reranking. Against the
stronger reranked neural arm, it gained three and lost one: **+5.9 points**, with
paired declaration-bootstrap 95% interval **−2.94 to +17.65 points**. This small,
previously exposed pilot does not establish superiority. In the larger completed
development comparison, CPU fusion did not beat neural fusion.

The native CPU/neural arms made **42/46 state-ranking calls** and no premise
calls; the reranked arms made **49/50 premise calls** and **24/23 state calls**.
Reranking used roughly four times the input tokens while leaving fewer calls for
state guidance. These observations do not isolate ranking quality from the
shared-budget tradeoff. All **7 ranking/API errors** remain counted (2/3/2/0).
There were **234 requests**, **2,714,475 reported input tokens**, **184,811 output
tokens**, and one request with unknown usage. No trials were budget-blocked.
Peak memory was **11.01 GB**, without memory events under **16 GB, zero swap**;
services stopped after replay. The 122 reserved evaluation locations are untouched.

The predeclared coverage-then-goal-time rule chooses native CPU order and Jev
reranking for neural fusion in the next rewrite-source screen. Those settings
will be shared by each control and its rewrite variant, with CPU settings for
the signature-only ablation. They are development choices, not unseen-goal claims.

[Complete configurations, paired intervals, request kinds, and costs](cpu-selector-rerank-v1.json),
[all 136 per-location outcomes](cpu-selector-rerank-v1-trials.jsonl).

## Corrected rewrite traversal and combined-source costs

Selector `fab11ad` includes application heads in the bounded rewrite traversal;
a synthetic function-equality regression fails against the previous build and
passes against the correction. Native structural/rewrite suites, 19 Python tests,
and combined fixture profiles pass. Full-Mathlib timing uses the same 32 public
statement types × 3 repeats, explicitly requesting 100 suggestions:

| Method | Median query | p95 query | Signature initialization |
|---|---:|---:|---:|
| Rewrite patterns | 15.99 ms | 75.10 ms | 28.28 s |
| Public sparse + conclusion patterns | 156.04 ms | 284.07 ms | 27.40 s |
| Conclusion + rewrite patterns | 67.14 ms | 200.25 ms | 56.40 s |
| Public sparse + conclusion + rewrite patterns | 209.73 ms | 361.55 ms | 55.87 s |

Both combined modes initialize two indexes. Initialization includes fixed `True`
warmup; actual-goal lazy expansion stays in query timing. Artifact loading is
separate (2.76–2.95 s). The shared serial scope peaked at **5.14 GB**, with no memory
events under **16 GB and zero swap**. The provisional 200 ms p95 target is exceeded
by both combined modes, slightly for signature-only and materially for three-source
fusion. Proof coverage is still unmeasured. Each method used a fresh Lean process;
no model calls were made, and the frozen proof benchmark stayed pinned to its old
selector during profiling. The report records the explicit import/plugin overlay
and binary checksums.

[Complete corrected and combined profile evidence](cpu-selector-profile-combined-v1.json).
