# Structural premise retrieval development screen

Frozen before proof outcomes, 2026-09-19. Reuse the exact 34 development locations
and require re-admission to verify every original goal. No reserved evaluation
location is used. Selector implementation: `b8b0a954ee12a776cd5d248d69f1f343e9ef0c22`.
Full-Mathlib cost profiling used `2270359`; subsequent changes isolate mutable
query caches and document costs without changing retrieval or fusion parameters.

| Method | Premise source |
|---|---|
| `Research.publicTarget` | Best current CPU pilot candidate: public-catalog target-weighted sparse retrieval |
| `Research.structural` | Public available signatures matched by Lean's lazy discrimination tree |
| `Research.structuralPublic` | Reciprocal-rank fusion of public target and structural retrieval |
| `Research.neuralWarm` | Strong warmed LeanHammer-style neural retrieval reference |
| `Research.structuralNeural` | Identical structural fusion added to that neural reference |

All methods retain the same Mathlib tactics, six-second goal budget, three shared
Jev calls, and Jev proof-state guidance with `guidePremises := false`. Closure
ranking is omitted: the completed prior pilot found extra cost without a gain.
Structural queries have 10,000 heartbeats. Fusion uses rank offset 16, pool factor
2, and maximum pool 256; parameters are fixed for the screen.

Structural initialization reads available imported signatures only, without proof
values, fitted statistics, or a neural encoder. It applies the standard premise
deny policy through signature lookups, ranks by pattern specificity, and checks
actual availability, type hashes, and caller filters before deduplication and
truncation. Current-file signatures are rebuilt for each query. The public sparse
companion still uses the same 188-owner holdouts and its original eligibility
checks. Third-party neural training overlap remains unknown.

Each structural arm receives its own mutable cache from a base initialized and
warmed only on fixed `True`. Immutable initialization data may be shared; lazy
refinement on an evaluation goal may not warm any other arm. Cache-copy isolation
has a native regression test. First-use refinement on real query shapes stays
inside goal timing. Record the shared initialization cost separately; per-method
warmup attribution is order-dependent. Each neural goal embedding is also timed
inside its query; imported and earlier current-file statement embeddings are warmed
outside goal timing as in the previous reference runs.

On matched 32-type × 3-repeat full-Mathlib profiles, structural retrieval is
6.12 ms median / 91.65 ms p95 after 27.54–27.56 s initialization. Sparse fusion
is 159.67 / 289.05 ms: it misses the provisional 200 ms p95 target and must earn
that cost in proof coverage. Scope peak was 4.71 GB with no memory events. These
timings establish no quality gain.

Run the CPU neural services and benchmark inside one **16,000,000,000-byte,
zero-swap cgroup**, with two threads, and stop services after replay. No other
heavy work runs concurrently. Cap the 170-trial screen at 510 Jev requests and
5,000,000 reported input tokens. Retain all errors, timeouts, late proofs, and
memory events. Independently replay every claimed success and publish all paired
outcomes. Compare with both neural arms; an exposed single-run pilot cannot prove
the significant-improvement objective.

After artifact preparation, fixed-site re-admission, and starting the pinned CPU
neural service as described in `integrations/neural`:

```sh
export JEVSELECTOR_PUBLIC_INDEX=artifacts/mathlib-public-v1/index.json
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-v5.json \
  --methods JevHammerBenchmark.Research.publicTarget \
    JevHammerBenchmark.Research.structural \
    JevHammerBenchmark.Research.structuralPublic \
    JevHammerBenchmark.Research.neuralWarm \
    JevHammerBenchmark.Research.structuralNeural \
  --config '{"guidePremises": false}' \
  --max-requests 510 --max-input-tokens 5000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-structural-v1
```
