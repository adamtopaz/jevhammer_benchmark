# Sine Qua Non baseline pilot

Protocol frozen before live collection, 2026-09-18. This is a small development
comparison, not a final held-out confirmation or full LeanHammer comparison.

## Arms and settings

- `JevHammerBenchmark.Methods.expanded`: JevSelector's wrapper of Lean's Sine
  Qua Non, depth factor 1.5, at most 1,024 raw imported candidates, current-file
  supplementation enabled.
- `JevHammerBenchmark.Prepared.sparse`: statement-symbol IDF retrieval using
  the existing held-out Mathlib artifact.

Both arms use `Methods.mathlibTactics`, Jev proof-state guidance, and the default
6,000 ms / 12-node / depth-3 / 3-request / 100-premise / 8-injected-premise
configuration. Jev premise reranking is **disabled** in both. All other defaults
are identical, including the 200,000 outer heartbeat limit and two Lean threads.
Warmup is outside the goal clock and measured separately. Rotate arm order by
site using the existing driver; do not tune individual goals.

## Cohort and artifacts

Rediscover seed-0, 32 locations from Mathlib.Topology.Basic,
Mathlib.LinearAlgebra.Basis.Basic, and Mathlib.RingTheory.Ideal.Basic, importing
both the prepared and neural adapters as in the original smoke cohort. Check
that the selected sites, goals and owning declarations remain identical before
running. The neural adapter is imported but no neural service is used.

The sparse artifact SHA-256 is
`bdef7b455146f3ae87ebc7600bd6c445010405a6e00214f61b41aed33bbb2aec`.
Its excluded owners are the same cohort's 25 declarations; the runtime adapter
must admit all owners and check available statement fingerprints. This cohort
has already been used for infrastructure testing, so it is a development pilot.

## Bounds and reporting

Use one 24,000,000,000-byte, zero-swap process tree, below the user's 32 GB ceiling.
Allow at most 192 Jev requests and 2,000,000 reported input tokens for the run;
retries are disabled. The input-token budget stops subsequent requests once
reached; a final request may cross it. No service process runs alongside Lean.

Preserve failures and budget exhaustion. Independently replay every successful
certificate. Report on-time and raw verified counts, paired gains/losses and
declaration-bootstrap intervals, time, warmup, requests/tokens, ranking errors,
and late successes. Runtime panics or incomplete collection invalidate a clean
comparison. Keep the original records if a generic implementation issue needs
fixing; any rerun must have a new directory and be identified explicitly.
