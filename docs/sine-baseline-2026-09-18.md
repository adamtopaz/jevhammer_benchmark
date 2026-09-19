# Sine Qua Non baseline: live pilot (2026-09-18)

Sine Qua Non solved **13/32** sampled Mathlib locations; the prepared sparse
selector solved **14/32**. All 27 successful trials independently replayed
against their original source goals. This small pilot does not establish a
coverage advantage for either selector.

Both arms used **live Jev proof-state guidance**, identical expanded Mathlib
tactics, a 6,000 ms goal budget, and **no Jev premise reranking**. This isolates
the retrieval choice within the same JevHammer configuration. No other neural
component or selector service was used.

| Metric | Sine Qua Non + current file | Prepared sparse IDF |
|---|---:|---:|
| On-time verified locations | 13/32 (40.6%) | 14/32 (43.8%) |
| Raw verified locations | 13 | 14 |
| Total goal time | 80.826 s | 87.739 s |
| Median goal time | 2.211 s | 2.261 s |
| Total selector retrieval time | 0.626 s | 3.505 s |
| Observed warmup per module | 40–50 ms | 3,968–3,982 ms |
| Jev proof-state requests | 56 | 49 |
| Jev premise-ranking requests | 0 | 0 |
| Reported input tokens | 298,469 | 256,183 |
| Reported output tokens | 8,570 | 7,524 |
| Ranking failures | 0 | 1 |

Retrieval times accumulate all selection calls and refreshes across the 32
trials. The selectors can lead search through different states and query counts,
so these are end-to-end component costs, not a controlled per-query speed ratio.
Warmup is outside the goal clock. Sine uses Lean's compiled statement statistics
without an external artifact; sparse loads and validates a prepared index.

Sine alone solved one location; sparse alone solved two. The declaration-grouped
bootstrap 95% interval for **Sine minus sparse** was **−15.2 to +6.9 percentage
points**, including zero. The cohort had prior infrastructure-test exposure and
is a development sample, not a fresh final confirmation. There was one live
run, without a repeat to estimate service/timing variation.

The single ranking failure was in the sparse arm: Jev returned probabilities
that failed the client's sum-to-one validation. The engine retained the original
candidate order for that decision, as its documented fallback specifies. The
failure and reported usage remain in the results; there was no retry or silent
discarding of the trial. No trials were budget-blocked, no successful proofs were
late, and no module failures or runtime panics occurred.

## Protocol and provenance

The [protocol](../notes/sine-baseline-pilot.md) and implementation were committed
before live collection at benchmark revision
`8754b4f1ec0c8f44a1cfdfdee9c42bcb5f50ef1b`. The comparison used:

- Lean 4.33.0; Mathlib `db584cd6d46c92f209a44c0f1c829460d327499d`.
- JevHammer `603573da7aa272dcaf2ef9860e7c886210a1433a`.
- JevSelector `aa77f05459cfc136dc88655e86d347b8ac110701`.
- Jev model `jev-1.13.0`, with retries disabled.
- `Methods.expanded` versus `Prepared.sparse`, both under the
  `JevHammerBenchmark` namespace.
- Seed 0, 32 of 250 eligible locations across 25 declarations in
  Mathlib.Topology.Basic, Mathlib.LinearAlgebra.Basis.Basic, and
  Mathlib.RingTheory.Ideal.Basic. Exact sites, goals and owners matched the prior
  infrastructure cohort before collection started.

The sparse artifact excluded the evaluation owners from fitting; its SHA-256 is
`bdef7b455146f3ae87ebc7600bd6c445010405a6e00214f61b41aed33bbb2aec`.
Sine used its own imported-statement statistics; it does not share that fitted
catalog. Both selectors were restricted to the actual preceding-command
environment and could not retrieve the target theorem or later declarations.

The run allowed 192 requests and 2,000,000 reported input tokens. It used **105
requests**, **554,652 input tokens**, and **16,094 output tokens**, with no unknown
usage. All heavy processes shared one **24 GB, zero-swap limit**, two Lean threads,
and serial module execution. There were no cgroup OOM or limit events.

The [machine-readable report](sine-baseline-2026-09-18.json) contains the exact
settings, pins, paired statistics, per-arm usage and component timings.

## Reproduce

Use the [Sine baseline guide](../integrations/selector/sine-qua-non.md) and
[prepared-selector guide](../integrations/selector/README.md) to install and
prepare a holdout-safe index. For this cohort, discovery also imports the neural
adapter for compatibility; it is not called by either arm:

```sh
jevbench discover --modules Mathlib.Topology.Basic Mathlib.LinearAlgebra.Basis.Basic \
  Mathlib.RingTheory.Ideal.Basic --import JevHammerBenchmark.Selector \
  --import JevHammerBenchmark.Neural --count 32 --seed 0 --output runs/sine-dataset
jevbench holdouts --dataset runs/sine-dataset/dataset.json --output runs/holdouts.json
jevselector prepare --modules Mathlib --scope Mathlib --exclude runs/holdouts.json \
  --output artifacts/sine-comparison
export JEVSELECTOR_INDEX="$PWD/artifacts/sine-comparison/index.json"
# Supply TYPESAFE_API_KEY through your environment/secret manager.
jevbench run --dataset runs/sine-dataset/dataset.json \
  --methods JevHammerBenchmark.Methods.expanded JevHammerBenchmark.Prepared.sparse \
  --max-requests 192 --max-input-tokens 2000000 --output runs/sine-live
```

A newly prepared artifact records its own provenance and checksum. The recorded
pilot reused the validated held-out artifact from the earlier preparation run.
New live calls and timings can produce different results; retain each run.
