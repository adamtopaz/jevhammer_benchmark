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

## Initial outcome

The first run under `2ddc190` reached the 600-second process timeout without
recording a query. Its peak cgroup memory was 4,490,452,992 bytes with no memory
events under the 16 GB zero-swap bound. No model calls or proof trials occurred.
See the [preserved failure report](cpu-selector-profile-graph-v1.json).

The original progress message appeared only after loading, validation and graph
construction; the failure does not identify which phase dominated. Subsequent
cost attempts must print separate phase markers. A reverse-edge map ownership
optimization is being checked against canonical old/new graph snapshots before
timing it. Preserve the original run and use a new output directory; do not
replace its timeout with a successful retry in the published evidence.

The follow-up pins selector `0ce4ccd`, whose reverse-edge update produced a
byte-identical 54,484-entry graph against `66197c1` on the Lean import set.
The constructor timings there were 7,410/3,778 ms (one run each), with graph
and unresolved-proof regression checks passing. This does not yet establish a
Mathlib speedup. The profiling source now flushes phase records to
`queries.json.phases.jsonl` and measures environment validation separately.
A no-output-path preflight reached its intentional error in 2.72 seconds under
a 200,000-heartbeat elaboration limit, establishing that the updated profiling
program reaches execution promptly. These checks used zero model calls.

Keep the same 384-query recipe and all production graph bounds for the
separate `cpu-selector-profile-graph-v2` run. Its initialization and query costs
are the next evidence needed before a proof screen.
