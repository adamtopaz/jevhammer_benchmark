# Mathlib broad benchmark v1

This cohort expands the three-module pilot to 17 subject areas. Module selection,
site sampling, exclusions and split rules are fixed before running either tactic.
The goal is 256 source locations, with at most two per owning declaration, and
approximately half reserved for later evaluation. Only development is used for
the initial live Sine Qua Non versus sparse comparison.

## Module selection

`modules.json` contains two candidate files from each of Algebra, Analysis,
CategoryTheory, Combinatorics, Computability, Data, Dynamics, FieldTheory,
Geometry, LinearAlgebra, MeasureTheory, NumberTheory, Order, Probability,
RingTheory, SetTheory and Topology. Selection uses the pinned Mathlib source:

1. Exclude the harness import closure and every module in `prior-exposure.json`.
2. Keep files of 3,000–30,000 bytes with at least 12 lexical `by` tokens, excluding
   files containing `deprecated_module` or `assert_not_exists`.
3. Within each subject area, order by SHA-256 of `jevbench-broad-v1:MODULE` and
   select the first two files.

`recipe.json` records source hashes, candidate counts and all sampling settings.
These lexical size filters bound source-elaboration costs; the result is a
deliberately stratified, size-filtered sample, not a uniform sample of Mathlib.

Discovery remains strict: incompatible imports, failed source elaboration and
missing locations must be diagnosed and recorded before finalizing the cohort.
Any compatibility changes to this candidate list must be published, without
consulting tactic success rates. Original failed discovery evidence is retained.

The first discovery completed all 34 modules but exposed unnamed `example`
parents in the eligible pool. Eligibility was strengthened to require an owner
that persists after its source command; otherwise it cannot identify a training
exclusion. The same module list, seed, cap and split rules are rediscovered under
that check. No tactic trials were run on the preliminary sample.

## Prior exposure and split

`prior-exposure.json` joins actual legacy trial sites to their recorded manifests
and unions the public pilot's trial owners. It excludes 827 owning declarations
and all 46 source modules seen in 27 recorded earlier runs. The file includes
source-record checksums; no previous checkout is needed to use these exclusions.
Only recorded exposure is claimed, not absence from every possible human or
third-party training source.

Site sampling uses seed 1, equal module turns, and a cap of two locations per
declaration. The 50/50 split uses seed 1 and groups declarations within each
module. A declaration and all its sampled locations stay in one partition.
Single-owner modules, if any survive discovery, stay entirely in development.
Exclude the union of both partitions when preparing the shared sparse artifact.

```sh
jevbench discover --modules-file datasets/mathlib-broad-v1/modules.json \
  --exclude datasets/mathlib-broad-v1/prior-exposure.json \
  --max-per-declaration 2 --count 256 --seed 1 \
  --import JevHammerBenchmark.Selector --import JevHammerBenchmark.Neural \
  --output runs/mathlib-broad-discovery
jevbench split --dataset runs/mathlib-broad-discovery/dataset.json \
  --test-fraction 0.5 --stratify-by-module --seed 1 --output runs/mathlib-broad-split
jevbench holdouts --dataset runs/mathlib-broad-discovery/dataset.json \
  --output runs/mathlib-broad-holdouts.json
jevselector prepare --modules Mathlib --scope Mathlib \
  --exclude runs/mathlib-broad-holdouts.json --output artifacts/mathlib-broad
```

## Initial comparison protocol

Use `JevHammerBenchmark.Methods.expanded` and
`JevHammerBenchmark.Prepared.sparse`, unchanged from the 32-location live pilot.
Both use live `jev-1.13.0` proof-state guidance, the same Mathlib tactics, six
seconds per location, at most three Jev calls per trial, and no premise reranking.
Freeze code before collection; do not tune methods using this run's outcomes.

For N development locations, allow at most 6N requests across both arms and
62,500N reported input tokens. Retries remain disabled. Warmup is separate from
the goal clock; every successful trial must replay independently. Report
failures, late successes and fallback decisions without dropping trials.

Use a single 24,000,000,000-byte zero-swap scope, two Lean threads, and serial
module execution. The reserved evaluation partition receives no tactic trials
during this expansion. Full LeanHammer and neural-selector comparisons remain
separate experiments.
