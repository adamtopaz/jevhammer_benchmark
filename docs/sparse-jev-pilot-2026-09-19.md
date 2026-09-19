# Sparse retrieval + Jev premise ranking: development pilot

**Eager Jev premise reranking did not improve coverage in this pilot.** With
100 candidates it lost one of the sparse control's successes; with 32 it solved
exactly the same locations as its control, with lower overhead than the larger
pool. All **51 successful trials independently replayed** against their original
source goals.

Each comparison evaluated the same **34 development locations from 34 distinct
declarations, 34 Mathlib modules and 17 subject areas**. Both arms used Jev
proof-state guidance, identical Mathlib tactics, six-second goal budgets, and
three total Jev calls. Within each pair, only `guidePremises` differed.

| Candidate pool | Sparse control | Sparse + Jev premises | Hybrid-only wins | Control-only wins | Total goal time, control / hybrid |
|---|---:|---:|---:|---:|---:|
| 100 | 13/34 (38.2%) | 12/34 (35.3%) | 0 | 1 | 119.350 / 145.530 s |
| 32 | 13/34 (38.2%) | 13/34 (38.2%) | 0 | 0 | 119.890 / 127.775 s |

The two controls solved the same thirteen locations. Hybrid total goal time was
**21.9% higher** at 100 candidates and **6.6% higher** at 32. These totals include unsuccessful attempts and exclude initialization. No successful trials were late.

## How the combination works

The existing `Prepared.sparseReranked` method retrieves the sparse selector's top
N available premises, then gives Jev the goal, local context, and each premise's
pretty-printed statement. It asks an independent usefulness question for each
lemma, using [TypeSafe's Noul API](https://docs.typesafe.ai/api#noul), and orders
the premises by those scores. Multiple premises can score highly. Lean then
tries the same premise-assisted tactics and proof-state search as the control.

This is eager reranking: it runs before the first premise-assisted finishing
attempt, and can run once more after a changed proof state triggers retrieval.
The original sparse order is retained if ranking fails. Every returned premise
must already exist in the actual source environment; Jev cannot invent lemmas
or proof steps.

## What the extra calls did

| Metric | Control, 100 | Hybrid, 100 | Control, 32 | Hybrid, 32 |
|---|---:|---:|---:|---:|
| Premise-ranking requests | 0 | 50 | 0 | 50 |
| Proof-state requests | 55 | 24 | 54 | 25 |
| Median premise request | — | 704 ms | — | 434.5 ms |
| Total premise request time | 0 | 36.482 s | 0 | 21.827 s |
| Median goal time | 4.282 s | 5.521 s | 4.336 s | 4.896 s |
| Total sparse retrieval time | 4.858 s | 4.958 s | 4.573 s | 4.626 s |
| Reported input tokens | 290,774 | 1,222,578 | 291,980 | 474,689 |
| Reported output tokens | 6,595 | 86,460 | 6,612 | 28,675 |
| Ranking failures | 4 | 0 | 2 | 1 |

Both hybrid runs invoked premise scoring at 28 of the 34 locations. All 100
premise-scoring requests across the two runs returned valid answers. Every
batch changed the top-sixteen premise set: the 100-candidate run introduced
**9.8 new top-sixteen members per batch on average**, and the 32-candidate run
introduced **5.74**. Reranking was a substantial intervention, not a no-op.

Premise and state calls share a three-call cap. The hybrid therefore made about
half as many proof-state requests, while spending more time on premise calls.
The measured result includes both the changed premise ordering and that resource
tradeoff. It does **not** isolate intrinsic premise-ranking quality from search
time or call allocation. The data do not establish which factor caused the lost
success in the 100-candidate run.

Retrieval totals include refreshes and can reflect different search paths.
Request time includes transport and response handling. The shared sparse index
is loaded once per source process; whichever arm runs first pays its loading
cost outside the goal clock. Per-arm warmup differences are not independent
measurements of selector initialization speed.

## Completeness and uncertainty

All **136 expected trials** were recorded and every successful trial replayed.
There were no module failures, runtime panics, late successes, or budget-blocked
trials. All seven ranking failures were proof-state requests:

- At 100 candidates, the control had three HTTP 400 responses and one invalid
  probability sum; the hybrid had no ranking failures.
- At 32 candidates, the control had two HTTP 400 responses; the hybrid had one
  invalid probability sum.

Failures used the existing original-order fallback and remained in the timing
and outcome records. No requests were retried. Five HTTP errors had no reported
usage, so token totals cover reported usage rather than a complete billing total.

The declaration-grouped bootstrap 95% interval for **hybrid minus control** is
**−8.8 to 0.0 percentage points** at 100 candidates. At 32 candidates every paired
outcome is identical, so resampling those observations yields the degenerate
interval **[0, 0]**. That is not evidence of exact population equivalence or an
absence of service/timing variation. This is a small, previously exposed
development subset with one run per setting, not a final held-out confirmation.
The 122-location reserved evaluation partition was not used.

## Reproduction and provenance

The [protocol](../notes/sparse-jev-pilot.md), [dataset](../datasets/sparse-jev-v1/dataset.json),
and both candidate limits were frozen before collection at benchmark revision
`ecee56a3e54788eb3afd4f5be98ef56d06338cde`. Selection used seed 19 and one location
per module from the broad development split, without consulting outcome files.
No methods or tactics were changed between the runs.

The comparison used Lean 4.33.0, Mathlib
`db584cd6d46c92f209a44c0f1c829460d327499d`, JevHammer
`603573da7aa272dcaf2ef9860e7c886210a1433a`, JevSelector
`41e1afac56702e2294bb036f6572f57348db15cf`, and `jev-1.13.0`.
The sparse artifact excludes all 188 owners of the full broad cohort from fitted
statistics; its SHA-256 is recorded in the machine-readable report.

Each run allowed 204 requests and 4,000,000 reported input tokens. Together they
used **258 requests**, **2,280,021 reported input tokens**, and **128,342 reported
output tokens**. Heavy work ran serially under a **24,000,000,000-byte, zero-swap
cgroup** with two Lean threads. There were no cgroup limit or OOM events.

- [Commands](../datasets/sparse-jev-v1/README.md) reproduce both matched runs.
- [Machine-readable report](sparse-jev-pilot-2026-09-19.json) records configurations,
  separate premise/state costs, uncertainty, resources, and evidence checksums.
- [Per-location results](sparse-jev-pilot-2026-09-19-trials.jsonl) contain every trial's
  verified outcome, timings, call counts, and reported usage. Original requests
  and proof certificates remain in the local run directories; new live runs
  generate their own independently replayed certificates.

## Follow-up hypotheses

A next experiment should try the sparse premise-assisted finisher **before**
paying for Jev reranking, then ask Jev only if that attempt fails. Separating
premise and proof-state call budgets would help test whether premise guidance
adds value without displacing state guidance. A rank blend that retains some
high-scoring sparse premises is another candidate. These policies were **not
implemented or measured** in this pilot; the present evidence supports keeping
plain sparse retrieval as the measured baseline.
