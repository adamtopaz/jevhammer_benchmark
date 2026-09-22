# jevhammer_benchmark

Public, reproducible source-location benchmarks for
[JevHammer](https://github.com/adamtopaz/jevhammer). Compare named premise
selectors, tactic sets, and search configurations at actual intermediate Lean
goals. Successful proofs are saved as expression certificates and independently
kernel-checked against the original source goals, without API calls.

JevHammer comparison arms use **Jev for proof-state guidance**. Offline mock ranking
is available for infrastructure tests and is explicitly labeled in reports.
The repository includes Sine Qua Non baselines, a prepared
[JevSelector](https://github.com/adamtopaz/jevselector) adapter, and an opt-in
neural premise-service adapter, plus an optional full LeanHammer comparison.

## Results: 1,024 fresh Mathlib goals

The completed confirmation attempted **3,072 trials** at 1,024 intermediate
goals from distinct declarations across 131 modules and 17 subject areas. Each
method had a six-second end-to-end deadline and the same 16 GB, zero-swap cap.

| Method | On-time, independently verified proofs | Success rate |
|---|---:|---:|
| JevHammer + CPU sparse/conclusion selector | 450/1,024 | 43.95% |
| JevHammer + neural/conclusion selector | 469/1,024 | 45.80% |
| Full LeanHammer + upstream neural selector | 372/1,024 | 36.33% |

The prespecified CPU-versus-full-LeanHammer difference is **+7.62 percentage
points**, with a module-bootstrap 95% interval of **+5.34 to +9.91**. Neural
JevHammer scored highest; CPU-selector superiority over it remains unachieved.
Both JevHammer arms use Jev for proof-state selection. Full LeanHammer retains
all its proof engines and makes no Jev calls. All 1,292 successful proofs replayed;
one late neural proof is excluded from the table. The memory cap was reached,
with no OOM kills. These results describe the pinned configurations and sampled
intermediate goals, not complete theorem synthesis or all Lean problems.

- [Results, costs, paired outcomes and limitations](docs/full-leanhammer-confirmation-v1.md).
- [How modules, proof states and holdouts were selected](docs/benchmark-selection.md).
- [Recompute the statistics or reproduce the experiment](docs/reproducing-confirmation.md).
- [Frozen protocol](docs/full-leanhammer-confirmation-protocol.md),
  [dataset and schedule](datasets/full-leanhammer-confirmation-v1/README.md),
  [machine-readable report](docs/full-leanhammer-confirmation-v1.json) and
  [all 3,072 trial records](docs/full-leanhammer-confirmation-v1-trials.jsonl).

## Install and run offline

Requires Lean **4.33.0**, Lake, Python **3.10+**, and Git. Mathlib and all Lean
dependencies are pinned in the Lake manifest.

```sh
git clone --branch main https://github.com/adamtopaz/jevhammer_benchmark
cd jevhammer_benchmark
lake update
lake exe cache get
lake build
python -m pip install .

jevbench discover --source BenchmarkFixture=tests/fixtures/Small.lean \
  --count 32 --output runs/fixture
jevbench run --dataset runs/fixture/dataset.json --mock \
  --methods JevHammerBenchmark.Methods.localOnly JevHammerBenchmark.Methods.expanded \
  --output runs/offline
jevbench replay runs/offline
jevbench report runs/offline
```

Read `runs/offline/REPORT.md` and `summary.json`. Replaying creates a new immutable
verification attempt; it never overwrites an earlier attempt. Reports count
only verified certificates. The supplied fixture includes multiple goals,
universes, local definitions, and earlier current-file theorems.

Linux CLI commands automatically enter a **24 GB zero-swap cgroup**. On other
systems use a bounded container/job and `--external-memory-limit`. That flag is
an explicit operator declaration; it does not impose a limit by itself. Limits
above 32 GB are rejected. Put manual Lake builds and any locally hosted selector
services inside the same bounded job. One source process runs at a time.

## Mathlib and live Jev

```sh
jevbench discover --modules Mathlib.Topology.Basic Mathlib.LinearAlgebra.Basis.Basic \
  --count 32 --seed 0 --output runs/mathlib
# Set TYPESAFE_API_KEY through your environment/secret manager.
jevbench run --dataset runs/mathlib/dataset.json \
  --methods JevHammerBenchmark.Methods.sineReranked JevHammerBenchmark.Methods.expandedReranked \
  --config '{"maxMillis":6000,"maxNodes":12,"maxCalls":3}' \
  --max-requests 192 --max-input-tokens 2000000 --output runs/live
```

Live runs require explicit request and reported-input-token budgets. Requests
are reserved before network IO, retries are disabled, and failed/unknown usage
is retained. The token budget prevents subsequent calls after the cumulative
reported usage reaches it; one request may cross that threshold. Budget-blocked
trials are reported separately. Cheap goals can close without making a Jev call.
All requests/responses and source goals are retained locally; keep private
project runs private. Never place credentials in Lean options or run metadata.

`--config` accepts JevHammer config fields; other controls include module process
`--timeout`, trial `--heartbeats`, `--threads`, and memory limits. No large live
benchmark is run by installation or CI.

## Custom methods

Declare a public `JevHammerBenchmark.Method` in a module built by your Lake
project, import it during discovery, then select its fully qualified name:

```lean
module
public meta import JevHammerBenchmark
public meta section
open JevHammerBenchmark

def myMethod : Method := {
  selector := Methods.sineSelector
  selectorName := "Sine Qua Non"
  tactics := { JevHammer.defaultTactics with
    close := .fixed #["omega", "simp_all"] }
  tacticSetName := "my arithmetic configuration"
  config := { maxMillis := 3000, guidePremises := true } }
```

```sh
jevbench discover --project . --import MyMethods --modules MyLibrary.Examples \
  --output runs/custom
jevbench run --dataset runs/custom/dataset.json --methods myMethod --mock --output runs/custom-run
```

`Method.warmup` performs goal-independent initialization outside the goal clock.
`Method.validate` receives **all** evaluation owners and supplies provenance or
rejects the run before trials. This lets selectors enforce training holdouts
without changing the runner. Both hooks are still inside the process/resource
limits. Their Lean state is restored; custom callbacks must manage their own IO.
Together they receive `Method.warmupHeartbeats` (default 5,000,000), independently
of the source context and the trial's heartbeat budget. Set it to zero to disable
only the initialization heartbeat limit; module timeouts and memory limits still
apply. Reports record this setting alongside warmup costs.

`Method.selectorFactory` optionally decorates the standard selector with
JevHammer's budgeted ranking callback. Selector decisions share the same clock,
Jev request allowance, and usage ledger as proof-state decisions. Reports mark
`selectorGuidance` and record `stats.selectorRankCalls` as a subset of premise
ranking calls. Warmup and validation hooks never receive this callback; initialize
only goal-independent data there. Include the factory recipe in `selectorName`.

## Holdouts and integrations

The [broad Mathlib cohort](datasets/mathlib-broad-v1/README.md) supplies a
frozen set of 256 locations across 34 modules and 17 subject areas, with
prior-exposure exclusions and declaration caps. Its module-stratified partitions
contain 134 development locations and 122 reserved evaluation locations.

```sh
jevbench split --dataset runs/mathlib/dataset.json --test-fraction 0.25 --output runs/split
jevbench holdouts --dataset runs/mathlib/dataset.json --output runs/holdouts.json
```

Splitting groups every location of a declaration together. Prepare selectors
with the appropriate evaluation union excluded; keep the final test partition
untouched while choosing methods.

- [Prepared CPU selector](integrations/selector/README.md): generic preparation,
  admission checks, and a paired selector comparison.
- [Sine Qua Non baseline](integrations/selector/sine-qua-non.md): no external
  artifact or neural service, with optional Jev premise reranking.
- [Live Sine versus sparse pilot](docs/sine-baseline-2026-09-18.md): 32 matched
  Mathlib locations with Jev state guidance and independently replayed proofs.
- [Broad live comparison](docs/mathlib-broad-v1-results.md): 134 matched locations,
  complete proof replay, per-location results, and a separate reserved split.
- [Sparse + Jev premise-ranking pilot](docs/sparse-jev-pilot-2026-09-19.md): matched
  100- and 32-candidate comparisons with separate premise/state request costs.
- [Neural selector](integrations/neural/README.md): optional explicit service,
  pinned historical model/corpus metadata, and comparison limitations.
- [CPU selector research status](docs/cpu-selector-research-status.md): broader
  CPU/neural results, retrieval costs, and the remaining selector-quality gap.
- [Full LeanHammer comparison](docs/full-leanhammer-pilot-v1.md): a matched
  34-location pilot, all proof engines enabled, independently replayed results,
  costs, and an [optional public adapter](integrations/leanhammer/README.md).
- [Confirmation cohort](datasets/full-leanhammer-confirmation-v1/README.md):
  1,024 fresh goals from distinct declarations, a counterbalanced three-method
  schedule, explicit training exclusions, and prespecified paired analysis.
- [Completed 1,024-goal confirmation](docs/full-leanhammer-confirmation-v1.md):
  CPU JevHammer 450, neural JevHammer 469, full LeanHammer 372; all successful
  proofs replayed, with paired confidence intervals, costs and resource events.
- [Protocol and output format](docs/protocol.md): isolation, timing, replay,
  sampling, usage, resource limits, and failure handling.
- [Initial validation](docs/validation.md): offline checks, Mathlib preparation,
  and CPU costs; separate from live proof-quality comparisons.
- [Contributing](CONTRIBUTING.md) and [research plans](notes/README.md).

The fresh confirmation study favors CPU/conclusion JevHammer over full LeanHammer
by 7.62 percentage points (module-bootstrap 95% interval +5.34 to +9.91) under
the tested six-second, 16 GB limits. Neural/conclusion JevHammer scored highest;
CPU-selector superiority over it remains unachieved. These are intermediate-goal
results for the pinned configurations, not a universal ranking or a comparison
with the historical monolithic pipeline. Full LeanHammer has additional proof
engines; the neural-selector adapter alone is not that tactic.

Run the complete offline suite inside a bounded job with `bash tests/run.sh`.
Licensed under the [Apache License, Version 2.0](LICENSE).
