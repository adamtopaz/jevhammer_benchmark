# Reproducing the available-premise follow-up

This comparison tests whether the original CPU results survive restricting its
fit and imported retrieval postings to statements available before the evaluated
theorem. Read the [protocol](available-premises-protocol.md) for the precise
imports-only policy and remaining pretrained-model limitations. This cohort's
outcomes were already published; it is a sensitivity study, not unseen validation.

Use the pinned Lean 4.33.0 optional `integrations/leanhammer` project. Follow the
[original setup guide](reproducing-confirmation.md) to install all native engines,
the pinned CPU neural environment, and the matching model/corpus. Validate the
embedding endpoint as documented there. Retain the original held-out CPU artifact
for the control; the strict arm does not load that artifact. Everything below
must run sequentially inside one 16 GB, zero-swap cgroup:

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
Allow several hours for the complete 4,096 trials plus source elaboration/replay.

The exporter requires complete matched datasets, all four methods, matching
search configurations, all replay checks, the frozen order, and a strict-index
preparation record for every source module. It publishes paired coverage,
stratified module-bootstrap uncertainty, costs, API failures, resource events,
and sanitized per-trial records. Keep the raw run directories for certificate
replay and detailed audit. Published counts must not be presented as evidence
that the pretrained neural selector or Jev has no training overlap.

Once results are published, recompute their coverage and paired statistics
without Lean, a service, or an API key:

```sh
python3 scripts/analyze_published_confirmation.py --study available-premises-v1
```

This verifies checksums and the recorded replay flags; it does not perform a
new kernel replay. The live reproduction above produces fresh certificates.
