# Reproducing the 1,024-goal confirmation

You can check the published statistics without Lean or Jev, or generate new
proofs using the same configurations. Jev responses and wall-clock timings vary;
reproduction does not promise identical proof counts. The study used Lean 4.33.0,
CPU neural inference, eight Lean workers, a six-second goal deadline and one
16 GB, zero-swap process tree.

## Check the published statistics

```sh
git clone --branch main https://github.com/adamtopaz/jevhammer_benchmark
cd jevhammer_benchmark
git rev-parse HEAD
python3 scripts/analyze_published_confirmation.py
```

This uses Python's standard library (3.10+), checks the frozen trial/dataset
hashes and all 3,072 distinct method/location pairs, and recomputes coverage,
paired module-bootstrap intervals and sensitivity tests. Expected coverage:
`cpu: 450`, `neural: 469`, `full: 372`, with `verified: true`.
It checks published replay flags, not proof certificates. Original certificates
and raw service logs remain local, with checksums in the public report. A fresh
run below creates its own replayable certificates. See
[problem selection](benchmark-selection.md) and [results](full-leanhammer-confirmation-v1.md).

## Set up the Lean project and memory limit

These orchestration commands target Linux with cgroup v2 and a systemd user
manager, Git, Lean/Elan, a C/C++ toolchain and Python 3.11. Other platforms can use
the generic benchmark CLI in a bounded container; these helpers require an
observable aggregate Linux cgroup. Record the repository commit above, and
preserve the checked-in Lake manifests rather than upgrading dependencies.

Start one bounded shell, and run the remaining setup and live commands inside
it, sequentially. Services and workers must share this cap, not separate scopes:

```sh
systemd-run --user --scope -p MemoryMax=16000000000 -p MemorySwapMax=0 -- bash
cd integrations/leanhammer
lake update
lake exe cache get
lake build
cd ../..
```

The optional project's base runner is pinned at
`bb2b1861f665c3854d49b3f115d6a413aab2611f`; current Python runner files still
match that snapshot. The new orchestration helpers sit outside the frozen Lean
project and do not alter tactics. Install all native engines required by pinned
[LeanHammer](https://github.com/JOSHCLUNE/LeanHammer/tree/21886b7ffbdf32017655a9d6e699f98779046533):
Aesop, grind, Lean-auto/Zipperposition/Duper and Lean-SMT/cvc5. The driver executes
`Smoke.lean` through Lake's native-plugin-aware setup before any live trial.
Do not disable a failing engine and report the result as full LeanHammer.

The original Nix deployment used a [cvc5/GMP link patch](full-leanhammer-cvc5-gmp.patch)
and a Zipperposition loader adaptation. Use native executables appropriate to
your host. The source-identity check includes cvc5's `lakefile.lean`; an unpatched
checkout may require the outcome-free re-admission below. Do not hand-edit
dataset project hashes to bypass validation.

## Install and validate CPU neural inference

```sh
python3.11 -m venv .lake/confirmation-python
.lake/confirmation-python/bin/python -m pip install 'torch==2.14.0+cpu' \
  --index-url https://download.pytorch.org/whl/cpu
.lake/confirmation-python/bin/python -m pip install -r integrations/neural/requirements-cpu.lock
git clone https://github.com/hanwenzhu/lean-premise-server .lake/lean-premise-server
git -C .lake/lean-premise-server checkout af21f771dc1ae25a04044a571f96f712b1ea934a

.lake/confirmation-python/bin/python scripts/confirmation_services.py \
  --upstream .lake/lean-premise-server --data cache/confirmation-neural \
  --validation artifacts/confirmation-embedding-validation.json --validate
```

The lock reproduces the published Python environment; first use downloads the
pinned model/corpus from [provenance metadata](../integrations/neural/provenance.example.json).
The label `v4.33.0` selects the upstream precomputed vector filename; inference
loads immutable model SHA `b9f33df6b8b615122872bf76eac91911fcf26468`.
Validation compares 32 fixed, evenly spaced corpus vectors with CPU float32
inference, requiring minimum cosine 0.99999 and maximum absolute error 0.0001.
The service helper checks the server revision, installed package versions and
validation's model, corpus and embedding-code identities. Ports 18080/18081
must be free; it refuses to take over an existing listener. No GPU or Jev key is
needed for this validation.

## Admit the dataset and prepare the CPU selector

Use the checked-in plan when the project matches it:

```sh
CONFIRMATION_PLAN="$PWD/datasets/full-leanhammer-confirmation-v1"
```

If your native deployment changes project identity, rediscover and re-admit the
same states before proof trials. The [cohort README](../datasets/full-leanhammer-confirmation-v1/README.md)
gives exact discovery/admission commands, including the five known whole-module
compatibility failures. Then freeze that admitted result into a new plan:

```sh
mkdir -p runs/confirmation-plan
cp datasets/full-leanhammer-confirmation-v1/{recipe,modules,exclusions}.json runs/confirmation-plan/
python3 scripts/freeze_confirmation_dataset.py runs/confirmation-admitted/dataset.json \
  datasets/mathlib-broad-v1/holdouts.json runs/confirmation-plan
CONFIRMATION_PLAN="$PWD/runs/confirmation-plan"
```

The reproduction driver checks every selected location, owner, goal text, source
checksum, batch assignment, holdout and budget against the published cohort.
Only explicitly re-admitted project metadata may differ. If compatibility
failures or selected states differ, retain the evidence and resolve the
deployment mismatch before running proofs. Do not substitute goals or filter
proof-trial failures.

Install the preparation CLI from the same pinned package used by Lean, and
exclude all 1,212 owners:

```sh
.lake/confirmation-python/bin/python -m pip install --no-deps \
  ./integrations/leanhammer/.lake/packages/jevselector
.lake/confirmation-python/bin/python -m jevselector prepare \
  --project integrations/leanhammer --modules Mathlib --scope Mathlib \
  --catalog public-constants --exclude "$CONFIRMATION_PLAN/holdouts.json" \
  --threads 2 --memory-limit 16000000000 --output artifacts/confirmation
```

Original preparation took 92.16 seconds and peaked at 7.768 GB. Before services
start, the driver checks the artifact/recipe and validates its compiled statement
catalog and every owner holdout in Lean. An index fitted on the whole library
without exclusions is appropriate for production use, not this evaluation.

## Run and export all six batches

Supply `TYPESAFE_API_KEY` through your environment or secret manager, never in
command arguments or committed files. This makes paid Jev requests, bounded by
6,144 requests and 71,680,000 reported input tokens across both Jev arms.
Failed/unknown requests are retained; reported usage can be incomplete. Full
LeanHammer makes zero Jev calls.

```sh
.lake/confirmation-python/bin/python scripts/reproduce_confirmation.py \
  --upstream .lake/lean-premise-server --data cache/confirmation-neural \
  --validation artifacts/confirmation-embedding-validation.json \
  --plan "$CONFIRMATION_PLAN" --index artifacts/confirmation/index.json \
  --output runs/confirmation-reproduction --execute

python3 scripts/compare_confirmation.py runs/confirmation-reproduction \
  "$CONFIRMATION_PLAN" runs/confirmation-reproduction/comparison.json
```

Omit `--execute` and use a separate fresh output path for only the offline Lean
holdout/native-engine preflight. The original complete run took about 4 hours
23 minutes; setup/downloads are additional. It reached the 16 GB cap, with
942 memory-pressure events and no OOM kills.

The portable helpers were separately validated with cached pinned assets:
CPU vector agreement, both live local service endpoints, all-owner Lean
validation, native-engine smoke checks and recomputation of the published
statistics all passed, with no Jev calls or new Mathlib benchmark trials and
an 11.253 GB peak. The 18-arm orchestration and failure-retention paths have
offline tests; this new launcher has not been used to collect another full
study. See the [validation record](reproduction-tools-validation.json).

The driver starts fresh services per arm, preserves disk caches, uses all six
method-order permutations and checks replay after each arm. It stops its owned
services on failure, retains incomplete records and never selectively retries
or overwrites a run. The core command is the public `python -m jevhammer_benchmark
run` with one `LeanHammerComparison.cpu`, `.neural` or `.full` method,
`--threads 8 --heartbeats 200000 --config '{}' --memory-limit 16000000000` and
the schedule's request/token bounds. Full LeanHammer receives positive ledger
bounds of one to satisfy the CLI and must report zero Jev usage.

The exporter rejects missing/duplicate trials, changed configurations, mock
guidance, incomplete replay and changed batch hashes. It writes JSON and trial
JSONL. Keep the primary contrast and analysis fixed, publish all methods and
resource/API failures, and disclose deployment differences. Do not pool a rerun
with the published study or tune on its outcomes while calling it fresh validation.
