# JevHammer versus full LeanHammer: 34-location pilot

Completed on 2026-09-21. The strongest current CPU configuration solved
**16/34 locations**, versus **13/34** for neural-premise JevHammer and **12/34**
for full LeanHammer. This favors the CPU configuration on this small development
pilot; it does **not** establish general superiority.

All three methods attempted the same 34 intermediate Mathlib goals, from 34
declarations in 34 modules. The primary outcome requires an independently
replayed proof produced within **six seconds end to end**, including retrieval,
search, reconstruction and certificate construction.

| Method | On-time verified | Rate | Total goal time | Premise retrieval | Initialization |
|---|---:|---:|---:|---:|---:|
| CPU sparse + conclusion matching, JevHammer | 16/34 | 47.1% | 115.454 s | 6.440 s | 142.813 s |
| Neural + conclusion matching, JevHammer | 13/34 | 38.2% | 124.683 s | 11.580 s | 154.540 s |
| Full LeanHammer, upstream neural selection | 12/34 | 35.3% | 123.216 s | 7.271 s | 121.178 s |

Goal times sum all attempts, including failures; retrieval is included in those
times. Initialization sums the per-module warmup hooks and is outside goal
timing. It is not a measurement of standalone service startup. Full LeanHammer's
retrieval time comes from its instrumented upstream selector, rather than the
JevHammer retrieval counter.

All **102 trials** were recorded, and **all 41 successful proofs independently
replayed** against the original source goals. There were no late successful
proofs, module failures, or request-budget-blocked trials.

## Paired outcomes and uncertainty

Each row compares the first method with the second on identical goals. Intervals
use a declaration bootstrap with 1,000 resamples and seed zero.

| Comparison | Gained | Lost | Net difference | 95% interval |
|---|---:|---:|---:|---:|
| CPU JevHammer versus full LeanHammer | 6 | 2 | +11.8 percentage points | −5.9 to +26.5 pp |
| Neural JevHammer versus full LeanHammer | 4 | 3 | +2.9 percentage points | −11.8 to +17.6 pp |
| CPU JevHammer versus neural JevHammer | 3 | 0 | +8.8 percentage points | 0.0 to +17.6 pp |

CPU JevHammer found four more proofs overall than full LeanHammer, but also
missed two proofs that LeanHammer found. The uncertainty interval includes zero.
This repeatedly exposed pilot is suitable for development decisions, not a
held-out superiority claim. All **122 reserved evaluation locations remain
unused**. Local artifact preparation excluded all 188 broad-cohort owners;
third-party neural training overlap is unknown.

The earlier [134-location selector comparison](cpu-selector-research-status.md)
found CPU/conclusion 63/134 and neural/conclusion 64/134, both inside JevHammer.
That larger result measures premise selection under a shared search engine;
it is not a full LeanHammer comparison. Historical monolithic results are not
attributed to these packages.

## Configuration and costs

The two JevHammer methods use identical Mathlib tactic sets and search settings:
depth 3, 12 nodes, beam 4, 24 successor candidates, 100 retrieved premises,
8/16 finishing prefixes, one permitted premise refresh, and at most three Jev
calls. Jev `jev-1.13.0` guides proof-state selection. Premise reranking and
deferred guidance are disabled.

Full [LeanHammer](https://github.com/JOSHCLUNE/LeanHammer) retains all upstream
engines and default parallelism: Aesop, grind, Lean-auto/Zipperposition/Duper,
and Lean-SMT/cvc5. It keeps its default five-second internal solver timeout,
which excludes retrieval. The common six-second observed deadline determines
the reported score. Its whole invocation receives 200,000 heartbeats;
JevHammer's 15,000-heartbeat limit applies to each small tactic attempt. All
methods have the same 200,000-heartbeat outer allowance and eight Lean workers.

| Method | Jev requests | Reported input tokens | Reported output tokens | Ranking failures |
|---|---:|---:|---:|---:|
| CPU JevHammer | 42 | 241,279 | 5,988 | 2 |
| Neural JevHammer | 45 | 267,350 | 6,876 | 2 |
| Full LeanHammer | 0 | 0 | 0 | 0 |

The CPU arm has one request with unknown token usage, so its reported token
total is incomplete. All failures remain in the scores; no selective retries
were performed. Full LeanHammer made 37 neural-selector calls across the 34
locations, because some locations have multiple goals. Every call returned
premises: **zero selector errors, zero Sine fallbacks, and zero unavailable
suggestions**. The neural model ran on CPUs with two embedding threads.

The complete job, including services and solvers, ran sequentially within one
**16,000,000,000-byte, zero-swap cgroup**. Peak usage was **10,514,669,568 bytes**
(10.515 GB), with no memory-limit or OOM events. Separate preflight validation
peaked at 11.029 GB. All services stopped after the run, and the benchmark scope
is gone.

Arms ran in fixed order: CPU, neural, full. Each method/module used a separate
Lean process. The full LeanHammer arm started fresh neural service processes;
model/corpus disk caches persisted. The pilot does not estimate sensitivity to
run order, network latency, alternative timeout settings, or stochastic Jev
responses. No individual failed goal was examined or used to tune the methods.

## Reproduction and evidence

The [optional LeanHammer integration](../integrations/leanhammer/README.md)
contains the public adapter and pinned dependencies. The
[precommitted protocol](full-leanhammer-pilot-protocol.md) gives settings,
holdouts, timing rules and resource limits. The
[preflight record](full-leanhammer-pilot-validation.json) records independent
engine smoke tests, nine synthetic proof replays, and unchanged goal admission.

- Benchmark freeze: `b6fdb4afa29d8846443087917fbfcdaacf0cdd26`.
- Base runner: `bb2b1861f665c3854d49b3f115d6a413aab2611f`.
- JevHammer: `bf848e36e2f70f5ca745e0f88f6953279e7d00a6`.
- JevSelector: `397bef6d03d6ef4c7cda8ada8f3f92fb567863e1`.
- Full LeanHammer: `21886b7ffbdf32017655a9d6e699f98779046533`.
- Lean 4.33.0; Mathlib `db584cd6d46c92f209a44c0f1c829460d327499d`.

The host's pre-existing cvc5/GMP link adjustment and Zipperposition loader
adaptation remain in use; binary and patch hashes are recorded. The exact
pinned Python runtime was restored from the Nix cache before validation,
without model or dependency-version changes.

See the [machine-readable report](full-leanhammer-pilot-v1.json) for paired
statistics, configs, deployment provenance, token counts and evidence hashes,
and the [102 per-trial records](full-leanhammer-pilot-v1-trials.jsonl) for
source identifiers, outcomes, timing and search statistics. Original response
logs and replay certificates are retained in the local run directory. The
checked exporter is `scripts/compare_full_leanhammer.py`; it does not launch runs.
