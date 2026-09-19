# Sine Qua Non baseline

The benchmark uses the public
[`JevSelector.SineQuaNon`](https://github.com/adamtopaz/jevselector/blob/main/docs/sine-qua-non.md)
wrapper around Lean's built-in algorithm. It requires no external preparation,
artifact, Python selector process, or neural service. Jev still guides proof
states in live JevHammer runs.

| Method | Tactics | Jev premise reranking |
|---|---|---|
| `Methods.sine` | JevHammer defaults | No |
| `Methods.sineReranked` | JevHammer defaults | Yes |
| `Methods.expanded` | Expanded Mathlib set | No |
| `Methods.expandedReranked` | Expanded Mathlib set | Yes |

Names in this table have the prefix `JevHammerBenchmark.`. All four use depth
factor 1.5, a cap of 1,024 raw imported candidates, and current-file
supplementation. Imported suggestions preserve Sine Qua Non priority; earlier
current-file theorems are interleaved 1:1. The wrapper applies caller filters,
availability checks and deduplication. It increases the raw request up to the
cap when filtering leaves too few usable suggestions.

For a small standalone baseline run:

```sh
jevbench discover --modules Mathlib.Topology.Basic Mathlib.LinearAlgebra.Basis.Basic \
  Mathlib.RingTheory.Ideal.Basic --count 32 --seed 0 --output runs/sine-dataset
# Supply TYPESAFE_API_KEY through your environment/secret manager.
jevbench run --dataset runs/sine-dataset/dataset.json \
  --methods JevHammerBenchmark.Methods.expanded \
  --max-requests 96 --max-input-tokens 1000000 --output runs/sine-live
```

For a paired comparison with the prepared sparse selector, import
`JevHammerBenchmark.Selector` during discovery, prepare with all evaluation
owners excluded, set `JEVSELECTOR_INDEX`, and run `Methods.expanded` alongside
`Prepared.sparse`. Both then use the same expanded tactics, Jev proof-state
guidance, and no premise reranking. The [preparation guide](README.md) explains
holdouts. Never compare live results to a mock run as if they shared guidance.

Warmup initializes both imported trigger and symbol-frequency maps outside the
goal clock. Run metadata records the selector settings, Lean version, and
statement-only statistics. No fitted artifact is required for this baseline;
the sparse selector's excluded whole-library fitting statistics are a different
source of prior information. The runner's original source environment prevents
either selector from retrieving the target theorem or later declarations.
