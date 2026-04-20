# Marketplace Inventory Less (MP-IL)

3P marketplace. Each seller is an independent BPP. Marketplace is the BAP.

## Architecture
```
Consumer → Marketplace BAP
           Seller A BPP (own stock, own fulfilment)
           Seller B BPP (own stock, own fulfilment)
```
Marketplace routes consumer's order to the specific seller BPP.


## Performance state machine
`performance-states/v1/states.yaml#standard`
Each seller BPP manages its own state machine independently.

## Key differences from B2C-SF
- Many BPPs — each seller = one BPP
- Marketplace aggregates multi-BPP catalog in own discovery layer
- `collectedBy = BAP` (marketplace collects from consumer, settles to seller)
- `PLATFORM_FEE` consideration line: marketplace commission deducted in reconcile
- `buyerFinderFeeAmount` in reconcile = marketplace commission
- Post-order: consumer communicates with marketplace; marketplace relays to BPP
- Dispute: marketplace intervenes if seller non-responsive (raise → ION escalation)
