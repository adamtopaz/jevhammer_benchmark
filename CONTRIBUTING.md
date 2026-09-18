# Contributing

Use the pinned Lean 4.33.0/Mathlib snapshot and Python 3.10+. After installing
Lake dependencies and Mathlib's cache, run `bash tests/run.sh` inside a bounded
job (or `--external-memory-limit` with an actual externally enforced limit).
The suite includes an intentionally corrupted certificate that must fail replay.

Use named `Method` values for experimental arms; keep the runner generic. Add
provenance/admission checks for prepared selectors. Never commit credentials,
large artifacts/results, or private-worktree paths. Keep shared heavy process
trees under 32 GB (24 GB, zero swap by default), including selector services.

Quality claims need matched source cohorts, imports, search/tactic settings,
Jev budgets, independent replay, and declared training overlap. Develop on a
separate partition, freeze candidates, and only then inspect final held-out data.
The historical research scores are not measurements of this public harness.

Contributions use Apache-2.0, like the repository.
