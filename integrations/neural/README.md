# Optional neural premise-selector arm

For the completed three-method confirmation, use the
[reproduction guide](../../docs/reproducing-confirmation.md). This directory
contains its pinned CPU package lock, embedding endpoint and validation script.
The confirmation's neural/conclusion method disables premise reranking; Jev
guides proof-state selection. The standalone adapter below is a different
configuration.

`JevHammerBenchmark.Neural.neural` uses the pinned upstream
[premise-selection client](https://github.com/hanwenzhu/premise-selection)
with an explicitly chosen compatible
[LeanPremise server](https://github.com/hanwenzhu/lean-premise-server).
Only premise selection uses that neural model; Jev still reranks premises and
guides proof-state selection. It uses the same expanded tactic set as
`Prepared.sparseReranked` and `Methods.expandedReranked`.

The adapter compiles in ordinary CI without contacting a service. Deploy the
server according to its upstream documentation, with the exact model/corpus
revisions in your provenance JSON. The example metadata records the historical
CPU reference artifacts; it does not attest that your endpoint serves them.
Retain deployment logs/checksums and validate inference against the matching
precomputed vectors before drawing comparisons. Services and the driver must
share ONE aggregate memory-limited process tree when hosted locally.

```sh
export JEVBENCH_NEURAL_URL=http://127.0.0.1:18080
export JEVBENCH_NEURAL_PROVENANCE="$PWD/integrations/neural/provenance.example.json"
jevbench discover --modules Mathlib.Topology.Basic Mathlib.LinearAlgebra.Basis.Basic \
  --import JevHammerBenchmark.Neural --import JevHammerBenchmark.Selector \
  --count 32 --output runs/neural-dataset
# Prepare an excluded selector for this dataset as in ../selector/README.md.
jevbench run --dataset runs/neural-dataset/dataset.json \
  --methods JevHammerBenchmark.Prepared.sparseReranked JevHammerBenchmark.Neural.neural \
  --max-requests 192 --max-input-tokens 2000000 --output runs/neural-paired
```

Imported-catalog warmup is measured outside the per-goal clock and fails clearly
if the service is unavailable. This initial adapter deliberately supplies no
Sine fallback; service failures must be diagnosed, not interpreted as neural
quality. Upstream HTTP requests do not have their own hard timeout: the driver's
module process timeout kills the entire subprocess group and marks the run
incomplete. Choose `--timeout` to bound this operational risk.

This is a neural-premise-selection comparison, **not full LeanHammer** (which
has additional proof engines). It is also not yet a reproduction of historical
coverage: imports, tactic configuration, fallbacks, and service deployment must
be matched and newly measured. The current full-tactic comparison is in the
[confirmation report](../../docs/full-leanhammer-confirmation-v1.md); historical
monolithic scores are not attributed to these packages. Third-party training overlap is recorded as unknown,
separately from JevSelector's explicit fitted-row holdouts.
