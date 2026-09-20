# Weighted sparse Bayes development screen

Recorded before proof trials. Full-library cost measurements, native adapter
compilation, and search-configuration checks are complete. All 34 original
locations and goal hashes were re-admitted unchanged with zero model calls.
This protocol and the admitted dataset are committed before collection. No
individual failed proof informed the candidate.
The selector implementation is `8b9ffbe9644afe5e982dab35088d2fd6f09449cc`.

Use the new weighted sparse Bayes model with eligible-only statement priors:
signature-prior weight 20, observed-feature factor 10, missing-feature log weight
-15, and 64 stored features per premise. Query features are distinct constants in
the goal and visible local context, each with unit weight. Keep all label priors
and sample at most 20,000 postings evenly per feature, with 10,000 query
heartbeats. The statement artifact is the existing public-constant catalog;
proof labels are direct public theorem references from eligible proofs. All 188
broad-cohort owners and named children remain excluded before fitting.

| Method | Premise sources | Jev premise reranking |
|---|---|---|
| `BayesStudy.cpuControl` | Public sparse + conclusion patterns | No |
| `BayesStudy.bayes` | Weighted sparse Bayes | No |
| `BayesStudy.bayesTarget` | Public sparse + Bayes | No |
| `BayesStudy.bayesStructuralTarget` | Public sparse + conclusion patterns + Bayes | No |
| `BayesStudy.neuralControl` | Warmed neural + conclusion patterns | Yes |

Control guidance follows the already completed matched-warmup study: CPU native
order and neural Jev premise reranking. All arms retain Jev proof-state guidance,
identical Mathlib tactics, six seconds per goal, three shared Jev calls, 100
retrieved names, eight injected premises, and the same premise-refresh policy.
CPU arms have identical search settings; the neural control differs in the
previously selected premise guidance. This compares complete selector
configurations rather than attributing all differences solely to retrieval.

Use flat reciprocal-rank fusion with offset 16, pool factor 2, and maximum pool
256. Mutable conclusion caches are independent per method, copied from the
fixed True warmup. Prepared arrays are immutable and may be shared. Validate
artifact identity and all evaluation-owner exclusions before trials. Load
artifacts and initialize signature indexes outside goal timing, reporting these
costs separately. Warm the fresh CPU neural service's imported and earlier
current-file statements; actual goal embeddings remain inside goal timing.

Re-admit all 34 original pilot locations and owners with exactly the same goal
hashes, making no model calls. Do not open the 122 reserved evaluation locations.
This pilot is exposed development data and cannot establish final superiority.
Report all three Bayes variants, even when worse. Select a promising variant by
on-time independently replayed coverage, then total goal time, then method name;
only promote it to a larger development comparison if it improves over the CPU
control. Do not promote timing-only wins as quality improvements.

Run 170 trials, with at most 510 Jev requests and 5,000,000 reported input tokens.
Enclose services, Lean workers, and independent replay in a single aggregate
16,000,000,000-byte, zero-swap scope. Use two CPU threads, serial modules, and no
other heavy job concurrently. Preserve API errors, late outcomes, and budget
blocking. Replay every claimed proof against the original source context; report
paired declaration-grouped uncertainty, query/goal/warmup costs, premise/state
calls, tokens, memory events, exact artifacts and code revisions. No selective
retries or theorem-specific tuning.

## Artifact lineage and measured costs

Statement index SHA-256: `e388078b747f85320c672a78570d3831bb4ce6b754d3df493ed7095afe4cd7f5`.
Theorem-dependency SHA-256: `a74115a01c104630d0491c084c02f307b2a44281fdb8e4ffc2045d6a1156d84e`.
Bayes JSONL SHA-256: `e6c60bf2da82c61296da74a36797cfe799e07d5c5fb07a1a719bba353d8642f4`.
The model contains 258,016 premise profiles and 7,587,133 retained feature edges,
from 254,885 eligible theorem owners. It occupies 387,851,440 bytes.

Statement preparation previously took 232.66 seconds. Fresh theorem-label
extraction took 762.15 seconds, followed by 18.40 seconds for Bayes fitting.
Their sum is 1,013.21 seconds (16.9 minutes), exceeding the provisional ten-minute
training target; the old faster theorem-only extraction timing is not substituted.
Standalone Bayes queries measured 116.35 ms median / 127.26 ms p95. Sparse/Bayes
fusion measured 276.84 / 350.15 ms, and sparse/conclusion/Bayes measured
319.30 / 467.19 ms. The matched sparse/conclusion control measured
160.29 / 282.52 ms. Fusions exceed the provisional 200 ms p95 target.
Bayes plus statement loading took about 18.7 seconds; conclusion initialization
added 28.6 seconds. Peak across serial preparation and profiling was 9.77 GB,
with no memory events. These costs are reported in
[cpu-selector-profile-bayes-v1.json](cpu-selector-profile-bayes-v1.json).
This small proof screen tests quality despite the cost overruns; it does not
promote the candidate or redefine the speed targets.

## Running the screen

Prepare the public statement index with all evaluation-owner exclusions and then
extract theorem-only labels and fit the Bayes companion:

```sh
python -m jevselector dependencies --modules Mathlib \
  --index artifacts/mathlib-public-v1/index.json --labels theorems \
  --output artifacts/mathlib-public-theorem-dependencies-v1 --threads 2 \
  --memory-limit 16000000000
python -m jevselector bayes --index artifacts/mathlib-public-v1/index.json \
  --dependencies artifacts/mathlib-public-theorem-dependencies-v1/dependencies.json \
  --output artifacts/mathlib-bayes-v1 --memory-limit 16000000000
python -m jevselector verify artifacts/mathlib-bayes-v1
```

Set `JEVSELECTOR_PUBLIC_INDEX` and `JEVSELECTOR_BAYES` to these artifacts and
configure the pinned CPU neural endpoint and provenance as described in
[integrations/neural](../integrations/neural). Keep the services and run command
inside one shared 16 GB, zero-swap job. Check the adapters with
`lake build JevHammerBenchmark.BayesStudy` and `lake env lean BayesStudyTests.lean`.

```sh
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-bayes-v1.json \
  --methods JevHammerBenchmark.BayesStudy.cpuControl \
    JevHammerBenchmark.BayesStudy.bayes \
    JevHammerBenchmark.BayesStudy.bayesTarget \
    JevHammerBenchmark.BayesStudy.bayesStructuralTarget \
    JevHammerBenchmark.BayesStudy.neuralControl \
  --config '{}' --max-requests 510 --max-input-tokens 5000000 \
  --memory-limit 16000000000 --threads 2 --output runs/cpu-selector-bayes-v1
```
