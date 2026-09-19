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
second pre-registered comparison disables premise reranking in both arms and
is still running; its outcomes must be reported separately.

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
