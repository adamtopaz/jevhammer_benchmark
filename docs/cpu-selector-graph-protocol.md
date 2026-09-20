# Jev-guided signature graph proof screen

Freeze this protocol, adapters and re-admitted dataset before live model calls.
This experiment tests whether Jev's choice of dependency traversal directions
finds premises useful beyond the existing CPU sparse/conclusion selector.
CPU-only graph profiles and exact old/new ranking comparisons are recorded in
the [cost protocol](cpu-selector-graph-cost-protocol.md). No individual failed
proof goal informed the graph algorithm or its performance changes.

Use the same 34 previously exposed development locations, owners and goal
hashes. Re-admit them with zero model calls under the new pinned dependencies.
The 122 reserved evaluation locations remain unopened for proof trials.

| Method | Premise source and guidance |
|---|---|
| `GraphStudy.cpuControl` | Existing public sparse + conclusion fusion, native order |
| `GraphStudy.guided` | Same base + Jev-guided signature graph, native final order |
| `GraphStudy.neuralNative` | Warmed neural + conclusion fusion, native order |
| `GraphStudy.neuralReranked` | Warmed neural + conclusion fusion, Jev premise reranking |

All arms use Jev proof-state guidance, the same Mathlib tactic set, six seconds,
200,000 outer heartbeats, three shared Jev calls, 100 retrieved names, eight
injected premises, and unchanged premise refresh. Preserve both neural guidance
modes because their relative strength varied across earlier experiments. Use
model `jev-1.13.0` and the same pinned CPU neural model/corpus as the prior
reference. This compares selectors inside JevHammer, not full LeanHammer.

The graph has one round, eight frontier nodes, 128 visited/reached names,
256 available forward candidates per node, 32 edges followed per expansion,
1,200 type characters, and 10,000 extra query heartbeats. Starting from goal and
context constants, Jev ranks the choices none/backward/forward, using printed
types and bounded neighborhood counts. The highest-ranked direction for each
node is taken. Neighbor ranking and reciprocal-rank fusion are unchanged from
the validated implementation, with offset 16. No-expansion/failure fallback
preserves the base ranking. Its selector calls consume the same allowance and
clock as proof-state calls; no additional client or hidden call budget is used.

Graph initialization reads signatures only and fits no proof statistics.
The prepared CPU base retains all 188 cohort-owner exclusions and uses unchanged
statement index SHA-256
`e388078b747f85320c672a78570d3831bb4ce6b754d3df493ed7095afe4cd7f5`.
Selector pin: `d6f4e2506c214c5d9cbb16118ff55c53130cb807`.
JevHammer pin: `2e3df668acbef581c81adccf70e629119cd28760`.
Structural query caches are independent per arm, starting from fixed synthetic
warmup; the graph cache contains immutable imported signatures and reconstructs
current-file signatures at each query. Warmup has the separate five-million
heartbeat limit and makes no Jev calls. Measure it outside the goal clock but
inside the resource limit. Neural imported/current-file statement embeddings are
warmed outside goal timing; actual goal embedding remains timed.

Collect all **136 trials**, with at most **408 Jev requests** and **4,000,000
reported input tokens**. Run serial modules, two CPU threads, and fresh neural
services in one **16,000,000,000-byte, zero-swap** scope. Do not run other heavy
jobs concurrently or selectively retry failures. Replay every claimed proof
against its original source context, rejecting self-dependence and admissions.

Report every outcome, on-time/late coverage, paired gains/losses and
declaration-grouped intervals, selector/premise/state calls, API errors, token
usage, retrieval/search/warmup time, source/artifact identities and memory events.
Promote the graph candidate to the larger development cohort only if its on-time
replayed count beats the CPU control and the stronger neural arm in this screen.
Otherwise keep the negative result visible and revise only from generic or
aggregate evidence. This repeatedly exposed pilot cannot establish final
superiority. Any promising candidate still needs untouched evaluation and a
fresh-response repeat.

After preparing the index and configuring the explicit CPU neural services,
run inside their same bounded scope:

```sh
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-graph-v1.json \
  --methods JevHammerBenchmark.GraphStudy.cpuControl \
    JevHammerBenchmark.GraphStudy.guided \
    JevHammerBenchmark.GraphStudy.neuralNative \
    JevHammerBenchmark.GraphStudy.neuralReranked \
  --config '{}' --max-requests 408 --max-input-tokens 4000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-graph-v1
```
