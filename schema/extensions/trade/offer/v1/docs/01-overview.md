# Trade Offer Extension — Overview

Terms of sale. Every commercial condition a buyer needs to know before committing to purchase.

## Policy IRIs
ION encodes standard policies as IRI strings — not freeform text. This enables machine-readable policy enforcement:
- `ion://policy/return.7d.sellerpays` — 7-day return, seller pays pickup
- `ion://policy/cancel/prepacked/free` — free cancellation before packed
- `ion://policy/warranty.1y.manufacturer` — 1-year manufacturer warranty
- `ion://policy/dispute/consumer/bpsk` — consumer dispute via BPSK
- `ion://policy/dispute/commercial/bani` — commercial dispute via BANI

## returnAllowedReasons
DEFECTIVE and DAMAGED_IN_TRANSIT are always implied by UU 8/1999 regardless of what this list says. The list declares additional reasons the seller accepts — CHANGE_OF_MIND, WRONG_ITEM_SENT etc.

## Promotions
`offerType = DISCOUNT/BUNDLE/CASHBACK/VOUCHER`, `voucherCode`, `stackable`, `subsidyBreakup` (which party funds the promotion: seller, platform, or brand).
