# B2C Single Fulfilment (B2C-SF)

The reference commerce pattern on ION. Consumer buys a physical product; delivery or self-pickup follows. Every other spine is defined as a delta from this one.

## Applicable categories
Food & Beverage, Grocery, Fashion, Electronics, Beauty, FMCG, Home & Kitchen, Agritech (consumer-facing)

## API sequence
```
Phase 1  BPP → publish_catalog → ION Catalogue Service
         ION Catalogue Service → on_discover → BAP

Phase 2  BAP → select  → BPP → on_select
         BAP → init    → BPP → on_init
         BAP → confirm → BPP → on_confirm

Phase 3  BPP → on_status [PACKED]
         BPP → on_status [DISPATCHED]        ← AWB + trackingUrl added
         BPP → on_status [OUT_FOR_DELIVERY]
         BPP → on_status [DELIVERED]         ← Contract COMPLETE
```

## Performance state machine
`performance-states/v1/states.yaml#standard`

## Available branches
All branches available. See `flows/trade/README.md` for the complete branch map.

## Key fields introduced
`resourceStructure`, `resourceTangibility`, `availability.status` (signal only — no stock count), `cancellationPolicy`, `returnPolicy`, `warrantyPolicy`, `disputePolicy`, `provinsiCode`, `deliveryOtp`, `fulfillingLocationId`
