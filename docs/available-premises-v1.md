# Available-premise sensitivity study: 1,024 Mathlib goals

These are whole-tactic results, not an ablation of Jev guidance: 353 of the strict
CPU arm's 438 on-time solves made no Jev call. A call on the other 85 does not
establish that Jev improved their outcomes. See the [attribution audit](guidance-attribution.md).

Completed on 2026-09-22 in Edmonton (2026-09-23 01:33 UTC). Restricting the CPU
selector's preparation to imported statements available before each tested
theorem produced **438/1,024 on-time verified proofs (42.77%)**. A fresh run of
the original CPU preparation produced **448 (43.75%)**, neural/conclusion
JevHammer **466 (45.51%)**, and full LeanHammer **371 (36.23%)**.

The primary strict-minus-original CPU difference is **−0.98 percentage points**,
with a stratified module-bootstrap 95% interval of **−2.14 to +0.19 points**.
This does not establish equivalence or show that the preparation policy has no
effect. Strict CPU remains ahead of full LeanHammer by **6.54 points**
(95% interval **+4.16 to +8.97**), while neural JevHammer scores highest.

This is a sensitivity study on the same previously exposed goals as the
[original confirmation](full-leanhammer-confirmation-v1.md), not a new unseen
evaluation. It addresses unavailable-statement exposure in the CPU selector;
Jev and the neural selector still have unknown pretraining overlap.

## What changed

The original CPU artifact excludes evaluated owners and their named children
from fitted statistics, but includes other Mathlib statements, including later
or downstream declarations. Those can affect symbol frequencies, mean statement
length, and bounded posting selection before environment filtering. It reads
no proof bodies, but that alone does not make its preparation dependency-isolated.

The strict arm builds its sparse index solely from **imported Mathlib signatures
in the safe environment preceding the tested declaration**. It never loads the
full-library artifact. All 1,212 original and earlier held-out owners, including
named children, remain excluded from fitting. Public definitions and constructors
are candidate-only. Both fitted statistics and imported retrieval postings use
only this available catalog; unavailable statements cannot influence posting
sampling. Earlier current-file premises are supplied from their live types,
without including that prefix in fitted statistics. The index is prepared once
per source module, outside the goal clock. This is a conservative subset of the
statements available before each theorem, rather than a fit on the growing prefix.

The discrimination trees for matching theorem conclusions, sparse scoring and
rank fusion, tactic set, and Jev proof-state search are unchanged. The experiment
therefore compares preparation policies, including their effect on retrieval;
it does not isolate one frequency statistic or remove all model-training overlap.

## Coverage and paired analysis

All four methods attempted identical intermediate states from 1,024 distinct
declarations across 131 modules and 17 subject areas. All **4,096 trials** were
retained. All **1,726 successful trial proofs passed independent kernel replay**;
one strict CPU proof and two neural JevHammer proofs arrived late and are excluded
from the 1,723 on-time successes. There were no missing trials, source-module
failures, replay failures, or budget-blocked trials.

| Method | On-time verified | Rate | Total goal time | Premise retrieval | Per-module warmup |
|---|---:|---:|---:|---:|---:|
| Strict imported-statements CPU + conclusion matching, JevHammer | 438/1,024 | 42.77% | 3,170.866 s | 73.932 s | 406.266 s |
| Original CPU sparse + conclusion matching, JevHammer | 448/1,024 | 43.75% | 3,216.435 s | 189.518 s | 531.382 s |
| Neural + conclusion matching, JevHammer | 466/1,024 | 45.51% | 3,350.090 s | 590.704 s | 422.736 s |
| Full LeanHammer, upstream neural selection | 371/1,024 | 36.23% | 3,918.389 s | 508.268 s | 308.085 s |

Goal time includes successful and unsuccessful attempts, retrieval, and proof
certificate construction. Full LeanHammer retrieval is measured by its upstream
selector instrumentation. Warmup is outside goal timing and excludes standalone
service startup and the remaining source elaboration. Faster retrieval does not
imply a proportional improvement in total goal time or proof coverage.

Each contrast is paired on the same goals. Intervals resample whole modules
within subject areas, with 20,000 draws and seed 20260921, as specified before
collection. Positive differences favor strict CPU.

| Strict CPU compared with | Role | Gained | Lost | Difference | Module-bootstrap 95% interval |
|---|---|---:|---:|---:|---:|
| Original CPU JevHammer | Primary | 12 | 22 | −0.98 pp | −2.14 to +0.19 pp |
| Neural JevHammer | Secondary | 28 | 56 | −2.73 pp | −4.56 to −0.96 pp |
| Full LeanHammer | Secondary | 112 | 45 | +6.54 pp | +4.16 to +8.97 pp |

The primary interval includes zero and also allows a decrease of about two
percentage points. No equivalence margin was specified. The neural and full
LeanHammer contrasts are secondary comparisons. The exact unclustered McNemar
sensitivity p-value is `0.12145` for the primary contrast; Holm-adjusted values
for the two secondary contrasts are `0.0029853` and `1.7845e-7`. These sensitivity
tests assume independent pairs; the main uncertainty estimate uses modules.
Declaration-bootstrap intervals and exact values are in the JSON report.

| Batch | Goals | Strict CPU | Original CPU | Neural JevHammer | Full LeanHammer | Order |
|---|---:|---:|---:|---:|---:|---|
| 1 | 252 | 100 | 106 | 105 | 81 | Strict, CPU, full, neural |
| 2 | 257 | 118 | 117 | 125 | 92 | CPU, neural, strict, full |
| 3 | 258 | 114 | 117 | 124 | 99 | Neural, full, CPU, strict |
| 4 | 257 | 106 | 108 | 112 | 99 | Full, strict, neural, CPU |
| **Total** | **1,024** | **438** | **448** | **466** | **371** | |

Whole modules were assigned by the frozen hash order, without resampling goals.
The four-treatment Williams design places each method in each position once
and each ordered adjacent method pair once. The original controls were rerun
to account for current timing and Jev variation; their historical counts of
450/469/372 are not substituted or pooled into this comparison.

## Search, preparation and inference costs

All JevHammer arms use the original Mathlib tactic set, depth 3, 12 nodes,
beam 4, at most 24 successor candidates, 100 premises, finishing prefixes of
8/16, one premise refresh, and at most three Jev calls. Jev `jev-1.13.0` guides
proof-state selection, with no premise reranking. Small tactic steps receive
15,000 heartbeats. Full LeanHammer retains all engines and default parallelism:
Aesop, grind, Lean-auto/Zipperposition/Duper, and Lean-SMT/cvc5. Its five-second
internal solver timeout excludes retrieval; coverage for every method uses the
same observed **six-second end-to-end deadline**. Outer heartbeats are 200,000,
with eight Lean workers and two CPU embedding threads.

| Method | Jev attempts | Reported input tokens | Reported output tokens | Ranking failures | Requests with unknown usage |
|---|---:|---:|---:|---:|---:|
| Strict CPU JevHammer | 1,513 | 9,800,123 | 246,306 | 96 | 53 |
| Original CPU JevHammer | 1,472 | 9,278,813 | 237,751 | 108 | 54 |
| Neural JevHammer | 1,344 | 8,474,450 | 214,626 | 93 | 38 |
| Full LeanHammer | 0 | 0 | 0 | 0 | 0 |

Reported token totals omit unknown usage from 145 requests. Ranking failures
remain part of the outcomes; none were retried or selectively removed. Full
LeanHammer made 1,054 neural-selector calls, with **zero errors and zero Sine
fallbacks**. One unavailable suggested constant was filtered out. Locations
with multiple goals can make more than one selector call.

The 131 strict warmups, including preparation and validation, total 406.266 s:
median 2.605 s, range 1.075–7.746 s. Imported catalogs range from 21,517 to
143,216 declarations, with 17,757–124,304 eligible fitting rows. Every preparation
record excludes its current module from imported fitting data and records the
full 1,212-owner holdout and no proof information. The original CPU artifact was
reused unchanged; its historical 92.16-second preparation cost is separate.

Before live collection, all 1,024 source states were re-admitted unchanged,
20 Python tests passed, native isolation and all-engine checks passed, and the
new fitter matched the original recipe on identical full-Mathlib input, including
all 318,231 catalog rows and exact posting order. These checks used no Jev calls
or benchmark proof trials; see the [validation record](available-premises-validation.json).

## Resources, limitations and reproduction

Collection and replay shared one **16,000,000,000-byte, zero-swap cgroup**, with
one heavy job at a time. Collection took **20,333.68 seconds (about 5 hours
39 minutes)**, including startup, source elaboration and replay. Peak memory was
**15,558,819,840 bytes (15.559 GB)**, with zero memory-limit, OOM or OOM-kill events.
Owned services stopped and the collection scope disappeared before analysis,
which also ran under the 16 GB cap. An initial credential lookup timed out before
the runner or any trials started; startup was repeated after unlocking it.
There were no benchmark restarts, selective retries, or outcome-dependent exclusions.

Neural service processes were fresh for each batch/method, including CPU runs
where their endpoint was unused; disk caches persisted. All 16 service provenance
records match. Native solver binaries and the existing cvc5/GMP patch match the
original study. Local inference used CPUs; Jev is a remote service.

These are single runs on a previously exposed, stratified and size-filtered
sample of intermediate goals, not all Mathlib or complete theorem synthesis.
The five original whole-module compatibility exclusions still limit the sampled
population. No new exclusions or tactic tuning followed the outcomes. The older
122 reserved goals remain untouched. Timing, network conditions and Jev decisions
vary, and neither pretrained model has certified training separation. The result
supports the strict CPU configuration's advantage over full LeanHammer on this
cohort and budget; it does not establish a universal tactic ranking or an entirely
uncontaminated stack.

- [Frozen protocol](available-premises-protocol.md) and [cohort/holdouts/schedule](../datasets/available-premises-v1/README.md).
- [Reproduction and offline statistical checks](reproducing-available-premises.md).
- [Machine-readable report](available-premises-v1.json), including all 131 preparation records, configurations, paired statistics and evidence hashes.
- [All 4,096 trial records](available-premises-v1-trials.jsonl).
- [Service, native-binary and dependency audit](available-premises-v1-deployment.json).

The pre-trial freeze is `4542261dff1d46d343ac1b926fb94a1cc04b4185`; the protocol
and implementation were committed earlier at `f9f4d79`. Lean, Mathlib, JevHammer,
JevSelector, LeanHammer and neural model/corpus pins remain those of the original
study. The unmodified exporter checked all sixteen complete arms, 4,096 distinct
method/location pairs, matching configurations, preparation provenance and proof
replays. Raw logs and certificates remain in `runs/available-premises-v1`, with
checksums published. The offline checker recomputes statistics and checks recorded
replay flags; a fresh live reproduction creates new certificates for kernel replay.
