#!/usr/bin/env bash
set -euo pipefail
python -m unittest discover -s tests -v
lake build JevHammerBenchmarkTests JevHammerBenchmark.Selector JevHammerBenchmark.Neural
lake env lean WarmupBudgetTests.lean
lake build JevHammerBenchmark.GraphStudy
lake env lean SelectorGuidanceTests.lean
scratch=$(mktemp -d)
trap 'status=$?; if [ "$status" -eq 0 ]; then rm -rf "$scratch"; else echo "Test evidence retained: $scratch" >&2; fi' EXIT
if python -m jevhammer_benchmark discover --modules Mathlib.Data.Nat.Basic --output "$scratch/import-cycle" "$@"; then
  echo 'ERROR: accepted a source already imported by the harness' >&2
  exit 1
fi
python -m jevhammer_benchmark discover --source BenchmarkFixture=tests/fixtures/Small.lean --count 32 --output "$scratch/dataset" "$@"
python - "$scratch/dataset" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
rows = [json.loads(line) for line in (root / 'discovery.jsonl').read_text().splitlines()]
examples = [row for row in rows if row['declaration'] == '_example']
assert examples and all(not row['eligible'] for row in examples)
assert len(json.loads((root / 'dataset.json').read_text())['sites']) == 14
PY
python -m jevhammer_benchmark split --dataset "$scratch/dataset/dataset.json" --output "$scratch/splits"
python -m jevhammer_benchmark holdouts --dataset "$scratch/dataset/dataset.json" --output "$scratch/holdouts.json"
python -m jevhammer_benchmark run --dataset "$scratch/dataset/dataset.json" --mock --methods JevHammerBenchmark.Methods.localOnly JevHammerBenchmark.Methods.expanded --output "$scratch/run" "$@"
python -m jevhammer_benchmark replay "$scratch/run" "$@"
python - "$scratch/run" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
summary = json.loads((root / 'summary.json').read_text())
assert summary['status'] == 'complete'
for method in summary['methods'].values():
    assert method['onTimeVerified'] == method['sites'] and method['sites'] >= 12
# Force a type mismatch; replay must reject it against the real source goal.
path = root / 'trials.jsonl'
rows = [json.loads(line) for line in path.read_text().splitlines()]
cert = next(r for r in rows if r['solved'])['certificates'][0]
cert['nodes'] = [['const', ['str', ['anonymous'], 'False'], []]]
cert['proof'] = 0
cert['type'] = 0
path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
PY
if python -m jevhammer_benchmark replay "$scratch/run" "$@"; then
  echo 'ERROR: accepted a corrupted certificate' >&2
  exit 1
fi
python - "$scratch/run/summary.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))['status'] == 'incomplete'
PY

# The public Method factory must reach the real hook, statistics and replay.
python -m jevhammer_benchmark discover --source GuidedFixture=tests/fixtures/Guided.lean --count 4 --output "$scratch/guided-dataset" "$@"
python -m jevhammer_benchmark run --dataset "$scratch/guided-dataset/dataset.json" --mock --methods GuidedFixture.method --max-requests 4 --output "$scratch/guided-run" "$@"
python -m jevhammer_benchmark replay "$scratch/guided-run" "$@"
python - "$scratch/guided-run" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
summary = json.loads((root / 'summary.json').read_text())
assert summary['status'] == 'complete'
rows = [json.loads(line) for line in (root / 'trials.jsonl').read_text().splitlines()]
assert rows
for row in rows:
    assert row['solved'] and row['onTime'] and row['selectorGuidance']
    assert row['stats']['selectorRankCalls'] == row['stats']['premiseRankCalls'] == row['stats']['rankCalls'] == 1
assert all(row['stats']['model'] == 'OFFLINE-MOCK' for row in rows)
# Mock rankings do not perform or record billable network requests.
assert json.loads((root / 'usage.json').read_text())['attempts'] == 0
PY
