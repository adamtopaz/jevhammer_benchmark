# jevhammer_benchmark

Public benchmarking infrastructure for [JevHammer](https://github.com/adamtopaz/jevhammer),
with Mathlib as the initial benchmark library.

**Status: design stage.** This repository currently contains planning notes.
The runner, package configuration, and installation workflow are not implemented.

The intended library will compare custom premise selectors, tactic collections,
and JevHammer configurations at reproducible source locations. It will record
proof coverage, timing, resource use, and Jev usage, with independent offline
verification of successful proofs.

Start with the [design notes](notes/README.md), including the
[benchmark contract](notes/benchmark-design.md) and
[implementation sequence](notes/implementation-plan.md).

Public reuse is a requirement: installation and reproduction must not depend on
private research checkouts, undocumented local setup, or machine-specific paths.
Large datasets, artifacts, caches, and results will be separate from the source
repository. Local development retains a 32 GB RAM ceiling, using a shared 24 GB
zero-swap scope for heavy work.

Related repositories:

- [JevPilot](https://github.com/adamtopaz/jevpilot): the Jev client.
- [JevHammer](https://github.com/adamtopaz/jevhammer): the configurable proof engine.
- [jevselector](https://github.com/adamtopaz/jevselector): planned generic selector
  preparation and CPU premise selection, with optional holdouts.
