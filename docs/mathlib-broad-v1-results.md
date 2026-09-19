# Broad Mathlib comparison: Sine Qua Non versus sparse

Sine Qua Non solved **49/134 (36.6%)** development locations; the prepared sparse selector solved **58/134 (43.3%)**. All **107 successful trials independently replayed** against their source goals.

The [frozen cohort](../datasets/mathlib-broad-v1/README.md) expands the public pilot from 32 locations in three modules to **256 locations in 34 modules and 17 subject areas**. This comparison uses its **134-location, 99-declaration development split**. The **122-location, 89-declaration reserved split received no tactic trials**.

Both arms use live `jev-1.13.0` proof-state guidance, identical expanded Mathlib tactics, six-second goal budgets, and no premise reranking. Neither arm calls a neural premise-selector service.

| Metric | Sine Qua Non + current file | Prepared sparse IDF |
|---|---:|---:|
| On-time verified locations | 49/134 | 58/134 |
| Raw verified trials | 49 | 58 |
| Late verified trials | 0 | 0 |
| Total goal time | 429.134 s | 410.550 s |
| Median goal time | 3.365 s | 3.292 s |
| Total selector retrieval time | 3.661 s | 18.663 s |
| Observed warmup per module | 30–193 ms | 3,950–4,283 ms |
| Jev proof-state requests | 215 | 182 |
| Jev premise-ranking requests | 0 | 0 |
| Reported input tokens | 1,015,449 | 966,670 |
| Reported output tokens | 27,673 | 23,497 |
| Requests with unavailable usage | 10 | 4 |
| Ranking failures | 14 | 11 |

Retrieval time includes every selection call and refresh in a trial. Different selectors can lead search through different states and query counts; these totals are component costs, not a controlled per-query speed ratio. Warmup is outside the goal clock.

Sine alone solved 0 locations; sparse alone solved 9. The declaration-grouped bootstrap 95% interval for **Sine minus sparse** is **-12.3 to -2.3 percentage points**. This interval describes this development cohort, not every Mathlib goal or service condition.

## Failures and completeness

All 268 expected paired trials were recorded. No trials were budget-blocked, no modules failed, and no runtime panics occurred. Every reported success passed source-bound offline replay.

Jev errors remained in the measured pipeline, with the engine retaining the original candidate order on a ranking failure. There were no retries or dropped trials:

- Sine: 4 × `TypeSafe response: rank: probabilities must sum to 1 (tolerance 0.001)`; 10 × `TypeSafe HTTP 400`.
- Sparse: 7 × `TypeSafe response: rank: probabilities must sum to 1 (tolerance 0.001)`; 4 × `TypeSafe HTTP 400`.

HTTP errors without reported usage remain in request counts and timing; token totals include only reported usage. The error log does not provide further details for HTTP 400 responses.

## Protocol and provenance

The complete run used benchmark revision `78b4eb8d2420bad75538ebfa50523ed36ee155da`; JevSelector `41e1afac56702e2294bb036f6572f57348db15cf`; JevHammer `603573da7aa272dcaf2ef9860e7c886210a1433a`; Mathlib `db584cd6d46c92f209a44c0f1c829460d327499d`; and Lean 4.33.0. The machine-readable report records the full configuration, dependency pins, hashes, and per-arm costs.

The [first collection attempt](mathlib-broad-v1-incomplete.json) was incomplete because sparse warmup rejected two freshly elaborated current-file statements. A general selector correction now computes current-file features from the live environment while retaining strict imported-statement checks. Its regression suite passed, and rediscovery reproduced all 256 sites, goals and split assignments exactly. An [offline admission and source-consistency check](mathlib-broad-v1-compatibility.json) passed all 134 development locations before this full paired rerun. No locations were removed or tactics tuned. The incomplete attempt remains separate; its outcomes were not merged with this run.

The sparse index excludes **all 188 benchmark owners** from its fitted statistics, including both splits. It contains 255,050 theorem statements, with 254,885 eligible for fitting; preparation took 207.7 seconds and produced a 155.7 MB artifact. The comparison reuses the original fit because its recipe and exclusion owners are unchanged. Sine uses its own compiled imported-statement statistics. Both selectors are restricted to declarations available in the preceding-command environment.

This complete run used **397 requests**, **1,982,119 reported input tokens**, and **51,170 reported output tokens**. Its caps were 804 requests and 8,375,000 reported input tokens. The earlier incomplete attempt used another 373 requests, 1,860,120 reported input tokens and 47,315 reported output tokens, with 16 requests of unknown usage.

Heavy processes ran serially under a **24,000,000,000-byte, zero-swap cgroup**, with two Lean threads. The complete run had no cgroup limit or OOM events.

This is one complete development comparison after a compatibility correction, without identical-version repeats to estimate service or timing variation. The cohort is stratified and size-filtered, not a uniform sample of Mathlib. It does not compare against full LeanHammer or a neural premise selector.

## Data and reproduction

- [Machine-readable report](mathlib-broad-v1-results.json): settings, pins, paired statistics, costs, and evidence hashes.
- [Per-location results](mathlib-broad-v1-trials.jsonl): all 268 trial outcomes, keyed by site and method, with timings and inclusive reported usage.
- [Dataset and commands](../datasets/mathlib-broad-v1/README.md): frozen development/evaluation manifests, exclusions, preparation, and collection instructions.

Per-location results summarize independently checked outcomes; they do not embed proof certificates or raw request payloads. Those are retained in the original local run. Reproduction makes new live calls and generates its own certificates, which the runner independently replays. Different runs can have different outcomes and timing.
