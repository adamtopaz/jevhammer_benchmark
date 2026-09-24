# Reproducing the current-system guidance ablation

Read the [frozen protocol](guidance-ablation-protocol.md) first. This comparison
uses 256 previously exposed Mathlib goals, five ranking policies, the strict
CPU selector, and the same search/tactic configuration in every arm.

Use the pinned Lean 4.33 optional `integrations/leanhammer` project, including
its native-library setup from the [comparison guide](reproducing-confirmation.md).
This ablation imports the existing comparison module to preserve its tactic
environment, but **does not need or start neural premise services**. It does not
load a full-library sparse artifact either: each module initializes its own
imports-only fit, excluding the original 1,212 held-out owners.

Run sequentially inside one 16 GB, zero-swap scope:

```sh
systemd-run --user --scope -p MemoryMax=16000000000 -p MemorySwapMax=0 -- bash
python3 -m unittest discover -s tests -v
python3 scripts/guidance_ablation.py prepare --output runs/guidance-admission
```

Admission rebuilds the required targets and checks the exact selected source
states without running tested tactics or making model requests. It stops on any
module failure. The resulting plan contains the dataset, complete holdouts, and
ten counterbalanced batches. Record the repository commit before proceeding;
keep the prepared project unchanged. A compatible checkout can reuse the
published `datasets/guidance-ablation-v1` plan; otherwise use fresh admission.

Supply `TYPESAFE_API_KEY` through your environment or secret manager, then run:

```sh
python3 scripts/guidance_ablation.py run \
  --plan runs/guidance-admission --output runs/guidance-comparison
python3 scripts/analyze_guidance_ablation.py \
  runs/guidance-comparison runs/guidance-admission runs/guidance-result.json
python3 scripts/analyze_guidance_ablation.py --check runs/guidance-result.json
```

All output directories must be fresh. The launcher performs 1,280 trials, strips
credentials from the four local baseline arms, and independently replays every
successful proof. The Jev arm permits at most 768 attempts and a total 8,960,000
reported-input-token stop allocated across batches. One response can cross a
batch threshold; failed requests can leave usage unknown. No automatic retries
or outcome-based exclusions are made. Raw evidence is retained on failure.

The exporter requires complete pairing, identical search settings and fitted
selector provenance, zero premise-ranking calls, valid fixed/random permutations,
zero baseline API usage, and complete independent replay. It publishes sanitized
trials and decision logs, coverage, paired uncertainty, latency, request usage,
warmup measurements, resource events, and source/evidence hashes. `--check`
recomputes the statistics from public rows; it is not a new Lean kernel replay.

For custom studies outside this frozen comparison, the ordinary CLI accepts
`--ranking-policy fixed` or `--ranking-policy random --ranking-seed 17`.
These are real local baselines, distinct from `--mock`. Keep `maxCalls` equal
across arms so that the ranking intervention does not alter refresh eligibility.
The local policy can also replace premise ranking if a different method enables
it; this protocol deliberately disables all premise-ranking decisions.
