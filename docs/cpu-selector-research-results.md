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
