# Sparse + Jev premise-ranking pilot

This frozen development subset contains **34 locations from 34 declarations in
34 Mathlib modules and 17 subject areas**: one location per module, selected with
seed 19 from [the broad development split](../mathlib-broad-v1/development.json).
It has prior development exposure; no reserved evaluation locations are included.
The [protocol](../../notes/sparse-jev-pilot.md) specifies two matched comparisons
with 100 and 32 retrieved candidates. Jev guides proof states in every arm.

Prepare a holdout-safe index using the full broad cohort's exclusion manifest:

```sh
jevselector prepare --modules Mathlib --scope Mathlib \
  --exclude datasets/mathlib-broad-v1/holdouts.json --output artifacts/mathlib-broad
export JEVSELECTOR_INDEX="$PWD/artifacts/mathlib-broad/index.json"
# Supply TYPESAFE_API_KEY through your environment or secret manager.
jevbench run --dataset datasets/sparse-jev-v1/dataset.json \
  --methods JevHammerBenchmark.Prepared.sparse JevHammerBenchmark.Prepared.sparseReranked \
  --config '{"maxPremises":100}' --max-requests 204 --max-input-tokens 4000000 \
  --output runs/sparse-jev-100
jevbench run --dataset datasets/sparse-jev-v1/dataset.json \
  --methods JevHammerBenchmark.Prepared.sparse JevHammerBenchmark.Prepared.sparseReranked \
  --config '{"maxPremises":32}' --max-requests 204 --max-input-tokens 4000000 \
  --output runs/sparse-jev-32
```

The candidate limit is the same for both methods in each run. The second method
sets `guidePremises := true`; all other search and tactic settings are identical.
Both sorts of Jev calls share a three-call budget, so record premise and state
usage separately. Premise reranking can trade state-guidance calls and proof time
for a better premise order; the experiment includes those costs.

To reproduce the subset without examining outcome files:

```sh
python - <<'PY'
from pathlib import Path
from jevhammer_benchmark.cli import read_json, select_sites, write_json
dataset = read_json(Path("datasets/mathlib-broad-v1/development.json"))
dataset["sites"] = select_sites(dataset["sites"], 34, 19, max_per_declaration=1)
assert len({site["module"] for site in dataset["sites"]}) == 34
write_json(Path("runs/sparse-jev-subset.json"), dataset)
PY
```
