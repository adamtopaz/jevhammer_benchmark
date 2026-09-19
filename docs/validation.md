# Initial validation (2026-09-18)

These are offline integration checks. Mock ranking preserves candidate order;
it does not measure Jev's decisions, API latency, or neural-selector quality.
No comparison with full LeanHammer or performance-parity claim follows from
these results.

## Automated checks

The bounded offline suite exercises 14 source locations with two methods, for
28 trials. Every fixture trial closes and independently replays. The fixture
includes multiple goals, universes, local definitions, earlier premises, and
private declarations. Negative checks reject corrupted certificates, mismatched
goals, admissions, inconsistent shared witnesses, changed/missing locations,
and importing a target module before its own evaluation.

The larger Mathlib check exposed a source-map bug in generated tactics.
JevHammer now evaluates each generated script with its own matching source map,
with a regression test that failed before the fix. The benchmark also rejects
runtime panic diagnostics even when Lean returns exit status zero. JevHammer's
test matrix covers Lean 4.33.0 and 4.34.0; this benchmark uses 4.33.0.

## Mathlib smoke results (mock ranking)

At benchmark commit `809ad64`, all 64 trials completed and all 23 successful
trial certificates replayed against their original source goals:

| Premise selector, with the same tactic set | On-time verified | Recorded trials |
|---|---:|---:|
| Prepared statement-symbol index | 13/32 | 32 |
| Sine Qua Non + current-file premises | 10/32 | 32 |

The prepared selector gained three locations and lost none in this small
cohort. There were no late successes, ranking failures, module failures, or
runtime panics, and no API calls. These results validate integration; they
do not establish a reliable quality improvement or predict live Jev results.
The [machine-readable summary](validation-2026-09-18.json) records pins,
settings, paired counts, preparation costs, and latency measurements.

## Whole-library preparation and CPU cost

Generic JevSelector preparation over the pinned Mathlib snapshot exported
255,050 theorem statements. The evaluation exclusion set removed 46
declarations/helpers, including 21 theorem rows, before fitting statistics.
The resulting 255,029-row fit took **202.6 seconds** and produced a
**155,686,860-byte** index. Toolchains and compiled Mathlib imports were already
available; downloading them is outside that measurement.

A separate native CPU profile with the same catalog and fitting eligibility
measured **46.6 ms median**, **104.1 ms 95th percentile**, and **3.7 seconds cold
loading** over 48 queries (16 theorem types, three repeats). See
[JevSelector's validation](https://github.com/adamtopaz/jevselector/blob/main/docs/validation.md)
for settings and limitations. Query latency does not establish proof coverage.

Heavy local checks use one 24,000,000,000-byte, zero-swap cgroup at a time, with
two Lean worker threads, below the requested 32 GB ceiling.

## Reproducing the Mathlib smoke cohort

The cohort uses seed 0 and 32 of 250 eligible locations across 25 declarations
in three modules. Use the repository's pinned dependencies and the same imports:

```sh
jevbench discover --modules Mathlib.Topology.Basic Mathlib.LinearAlgebra.Basis.Basic \
  Mathlib.RingTheory.Ideal.Basic --import JevHammerBenchmark.Selector \
  --import JevHammerBenchmark.Neural --count 32 --seed 0 --output runs/validation
jevbench holdouts --dataset runs/validation/dataset.json --output runs/holdouts.json
jevselector prepare --project . --modules Mathlib --scope Mathlib \
  --exclude runs/holdouts.json --output artifacts/validation
export JEVSELECTOR_INDEX="$PWD/artifacts/validation/index.json"
jevbench run --dataset runs/validation/dataset.json --mock \
  --methods JevHammerBenchmark.Prepared.sparseReranked JevHammerBenchmark.Methods.expandedReranked \
  --output runs/validation-paired
```

The neural adapter is imported to check compatibility, but neither arm calls
a neural selector service. Both use the same expanded Mathlib tactic collection
and default 6-second search budget. The mock replaces both premise reranking
and proof-state guidance. Replace `--mock` with explicit API budgets only for
a separately recorded live experiment.
