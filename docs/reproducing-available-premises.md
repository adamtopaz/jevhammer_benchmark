# Reproducing the available-premise follow-up

This comparison tests whether the original CPU results survive restricting its
fit and imported retrieval postings to statements available before the evaluated
theorem. Read the [protocol](available-premises-protocol.md) for the precise
imports-only policy and remaining pretrained-model limitations. This cohort's
outcomes were already published; it is a sensitivity study, not unseen validation.

The [completed run](available-premises-v1.md) contains 4,096 trials, with on-time
verified coverage `strict: 438`, `cpu: 448`, `neural: 466`, `full: 371`.
Jev responses and timing vary; a reproduction need not return identical counts.

## Check the published results offline

From a clone of this repository, using Python 3.10+ and its standard library:

```sh
python3 scripts/analyze_published_confirmation.py --study available-premises-v1
```

Expected output includes `verified: true` and the four counts above. This checks
trial/dataset hashes, complete paired coverage, timing and recorded replay flags,
and recomputes the published intervals and sensitivity tests. It does not perform
a new kernel replay. The live reproduction below produces fresh certificates.

## Prepare a live reproduction

Use the pinned Lean 4.33.0 optional `integrations/leanhammer` project. Follow the
Lean/native-engine and CPU-neural-inference setup sections of the
[original setup guide](reproducing-confirmation.md), including embedding validation.
Do not run its separate three-method experiment. Preserve dependency pins and
record `git rev-parse HEAD`. Everything below must run sequentially inside one
16 GB, zero-swap cgroup; enter a bounded shell once for setup and collection:

```sh
systemd-run --user --scope -p MemoryMax=16000000000 -p MemorySwapMax=0 -- bash
cd integrations/leanhammer
lake build AvailablePremises AvailableFixture LeanHammerComparison
lake lean AvailablePremisesTests.lean
cd ../..
python3 -m unittest discover -s tests -v
python3 scripts/available_premises_study.py prepare --output runs/available-admission
```

Preparation fully elaborates the original 131 source modules without calling
tested tactics or Jev. It checks every original selected location and goal text,
records the new project fingerprints, and writes four batches in the fixed
counterbalanced order. A module failure stops admission; no replacement or
outcome-based exclusion is allowed. `admission.json` records resource use.

Prepare the original-policy CPU control with all 1,212 owners excluded (or reuse
an artifact made by this exact recipe with the pinned dependencies). The strict
arm never loads it. Run from the repository root, still in the bounded shell:

```sh
.lake/confirmation-python/bin/python -m pip install --no-deps \
  ./integrations/leanhammer/.lake/packages/jevselector
.lake/confirmation-python/bin/python -m jevselector prepare \
  --project integrations/leanhammer --modules Mathlib --scope Mathlib \
  --catalog public-constants --exclude runs/available-admission/holdouts.json \
  --threads 2 --memory-limit 16000000000 --output artifacts/confirmation
```

All output directories must be fresh. If your project exactly matches the
published admission, `datasets/available-premises-v1` can replace
`runs/available-admission` in both preparation and collection. Otherwise use the
outcome-free admission above; never hand-edit project fingerprints. The native
deployment differences described in the original setup guide apply here too.

## Collect and export

Supply `TYPESAFE_API_KEY` through your environment or secret manager. The next
command makes paid Jev requests: at most 9,216 attempts and 107,520,000 reported
input tokens across the three JevHammer arms. As in the original study, one
request may cross the reported-token threshold, and failed requests can leave
usage unknown. Full LeanHammer makes no Jev calls.

```sh
.lake/confirmation-python/bin/python scripts/available_premises_study.py run \
  --plan runs/available-admission \
  --index artifacts/confirmation/index.json \
  --upstream .lake/lean-premise-server --data cache/confirmation-neural \
  --validation artifacts/confirmation-embedding-validation.json \
  --python .lake/confirmation-python/bin/python \
  --output runs/available-comparison

python3 scripts/compare_available_premises.py runs/available-comparison \
  runs/available-admission runs/available-result.json
```

The launcher checks the admitted project, original held-out control artifact and
native engines before trials. Each of the sixteen batch/arm runs gets fresh
local services and independently replays its successful certificates. It stops
and retains evidence on failure; it never silently retries or drops an arm.
Initialization is outside the six-second goal clock and reported separately.
The published run took about 5 hours 39 minutes for the complete 4,096 trials
plus startup, source elaboration and replay, excluding earlier setup/admission.

The exporter requires complete matched datasets, all four methods, matching
search configurations, all replay checks, the frozen order, and a strict-index
preparation record for every source module. It publishes paired coverage,
stratified module-bootstrap uncertainty, costs, API failures, resource events,
and sanitized per-trial records. Keep the raw run directories for certificate
replay and detailed audit. Published counts must not be presented as evidence
that the pretrained neural selector or Jev has no training overlap.

This public four-method launcher and exporter collected the published study
unchanged, using cached pinned assets. All 16 runs and their replay checks
completed. The [deployment audit](available-premises-v1-deployment.json) records
matching service provenance, model/corpus and dependency pins, native binary
hashes, and raw-evidence checksums. The [validation record](available-premises-validation.json)
documents the earlier preparation/isolation and native-engine tests. Keep your
fresh results separate from these exposed-cohort results and report failures,
resource events and deployment differences along with coverage.
