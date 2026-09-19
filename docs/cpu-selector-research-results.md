# CPU selector research: development results

These exploratory comparisons belong to `research/cpu-selector`. The
[protocol](../notes/cpu-selector-research.md) was committed before collection.
The 122-site reserved evaluation partition has not been used.

## First neural reference: complete

On the fixed 34-site, 34-module development pilot, with six seconds per goal:

| Configuration | On-time verified | Total goal time |
|---|---:|---:|
| Prepared sparse + Jev state guidance | 13/34 | 120.289 s |
| Neural retrieval + Jev premise/state guidance | 11/34 | 160.954 s |

Sparse gained three locations and lost one. The declaration-bootstrap 95%
interval for sparse minus neural is **−5.9 to +17.6 percentage points**. This
small development result does not establish superiority. All 68 trials were
recorded and all 24 successful proofs independently replayed, with no late
successes or budget-blocked trials. The sparse arm had five ranking failures;
the neural arm had none. Failures remain included in the results.

Both used the same expanded Mathlib tactics and Jev proof-state guidance. The
neural arm additionally reranked premises, sharing the same three-call cap with
state guidance. This is a comparison of the two existing configurations. The
second pre-registered comparison disables premise reranking in both arms;
its separate results follow below.

The pinned CPU neural service and the benchmark shared one **16,000,000,000-byte,
zero-swap cgroup**. The measured peak was **11,343,564,800 bytes**, with no limit
or OOM events. This replaces the earlier 24 GB execution limit. Model, corpus,
deployment validation, request costs, configurations, and evidence hashes are
in the [machine-readable report](cpu-selector-neural-reranked-reference.json).
[Every trial](cpu-selector-neural-reranked-reference-trials.jsonl) is also published.

Neural initialization warms the imported catalog outside the goal clock. New
current-file statements can still require embedding during retrieval, and that
time is included. The service remains alive between the two configurations, so
the second run can benefit from its embedding cache. The external model's
training overlap is unknown. No new selector has been benchmarked at this stage,
and no result here reproduces or supersedes the historical 1,024-site evaluation.

## Neural retrieval without premise reranking: complete

| Configuration | On-time verified | Total goal time | Retrieval time |
|---|---:|---:|---:|
| Prepared sparse + Jev state guidance | 14/34 | 116.860 s | 4.669 s |
| Neural retrieval + Jev state guidance | 15/34 | 117.648 s | 10.788 s |

Neural gained one location and lost none against the concurrent sparse control.
The paired interval for neural minus sparse is **0.0 to +8.8 points**. All 68
trials were recorded and all 29 successes independently replayed. Neither arm
had late successes or budget-blocked trials. Sparse had two ranking failures;
neural had three. All failures are included. The run used 102 Jev requests,
535,487 reported input tokens, and 12,146 reported output tokens, with unknown
usage on four requests. The cumulative service/benchmark memory peak remained
11.34 GB, with no cgroup limit or OOM events.

The higher neural result does **not** isolate the effect of removing premise
reranking: this second run also reused the first run's service embedding cache,
and the fresh sparse control itself changed from 13 to 14 successes. Neural
retrieval's total time fell from 48.814 to 10.788 seconds across runs. Use the
15/34 configuration as the stronger observed reference for further experiments,
with matched fresh controls and explicit cache conditions.

[Second machine-readable report](cpu-selector-neural-retrieval-reference.json)
and [all second-run trials](cpu-selector-neural-retrieval-reference-trials.jsonl).
Across both runs there are 136 recorded trials and 53 independently replayed
successful trials, on the same 34 development locations. This is a baseline
milestone; no new-selector improvement has been demonstrated yet.
