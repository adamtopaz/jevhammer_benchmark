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
  python - <<'PY'
import os
from pathlib import Path
from jevhammer_benchmark.cli import lean_file
lean_file(Path.cwd(), Path("GraphCostProfile.lean").resolve(),
          Path("/tmp/graph-profile.log"), dict(os.environ), 600,
          ["-j2", "-M0", "-DmaxHeartbeats=0"], "GraphCostProfile")
PY
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

## Launcher correction before interpreting costs

The v2 diagnostic completed graph construction and began queries, but its
unchanged CPU base ran much slower than established profiles. Inspection found
that the new launcher used `lake env lean` directly, omitting Lake's compiled
dependency plugin setup. Both v1 and v2 therefore measured interpreted execution
and are unsuitable for comparisons with the production harness. V2 was explicitly
stopped; its [partial diagnostic report](cpu-selector-profile-graph-v2.json) is
retained. No proof trials or model calls occurred.

Use the existing `lean_file` helper, as in the corrected reproduction command
above. It obtains Lake's setup file and passes the plugin configuration to Lean.
The distinct v3 run keeps selector `0ce4ccd`, the same 384 queries and bounds,
and records the setup/plugin evidence. Do not report either discarded launcher's
timings as production latency. The canonical old/new graph equality and
functional regressions remain valid; their small-environment timings were also
from direct interpreted launches.

## First complete native result

The corrected v3 run completed all 384 queries with zero failures and no model
or proof calls. It indexed 376,987 signatures in 67.840 seconds; statement
loading, validation and structural initialization took 2.839, 0.244 and 30.687
seconds. Peak memory was 4,636,672,000 bytes, with no memory events.

| Mode | Median ms | p95 ms |
|---|---:|---:|
| CPU base | 175.64 | 304.21 |
| No expansion | 676.66 | 2,153.99 |
| Forward | 782.54 | 2,382.00 |
| Backward | 684.82 | 2,228.31 |

No expansion preserved the complete base order on all 96 queries. Forward and
backward traversal changed the top-eight ranking substantially (mean overlap
55.47% and 57.42%); these are not quality gains. Each traversal made one mock
callback per query, with at most 24 choices and a median 5,958.5 bytes of choice
and question text, excluding the goal/context payload. See the
[full native report](cpu-selector-profile-graph-v3.json) and per-query digests.

These costs are too high to interpret as a fast extension to the CPU selector.
Code review identified repeated construction of the import-name array inside
the signature deny predicate. Check a direct module lookup against exact graphs
and all selector regressions before timing that isolated change. Keep the
scoring recipe and query cases fixed; proof comparisons remain pending.

The isolated v4 follow-up pins selector `d6f4e25`. Native canonical snapshots
remained byte identical and the complete selector offline suite passed. Keep
all v3 cases, graph limits, modes and native setup unchanged. Require every
ordered suggestion array and callback/choice count to match v3 before treating
v4 as a performance-only comparison. Report failures rather than selectively
retrying queries. The run remains CPU-only, with zero proof/model calls.

## Completed isolated optimization

V4 completed all 384 queries with **exactly the same ordered suggestions,
callback/choice counts, and payload sizes** as v3, with zero failures. All 32
statement groups were stable across their three repetitions in every mode.
Graph initialization fell from 67.840 to **14.719 seconds**, and structural
initialization from 30.687 to **6.713 seconds**. The indexed set remains 376,987
signatures. Loading and validation took 2.956 and 0.247 seconds.

| Mode | Median ms | p95 ms |
|---|---:|---:|
| CPU base | 112.41 | 233.24 |
| No expansion | 122.86 | 221.70 |
| Forward | 201.81 | 349.83 |
| Backward | 123.16 | 220.73 |

This is a substantial implementation speedup with unchanged rankings. Do not
infer that no expansion improves tail latency over the base from a single run:
their ordered outputs are identical and timings vary. Forward expansion still
exceeds the provisional 200 ms p95 target; any useful coverage gain must justify
that cost plus actual Jev latency. The bounded overhead now warrants a small
proof screen, not a claim that the research goal has been achieved. Peak memory
was 4,553,039,872 bytes with no memory events. See the
[full matched report](cpu-selector-profile-graph-v4.json).


## Destination-preview cost gate

After the original graph proof screen completed (14/34 versus CPU 16/34),
selector `397bef6` adds an opt-in preview of destination statements to each
model choice. It passes the full offline suite. No preview proof result exists.
Freeze two serial native profiles using this revision and the same 32 statement
types, three repeats and four direction modes as v4:

1. v5: `JEVSELECTOR_GRAPH_PROFILE_PREVIEW_CANDIDATES=0`. Require every ordered
   suggestion list, callback/choice count, payload size and error to match v4.
2. v6: `JEVSELECTOR_GRAPH_PROFILE_PREVIEW_CANDIDATES=3`, with 480 type characters
   per preview. Require the same fixed-direction suggestions and call/choice
   counts as v5; measure the intentionally increased payload size separately.

The profiler defaults to zero previews and records the configured preview count.
Use the existing native Lake setup helper, independent per-mode structural caches
from the same fixed `True` warmup, and the unchanged CPU index. Report loading,
graph and structural initialization, query median/p95, errors, payload bytes,
ranking identity, and peak memory. Both runs make zero model calls and zero
proof trials. Keep one 16 GB zero-swap scope active at a time, with two threads.
Do not infer proof quality from deterministic output preservation. A subsequent
matched proof comparison must freeze its own adapters, admission and protocol.
