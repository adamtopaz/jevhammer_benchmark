# Jev graph destination-preview proof comparison

Freeze these adapters, configuration and re-admitted dataset before live model
calls. The original graph screen solved 14/34 versus CPU control 16/34 and the
stronger neural arm 15/34; it was not promoted. This comparison tests whether
showing reachable statements makes the graph's direction choices more useful.
It does not change the graph's fixed-direction ranking rule.

Use the same 34 exposed development locations and source-goal hashes. All 188
broad-cohort owners remain excluded from the prepared CPU index. Re-admission
makes zero model calls. The 122 reserved evaluation locations stay unused.

| Method in `JevHammerBenchmark.GraphPreviewStudy` | Premise selection |
|---|---|
| `cpuControl` | Public sparse + conclusion fusion, native order |
| `original` | Same base + original Jev signature-graph choices |
| `preview` | Same base + Jev graph choices with destination statements |
| `neuralNative` | Warmed neural + conclusion fusion, native order |
| `neuralReranked` | Same neural source + Jev premise reranking |

Every arm uses Jev proof-state guidance, the same Mathlib tactics, six seconds,
200,000 outer heartbeats, three shared Jev calls, 100 retrieved names, eight
injected premises initially (the unchanged finisher also tries sixteen), and
unchanged search/refresh settings. Only `neuralReranked` sets `guidePremises`.
Both graph arms use the budgeted selector factory; their requests consume the
same call and clock allowance as proof-state requests. No additional client,
hidden guidance budget, or warmed evaluation-goal query is permitted.

The graph retains one round, eight frontier nodes, 128 visited/reached names,
256 available forward candidates per node, 32 followed edges, 1,200 seed-type
characters, 10,000 extra query heartbeats and reciprocal-rank offset 16. The
preview arm adds at most three admissible destination examples per direction,
each with at most 480 printed type characters. Filtering precedes the display
limit, truncation/omission flags are explicit, and previews use the same ranked
edges as expansion. Zero previews retain the original payload. The preview
question explains how the displayed destination statements relate to an action.

Native profiles preserved all 384 ordered outputs for zero-preview compatibility
and all 384 fixed-direction outputs for three previews, with no query errors.
Preview CPU cost is approximately 243–248 ms median and 383–387 ms p95, excluding
real Jev latency; choice-plus-question payloads grew from about 6 KB to 17 KB.
This exceeds the provisional 200 ms CPU p95 target. Measure whether proof quality
earns that additional cost without redefining the target after observing results.
See [the cost protocol and evidence](cpu-selector-graph-cost-protocol.md).

Selector pin: `397bef6d03d6ef4c7cda8ada8f3f92fb567863e1`.
JevHammer pin: `2e3df668acbef581c81adccf70e629119cd28760`.
Public statement-index SHA-256:
`e388078b747f85320c672a78570d3831bb4ce6b754d3df493ed7095afe4cd7f5`.
Use Jev `jev-1.13.0` and the same pinned CPU neural model/corpus as the original
screen, with fresh services. Third-party neural training overlap remains unknown.
This compares selectors within JevHammer, not the complete LeanHammer tactic.

Each arm has an independent structural query cache cloned from the fixed `True`
warmup. The imported signature graph is immutable and shared; current-file
signatures are rebuilt live. Neural imported and earlier current-file statement
embeddings are warmed outside goal timing, with actual goal embedding timed.
Record goal-independent initialization separately, under the five-million
warmup heartbeat limit and the same memory scope. Per-arm initialization cost
attribution is order-dependent where immutable preparation is shared.

Collect all **170 trials** serially, with at most **510 Jev requests** and
**5,000,000 reported input tokens**. Use two CPU threads and one aggregate
**16,000,000,000-byte, zero-swap scope** containing all services and Lean workers.
Do not run other heavy work concurrently, alter the run after seeing partial
results, or selectively retry model failures. Independently replay every claimed
proof against its source context, rejecting self-dependence and admissions.

Report on-time and late verified coverage, paired gains/losses and declaration-
grouped intervals, selector/premise/state call counts, API failures, token usage,
retrieval/search/warmup time, source/artifact identities and memory events. Analyze
model direction choices mechanically in aggregate; do not inspect individual
failed goals. Preserve negative results.

Advance the preview candidate to the 134-location development cohort only if
its on-time replayed count beats CPU control, the original graph, and both neural
arms. The exposed pilot cannot establish final superiority. The research goal
still requires a substantial gain on untouched evaluation with a fresh-response
repeat; all 122 reserved locations remain untouched during this screen.

With the CPU reference services configured in the same bounded scope:

```sh
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-graph-preview-v1.json \
  --methods JevHammerBenchmark.GraphPreviewStudy.cpuControl \
    JevHammerBenchmark.GraphPreviewStudy.original \
    JevHammerBenchmark.GraphPreviewStudy.preview \
    JevHammerBenchmark.GraphPreviewStudy.neuralNative \
    JevHammerBenchmark.GraphPreviewStudy.neuralReranked \
  --config '{}' --max-requests 510 --max-input-tokens 5000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-graph-preview-v1
```
