# Available-premise sensitivity cohort

The study completed on 2026-09-22 (Edmonton): all 4,096 trials were retained and
all successful proofs replayed. On-time counts are strict CPU 438, original CPU
448, neural JevHammer 466 and full LeanHammer 371. See the
[results and limitations](../../docs/available-premises-v1.md).

Exactly the same 1,024 sites, owners and goal texts as
[`full-leanhammer-confirmation-v1`](../full-leanhammer-confirmation-v1/README.md),
re-admitted under the strict method's imports with no proof trials or model calls.
All 131 original source modules elaborated successfully. This is an exposed
follow-up cohort, not fresh unseen evaluation. The `confirmation` metadata in
the copied dataset describes its original study; `followup` describes this run.

The four batches contain whole modules assigned by the protocol's fixed hash
order. All four configurations attempt all sites. The schedule counterbalances
each method's position and preceding method, with fresh local services per arm.
The complete holdout file still contains all 1,212 original and earlier owners.

- [Protocol and fitting policy](../../docs/available-premises-protocol.md)
- [Portable reproduction and analysis](../../docs/reproducing-available-premises.md)
- [Admission evidence](admission.json)
- [Native isolation, reference-fit parity and engine validation](../../docs/available-premises-validation.json)

No statistics are fitted from the current-file prefix in the strict arm. It fits
only imported Mathlib signatures; earlier current-file premises are available
through live retrieval. Jev and neural-selector pretraining overlap remain
unknown. This study only removes the CPU selector's unavailable-statement
exposure, not every possible source of contamination in the full stack.
