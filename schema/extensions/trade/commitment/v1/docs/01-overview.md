# Trade Commitment Extension — Overview

Per-line item details within a contract. One Commitment per item line.

## lineId
Assigned by BAP at select. Persists through the entire lifecycle. Used to reference specific lines in partial cancellations, line-level returns, and price adjustments. Never reassigned.

## Locked price
`price.value` is locked at `on_select`. It does not change unless a `price-adjustment` branch is triggered. This is the source of truth for per-line amounts in reconciliation.

## customisationSelections
For COMPOSED and WITH_EXTRAS resources — records exactly what the buyer chose from each customisationGroup. Enables the seller to prepare the exact variant requested and the BPP to compute the correct price including priceDelta values.
