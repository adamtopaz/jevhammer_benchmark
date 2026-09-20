# Signature graph CPU cost screen

Before live proof trials, measure graph initialization and extra query work on
the same 32 fixed public Mathlib statement types used by the previous CPU
profiles, with three repetitions. These are cost diagnostics, not proof goals
from the reserved evaluation split. No mathematical proof is attempted and no
model service is called.

`GraphCostProfile.lean` uses the production graph selector with deterministic
rankings selecting no expansion, forward, or backward at every frontier node.
A fourth arm is the unchanged sparse/conclusion CPU base. All arms retrieve
100 suggestions and exclude the query declaration itself. Each arm gets an
independent conclusion-matching cache from the same fixed warmup. Graph data
are immutable and shared. Report loading, graph initialization, and structural
initialization separately from queries; no warmup cost is claimed to disappear.

Keep the default graph bounds: one round, eight frontier nodes, 128 visited or
reached names, 256 available forward candidates per node, 32 expansion edges,
1,200 type characters, and 10,000 additional query heartbeats. There are 384
queries in total. Record every failure, callback count, choice count, choice
payload bytes, ordered suggestions, and query duration. Independently compare
no-expansion ordering with the base, and describe ranking changes for the two
expansion modes. Ranking changes alone are not proof-quality evidence.

Use the unchanged public statement index SHA-256
`e388078b747f85320c672a78570d3831bb4ce6b754d3df493ed7095afe4cd7f5`.
Selector `66197c1` and JevHammer `2e3df66` supply the validated graph and shared
budget API. Mathlib and the Lean 4.33 toolchain remain pinned in this repository.
Run one serial job with two Lean threads, a 16,000,000,000-byte memory limit,
and no swap. The process has a ten-minute timeout. Initialization/query failures
must be resolved before freezing any graph proof screen; use aggregate
diagnostics and synthetic tests, not individual failed evaluation goals.

To reproduce after building `JevHammerBenchmark.GraphStudy` and Mathlib:

```sh
JEVSELECTOR_PUBLIC_INDEX=/path/to/index.json \
JEVSELECTOR_GRAPH_PROFILE_OUTPUT=/path/to/queries.json \
  lake env lean -j2 -M0 -DmaxHeartbeats=0 GraphCostProfile.lean
```

Place this command in an externally bounded job as above. Disabling the outer
heartbeat limit permits full-library initialization; production per-query
graph/structural limits remain enforced. The checked-in source records partial
diagnostics if a later query fails. Actual Jev latency and its opportunity cost
within the shared three-call search budget require a separate proof experiment.
