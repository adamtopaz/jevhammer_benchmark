# Public-catalog and closure-ranking development screen

Protocol frozen before proof outcomes, 2026-09-19. This reuses the exact 34-site
development pilot (34 owners/modules, 17 areas, seed 19); it does not select new
sites based on previous outcomes. Re-admission must verify all original goals.
The 122 reserved evaluation locations remain unused.

Selector code: `f601085bab31337b3aa829511b83bea123e88e09`. Expanded artifacts were
prepared with `dbcf4f765a87fe6caa515e322da1d150a63c83ae`, with the same 188 owner
holdouts as the original statement and dependency models. Full artifact audits
confirm unchanged fitted owners, exclusions, original statement rows, symbol
weights, original dependency edges, and original label hashes/weights. Preparation
costs are published separately, including the increased public-label cost.

All six arms use the same Mathlib tactic configuration, Jev proof-state guidance,
and `guidePremises := false`. There are no extra Jev calls in the new selectors.

| Method | Premise selection |
| --- | --- |
| `Research.target` | Existing theorem-only target-weighted sparse ranking |
| `Research.publicTarget` | Same ranking with a public-constant candidate catalog |
| `Research.publicNeighbors` | Existing 32-neighbor voting formula with direct public-constant labels |
| `Research.closingTarget` | Existing target ranking plus bounded closure promotion |
| `Research.neuralWarm` | Strong warmed LeanHammer-style neural retrieval reference |
| `Research.closingNeural` | The same neural reference plus identical closure promotion |

The closure wrapper retrieves at most 100 candidates, probes the first 64 after
availability/filter checks and deduplication, and attempts application followed
by local assumptions or definitional reflexivity. Each probe has 1,000 heartbeats
and at most four subgoals. It restores Lean state and returns only names. All
retrieval/probe costs remain within the per-goal clock. Numeric scores encode
rank. Parameters are fixed for this first screen.

The unchanged neural reference and its equally enhanced version both matter:
generic additional Lean checking must not be described as a selector-specific
gain. The public-neighbor arm tests expanded direct labels; its old 12/34 score
is historical context, not a concurrently matched theorem-only-neighbor control.
Any apparent gain from that arm needs a fresh matched ablation before attribution.

Use CPU-only services, two threads, and one shared **16,000,000,000-byte,
zero-swap cgroup** for the services and run. Run heavy work serially. Cap this
screen at 612 Jev requests and 6,000,000 reported input tokens. Services must stop
when the run exits. Warm imported and earlier current-file neural statements
before trial timing and record the warmup cost; never warm on evaluation goals.
Record cold artifact loads, API errors, timeouts, late successes, and memory events.

Run command (after artifact preparation, fixed-site re-admission, and starting
the pinned CPU neural service as documented in `integrations/neural`):

```sh
export JEVSELECTOR_INDEX=artifacts/mathlib-broad-v1/index.json
export JEVSELECTOR_PUBLIC_INDEX=artifacts/mathlib-public-v1/index.json
export JEVSELECTOR_PUBLIC_DEPENDENCIES=artifacts/mathlib-public-dependencies-v1/dependencies.json
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-v4.json \
  --methods JevHammerBenchmark.Research.target \
    JevHammerBenchmark.Research.publicTarget \
    JevHammerBenchmark.Research.publicNeighbors \
    JevHammerBenchmark.Research.closingTarget \
    JevHammerBenchmark.Research.neuralWarm \
    JevHammerBenchmark.Research.closingNeural \
  --config '{"guidePremises": false}' \
  --max-requests 612 --max-input-tokens 6000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-public-closure-v1
```

Independently replay every claimed success at the original source location.
Publish all 204 trial records and paired differences, retaining API failures and
late proofs. This exposed, single-run pilot can reject candidates or motivate a
larger development check; it cannot establish significant superiority. The main
research acceptance test still requires a meaningful paired improvement against
the strongest matched reference on untouched evaluation, repeated with fresh Jev
decisions. No individual-goal inspection or theorem-specific patching is allowed.
