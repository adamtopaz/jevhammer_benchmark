# Frozen current-system guidance ablation

256 previously exposed intermediate goals, one per declaration, from 33 modules
and all 17 areas of the original 1,024-goal cohort. Every selected goal was
re-admitted unchanged under the updated harness before proof trials. The exact
dataset, ten counterbalanced batches, full 1,212-owner holdout, and admission
record are preserved here.

The run was frozen at `fee6c9bbdfc718e08586f66c44be519502077548`, using benchmark
dependency `fc5f5ea5aed665918f7cc4d84fd64408f8d0c2e2`. See the
[protocol](../../docs/guidance-ablation-protocol.md),
[results](../../docs/guidance-ablation-v1.md), and
[reproduction guide](../../docs/reproducing-guidance-ablation.md).

Fields such as `sampling` and `confirmation` inherited from the parent dataset
describe that original cohort. The `followup` field identifies this subset and
its outcome-free selection rule; the `sites` and `sources` fields contain only
the selected 256 locations and 33 modules. No trials or result files were read
by the selection function.

Editorial correction to the frozen protocol: its analysis paragraph says
"two single-module strata". There is **one**, Topology; each other area has two
modules. The dataset and bootstrap implementation always used the actual
grouping, so no selection, analysis, or result changed. The protocol file is
retained byte-for-byte to preserve its pre-trial checksum. Publication corrects
the same wording in the report's limitations and adds an analysis-source hash
and request-ledger reconciliation. Identical preparation provenance is stored
once per module in a companion file. The numerical analysis is unchanged from
the frozen version.
