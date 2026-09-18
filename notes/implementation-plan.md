# Implementation sequence and acceptance checks

Status: proposed work order, recorded 2026-09-18. Notes come first; implementation
and live benchmark collection have not started in these new repositories.

## 1. Public benchmark foundation

- Create the `jevhammer_benchmark` package with explicit compatible Mathlib and
  JevHammer pins, a public README, installation instructions, license decision,
  contribution guidance, and CI.
- Implement named methods using the existing selector, tactic-set, and search
  configuration interfaces. Keep optional selector/services as integrations.
- Define versioned dataset/run/trial/artifact metadata and a portable output
  layout. Keep credentials, local caches, and large results out of Git.
- Provide small offline fixtures and mock Jev responses for ordinary tests.

Acceptance: a clean consumer can install and run a synthetic comparison without
private worktrees, credentials, or machine-specific paths. Two custom selectors
and two tactic sets can be compared without editing the runner.

## 2. Source-location harness and proof replay

- Extract reusable source discovery, exact-location matching, state restoration,
  and certificate verification from the research harness where appropriate.
- Separate project/module discovery, partitioning, collection, replay, and report
  generation; each should have documented inputs and outputs.
- Test multiple goals, shared metavariables, current-file premises, unavailable
  later declarations, stale locations, timeouts, fallback, and partial runs.
- Enforce the shared local memory limit and retain errors/resource events.

Acceptance: every reported success replays offline; every arm starts from the
same allowed state; no later declaration or held-out target can be retrieved.
Reports can be regenerated from retained records without API calls.

## 3. Reproduce the reference configuration

- Package the historical neural selector adapter and its documented deployment,
  including the same exclusions, fallback, and pinned model/corpus.
- Supply the matching Aesop/Mathlib tactic environment, Jev premise reranking,
  Jev state guidance, and practical/extended settings.
- Start with a small fixed smoke cohort, then a paired regression comparison
  with the preserved implementation. Diagnose generic migration differences.
- Record a new baseline under the public harness before claiming that a new
  selector matches or beats it. Do not inherit historical scores merely because
  the configuration has the same name.

Acceptance: baseline configuration, resource/timing policies, raw records, and
replay results are reproducible. Differences from historical runs remain visible.

## 4. Generic `jevselector` preparation foundation

- Create the separate public library and standard-selector adapter.
- Implement corpus extraction for arbitrary Lean projects/modules, artifact
  schemas, optional exclusions, and provenance verification.
- Begin with an inspectable deterministic artifact/index baseline before
  introducing more complicated fitted models or Jev-assisted preparation.
- Test full-library, empty-holdout, declaration-holdout, module-holdout, and
  generated-helper cases using an independent small Lean fixture library.
- Connect artifact/split validation to the benchmark as an adapter, without
  making `jevselector` depend on Mathlib or on benchmark code.

Acceptance: the same preparation pipeline works on Mathlib and a different Lean
library; excluded proof information cannot reach prepared aggregates; the
benchmark detects incompatible or overlapping preparation manifests. Production
preparation with no exclusions is supported and explicitly labeled.

## 5. Improve selection using controlled experiments

- Establish preparation-time, CPU-latency, memory, and artifact-size baselines.
- Explore the general candidate families in [the selector design](https://github.com/adamtopaz/jevselector/blob/main/notes/design.md).
- Use small fixed development cohorts first. Vary one component at a time when
  attributing an improvement, and report full-pipeline changes separately.
- Keep Jev state guidance in all JevHammer arms. Account for premise reranking
  and selector-owned Jev calls separately and in total.
- Freeze candidates before confirmation; reserve an untouched final partition.
  Expand evaluation after promising implementations, not after inspecting
  individual proof failures for ad hoc fixes.

Acceptance target: deadline-verified JevHammer coverage at least as high as the
matched reference configuration, with fast CPU retrieval and practical full-
library preparation under the memory ceiling. Report paired gains/losses,
uncertainty, repeated-run variation, and preparation/query costs. A tie on a
small pilot is insufficient evidence for the final target. Do not weaken the
comparison by changing cohorts, budgets, imports, or warmup accounting.

## 6. Public release workflows

- Document ordinary installation, preparing any supported Lean library,
  optional holdouts, loading artifacts, using the selector, and reproducing a
  benchmark. Provide actionable errors for incompatible artifacts.
- Publish small examples and metadata/checksums for any distributed artifacts.
  Keep heavyweight optional service setup out of the minimal path.
- Support both benchmark-safe prepared artifacts and full-library production
  artifacts through the same API, with their provenance clearly distinguished.
- Record the tested toolchain/dependency matrix and actual achieved results.

## Working rules

- Maximum local RAM: 32 GB; operational heavy-work limit: one 24 GB zero-swap
  scope encompassing the complete process tree.
- No new live model calls or large training runs until their run configuration,
  artifact/split inputs, resource limits, and usage budget are explicit.
- Preserve prior commits, manifests, certificates, caches, and failed-run
  evidence; start a new run directory for a new configuration.
- Public source and reusable tooling belong in the repositories. Machine-local
  paths, secrets, transient setup, and bulk experiment outputs do not.
