# Full LeanHammer comparison

This optional Lake project adds full LeanHammer to the public benchmark runner.
The main benchmark library does not acquire a LeanHammer dependency. All three
methods use the same Lean 4.33.0 / Mathlib snapshot and source-bound certificate
replay. The base runner revision and all dependencies are pinned in the manifest.

| Method | Engine and premises |
|---|---|
| `LeanHammerComparison.cpu` | JevHammer, target-weighted sparse + conclusion matching |
| `LeanHammerComparison.neural` | JevHammer, neural + conclusion matching |
| `LeanHammerComparison.full` | Full LeanHammer with upstream neural selection and normal Sine fallback |

Full LeanHammer retains Aesop, grind, Lean-auto/Zipperposition/Duper, Lean-SMT/cvc5
and default parallelism. Its wrapper dispatches one complete `hammer` invocation
through the existing proof and certificate gates. No Jev search is added. The
whole invocation receives the common 200,000-heartbeat allowance, instead of
JevHammer's 15,000-heartbeat allowance for each small tactic step.

Use eight Lean workers and synchronous elaboration for every arm, so LeanHammer's
parallel solvers are not starved by command elaboration. Run methods in separate
Lean processes, using one runner invocation per method. This avoids copying our
prepared selector's caches into LeanHammer's solver processes. Keep all services
and workers within one aggregate memory scope, capped at 16 GB with zero swap.

The primary deadline is six seconds end to end, including selection, search,
reconstruction and certificate construction. JevHammer uses its six-second soft
budget; LeanHammer retains its default five-second internal solver timeout,
which excludes retrieval. Retain and replay overruns but exclude them from
on-time coverage. Do not treat the numeric internal timeouts as equal budgets.

Configure `JEVBENCH_NEURAL_URL` and `JEVBENCH_NEURAL_PROVENANCE` as described in
the sibling neural integration. Configure `JEVSELECTOR_PUBLIC_INDEX` for the
CPU artifact, prepared with the evaluation owners excluded. Both neural arms
warm the imported and earlier current-file statement catalog outside goal
timing; actual goal queries remain timed. Report warmup costs and service order.
The comparator records neural fallbacks, rejected unavailable suggestions and
retrieval time in `leanhammer-selector.jsonl` beside the ordinary trial records.
Third-party neural training overlap remains unknown.

From this directory, run `lake update` and `lake build`. Execute `Smoke.lean`
using Lake's module setup, including native plugins; the runner's `lean_file`
helper provides this. Each external proof engine must pass its offline smoke
test before a comparison. Then use the standard Python benchmark CLI with
`--project integrations/leanhammer` from the repository root, admitting sources
with `--import LeanHammerComparison`. The runner is installed from the pinned
base benchmark revision, or run with an identical Python source snapshot.

The completed [1,024-goal confirmation](../../docs/full-leanhammer-confirmation-v1.md)
uses 131 modules, six counterbalanced batches and all 3,072 trials, separately
from the earlier 34-location pilot. See the
[reproduction guide](../../docs/reproducing-confirmation.md) for pinned CPU
services, inference validation, preparation, source admission, native-engine
preflight and full run/export commands. The [selection guide](../../docs/benchmark-selection.md)
explains intermediate goals, exclusions, holdouts and sampling.

On this Nix host, the pre-existing cvc5 build uses Lean's own GMP library instead
of linking a duplicate static GMP; Zipperposition's loader was adapted to the
host. These deployment adjustments are recorded with source/binary hashes.
They do not disable or change any proof-search engine. Other platforms should
use the upstream installation instructions and need not apply these changes.
