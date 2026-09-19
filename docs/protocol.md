# Benchmark protocol, schema 1

## Source locations and isolation

The discovery preflight rejects target modules already imported by the harness
or selected tactic imports: re-elaborating them would expose their completed
declarations. Choose source modules outside that closure, or reduce the tactic
imports. `--modules-file` accepts a JSON module list for larger cohorts.

Discovery imports the harness into copies of requested sources and uses Mathlib's
TacticAnalysis nodes. Identifiers combine module, original UTF-8 byte span, and
pretty-printed before-goal hash. The dataset additionally stores the full goal,
owning declaration, goal count, source SHA-256, imports, Lean options, project
source/dependency fingerprints, and runner hashes. Collection and replay require
exact location/context matches and the same project snapshot. Generated files
use Lake module setup (including native plugins) with the original module name
restored, so private declarations retain their source identities.

Each arm receives a fresh `ContextInfo.runMetaM` context with `mctxBefore` and the
preceding source command's environment. The completed owning declaration and
its generated auxiliaries are unavailable. All goals and local expression
constants must be present in that environment. Nodes inside speculative/failing
branches, empty goals, anonymous owners, and contexts that cannot be certified
this way are excluded; both discovered and eligible counts are retained. A first
command without a prior environment snapshot may be excluded conservatively.
This is coverage over the sampled eligible tactic locations, not all theorems.
Additional tactic imports can also violate a file's `assert_not_exists` import
invariants or meta-import restrictions; those are recorded as module failures,
never silently removed from a successful discovery.
Runtime panic diagnostics also fail the module, even if Lean exits with status
zero after recovering a default value. Logs remain available for diagnosis.

Selection is deterministic, round-robin by module after seeded hash ordering.
`discover --exclude FILE` accepts repeatable schema-1 declaration/module
exclusion manifests (the same name lists as `holdouts`). Declaration exclusions
also remove named children; module exclusions are exact names. Input manifests
and their checksums are retained with the dataset. Unknown exclusions are allowed
here because earlier evaluation can cover modules outside the current discovery.
`--max-per-declaration N` limits sampled locations per owner; zero is unlimited.
Eligibility counts before and after exclusions are recorded separately. The
requested count is an upper bound if the remaining pool is too small.
Declaration-grouped development/test splitting prevents the same owner from
appearing in both partitions. Method order is deterministically rotated by site.
`split --stratify-by-module` assigns declarations within each module instead of
globally. Each module with at least two owners appears in both partitions;
single-owner strata remain in development and are listed in partition metadata.
Shared runtime caches can still affect timings; repeat runs before making strong
latency claims. Source modules run serially in separate processes.

## Trial clock and proof certificates

Goal-independent admission and warmup are separately timed once per method per
module. The trial clock covers search, goal-specific selection, Jev calls, proof
closure, kernel checks, and certificate construction. `onTime` requires all
before-goals solved and elapsed time no greater than `maxMillis`. Late successes
are retained separately. JevHammer's deadline is cooperative between steps;
heartbeats bound Lean work, and the driver has a hard per-module process timeout.
A hung external call can reach that process timeout; collection is then incomplete.

Certificates encode exact logical expression DAGs, names, universe levels, and
binders. All local variables/lets are abstracted, metavariables resolved, and
new auxiliary definitions inlined. Independent replay reloads the source state
without API credentials, rejects admissions/open proofs/self references, checks
proof and type in Lean's kernel, and unifies the certificate target with the
closed original goal type. Shared source metavariables persist across all goals
of a location during this check. Replay is not an elaboration of pretty-printed
proof text and does not repeat search.

## Retained output and reports

- `dataset.json`: frozen selected locations, source and project identity.
- `run.json`: arms, overrides, status, budgets, timestamps, resource observations.
- `trials.jsonl`: outcomes, elapsed time, search/retrieval counters, certificates.
- `warmup.jsonl`: method identities, admission provenance, initialization cost.
- `decisions.jsonl`, `usage.json`: Jev requests/responses and reserved usage.
- `sources/`, `work/`, `settings/`, `logs/`: original sources, instrumented copies,
  per-process configuration, and complete diagnostics.
- `replay-N/`, `verification.json`: immutable replay attempts and latest status.
- `summary.json`, `REPORT.md`: offline-regenerable summaries.

Fresh output directories are required. Module errors, missing/duplicate trials,
stale locations, replay failures, and interrupted runs cannot become complete
runs. Denominators remain the full selected cohort. Reports distinguish raw
verified, deadline-verified, and late proofs, rank failures, and usage-budget
blocking. Paired gains/losses and seeded declaration-cluster bootstrap intervals
(1,000 samples) are emitted only for complete runs. Intervals are exploratory:
locations are correlated, and they do not address development-set overfitting,
unknown third-party training overlap, or repeated-run variability.

The driver records source and dependency source hashes, not just Git revisions.
It deliberately refuses collection after method/runner source changes; rediscover
the frozen cohort for a new configuration. Artifact identity belongs in a
method's admission metadata. The driver does not own third-party model deployment
or validate its claimed training corpus.

## Budgets and portability

One process tree defaults to a 24,000,000,000-byte cgroup with swap disabled.
Maximum accepted limit is 32,000,000,000 bytes. Memory peaks/events are recorded
when cgroup files are available. Outside Linux/systemd, explicit externally
managed mode records a declaration and observed limits; it does not pretend to
measure unavailable data. A shared existing cgroup's peak can include earlier
commands in that same job. Per-module Lean uses two worker threads. The aggregate cgroup/job limit is
authoritative; a separate Lean allocator limit is disabled because large
memory-mapped import sets can reach it with much smaller resident memory.

Every live call consumes a reserved attempt before IO. Unknown token usage is
retained after transport errors or interruption. Token counts are provider-reported;
no exact preflight token count exists, so a last response may exceed the token
threshold. JevHammer can continue with deterministic fallback after a failed or
budget-blocked ranking; those trials remain flagged. Selector-owned external
calls are not automatically charged to this ranker: custom methods must account
for their own service usage/provenance and use the same process/resource budget.

Mock mode applies identity rankings, never claims Jev quality, and does not use
Jev credentials. It does not sandbox arbitrary custom selector IO. No decision
cache or distributed/parallel collection is implemented in schema 1. Exact
certificate replay is fully offline. Keep mutable services and artifacts fixed
for the duration of a run.
