# COD Branch

Cash-on-delivery collection, refusal handling, and remittance.

## Applies to
LOG-PARCEL, LOG-HYPERLOCAL.

## Trigger
`offer.availableOnCod = true` AND `settlement.collectedBy = BPP` AND `settlement.method = COD`.

## Sub-branches
`cod-collection` (successful), `cod-refusal` (buyer refuses), `cod-partial-collection` (rare — partial payment), `cod-remittance` (LSP remits to BAP).

## Remittance
Scheduled per `offer.codPolicy` IRI (weekly, bi-weekly). LSP holds funds until remittance date. Remittance breach triggers `penalty.cod-remittance-late` policy.
