# Exception Branch

Damage, loss, address-unserviceable, and pickup-failed scenarios.

## Applies to
LOG-PARCEL, LOG-FREIGHT, LOG-HYPERLOCAL, LOG-XB.

## Sub-branches
`damage-claim`, `loss-claim`, `address-unserviceable`, `pickup-failed`.

## Dispute flow
All claims flow through `/update` with policy IRI referencing the applicable claim policy. Evidence is mandatory per the `evidencePolicy` IRI on the offer. Escalation to `/raise` after policy-defined SLA.

## Attribution
For `pickup-failed`, `failureAttribution` (CONSIGNOR_FAULT, LSP_FAULT, FORCE_MAJEURE) determines if a fee is charged per policy.
