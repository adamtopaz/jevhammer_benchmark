# Prepared selector comparison

`JevHammerBenchmark.Selector` supplies `Prepared.sparse` and
`Prepared.sparseReranked`. Both use the expanded Mathlib tactic set; the second
also asks Jev to rerank retrieved premises. Jev guides proof states in both.
The [live reranking pilot](../../docs/sparse-jev-pilot-2026-09-19.md) compares
these methods at 100 and 32 candidates, including their shared call-budget cost.
The lightweight Lean dependency is pinned in the root Lake manifest; the adapter
is an opt-in import. Install the preparation CLI separately:

```sh
python -m pip install 'git+https://github.com/adamtopaz/jevselector'
jevbench discover --modules Mathlib.Topology.Basic Mathlib.LinearAlgebra.Basis.Basic \
  --import JevHammerBenchmark.Selector --count 32 --output runs/discovery
jevbench holdouts --dataset runs/discovery/dataset.json --output runs/holdouts.json
jevselector prepare --project . --modules Mathlib --scope Mathlib \
  --exclude runs/holdouts.json --output artifacts/selector
export JEVSELECTOR_INDEX="$PWD/artifacts/selector/index.json"
jevbench run --dataset runs/discovery/dataset.json \
  --methods JevHammerBenchmark.Prepared.sparseReranked JevHammerBenchmark.Methods.expandedReranked \
  --max-requests 192 --max-input-tokens 2000000 --output runs/paired
```

Set `TYPESAFE_API_KEY` for live runs; use `--mock` to test infrastructure offline.
The run directory records that distinction. Token limits stop new calls after
reported cumulative usage reaches the limit; a single response may cross it.

The adapter loads once per source process, rejects all fitted-row/evaluation
owner overlap before any trials, and validates available statement fingerprints
outside the goal clock. This check runs even if cheap tactics would solve every
goal without retrieving. All dataset owners are checked, not just the current
module. Do not replace an artifact while a run is active.

For development/test partitions use `jevbench split`, then derive exclusions
from the full evaluation union when one artifact serves both. Freeze candidates
before looking at the final test partition. A whole-Mathlib production artifact
is supported by JevSelector but rejected here for overlapping evaluation data.
