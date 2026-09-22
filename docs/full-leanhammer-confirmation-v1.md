# JevHammer versus full LeanHammer: 1,024-goal confirmation

Completed on 2026-09-21 in Edmonton (2026-09-22 01:33 UTC). On **1,024 fresh
intermediate Mathlib goals**, CPU/conclusion JevHammer solved **450 (43.95%)**,
neural/conclusion JevHammer **469 (45.80%)**, and full LeanHammer **372 (36.33%)**
within six seconds. Every counted proof passed independent replay.

The prespecified primary comparison favors CPU JevHammer over full LeanHammer:
**+7.62 percentage points**, with a stratified module-bootstrap 95% interval of
**+5.34 to +9.91 points**. CPU JevHammer found 117 proofs that LeanHammer missed
and missed 39 that LeanHammer found. That is 78 more proofs overall, or 21.0%
more relative to LeanHammer's count, under the tested configuration and limits.

Neural JevHammer scored highest. The secondary CPU-versus-neural comparison
favors neural by 1.86 points; this study does **not** establish CPU-selector
superiority. Both JevHammer arms use Jev for proof-state selection, and their
premise selectors both include structural conclusion matching.

## Coverage and paired analysis

The methods attempted identical source states from 1,024 distinct declarations
in 131 modules across 17 subject areas. All **3,072 trials** were retained.
All **1,292 successful trial proofs** replayed: 1,291 arrived on time, and one
neural JevHammer proof arrived late and is excluded from the scores. There were
no module failures, missing trials, replay failures or budget-blocked trials.

| Method | On-time verified | Rate | Total goal time | Premise retrieval | Warmup |
|---|---:|---:|---:|---:|---:|
| CPU sparse + conclusion matching, JevHammer | 450/1,024 | 43.95% | 3,143.744 s | 190.369 s | 536.365 s |
| Neural + conclusion matching, JevHammer | 469/1,024 | 45.80% | 3,271.963 s | 577.650 s | 504.615 s |
| Full LeanHammer, upstream neural selection | 372/1,024 | 36.33% | 3,911.933 s | 503.339 s | 394.488 s |

Goal times sum successful and failed attempts, including retrieval and proof
certificate construction. Warmup sums the per-module hooks outside goal timing;
it does not measure standalone service startup or all source elaboration.
Full LeanHammer retrieval uses its instrumented upstream selector, rather than
the JevHammer adapter's retrieval counter. CPU retrieval took about one third
as much time as neural/conclusion retrieval, but the total goal-time difference
was much smaller. These are aggregate costs, not successful-proof latency alone.

Each comparison below is paired on the same goals. The main intervals resample
whole modules within each of the 17 subject areas, with 20,000 resamples and
seed 20260921. Positive differences favor the first method.

| Comparison | Role | Gained | Lost | Difference | Module-bootstrap 95% interval |
|---|---|---:|---:|---:|---:|
| CPU JevHammer − full LeanHammer | Primary | 117 | 39 | +7.62 pp | +5.34 to +9.91 pp |
| Neural JevHammer − full LeanHammer | Secondary | 128 | 31 | +9.47 pp | +7.16 to +11.83 pp |
| CPU JevHammer − neural JevHammer | Secondary | 24 | 43 | −1.86 pp | −3.47 to −0.29 pp |

The primary interval excludes zero, meeting the prespecified criterion for a
positive result on this population and budget. Secondary comparisons remain
exploratory. The exact unclustered McNemar sensitivity p-value is
`2.9939e-10` for the primary contrast. For the secondary contrasts, Holm-adjusted
McNemar p-values are `6.6703e-15` and `0.02712`, respectively. These sensitivity
tests assume independent pairs; the primary inference uses the module interval.
Declaration-bootstrap intervals and exact values are in the JSON report.

The six batches used all six method-order permutations exactly once:

| Batch | Goals | CPU JevHammer | Neural JevHammer | Full LeanHammer | Order |
|---|---:|---:|---:|---:|---|
| 1 | 169 | 71 | 77 | 64 | CPU, full, neural |
| 2 | 176 | 75 | 75 | 58 | CPU, neural, full |
| 3 | 169 | 72 | 79 | 65 | Full, CPU, neural |
| 4 | 174 | 88 | 88 | 69 | Full, neural, CPU |
| 5 | 178 | 79 | 86 | 65 | Neural, CPU, full |
| 6 | 158 | 65 | 64 | 51 | Neural, full, CPU |
| **Total** | **1,024** | **450** | **469** | **372** | |

## Fixed methods and costs

The [protocol](full-leanhammer-confirmation-protocol.md) was committed before
fresh discovery. The dataset, CPU artifact identity, schedule and analysis code
were frozen before proof collection. No tactics, selector settings or sample
sizes changed during collection. No individual failed goal was inspected for
tuning, and there were no selective retries or outcome-dependent exclusions.
The earlier [34-goal pilot](full-leanhammer-pilot-v1.md) is not pooled here.

Both JevHammer arms use the same Mathlib tactic set, depth 3, 12 nodes, beam 4,
24 successor candidates, 100 premises, finishing prefixes of 8/16, one permitted
premise refresh and at most three Jev calls. Jev `jev-1.13.0` guides proof-state
selection; premise reranking and deferred guidance are disabled. Each small
tactic attempt receives 15,000 heartbeats.

Full LeanHammer retains all upstream engines and default parallelism: Aesop,
grind, Lean-auto/Zipperposition/Duper and Lean-SMT/cvc5. It keeps its five-second
internal solver timeout, excluding retrieval. All methods have an outer
200,000-heartbeat allowance, eight Lean workers and the same observed six-second
end-to-end deadline. Local neural inference runs on CPUs with two embedding
threads. Jev is a remote service; full LeanHammer makes no Jev calls.

| Method | Jev request attempts | Reported input tokens | Reported output tokens | Ranking failures | Requests with unknown usage |
|---|---:|---:|---:|---:|---:|
| CPU JevHammer | 1,471 | 9,509,819 | 240,832 | 104 | 47 |
| Neural JevHammer | 1,365 | 8,704,268 | 217,884 | 88 | 45 |
| Full LeanHammer | 0 | 0 | 0 | 0 | 0 |

Reported token totals are incomplete because 92 requests have unknown usage.
Ranking failures remain part of the results. No trial was blocked by a request
or token budget. Full LeanHammer made **1,054 neural-selector calls**, with
**zero selector errors and zero Sine fallbacks**. One suggested constant was
unavailable in the current environment and was filtered out. The call count can
exceed the number of locations because a location can contain multiple goals.

The unchanged CPU preparation recipe took **92.16 seconds** on Mathlib, with
a **7.768 GB** peak. Its separate compiled-statement/holdout admission check
peaked at **7.874 GB**. Preparation computes sparse public-signature/IDF data;
it uses no proof bodies or neural training. All 1,024 evaluation owners and 188
earlier cohort owners, including resolved named children, were excluded from
the fitted artifact. The initial admission helper had an API compatibility
error after successful preparation; only that helper was corrected, and the
artifact was not prepared again. [Preparation metadata](../datasets/full-leanhammer-confirmation-v1/preparation.json)
records this history and the successful validation.

## Resource limits and scope of the conclusion

All benchmark services, Lean processes, solvers and replay shared one
**16,000,000,000-byte, zero-swap cgroup**, with one heavy job at a time. The full
collection took 15,777.93 seconds (about 4 hours 23 minutes), including startup,
source elaboration and replay. The peak reached exactly the **16 GB cap**.
There were **942 `memory.events:max` events**, first observed during the final
full LeanHammer arm, and **zero OOM events or kills**. The counter stayed at 942
through the final CPU arm. No run was restarted or discarded. These results
therefore describe performance under this memory constraint, not an
unconstrained LeanHammer deployment. All owned services stopped, and the scope
was gone before analysis began. Analysis also ran in a 16 GB, zero-swap scope.

Each method/module used a separate Lean process. Neural service processes were
fresh for every batch/arm, including CPU arms where that endpoint was unused.
Model/corpus disk caches persisted. Counterbalancing addresses method order,
but this single study does not estimate sensitivity to Jev randomness, network
conditions, alternative deadlines, different hardware or other configurations.

This is a stratified, size-filtered sample of intermediate goals, not a uniform
sample of all Mathlib or a test of complete theorem synthesis. Five entire
modules failed original-source elaboration under benchmark imports and were
excluded before sampling or tested-tactic calls; their identities and diagnostic
hashes are retained. No source proofs were patched. This compatibility restriction
limits the population represented. Third-party neural training overlap remains
unknown. The older 122 reserved goals remain untouched. This result neither
establishes a universal best tactic nor attributes historical monolithic scores
to the current packages.

## Reproduction and evidence

- [Frozen cohort, holdouts, schedule and reproduction instructions](../datasets/full-leanhammer-confirmation-v1/README.md).
- [Optional full LeanHammer integration](../integrations/leanhammer/README.md).
- [Machine-readable report](full-leanhammer-confirmation-v1.json): full configs,
  statistics, resources, pins and checksums of all run/replay evidence.
- [All 3,072 trial records](full-leanhammer-confirmation-v1-trials.jsonl): source
  identifiers, outcomes, timing and search statistics.
- [cvc5/GMP deployment patch](full-leanhammer-cvc5-gmp.patch), matching the
  checksum in the deployment record. The prior Zipperposition loader adaptation
  is unchanged; both native binary hashes are recorded.

The study freeze is `1d094f195531ca329dcdbaa22b9c16d84fe1bc52`. The base runner is
`bb2b1861f665c3854d49b3f115d6a413aab2611f`, JevHammer
`bf848e36e2f70f5ca745e0f88f6953279e7d00a6`, JevSelector
`397bef6d03d6ef4c7cda8ada8f3f92fb567863e1`, full LeanHammer
`21886b7ffbdf32017655a9d6e699f98779046533`, and Mathlib
`db584cd6d46c92f209a44c0f1c829460d327499d`, with Lean 4.33.0.

The exporter `scripts/compare_confirmation.py` checked the six frozen batch
datasets, all 18 complete arms, 3,072 unique method/location pairs, one location
per declaration, matching configurations and all proof replays. Its assertions
passed unchanged. Original logs and proof certificates remain in
`runs/full-leanhammer-confirmation-v1`; their checksums are published rather
than the machine-specific raw directories.
