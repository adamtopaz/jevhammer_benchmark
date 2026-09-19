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

## Experimental proof-neighbor models

On the `research/cpu-selector` branch, `JevHammerBenchmark.Research` also provides
`neighbors` and `proofHybrid`. These use a dependency companion prepared from the
exact eligible theorem set of the sparse index:

```sh
jevselector dependencies --project . --modules Mathlib \
  --index artifacts/selector/index.json --output artifacts/dependencies \
  --memory-limit 16000000000
export JEVSELECTOR_DEPENDENCIES="$PWD/artifacts/dependencies/dependencies.json"
```

The adapter caches the dependency model separately, validates its linked index
and imported premise hashes during warmup, and rejects evaluation overlap before
trials. Neither method reads proof bodies during selection. Both retain Jev
proof-state guidance; the dependency selector itself runs entirely on the CPU.
Use a dataset admitted with the `JevHammerBenchmark.Research` import and the
matching source fingerprint. See the [research protocol](../../notes/cpu-selector-research.md)
for the fixed candidate screen and paired neural reference. These methods are
research candidates, not established improvements.

`Research.usage` uses learned sparse profiles of the statements whose eligible
proofs use each premise. It fits from the same two artifacts without new Lean
extraction:

```sh
jevselector usage --index artifacts/selector/index.json \
  --dependencies artifacts/dependencies/dependencies.json \
  --output artifacts/usage --memory-limit 16000000000
export JEVSELECTOR_USAGE="$PWD/artifacts/usage/usage.json"
```

This frozen adapter requires the initial smoothing mass 20 and top-64 feature
policy; other configurations can be used through JevSelector's generic API with
their own named benchmark method. Pin the Python CLI to the same research commit
as the Lake package. The model has an independent cache and holdout/statement
validation. This variant remains experimental until its matched proof screen is
complete; fitting speed alone does not establish retrieval quality.
