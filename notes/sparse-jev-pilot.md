# Sparse retrieval followed by Jev premise ranking

Protocol frozen before live collection, 2026-09-19. This is an exploratory
development comparison. The 122-location reserved evaluation split stays unused.

## Question and arms

Does Jev improve a prepared sparse selector's premise order enough to offset
the extra request latency and shared call-budget cost in a six-second finisher?

Use the existing, unmodified public adapters:

- `JevHammerBenchmark.Prepared.sparse`: CPU statement-symbol IDF retrieval;
  Jev ranks proof states only.
- `JevHammerBenchmark.Prepared.sparseReranked`: the same retrieval followed by
  Jev premise ranking, with Jev proof-state ranking still enabled.

Run two matched comparisons, fixed before inspecting outcomes:

1. `maxPremises = 100` in both arms: the existing default pool.
2. `maxPremises = 32` in both arms: a smaller pool to reduce model input and
   question count. This also measures any candidate-cap effect on the control.

Each run reruns its own control; do not compare against the old broad aggregate
or splice the best result at each goal. Keep the runs separate when reporting.
Run the 100-candidate comparison first, then the 32-candidate comparison.

## Fixed configuration

Both arms retain `Methods.mathlibTactics`, `jev-1.13.0`, 6,000 ms per location,
12 nodes, depth 3, beam width 4, 24 successor candidates, three total Jev calls,
eight injected premises (the finisher also tries sixteen), 15,000 tactic
heartbeats, a 5-second request timeout, and premise refresh enabled. The outer
heartbeat budget is 200,000. Only `guidePremises` differs within a pair.

Premise ranking sends the goal/local context and each candidate's pretty-printed
statement. Independent usefulness questions allow multiple complementary lemmas
to receive high scores, using the documented [TypeSafe Noul API](https://docs.typesafe.ai/api#noul).
Jev reorders candidates; it cannot invent declarations
or proof steps. Proof-state ranking remains enabled in every arm.

Premise and state decisions share the three-call budget. The hybrid may therefore
make fewer state-ranking calls, especially after its one permitted premise
refresh. This pilot measures that existing policy, not an isolated premise
quality intervention. Report premise and state requests and their separate
latency/usage; a promising follow-up could reserve separate call budgets.

## Cohort and preparation

Use [the frozen pilot](../datasets/sparse-jev-v1/dataset.json): 34 locations, one
from each of the broad cohort's 34 source modules and 17 areas. Starting only
from its development partition, use `select_sites` with count 34, seed 19 and
maximum one location per declaration. This yields 34 distinct owners. Selection
does not use earlier tactic outcomes; the development partition already has
benchmark exposure. Preserve all selected locations, including easy ones.

Reuse the existing sparse artifact with SHA-256
`39b500a9776a562f3982897acf5790c4ecbb87f716a5728203cfff1b3360e1ed`.
It excludes all 188 owners of the full broad cohort from fitted statistics.
The selector's current-file compatibility fix is pinned at JevSelector
`41e1afac56702e2294bb036f6572f57348db15cf`. No preparation or tactic changes are
needed for these comparisons.

## Bounds and acceptance

Run modules serially with two Lean threads in a 24,000,000,000-byte zero-swap
cgroup. Do not run another heavy local job alongside collection or replay.
Allow at most 204 requests and 4,000,000 reported input tokens per paired run;
the two-run ceiling is 408 requests and 8,000,000 reported input tokens.
Retries are disabled. Missing usage stays visible; the token cap gates subsequent
calls and one response may cross it. A failed ranking retains original order.

Every success must independently replay against its source goal. Report fixed
denominators, on-time and raw verified coverage, paired gains/losses and
declaration-bootstrap intervals, goal/retrieval times, startup, premise/state
request counts, request latency, reported tokens, unknown usage, model failures,
late successes and budget blocking. The shared index is loaded once per source
process, so whichever arm runs first pays its initialization cost outside the
goal clock. Do not interpret per-arm warmup differences as selector speed.

Incomplete collection or replay is not an accepted comparison. Preserve it and
document any generic correction before restarting. Do not tune individual goals
or run a winner on the reserved partition during this pilot.
