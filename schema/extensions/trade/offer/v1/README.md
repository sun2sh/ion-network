# trade/offer/v1

Terms of sale — cancellation, returns, warranties, COD, promotions.

## Attaches to
`beckn:Offer.offerAttributes`

## Policy IRIs
ION uses IRI-encoded policy identifiers for canonical terms:

### Return policies
- `ion://policy/return.7d.sellerpays` — 7-day return, seller arranges pickup
- `ion://policy/return.15d.sellerpays` — 15-day return, seller pays
- `ion://policy/return.7d.buyerpays` — 7-day return, buyer ships back
- `ion://policy/return/standard/none` — no returns

### Cancellation policies
- `ion://policy/cancel/prepacked/free` — free cancellation before packed
- `ion://policy/cancel/mto/nofee-before-prepare` — MTO free before preparation
- `ion://policy/cancel/standard/none` — no cancellation

### Warranty policies
- `ion://policy/warranty.1y.manufacturer`
- `ion://policy/warranty.2y.manufacturer`
- `ion://policy/warranty/standard/none`

### Dispute policies
- `ion://policy/dispute/consumer/bpsk` — B2C via BPSK
- `ion://policy/dispute/commercial/bani` — B2B via BANI arbitration
