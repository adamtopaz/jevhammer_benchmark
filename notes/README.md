# Benchmark and selector planning notes

Recorded 2026-09-18. These documents capture the agreed requirements before
implementation. Proposed interfaces and workflows are designs, not existing APIs.
The benchmark and initial sparse selector are now implemented. These notes
retain the broader research requirements; consult the root README for shipped APIs.

- [Benchmark design](benchmark-design.md): public repository boundaries,
  configurable methods, source-location evaluation, metrics, and reproducibility.
- [Selector design](https://github.com/adamtopaz/jevselector/blob/main/notes/design.md): generic offline preparation, optional
  holdouts, artifact provenance, CPU inference, and candidate approaches.
- [Implementation sequence](implementation-plan.md): milestones, validation,
  migration of the historical baseline, and acceptance criteria.

## Agreed direction

1. Develop `jevhammer_benchmark` first. It depends on Mathlib and JevHammer and
   provides reusable infrastructure for comparing selectors, tactic collections,
   and search configurations.
2. Develop `jevselector` afterward. It provides premise selectors through Lean's
   standard `Lean.LibrarySuggestions.Selector` interface and may use JevPilot.
   Its preparation pipeline must work on arbitrary Lean libraries, with or
   without an explicit holdout set.
3. "Training" means any offline computation of artifacts used in selection. It
   does not require a neural network. Indexes, dependency statistics, weights,
   graph structures, and embeddings are all possible artifacts.
4. Aim for fast full-library preparation, fast CPU selection, and end-to-end
   JevHammer performance at least as good as the strongest previously measured
   configuration under matched budgets. This is an objective to demonstrate,
   not a result established by choosing an architecture.
5. Keep Jev proof-state guidance enabled in all new JevHammer comparison arms.
   Premise reranking and premise-selector implementations are configurable.
6. Design both repositories for public reuse: portable installation, documented
   APIs, reproducible artifacts, tests, and separation of library code from local
   datasets, caches, credentials, and run outputs.
7. Never exceed the user's **32 GB RAM ceiling**. Heavy local work should use one
   shared **24,000,000,000-byte, zero-swap process scope** at a time, including
   selector services, subprocesses, training, and replay.

The public repositories are [jevhammer_benchmark](https://github.com/adamtopaz/jevhammer_benchmark)
and [jevselector](https://github.com/adamtopaz/jevselector). Numerical
preparation/latency targets remain to be established from baseline measurements.
All four libraries use Apache-2.0, as requested.
