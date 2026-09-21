# Full LeanHammer confirmation cohort

**1,024 source locations from 1,024 distinct declarations in 131 modules across
17 Mathlib subject areas.** This cohort is new relative to recorded earlier
proof trials. The original 122 reserved locations remain untouched.

The [protocol](../../docs/full-leanhammer-confirmation-protocol.md) was committed
before discovery and fixes the methods, timing, resource limits, sampling and
statistical analysis. No method was tuned on this cohort.

## Files

- `modules.json`: the original 136-module candidate list.
- `recipe.json`: lexical filters, hash ordering and full candidate queues.
- `exclusions.json`: earlier tested owners/modules and evidence checksums;
  also excludes the entire older broad cohort.
- `dataset.json`: the final 1,024 admitted source locations and goal hashes.
- `summary.json`: counts by subject area.
- `holdouts.json`: all 1,024 new owners plus 188 old owners for CPU preparation.
- `batch-0.json` through `batch-5.json`: disjoint subsets with whole modules.
- `schedule.json`: the six method orders, dataset hashes and request budgets.
- `preparation.json`: preparation/validation costs and artifact identity.

The optional project is `integrations/leanhammer`; its pinned base runner and
all tactic dependencies are identical to the 34-location pilot. CPU and neural
JevHammer use Jev for proof-state guidance. Full LeanHammer retains all engines.

## Compatibility admission

The initial discovery found 15,043 locations but failed to completely elaborate
five original source modules after benchmark imports were added. Those modules
are excluded in full, before site sampling or any tested-tactic calls. They are
listed with diagnostic checksums in `dataset.json` under `compatibility`.
No source proofs were patched. The admitted 131 modules contain 14,424 discovered
locations, of which 14,038 are eligible before the one-owner sampling cap.

The outcome-free admission script refuses input directories containing proof
trial records. It preserves the incomplete discovery identity and every rejected
module. Subsequent proof-trial failures may not be excluded with this mechanism.
The original incomplete discovery remains local evidence; the public metadata
records its checksum. Module import compatibility adds a population limitation.

## Reproduce

After installing the optional integration, discover with the frozen module list:

```sh
python -m jevhammer_benchmark discover --project integrations/leanhammer \
  --modules-file datasets/full-leanhammer-confirmation-v1/modules.json \
  --exclude datasets/full-leanhammer-confirmation-v1/exclusions.json \
  --import LeanHammerComparison --count 1024 --max-per-declaration 1 \
  --seed 20260921 --threads 8 --memory-limit 16000000000 \
  --output runs/confirmation-discovery
```

The pinned source/import combination yields the five documented compatibility
failures. Retain them, then admit the complete modules into a fresh directory:

```sh
python scripts/admit_complete_discovery.py runs/confirmation-discovery \
  datasets/full-leanhammer-confirmation-v1/exclusions.json runs/confirmation-admitted
```

The checked-in dataset is already frozen; do not overwrite it. To create an
independent reproduction, copy the plan's recipe/module/exclusion files into
a new directory and use `scripts/freeze_confirmation_dataset.py` with the
admitted dataset and `datasets/mathlib-broad-v1/holdouts.json`.

Prepare the public-constant CPU artifact using the pinned JevSelector package:

```sh
python -m jevselector prepare --project integrations/leanhammer --modules Mathlib \
  --scope Mathlib --catalog public-constants \
  --exclude datasets/full-leanhammer-confirmation-v1/holdouts.json \
  --threads 2 --memory-limit 16000000000 --output artifacts/confirmation
export JEVSELECTOR_PUBLIC_INDEX="$PWD/artifacts/confirmation/index.json"
```

For each scheduled batch/arm, start fresh CPU neural services using the pinned
[neural deployment](../../integrations/neural/README.md), then run the standard
CLI with that batch's dataset and singleton method (`LeanHammerComparison.cpu`,
`.neural`, or `.full`). Use eight Lean threads, 200,000 outer heartbeats and the
schedule's request/token budgets. Supply the usual explicit service provenance
and Jev credential through the environment. Full LeanHammer uses zero Jev calls;
the CLI still requires positive ledger bounds, set to one for that arm. Stop
owned services before the next arm. Keep services, Lean and solvers inside one
**16 GB zero-swap scope**, with no concurrent heavy job.

Collection produces `batch-N/ARM/{run,summary,verification}.json`, trial records,
certificates, selector instrumentation and deployment metadata. Every successful
proof must independently replay. The completed-study exporter is:

```sh
python scripts/compare_confirmation.py runs/full-leanhammer-confirmation-v1 \
  datasets/full-leanhammer-confirmation-v1 docs/full-leanhammer-confirmation-v1.json
```

It rejects missing batches, changed datasets, duplicate owners/trials, mismatched
methods/configurations, incomplete replay and mock performance runs. It reports
paired stratified module-bootstrap intervals and an explicitly unclustered exact
McNemar sensitivity test. An unfinished run is not confirmation evidence.
