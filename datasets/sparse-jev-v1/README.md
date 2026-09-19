# Sparse + Jev premise-ranking pilot

This frozen development subset contains **34 locations from 34 declarations in
34 Mathlib modules and 17 subject areas**: one location per module, selected with
seed 19 from [the broad development split](../mathlib-broad-v1/development.json).
It has prior development exposure; no reserved evaluation locations are included.
The [protocol](../../notes/sparse-jev-pilot.md) specifies two matched comparisons
with 100 and 32 retrieved candidates. Jev guides proof states in every arm.

The [completed pilot](../../docs/sparse-jev-pilot-2026-09-19.md) found no coverage
gain from eager reranking: 13 versus 12 successes at 100 candidates, and 13 versus
13 at 32. All 51 successful trials independently replayed. Detailed timing,
premise/state usage, and every location's outcome are published with the report.

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

## CPU selector research branch

`research-v1.json` preserves exactly the same 34 selected locations, owners, and
goal texts under the updated selector dependency and the additional
`JevHammerBenchmark.Research` import. All locations passed offline source
re-admission with zero model calls. Its project fingerprint belongs to the
`research/cpu-selector` branch; the original dataset remains unchanged.

With the excluded sparse index and an explicitly configured neural service
(including deployment provenance), run the frozen four-arm screen:

```sh
jevbench run --dataset datasets/sparse-jev-v1/research-v1.json \
  --methods JevHammerBenchmark.Prepared.sparse \
    JevHammerBenchmark.Research.target JevHammerBenchmark.Research.ensemble \
    JevHammerBenchmark.Research.neuralWarm \
  --config '{"guidePremises":false}' --memory-limit 16000000000 \
  --max-requests 408 --max-input-tokens 4000000 --output runs/cpu-selector-candidates
```

The neural service and benchmark must share the same 16 GB zero-swap process
tree. The neural reference additionally warms earlier current-file statement
embeddings outside the goal clock. See the
[research protocol](../../notes/cpu-selector-research.md) for initialization,
resource, and reporting requirements. This screen is exploratory development;
the reserved evaluation locations are not included.

`research-v2.json` re-admits the same locations and goals with the proof-neighbor
implementation. Prepare and export `JEVSELECTOR_DEPENDENCIES` as described in
the [selector integration](../../integrations/selector/README.md), then run:

```sh
jevbench run --dataset datasets/sparse-jev-v1/research-v2.json \
  --methods JevHammerBenchmark.Research.target JevHammerBenchmark.Research.neighbors \
    JevHammerBenchmark.Research.proofHybrid JevHammerBenchmark.Research.neuralWarm \
  --config '{"guidePremises":false}' --memory-limit 16000000000 \
  --max-requests 408 --max-input-tokens 4000000 --output runs/cpu-selector-neighbors
```

Both neural services must run inside the same shared 16 GB scope as this command.
The linked dependency model and statement index must both exclude all owners in
the full broad cohort. See the research protocol for the fixed voting/fusion
parameters and the cold-initialization accounting policy.
