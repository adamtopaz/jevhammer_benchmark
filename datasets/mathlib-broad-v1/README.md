# Mathlib broad benchmark v1

This frozen cohort contains **256 source locations from 188 declarations across
34 modules in 17 subject areas**, sampled from 2,916 eligible locations (3,012
discovered). Every module elaborated successfully. At most two locations come
from any one declaration.

| Partition | Locations | Declarations | Modules |
|---|---:|---:|---:|
| [Development](development.json) | 134 | 99 | 34 |
| [Reserved evaluation](test.json) | 122 | 89 | 34 |

The partitions share no owning declarations. Module selection, site sampling,
exclusions and split rules were fixed before running either tactic. Only
development is used for the initial live Sine Qua Non versus sparse comparison.
The [full dataset](dataset.json), [per-module summary](summary.json), and
[combined preparation holdouts](holdouts.json) are portable files in this repo.
Use the matching source revision: the driver enforces project/dependency hashes.

The [completed development comparison](../../docs/mathlib-broad-v1-results.md)
recorded all 268 paired trials: Sine Qua Non verified 49/134 locations and sparse
verified 58/134. All 107 successful trials replayed independently. The report
includes per-location outcomes and the earlier incomplete attempt; the reserved
evaluation split has not been attempted.

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

To use the shipped manifests after the repository's standard installation:

```sh
jevselector prepare --modules Mathlib --scope Mathlib \
  --exclude datasets/mathlib-broad-v1/holdouts.json --output artifacts/mathlib-broad
export JEVSELECTOR_INDEX="$PWD/artifacts/mathlib-broad/index.json"
# Supply TYPESAFE_API_KEY through your environment/secret manager.
jevbench run --dataset datasets/mathlib-broad-v1/development.json \
  --methods JevHammerBenchmark.Methods.expanded JevHammerBenchmark.Prepared.sparse \
  --max-requests 804 --max-input-tokens 8375000 --output runs/mathlib-broad-live
```

To reproduce discovery and splitting instead:

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
`JevHammerBenchmark.Prepared.sparse`, with the same tactic settings as the
32-location live pilot and the current-file compatibility correction below.
Both use live `jev-1.13.0` proof-state guidance, the same Mathlib tactics, six
seconds per location, at most three Jev calls per trial, and no premise reranking.
Freeze code before collection; do not tune methods using this run's outcomes.

For N development locations, allow at most 6N requests across both arms and
62,500N reported input tokens. Retries remain disabled. Warmup is separate from
the goal clock; every successful trial must replay independently. Report
failures, late successes and fallback decisions without dropping trials.
For the frozen 134-location development partition these limits are **804
requests** and **8,375,000 reported input tokens**.

Use a single 24,000,000,000-byte zero-swap scope, two Lean threads, and serial
module execution. The reserved evaluation partition receives no tactic trials
during this expansion. Full LeanHammer and neural-selector comparisons remain
separate experiments.

## Compatibility correction before the complete comparison

The [first live attempt](../../docs/mathlib-broad-v1-incomplete.json) recorded
253 of 268 expected trials. Sparse warmup rejected freshly elaborated statements
in two modules: their raw expression hashes differed from the compiled catalog
because elaboration produced different auxiliary names or instance terms.
Collection was incomplete, so no comparative success rates were accepted.

JevSelector `41e1afac56702e2294bb036f6572f57348db15cf` recomputes all current-file
premise features from the live environment and retains strict hash checks for
imported declarations. Its regression tests also ensure that disabling
current-file premises excludes cataloged current-file declarations. This is a
general correction for editing and re-elaboration; no goals or modules were
removed, and no tactic settings were tuned.

Rediscovery under the corrected dependency reproduced every sampled site, goal,
owner and split assignment exactly; only dependency/resource fingerprints were
refreshed. The [offline compatibility check](../../docs/mathlib-broad-v1-compatibility.json)
then passed admission and source consistency at all 134 development locations
across 34 modules. It used a zero goal budget and made no Jev calls, so it is not
a performance measurement. The entire paired live comparison was repeated, with
the incomplete attempt and its usage retained separately. The reserved
evaluation partition stays untouched.

The comparison reuses the [prepared artifact](preparation.json): fitting and the
188-owner exclusion set did not change. Its provenance references the original
dataset fingerprint, preserved in Git history. Re-preparing with the current
dependency records new provenance while using the same fitting recipe.
